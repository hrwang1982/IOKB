"""
认证依赖
FastAPI依赖注入，用于路由鉴权
"""

from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.jwt import jwt_service, TokenPayload


# HTTP Bearer认证
security = HTTPBearer()


class AuthDependency:
    """认证依赖"""
    
    def __init__(self, required_permissions: List[str] = None):
        self.required_permissions = required_permissions or []
    
    async def __call__(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> TokenPayload:
        """验证令牌"""
        token = credentials.credentials
        
        # 验证JWT
        payload = jwt_service.verify_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if payload.token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌类型错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 检查权限
        if self.required_permissions:
            user_permissions = set(payload.permissions)
            # 管理员拥有所有权限
            if "admin" not in payload.roles:
                for perm in self.required_permissions:
                    if perm not in user_permissions:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"缺少权限: {perm}",
                        )
        
        return payload


# 常用依赖实例
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenPayload:
    """获取当前用户（仅验证登录）"""
    token = credentials.credentials
    payload = jwt_service.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if payload.token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌类型错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


def require_permissions(*permissions: str):
    """需要指定权限"""
    return AuthDependency(required_permissions=list(permissions))


def require_roles(*roles: str):
    """需要指定角色"""
    async def check_roles(
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> TokenPayload:
        token = credentials.credentials
        payload = jwt_service.verify_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌",
            )
        
        user_roles = set(payload.roles)
        required_roles = set(roles)
        
        if not user_roles & required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要角色: {', '.join(roles)}",
            )
        
        return payload
    
    return check_roles


def require_admin():
    """需要管理员角色"""
    return require_roles("admin")


# 权限检查快捷方式
kb_read = require_permissions("kb:read")
kb_write = require_permissions("kb:create", "kb:update")
kb_admin = require_permissions("kb:admin")

cmdb_read = require_permissions("cmdb:read")
cmdb_write = require_permissions("cmdb:create", "cmdb:update")
cmdb_admin = require_permissions("cmdb:admin")

alert_read = require_permissions("alert:read")
alert_write = require_permissions("alert:ack", "alert:resolve")
alert_admin = require_permissions("alert:admin")

user_read = require_permissions("user:read")
user_admin = require_permissions("user:admin")
