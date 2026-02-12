"""
数据库连接管理模块
提供异步SQLAlchemy session管理
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings
from app.models.user import Base


# 创建异步数据库引擎
engine = create_async_engine(
    settings.mysql_async_url,
    echo=settings.debug,
    poolclass=NullPool,  # 使用NullPool避免连接池问题
)

# 创建异步session工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def _auto_migrate(conn):
    """自动执行必要的Schema变更（简单的Migration）"""
    from sqlalchemy import text
    from loguru import logger
    
    async def _column_exists(table: str, column: str) -> bool:
        """检查列是否存在"""
        try:
            await conn.execute(text(f"SELECT {column} FROM {table} LIMIT 1"))
            return True
        except Exception:
            return False
    
    async def _add_column(table: str, column: str, col_def: str):
        """添加列（如果不存在）"""
        if not await _column_exists(table, column):
            try:
                await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}"))
                logger.info(f"Added column '{column}' to '{table}'")
            except Exception as e:
                logger.error(f"Failed to add column '{column}' to '{table}': {e}")
    
    # 检查 data_sources.extra_config
    try:
        await conn.execute(text("SELECT extra_config FROM data_sources LIMIT 1"))
    except Exception:
        logger.warning("Detected missing column 'extra_config' in 'data_sources'. Fixing...")
        try:
            await conn.execute(text("ALTER TABLE data_sources ADD COLUMN extra_config JSON COMMENT '额外配置'"))
            await conn.commit()
            logger.info("Successfully added 'extra_config' column.")
        except Exception as e:
            logger.error(f"Auto-migration failed: {e}")
    
    # === users 表迁移 ===
    # 添加 display_name 列
    await _add_column("users", "display_name", "VARCHAR(100) COMMENT '显示名称'")
    
    # last_login → last_login_at 重命名
    if await _column_exists("users", "last_login") and not await _column_exists("users", "last_login_at"):
        try:
            await conn.execute(text("ALTER TABLE users CHANGE COLUMN last_login last_login_at DATETIME COMMENT '最后登录时间'"))
            logger.info("Renamed column 'last_login' to 'last_login_at' in 'users'")
        except Exception as e:
            logger.error(f"Failed to rename 'last_login' column: {e}")
    elif not await _column_exists("users", "last_login_at"):
        await _add_column("users", "last_login_at", "DATETIME COMMENT '最后登录时间'")
    
    # === permissions 表迁移 ===
    await _add_column("permissions", "code", "VARCHAR(50) COMMENT '权限编码'")
    await _add_column("permissions", "name", "VARCHAR(50) COMMENT '权限名称'")
    await _add_column("permissions", "module", "VARCHAR(50) DEFAULT '' COMMENT '所属模块'")
    
    # 将旧列改为 nullable（如果存在）
    if await _column_exists("permissions", "resource"):
        try:
            await conn.execute(text("ALTER TABLE permissions MODIFY COLUMN resource VARCHAR(50) NULL DEFAULT NULL COMMENT '资源标识(旧)'"))
            logger.info("Modified 'resource' column to nullable in 'permissions'")
        except Exception as e:
            logger.error(f"Failed to modify 'resource' column: {e}")
    if await _column_exists("permissions", "action"):
        try:
            await conn.execute(text("ALTER TABLE permissions MODIFY COLUMN action VARCHAR(20) NULL DEFAULT NULL COMMENT '操作类型(旧)'"))
            logger.info("Modified 'action' column to nullable in 'permissions'")
        except Exception as e:
            logger.error(f"Failed to modify 'action' column: {e}")
    
    # === roles 表迁移 ===
    await _add_column("roles", "updated_at", "DATETIME COMMENT '更新时间'")
    
    try:
        await conn.commit()
    except Exception:
        pass


async def _init_data():
    """初始化预置数据"""
    from loguru import logger
    from app.core.cmdb.service import ci_type_service
    from app.auth.rbac import rbac_initializer
    from app.auth.user_service import user_service
    from app.auth.rbac import role_service
    
    # 使用新的Session进行数据初始化
    try:
        async with async_session_maker() as db:
            await ci_type_service.init_preset_types(db)
    except Exception as e:
        logger.error(f"CMDB data initialization failed: {e}")
    
    # 初始化RBAC权限和角色
    try:
        async with async_session_maker() as db:
            await rbac_initializer.init_all(db)
            logger.info("RBAC permissions and roles initialized")
    except Exception as e:
        logger.error(f"RBAC initialization failed: {e}")
    
    # 初始化管理员用户
    try:
        async with async_session_maker() as db:
            existing_admin = await user_service.get_by_username(db, "admin")
            if not existing_admin:
                admin_user = await user_service.create(
                    db,
                    username="admin",
                    password="admin123",
                    email="admin@example.com",
                    display_name="系统管理员",
                )
                # 分配admin角色
                admin_role = await role_service.get_by_code(db, "admin")
                if admin_role:
                    await user_service.assign_role(db, admin_user.id, admin_role.id)
                logger.info("Default admin user created: admin/admin123")
            else:
                logger.info("Admin user already exists, skipping creation")
    except Exception as e:
        logger.error(f"Admin user initialization failed: {e}")


async def init_db():
    """初始化数据库，创建所有表"""
    # 导入所有模型以确保它们被注册
    from app.models import user, knowledge, cmdb, alert
    
    async with engine.begin() as conn:
        # 创建所有表（如果不存在）
        await conn.run_sync(Base.metadata.create_all)
        
        # 执行自动修复
        await _auto_migrate(conn)
    
    # 初始化预置数据
    await _init_data()


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库session的依赖注入函数
    
    用法:
        @router.get("/items")
        async def get_items(session: AsyncSession = Depends(get_async_session)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库session的上下文管理器
    
    用法:
        async with get_session_context() as session:
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
