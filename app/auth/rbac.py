"""
RBAC权限服务
角色和权限管理
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import Role, Permission


# 预定义权限
PRESET_PERMISSIONS = [
    # 知识库权限
    {"code": "kb:read", "name": "知识库查看", "module": "knowledge", "description": "查看知识库文档"},
    {"code": "kb:create", "name": "知识库创建", "module": "knowledge", "description": "创建知识库文档"},
    {"code": "kb:update", "name": "知识库编辑", "module": "knowledge", "description": "编辑知识库文档"},
    {"code": "kb:delete", "name": "知识库删除", "module": "knowledge", "description": "删除知识库文档"},
    {"code": "kb:admin", "name": "知识库管理", "module": "knowledge", "description": "管理知识库设置"},
    
    # CMDB权限
    {"code": "cmdb:read", "name": "CMDB查看", "module": "cmdb", "description": "查看配置项"},
    {"code": "cmdb:create", "name": "CMDB创建", "module": "cmdb", "description": "创建配置项"},
    {"code": "cmdb:update", "name": "CMDB编辑", "module": "cmdb", "description": "编辑配置项"},
    {"code": "cmdb:delete", "name": "CMDB删除", "module": "cmdb", "description": "删除配置项"},
    {"code": "cmdb:admin", "name": "CMDB管理", "module": "cmdb", "description": "管理CMDB设置"},
    
    # 告警权限
    {"code": "alert:read", "name": "告警查看", "module": "alert", "description": "查看告警"},
    {"code": "alert:ack", "name": "告警确认", "module": "alert", "description": "确认告警"},
    {"code": "alert:resolve", "name": "告警处理", "module": "alert", "description": "处理告警"},
    {"code": "alert:admin", "name": "告警管理", "module": "alert", "description": "管理告警设置"},
    
    # 用户权限
    {"code": "user:read", "name": "用户查看", "module": "user", "description": "查看用户列表"},
    {"code": "user:create", "name": "用户创建", "module": "user", "description": "创建用户"},
    {"code": "user:update", "name": "用户编辑", "module": "user", "description": "编辑用户"},
    {"code": "user:delete", "name": "用户删除", "module": "user", "description": "删除用户"},
    {"code": "user:admin", "name": "用户管理", "module": "user", "description": "管理用户权限"},
    
    # 系统权限
    {"code": "system:config", "name": "系统配置", "module": "system", "description": "修改系统配置"},
    {"code": "system:audit", "name": "审计日志", "module": "system", "description": "查看审计日志"},
    {"code": "system:admin", "name": "系统管理", "module": "system", "description": "系统管理员权限"},
]

# 预定义角色
PRESET_ROLES = [
    {
        "code": "admin",
        "name": "系统管理员",
        "description": "拥有所有权限",
        "permissions": ["*"],  # 所有权限
    },
    {
        "code": "kb_admin",
        "name": "知识库管理员",
        "description": "管理知识库",
        "permissions": ["kb:read", "kb:create", "kb:update", "kb:delete", "kb:admin"],
    },
    {
        "code": "cmdb_admin",
        "name": "CMDB管理员",
        "description": "管理CMDB配置",
        "permissions": ["cmdb:read", "cmdb:create", "cmdb:update", "cmdb:delete", "cmdb:admin"],
    },
    {
        "code": "alert_operator",
        "name": "告警运维",
        "description": "处理告警",
        "permissions": ["alert:read", "alert:ack", "alert:resolve", "kb:read", "cmdb:read"],
    },
    {
        "code": "viewer",
        "name": "只读用户",
        "description": "只能查看",
        "permissions": ["kb:read", "cmdb:read", "alert:read"],
    },
]


class RoleService:
    """角色服务"""
    
    async def create(
        self,
        db: AsyncSession,
        code: str,
        name: str,
        description: str = "",
    ) -> Role:
        """创建角色"""
        # 检查是否已存在
        existing = await self.get_by_code(db, code)
        if existing:
            raise ValueError(f"角色已存在: {code}")
        
        role = Role(
            code=code,
            name=name,
            description=description,
        )
        db.add(role)
        await db.commit()
        await db.refresh(role)
        
        logger.info(f"创建角色: {code}")
        return role
    
    async def get_by_id(self, db: AsyncSession, role_id: int) -> Optional[Role]:
        """根据ID获取角色"""
        result = await db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.id == role_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_code(self, db: AsyncSession, code: str) -> Optional[Role]:
        """根据编码获取角色"""
        result = await db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.code == code)
        )
        return result.scalar_one_or_none()
    
    async def list(self, db: AsyncSession) -> List[Role]:
        """获取所有角色"""
        result = await db.execute(
            select(Role).options(selectinload(Role.permissions))
        )
        return result.scalars().all()
    
    async def update(
        self,
        db: AsyncSession,
        role_id: int,
        name: str = None,
        description: str = None,
    ) -> Optional[Role]:
        """更新角色"""
        role = await self.get_by_id(db, role_id)
        if not role:
            return None
        
        if name:
            role.name = name
        if description is not None:
            role.description = description
        
        role.updated_at = datetime.now()
        await db.commit()
        await db.refresh(role)
        
        return role
    
    async def delete(self, db: AsyncSession, role_id: int) -> bool:
        """删除角色"""
        role = await self.get_by_id(db, role_id)
        if not role:
            return False
        
        await db.delete(role)
        await db.commit()
        return True
    
    async def assign_permission(
        self,
        db: AsyncSession,
        role_id: int,
        permission_id: int,
    ) -> bool:
        """分配权限"""
        role = await self.get_by_id(db, role_id)
        if not role:
            return False
        
        result = await db.execute(
            select(Permission).where(Permission.id == permission_id)
        )
        permission = result.scalar_one_or_none()
        if not permission:
            return False
        
        if permission not in role.permissions:
            role.permissions.append(permission)
            await db.commit()
        
        return True
    
    async def remove_permission(
        self,
        db: AsyncSession,
        role_id: int,
        permission_id: int,
    ) -> bool:
        """移除权限"""
        role = await self.get_by_id(db, role_id)
        if not role:
            return False
        
        result = await db.execute(
            select(Permission).where(Permission.id == permission_id)
        )
        permission = result.scalar_one_or_none()
        if not permission:
            return False
        
        if permission in role.permissions:
            role.permissions.remove(permission)
            await db.commit()
        
        return True


class PermissionService:
    """权限服务"""
    
    async def create(
        self,
        db: AsyncSession,
        code: str,
        name: str,
        module: str = "",
        description: str = "",
    ) -> Permission:
        """创建权限"""
        existing = await self.get_by_code(db, code)
        if existing:
            raise ValueError(f"权限已存在: {code}")
        
        permission = Permission(
            code=code,
            name=name,
            module=module,
            description=description,
        )
        db.add(permission)
        await db.commit()
        await db.refresh(permission)
        
        logger.info(f"创建权限: {code}")
        return permission
    
    async def get_by_id(self, db: AsyncSession, permission_id: int) -> Optional[Permission]:
        """根据ID获取权限"""
        result = await db.execute(
            select(Permission).where(Permission.id == permission_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_code(self, db: AsyncSession, code: str) -> Optional[Permission]:
        """根据编码获取权限"""
        result = await db.execute(
            select(Permission).where(Permission.code == code)
        )
        return result.scalar_one_or_none()
    
    async def list(
        self,
        db: AsyncSession,
        module: str = None,
    ) -> List[Permission]:
        """获取权限列表"""
        query = select(Permission)
        if module:
            query = query.where(Permission.module == module)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def delete(self, db: AsyncSession, permission_id: int) -> bool:
        """删除权限"""
        permission = await self.get_by_id(db, permission_id)
        if not permission:
            return False
        
        await db.delete(permission)
        await db.commit()
        return True


class RBACInitializer:
    """RBAC初始化器"""
    
    def __init__(self):
        self.role_service = RoleService()
        self.permission_service = PermissionService()
    
    async def init_permissions(self, db: AsyncSession) -> int:
        """初始化预定义权限"""
        count = 0
        for perm_data in PRESET_PERMISSIONS:
            existing = await self.permission_service.get_by_code(db, perm_data["code"])
            if not existing:
                await self.permission_service.create(
                    db=db,
                    code=perm_data["code"],
                    name=perm_data["name"],
                    module=perm_data.get("module", ""),
                    description=perm_data.get("description", ""),
                )
                count += 1
        
        logger.info(f"初始化权限: {count}个")
        return count
    
    async def init_roles(self, db: AsyncSession) -> int:
        """初始化预定义角色"""
        count = 0
        for role_data in PRESET_ROLES:
            existing = await self.role_service.get_by_code(db, role_data["code"])
            if existing:
                continue
            
            role = await self.role_service.create(
                db=db,
                code=role_data["code"],
                name=role_data["name"],
                description=role_data.get("description", ""),
            )
            
            # 分配权限
            perm_codes = role_data.get("permissions", [])
            if "*" in perm_codes:
                # 所有权限
                all_perms = await self.permission_service.list(db)
                for perm in all_perms:
                    await self.role_service.assign_permission(db, role.id, perm.id)
            else:
                for perm_code in perm_codes:
                    perm = await self.permission_service.get_by_code(db, perm_code)
                    if perm:
                        await self.role_service.assign_permission(db, role.id, perm.id)
            
            count += 1
        
        logger.info(f"初始化角色: {count}个")
        return count
    
    async def init_all(self, db: AsyncSession):
        """初始化所有RBAC数据"""
        await self.init_permissions(db)
        await self.init_roles(db)


# 创建全局服务实例
role_service = RoleService()
permission_service = PermissionService()
rbac_initializer = RBACInitializer()
