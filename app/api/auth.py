"""
认证与用户管理 API
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ==================== 数据模型 ====================

class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: Optional[EmailStr] = None
    
    
class UserCreate(UserBase):
    """创建用户请求"""
    password: str


class UserResponse(UserBase):
    """用户响应"""
    id: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token数据"""
    username: Optional[str] = None
    user_id: Optional[int] = None


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class PasswordChange(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str


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
    resource: str
    action: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


# ==================== API 路由 ====================

@router.post("/login", response_model=Token, summary="用户登录")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    用户登录获取Token
    
    - **username**: 用户名
    - **password**: 密码
    """
    # TODO: 实现实际的用户验证逻辑
    # 临时返回模拟数据
    return Token(
        access_token="mock_access_token",
        refresh_token="mock_refresh_token",
        expires_in=1800
    )


@router.post("/refresh", response_model=Token, summary="刷新Token")
async def refresh_token(refresh_token: str):
    """使用refresh_token刷新access_token"""
    # TODO: 实现Token刷新逻辑
    return Token(
        access_token="new_mock_access_token",
        refresh_token="new_mock_refresh_token",
        expires_in=1800
    )


@router.post("/logout", summary="用户登出")
async def logout(token: str = Depends(oauth2_scheme)):
    """用户登出，使Token失效"""
    # TODO: 实现Token失效逻辑
    return {"message": "登出成功"}


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """获取当前登录用户信息"""
    # TODO: 从Token解析用户信息
    return UserResponse(
        id=1,
        username="admin",
        email="admin@example.com",
        status="active",
        created_at=datetime.now()
    )


@router.put("/me/password", summary="修改密码")
async def change_password(
    password_data: PasswordChange,
    token: str = Depends(oauth2_scheme)
):
    """修改当前用户密码"""
    # TODO: 实现密码修改逻辑
    return {"message": "密码修改成功"}


# ==================== 用户管理 (管理员) ====================

@router.get("/users", summary="获取用户列表")
async def list_users(
    page: int = 1,
    size: int = 20,
    token: str = Depends(oauth2_scheme)
):
    """获取用户列表（需要管理员权限）"""
    # TODO: 实现分页查询用户
    return {
        "items": [],
        "total": 0,
        "page": page,
        "size": size
    }


@router.post("/users", response_model=UserResponse, summary="创建用户")
async def create_user(
    user: UserCreate,
    token: str = Depends(oauth2_scheme)
):
    """创建新用户（需要管理员权限）"""
    # TODO: 实现用户创建逻辑
    return UserResponse(
        id=1,
        username=user.username,
        email=user.email,
        status="active",
        created_at=datetime.now()
    )


@router.get("/users/{user_id}", response_model=UserResponse, summary="获取用户详情")
async def get_user(user_id: int, token: str = Depends(oauth2_scheme)):
    """获取指定用户详情"""
    # TODO: 查询用户
    return UserResponse(
        id=user_id,
        username="user",
        email="user@example.com",
        status="active",
        created_at=datetime.now()
    )


@router.delete("/users/{user_id}", summary="删除用户")
async def delete_user(user_id: int, token: str = Depends(oauth2_scheme)):
    """删除用户（需要管理员权限）"""
    # TODO: 实现用户删除逻辑
    return {"message": f"用户 {user_id} 已删除"}


# ==================== 角色管理 ====================

@router.get("/roles", summary="获取角色列表")
async def list_roles(token: str = Depends(oauth2_scheme)):
    """获取所有角色"""
    # TODO: 查询角色列表
    return {
        "items": [
            {"id": 1, "name": "系统管理员", "code": "admin"},
            {"id": 2, "name": "运维工程师", "code": "operator"},
            {"id": 3, "name": "知识库管理员", "code": "kb_admin"},
            {"id": 4, "name": "只读用户", "code": "viewer"},
        ]
    }


@router.post("/roles", response_model=RoleResponse, summary="创建角色")
async def create_role(role: RoleBase, token: str = Depends(oauth2_scheme)):
    """创建新角色"""
    # TODO: 实现角色创建
    return RoleResponse(id=1, **role.model_dump())


@router.get("/roles/{role_id}/permissions", summary="获取角色权限")
async def get_role_permissions(role_id: int, token: str = Depends(oauth2_scheme)):
    """获取角色的权限列表"""
    # TODO: 查询角色权限
    return {"role_id": role_id, "permissions": []}


@router.put("/roles/{role_id}/permissions", summary="设置角色权限")
async def set_role_permissions(
    role_id: int,
    permission_ids: list[int],
    token: str = Depends(oauth2_scheme)
):
    """设置角色的权限"""
    # TODO: 更新角色权限
    return {"message": "权限更新成功"}


# ==================== 权限管理 ====================

@router.get("/permissions", summary="获取权限列表")
async def list_permissions(token: str = Depends(oauth2_scheme)):
    """获取所有权限"""
    return {
        "items": [
            {"id": 1, "resource": "knowledge", "action": "read", "description": "知识库-读取"},
            {"id": 2, "resource": "knowledge", "action": "write", "description": "知识库-写入"},
            {"id": 3, "resource": "cmdb", "action": "read", "description": "CMDB-读取"},
            {"id": 4, "resource": "cmdb", "action": "write", "description": "CMDB-写入"},
            {"id": 5, "resource": "alert", "action": "read", "description": "告警-读取"},
            {"id": 6, "resource": "alert", "action": "handle", "description": "告警-处理"},
        ]
    }
