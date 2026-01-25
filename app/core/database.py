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
    
    # 检查 data_sources.extra_config
    try:
        # 尝试查询，如果列不存在会报错
        await conn.execute(text("SELECT extra_config FROM data_sources LIMIT 1"))
    except Exception:
        # 列不存在，尝试添加
        logger.warning("Detected missing column 'extra_config' in 'data_sources'. Fixing...")
        try:
            await conn.execute(text("ALTER TABLE data_sources ADD COLUMN extra_config JSON COMMENT '额外配置'"))
            await conn.commit()
            logger.info("Successfully added 'extra_config' column.")
        except Exception as e:
            logger.error(f"Auto-migration failed: {e}")


async def _init_data():
    """初始化预置数据"""
    from loguru import logger
    from app.core.cmdb.service import ci_type_service
    
    # 使用新的Session进行数据初始化
    try:
        async with async_session_maker() as db:
            await ci_type_service.init_preset_types(db)
    except Exception as e:
        logger.error(f"Data initialization failed: {e}")


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
