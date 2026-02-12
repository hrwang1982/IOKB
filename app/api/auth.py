"""
认证与用户管理 API
"""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.auth.user_service import user_service
from app.auth.rbac import role_service, permission_service
from app.auth.jwt import jwt_service
from app.auth.dependencies import get_current_user

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ==================== 数据模型 ====================

class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: Optional[str] = None
    display_name: Optional[str] = None


class UserCreate(UserBase):
    """创建用户请求"""
    password: str
    role_codes: Optional[List[str]] = None


class UserUpdate(BaseModel):
    """更新用户请求"""
    email: Optional[str] = None
    display_name: Optional[str] = None
    status: Optional[str] = None


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    status: str
    roles: List[str] = []
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class PasswordChange(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str


class PasswordReset(BaseModel):
    """重置密码请求"""
    new_password: str


class StatusUpdate(BaseModel):
    """状态更新请求"""
    status: str


class RoleBase(BaseModel):
    """角色基础模型"""
    name: str
    code: str
    description: Optional[str] = None


class RoleResponse(RoleBase):
    """角色响应"""
    id: int

    class Config:
        from_attributes = True


class PermissionResponse(BaseModel):
    """权限响应"""
    id: int
    code: str
    name: str
    module: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== 辅助函数 ====================

def _user_to_response(user) -> dict:
    """将User模型转为响应字典"""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "display_name": user.display_name,
        "status": user.status,
        "roles": [r.code for r in user.roles] if user.roles else [],
        "last_login_at": user.last_login_at,
        "created_at": user.created_at,
    }


# ==================== API 路由 ====================

@router.post("/login", summary="用户登录")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_session),
):
    """
    用户登录获取Token

    - **username**: 用户名
    - **password**: 密码
    """
    result = await user_service.authenticate(db, form_data.username, form_data.password)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return result


@router.post("/refresh", summary="刷新Token")
async def refresh_token(refresh_token: str):
    """使用refresh_token刷新access_token"""
    result = jwt_service.refresh_access_token(refresh_token)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌",
        )
    return result


@router.post("/logout", summary="用户登出")
async def logout(token: str = Depends(oauth2_scheme)):
    """用户登出，使Token失效"""
    # JWT是无状态的，客户端删除token即可
    return {"message": "登出成功"}


@router.get("/me", summary="获取当前用户信息")
async def get_me(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """获取当前登录用户信息"""
    user = await user_service.get_by_id(db, int(current_user.sub))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    return _user_to_response(user)


@router.put("/me/password", summary="修改密码")
async def change_password(
    password_data: PasswordChange,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """修改当前用户密码"""
    success = await user_service.change_password(
        db,
        int(current_user.sub),
        password_data.old_password,
        password_data.new_password,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误",
        )
    return {"message": "密码修改成功"}


# ==================== 用户管理 (管理员) ====================

@router.get("/users", summary="获取用户列表")
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme),
):
    """获取用户列表（需要管理员权限）"""
    offset = (page - 1) * size
    users, total = await user_service.list(
        db,
        status=status_filter,
        keyword=keyword,
        offset=offset,
        limit=size,
    )

    return {
        "items": [_user_to_response(u) for u in users],
        "total": total,
        "page": page,
        "size": size,
    }


@router.post("/users", summary="创建用户")
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme),
):
    """创建新用户（需要管理员权限）"""
    try:
        user = await user_service.create(
            db,
            username=user_data.username,
            password=user_data.password,
            email=user_data.email,
            display_name=user_data.display_name,
        )

        # 分配角色
        if user_data.role_codes:
            for role_code in user_data.role_codes:
                role = await role_service.get_by_code(db, role_code)
                if role:
                    await user_service.assign_role(db, user.id, role.id)

        # 重新查询以获取完整关系数据
        user = await user_service.get_by_id(db, user.id)
        return _user_to_response(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/users/{user_id}", summary="获取用户详情")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme),
):
    """获取指定用户详情"""
    user = await user_service.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    return _user_to_response(user)


@router.put("/users/{user_id}", summary="更新用户信息")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme),
):
    """更新用户信息"""
    user = await user_service.update(
        db,
        user_id=user_id,
        email=user_data.email,
        display_name=user_data.display_name,
        status=user_data.status,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    return _user_to_response(user)


@router.put("/users/{user_id}/status", summary="切换用户状态")
async def update_user_status(
    user_id: int,
    status_data: StatusUpdate,
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme),
):
    """启用/禁用用户"""
    if status_data.status not in ("active", "disabled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="状态值只能是 active 或 disabled",
        )
    user = await user_service.update(db, user_id=user_id, status=status_data.status)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    return _user_to_response(user)


@router.put("/users/{user_id}/password", summary="重置用户密码")
async def reset_user_password(
    user_id: int,
    password_data: PasswordReset,
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme),
):
    """管理员重置用户密码"""
    success = await user_service.reset_password(db, user_id, password_data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    return {"message": "密码重置成功"}


@router.delete("/users/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme),
):
    """删除用户（需要管理员权限）"""
    success = await user_service.delete(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    return {"message": f"用户 {user_id} 已删除"}


# ==================== 角色管理 ====================

@router.get("/roles", summary="获取角色列表")
async def list_roles(
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme),
):
    """获取所有角色"""
    roles = await role_service.list(db)
    return {
        "items": [
            {
                "id": r.id,
                "name": r.name,
                "code": r.code,
                "description": r.description,
                "permissions": [p.code for p in r.permissions] if r.permissions else [],
            }
            for r in roles
        ]
    }


@router.post("/roles", summary="创建角色")
async def create_role(
    role: RoleBase,
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme),
):
    """创建新角色"""
    try:
        new_role = await role_service.create(db, code=role.code, name=role.name, description=role.description)
        return {"id": new_role.id, "name": new_role.name, "code": new_role.code, "description": new_role.description}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/roles/{role_id}/permissions", summary="获取角色权限")
async def get_role_permissions(
    role_id: int,
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme),
):
    """获取角色的权限列表"""
    role = await role_service.get_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    return {
        "role_id": role_id,
        "permissions": [
            {"id": p.id, "code": p.code, "name": p.name, "module": p.module, "description": p.description}
            for p in role.permissions
        ],
    }


@router.put("/roles/{role_id}/permissions", summary="设置角色权限")
async def set_role_permissions(
    role_id: int,
    permission_ids: list[int],
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme),
):
    """设置角色的权限"""
    role = await role_service.get_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    # 清除现有权限，重新分配
    role.permissions.clear()
    await db.flush()

    for pid in permission_ids:
        await role_service.assign_permission(db, role_id, pid)

    return {"message": "权限更新成功"}


# ==================== 权限管理 ====================

@router.get("/permissions", summary="获取权限列表")
async def list_permissions(
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme),
):
    """获取所有权限"""
    permissions = await permission_service.list(db)
    return {
        "items": [
            {"id": p.id, "code": p.code, "name": p.name, "module": p.module, "description": p.description}
            for p in permissions
        ]
    }
