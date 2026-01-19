"""
JWT认证服务
生成和验证JWT令牌
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from loguru import logger
from passlib.context import CryptContext

from app.config import settings


# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordService:
    """密码服务"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """加密密码"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)


class TokenPayload:
    """Token载荷"""
    
    def __init__(
        self,
        sub: str,  # 用户ID
        username: str,
        roles: list = None,
        permissions: list = None,
        exp: datetime = None,
        iat: datetime = None,
        token_type: str = "access",
    ):
        self.sub = sub
        self.username = username
        self.roles = roles or []
        self.permissions = permissions or []
        self.exp = exp
        self.iat = iat or datetime.utcnow()
        self.token_type = token_type
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "sub": self.sub,
            "username": self.username,
            "roles": self.roles,
            "permissions": self.permissions,
            "exp": self.exp.timestamp() if self.exp else None,
            "iat": self.iat.timestamp() if self.iat else None,
            "token_type": self.token_type,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenPayload":
        """从字典创建"""
        exp = data.get("exp")
        iat = data.get("iat")
        return cls(
            sub=data.get("sub", ""),
            username=data.get("username", ""),
            roles=data.get("roles", []),
            permissions=data.get("permissions", []),
            exp=datetime.fromtimestamp(exp) if exp else None,
            iat=datetime.fromtimestamp(iat) if iat else None,
            token_type=data.get("token_type", "access"),
        )


class JWTService:
    """JWT服务"""
    
    def __init__(
        self,
        secret_key: str = None,
        algorithm: str = None,
        access_token_expire_minutes: int = None,
        refresh_token_expire_days: int = None,
    ):
        self.secret_key = secret_key or settings.jwt_secret_key
        self.algorithm = algorithm or settings.jwt_algorithm
        self.access_token_expire_minutes = (
            access_token_expire_minutes or settings.jwt_access_token_expire_minutes
        )
        self.refresh_token_expire_days = (
            refresh_token_expire_days or settings.jwt_refresh_token_expire_days
        )
    
    def create_access_token(
        self,
        user_id: str,
        username: str,
        roles: list = None,
        permissions: list = None,
        expires_delta: timedelta = None,
    ) -> str:
        """创建访问令牌"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = TokenPayload(
            sub=str(user_id),
            username=username,
            roles=roles or [],
            permissions=permissions or [],
            exp=expire,
            token_type="access",
        )
        
        encoded_jwt = jwt.encode(
            payload.to_dict(),
            self.secret_key,
            algorithm=self.algorithm,
        )
        return encoded_jwt
    
    def create_refresh_token(
        self,
        user_id: str,
        username: str,
        expires_delta: timedelta = None,
    ) -> str:
        """创建刷新令牌"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        payload = TokenPayload(
            sub=str(user_id),
            username=username,
            exp=expire,
            token_type="refresh",
        )
        
        encoded_jwt = jwt.encode(
            payload.to_dict(),
            self.secret_key,
            algorithm=self.algorithm,
        )
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenPayload]:
        """验证令牌"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            return TokenPayload.from_dict(payload)
        except JWTError as e:
            logger.warning(f"JWT验证失败: {e}")
            return None
    
    def create_token_pair(
        self,
        user_id: str,
        username: str,
        roles: list = None,
        permissions: list = None,
    ) -> Dict[str, str]:
        """创建令牌对（访问令牌+刷新令牌）"""
        access_token = self.create_access_token(
            user_id=user_id,
            username=username,
            roles=roles,
            permissions=permissions,
        )
        refresh_token = self.create_refresh_token(
            user_id=user_id,
            username=username,
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60,
        }
    
    def refresh_access_token(
        self,
        refresh_token: str,
        roles: list = None,
        permissions: list = None,
    ) -> Optional[Dict[str, str]]:
        """使用刷新令牌获取新的访问令牌"""
        payload = self.verify_token(refresh_token)
        
        if not payload:
            return None
        
        if payload.token_type != "refresh":
            logger.warning("尝试使用非刷新令牌刷新")
            return None
        
        # 创建新的访问令牌
        access_token = self.create_access_token(
            user_id=payload.sub,
            username=payload.username,
            roles=roles or payload.roles,
            permissions=permissions or payload.permissions,
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60,
        }


# 创建全局服务实例
password_service = PasswordService()
jwt_service = JWTService()
