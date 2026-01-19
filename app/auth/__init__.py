"""
认证与授权模块
"""

from app.auth.config import (
    auth_config,
    get_auth_config,
    reload_auth_config,
    validate_password,
    AuthConfig,
)
from app.auth.jwt import (
    jwt_service,
    password_service,
    JWTService,
    PasswordService,
    TokenPayload,
)
from app.auth.user_service import user_service, UserService
from app.auth.rbac import (
    role_service,
    permission_service,
    rbac_initializer,
    RoleService,
    PermissionService,
    PRESET_ROLES,
    PRESET_PERMISSIONS,
)
from app.auth.dependencies import (
    get_current_user,
    require_permissions,
    require_roles,
    require_admin,
    AuthDependency,
    kb_read, kb_write, kb_admin,
    cmdb_read, cmdb_write, cmdb_admin,
    alert_read, alert_write, alert_admin,
    user_read, user_admin,
)
from app.auth.ldap import ldap_service, sso_service, LDAPService, SSOService

__all__ = [
    # JWT
    "jwt_service",
    "password_service",
    "JWTService",
    "PasswordService",
    "TokenPayload",
    # 用户服务
    "user_service",
    "UserService",
    # RBAC
    "role_service",
    "permission_service",
    "rbac_initializer",
    "RoleService",
    "PermissionService",
    "PRESET_ROLES",
    "PRESET_PERMISSIONS",
    # 认证依赖
    "get_current_user",
    "require_permissions",
    "require_roles",
    "require_admin",
    "AuthDependency",
    "kb_read", "kb_write", "kb_admin",
    "cmdb_read", "cmdb_write", "cmdb_admin",
    "alert_read", "alert_write", "alert_admin",
    "user_read", "user_admin",
    # LDAP/SSO
    "ldap_service",
    "sso_service",
    "LDAPService",
    "SSOService",
]
