"""
Auth模块配置管理
从YAML配置文件加载配置
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from loguru import logger


@dataclass
class JWTConfig:
    """JWT配置"""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


@dataclass
class PasswordConfig:
    """密码策略配置"""
    min_length: int = 8
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digit: bool = True
    require_special: bool = False
    special_chars: str = "!@#$%^&*()_+-="


@dataclass
class LDAPConfig:
    """LDAP配置"""
    enabled: bool = False
    user_filter: str = "(uid={username})"
    group_filter: str = "(member={dn})"
    sync_interval_minutes: int = 60
    auto_create_user: bool = True
    default_role: str = "viewer"
    group_role_mapping: Dict[str, str] = field(default_factory=dict)


@dataclass
class SSOConfig:
    """SSO配置"""
    enabled: bool = False
    provider: str = "oauth2"
    auto_create_user: bool = True
    default_role: str = "viewer"
    attribute_mapping: Dict[str, str] = field(default_factory=lambda: {
        "username": "preferred_username",
        "email": "email",
        "display_name": "name",
        "groups": "groups",
    })


@dataclass
class SessionConfig:
    """会话配置"""
    max_sessions_per_user: int = 5
    idle_timeout_minutes: int = 30
    absolute_timeout_hours: int = 24


@dataclass
class SecurityConfig:
    """安全配置"""
    login_attempts_limit: int = 5
    lockout_duration_minutes: int = 15
    require_2fa: bool = False


@dataclass
class PermissionDef:
    """权限定义"""
    code: str
    name: str
    module: str = ""
    description: str = ""


@dataclass
class RoleDef:
    """角色定义"""
    code: str
    name: str
    description: str = ""
    permissions: List[str] = field(default_factory=list)


@dataclass
class AuthConfig:
    """Auth模块完整配置"""
    jwt: JWTConfig = field(default_factory=JWTConfig)
    password: PasswordConfig = field(default_factory=PasswordConfig)
    ldap: LDAPConfig = field(default_factory=LDAPConfig)
    sso: SSOConfig = field(default_factory=SSOConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    permissions: List[PermissionDef] = field(default_factory=list)
    roles: List[RoleDef] = field(default_factory=list)


class AuthConfigLoader:
    """Auth配置加载器"""
    
    DEFAULT_CONFIG_PATHS = [
        "config/auth.yaml",
        "config/auth.yml",
        "../config/auth.yaml",
        "/etc/skb/auth.yaml",
    ]
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self._config: Optional[AuthConfig] = None
        self._raw_config: Dict[str, Any] = {}
    
    def _find_config_file(self) -> Optional[str]:
        """查找配置文件"""
        if self.config_path and os.path.exists(self.config_path):
            return self.config_path
        
        base_dir = Path(__file__).parent.parent.parent
        
        for path in self.DEFAULT_CONFIG_PATHS:
            full_path = base_dir / path
            if full_path.exists():
                return str(full_path)
        
        return None
    
    def _load_yaml(self) -> Dict[str, Any]:
        """加载YAML配置"""
        config_file = self._find_config_file()
        
        if not config_file:
            logger.warning("未找到Auth配置文件，使用默认配置")
            return {}
        
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                logger.info(f"加载Auth配置文件: {config_file}")
                return data or {}
        except Exception as e:
            logger.error(f"加载Auth配置文件失败: {e}")
            return {}
    
    def load(self) -> AuthConfig:
        """加载配置"""
        if self._config is not None:
            return self._config
        
        self._raw_config = self._load_yaml()
        
        # JWT配置
        jwt_data = self._raw_config.get("jwt", {})
        jwt = JWTConfig(
            algorithm=jwt_data.get("algorithm", "HS256"),
            access_token_expire_minutes=jwt_data.get("access_token_expire_minutes", 30),
            refresh_token_expire_days=jwt_data.get("refresh_token_expire_days", 7),
        )
        
        # 密码策略
        pwd_data = self._raw_config.get("password", {})
        password = PasswordConfig(
            min_length=pwd_data.get("min_length", 8),
            require_uppercase=pwd_data.get("require_uppercase", True),
            require_lowercase=pwd_data.get("require_lowercase", True),
            require_digit=pwd_data.get("require_digit", True),
            require_special=pwd_data.get("require_special", False),
            special_chars=pwd_data.get("special_chars", "!@#$%^&*()_+-="),
        )
        
        # LDAP配置
        ldap_data = self._raw_config.get("ldap", {})
        ldap = LDAPConfig(
            enabled=ldap_data.get("enabled", False),
            user_filter=ldap_data.get("user_filter", "(uid={username})"),
            group_filter=ldap_data.get("group_filter", "(member={dn})"),
            sync_interval_minutes=ldap_data.get("sync_interval_minutes", 60),
            auto_create_user=ldap_data.get("auto_create_user", True),
            default_role=ldap_data.get("default_role", "viewer"),
            group_role_mapping=ldap_data.get("group_role_mapping", {}),
        )
        
        # SSO配置
        sso_data = self._raw_config.get("sso", {})
        sso = SSOConfig(
            enabled=sso_data.get("enabled", False),
            provider=sso_data.get("provider", "oauth2"),
            auto_create_user=sso_data.get("auto_create_user", True),
            default_role=sso_data.get("default_role", "viewer"),
            attribute_mapping=sso_data.get("attribute_mapping", {
                "username": "preferred_username",
                "email": "email",
                "display_name": "name",
                "groups": "groups",
            }),
        )
        
        # 会话配置
        session_data = self._raw_config.get("session", {})
        session = SessionConfig(
            max_sessions_per_user=session_data.get("max_sessions_per_user", 5),
            idle_timeout_minutes=session_data.get("idle_timeout_minutes", 30),
            absolute_timeout_hours=session_data.get("absolute_timeout_hours", 24),
        )
        
        # 安全配置
        security_data = self._raw_config.get("security", {})
        security = SecurityConfig(
            login_attempts_limit=security_data.get("login_attempts_limit", 5),
            lockout_duration_minutes=security_data.get("lockout_duration_minutes", 15),
            require_2fa=security_data.get("require_2fa", False),
        )
        
        # 权限定义
        permissions = []
        for perm_data in self._raw_config.get("permissions", []):
            permissions.append(PermissionDef(
                code=perm_data.get("code", ""),
                name=perm_data.get("name", ""),
                module=perm_data.get("module", ""),
                description=perm_data.get("description", ""),
            ))
        
        # 角色定义
        roles = []
        for role_data in self._raw_config.get("roles", []):
            roles.append(RoleDef(
                code=role_data.get("code", ""),
                name=role_data.get("name", ""),
                description=role_data.get("description", ""),
                permissions=role_data.get("permissions", []),
            ))
        
        self._config = AuthConfig(
            jwt=jwt,
            password=password,
            ldap=ldap,
            sso=sso,
            session=session,
            security=security,
            permissions=permissions,
            roles=roles,
        )
        
        return self._config
    
    def reload(self) -> AuthConfig:
        """重新加载配置"""
        self._config = None
        self._raw_config = {}
        return self.load()
    
    def get_raw_config(self) -> Dict[str, Any]:
        """获取原始配置"""
        if not self._raw_config:
            self._raw_config = self._load_yaml()
        return self._raw_config


# 创建全局配置加载器和配置对象
auth_config_loader = AuthConfigLoader()
auth_config = auth_config_loader.load()


def get_auth_config() -> AuthConfig:
    """获取Auth配置"""
    return auth_config


def reload_auth_config() -> AuthConfig:
    """重新加载Auth配置"""
    global auth_config
    auth_config = auth_config_loader.reload()
    return auth_config


def validate_password(password: str) -> tuple[bool, str]:
    """验证密码是否符合策略"""
    config = auth_config.password
    
    if len(password) < config.min_length:
        return False, f"密码长度不能少于{config.min_length}位"
    
    if config.require_uppercase and not any(c.isupper() for c in password):
        return False, "密码必须包含大写字母"
    
    if config.require_lowercase and not any(c.islower() for c in password):
        return False, "密码必须包含小写字母"
    
    if config.require_digit and not any(c.isdigit() for c in password):
        return False, "密码必须包含数字"
    
    if config.require_special and not any(c in config.special_chars for c in password):
        return False, f"密码必须包含特殊字符({config.special_chars})"
    
    return True, ""
