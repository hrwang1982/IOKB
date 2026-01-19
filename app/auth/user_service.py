"""
用户服务
用户管理、认证、授权
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User, Role, Permission, UserRole
from app.auth.jwt import password_service, jwt_service


class UserService:
    """用户服务"""
    
    async def create(
        self,
        db: AsyncSession,
        username: str,
        password: str,
        email: str = None,
        display_name: str = None,
        department: str = None,
    ) -> User:
        """创建用户"""
        # 检查用户名是否已存在
        existing = await self.get_by_username(db, username)
        if existing:
            raise ValueError(f"用户名已存在: {username}")
        
        # 检查邮箱是否已存在
        if email:
            existing_email = await self.get_by_email(db, email)
            if existing_email:
                raise ValueError(f"邮箱已被使用: {email}")
        
        # 加密密码
        hashed_password = password_service.hash_password(password)
        
        user = User(
            username=username,
            password_hash=hashed_password,
            email=email,
            display_name=display_name or username,
            department=department,
            status="active",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"创建用户: {username}")
        return user
    
    async def get_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        result = await db.execute(
            select(User)
            .options(selectinload(User.roles))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        result = await db.execute(
            select(User)
            .options(selectinload(User.roles))
            .where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def list(
        self,
        db: AsyncSession,
        status: str = None,
        department: str = None,
        keyword: str = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[List[User], int]:
        """获取用户列表"""
        query = select(User).options(selectinload(User.roles))
        count_query = select(User)
        
        if status:
            query = query.where(User.status == status)
            count_query = count_query.where(User.status == status)
        
        if department:
            query = query.where(User.department == department)
            count_query = count_query.where(User.department == department)
        
        if keyword:
            query = query.where(
                or_(
                    User.username.contains(keyword),
                    User.display_name.contains(keyword),
                    User.email.contains(keyword),
                )
            )
            count_query = count_query.where(
                or_(
                    User.username.contains(keyword),
                    User.display_name.contains(keyword),
                    User.email.contains(keyword),
                )
            )
        
        # 总数
        count_result = await db.execute(count_query)
        total = len(count_result.all())
        
        # 分页
        query = query.offset(offset).limit(limit).order_by(User.id.desc())
        result = await db.execute(query)
        
        return result.scalars().all(), total
    
    async def update(
        self,
        db: AsyncSession,
        user_id: int,
        email: str = None,
        display_name: str = None,
        department: str = None,
        status: str = None,
    ) -> Optional[User]:
        """更新用户"""
        user = await self.get_by_id(db, user_id)
        if not user:
            return None
        
        if email:
            user.email = email
        if display_name:
            user.display_name = display_name
        if department:
            user.department = department
        if status:
            user.status = status
        
        user.updated_at = datetime.now()
        await db.commit()
        await db.refresh(user)
        
        return user
    
    async def change_password(
        self,
        db: AsyncSession,
        user_id: int,
        old_password: str,
        new_password: str,
    ) -> bool:
        """修改密码"""
        user = await self.get_by_id(db, user_id)
        if not user:
            return False
        
        # 验证旧密码
        if not password_service.verify_password(old_password, user.password_hash):
            return False
        
        # 更新密码
        user.password_hash = password_service.hash_password(new_password)
        user.updated_at = datetime.now()
        await db.commit()
        
        logger.info(f"用户修改密码: {user.username}")
        return True
    
    async def reset_password(
        self,
        db: AsyncSession,
        user_id: int,
        new_password: str,
    ) -> bool:
        """重置密码（管理员操作）"""
        user = await self.get_by_id(db, user_id)
        if not user:
            return False
        
        user.password_hash = password_service.hash_password(new_password)
        user.updated_at = datetime.now()
        await db.commit()
        
        logger.info(f"重置用户密码: {user.username}")
        return True
    
    async def delete(self, db: AsyncSession, user_id: int) -> bool:
        """删除用户"""
        user = await self.get_by_id(db, user_id)
        if not user:
            return False
        
        await db.delete(user)
        await db.commit()
        return True
    
    async def authenticate(
        self,
        db: AsyncSession,
        username: str,
        password: str,
    ) -> Optional[Dict[str, Any]]:
        """用户认证"""
        user = await self.get_by_username(db, username)
        
        if not user:
            logger.warning(f"用户不存在: {username}")
            return None
        
        if user.status != "active":
            logger.warning(f"用户已停用: {username}")
            return None
        
        if not password_service.verify_password(password, user.password_hash):
            logger.warning(f"密码错误: {username}")
            return None
        
        # 更新最后登录时间
        user.last_login_at = datetime.now()
        await db.commit()
        
        # 获取用户角色和权限
        roles = [role.code for role in user.roles]
        permissions = await self._get_user_permissions(db, user.id)
        
        # 生成令牌
        tokens = jwt_service.create_token_pair(
            user_id=str(user.id),
            username=user.username,
            roles=roles,
            permissions=permissions,
        )
        
        logger.info(f"用户登录成功: {username}")
        
        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "email": user.email,
                "roles": roles,
            },
            **tokens,
        }
    
    async def _get_user_permissions(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> List[str]:
        """获取用户权限列表"""
        # 通过角色获取权限
        result = await db.execute(
            select(Permission)
            .join(Permission.roles)
            .join(Role.users)
            .where(User.id == user_id)
        )
        permissions = result.scalars().all()
        return list(set(p.code for p in permissions))
    
    async def assign_role(
        self,
        db: AsyncSession,
        user_id: int,
        role_id: int,
    ) -> bool:
        """分配角色"""
        user = await self.get_by_id(db, user_id)
        if not user:
            return False
        
        result = await db.execute(
            select(Role).where(Role.id == role_id)
        )
        role = result.scalar_one_or_none()
        if not role:
            return False
        
        # 检查是否已有该角色
        if role in user.roles:
            return True
        
        user.roles.append(role)
        await db.commit()
        
        logger.info(f"分配角色: user={user.username}, role={role.code}")
        return True
    
    async def remove_role(
        self,
        db: AsyncSession,
        user_id: int,
        role_id: int,
    ) -> bool:
        """移除角色"""
        user = await self.get_by_id(db, user_id)
        if not user:
            return False
        
        result = await db.execute(
            select(Role).where(Role.id == role_id)
        )
        role = result.scalar_one_or_none()
        if not role:
            return False
        
        if role in user.roles:
            user.roles.remove(role)
            await db.commit()
            logger.info(f"移除角色: user={user.username}, role={role.code}")
        
        return True


# 创建全局服务实例
user_service = UserService()
