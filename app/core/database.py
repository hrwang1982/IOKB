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


async def init_db():
    """初始化数据库，创建所有表"""
    # 导入所有模型以确保它们被注册
    from app.models import user, knowledge, cmdb, alert
    
    async with engine.begin() as conn:
        # 创建所有表（如果不存在）
        await conn.run_sync(Base.metadata.create_all)


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
