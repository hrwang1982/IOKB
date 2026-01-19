"""
用户权限相关数据模型
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """SQLAlchemy基类"""
    pass


class Tenant(Base):
    """租户表"""
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="租户名称")
    code = Column(String(50), unique=True, nullable=False, comment="租户编码")
    status = Column(String(20), default="active", comment="状态")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    users = relationship("User", back_populates="tenant")


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    email = Column(String(100), comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    status = Column(String(20), default="active", comment="状态(active/disabled)")
    last_login = Column(DateTime, comment="最后登录时间")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    tenant = relationship("Tenant", back_populates="users")
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")


class Role(Base):
    """角色表"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    name = Column(String(50), nullable=False, comment="角色名称")
    code = Column(String(50), nullable=False, comment="角色编码")
    description = Column(String(200), comment="角色描述")
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    users = relationship("User", secondary="user_roles", back_populates="roles")
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")


class UserRole(Base):
    """用户角色关联表"""
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)


class Permission(Base):
    """权限表"""
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    resource = Column(String(50), nullable=False, comment="资源标识")
    action = Column(String(20), nullable=False, comment="操作类型")
    description = Column(String(200), comment="权限描述")
    
    # 关系
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")


class RolePermission(Base):
    """角色权限关联表"""
    __tablename__ = "role_permissions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)


class AuditLog(Base):
    """操作审计日志表"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False, comment="操作类型")
    resource = Column(String(100), comment="操作资源")
    resource_id = Column(String(50), comment="资源ID")
    details = Column(JSON, comment="详细信息")
    ip_address = Column(String(50), comment="IP地址")
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    user = relationship("User", back_populates="audit_logs")


class APIKey(Base):
    """API密钥表"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False, comment="密钥名称")
    key_hash = Column(String(255), nullable=False, comment="密钥哈希")
    prefix = Column(String(10), nullable=False, comment="密钥前缀(用于识别)")
    expires_at = Column(DateTime, comment="过期时间")
    last_used_at = Column(DateTime, comment="最后使用时间")
    status = Column(String(20), default="active", comment="状态")
    created_at = Column(DateTime, default=datetime.now)
