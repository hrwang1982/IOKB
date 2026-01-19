"""
测试配置和fixtures
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.user import Base


# 测试数据库URL（使用内存SQLite）
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    async_session_maker = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        "username": "testuser",
        "password": "TestPassword123",
        "email": "test@example.com",
        "display_name": "Test User",
        "department": "IT",
    }


@pytest.fixture
def sample_alert_data():
    """示例告警数据"""
    return {
        "alert_id": "ALERT001",
        "ci_identifier": "server-001",
        "level": "warning",
        "title": "CPU使用率过高",
        "content": "服务器CPU使用率超过80%",
        "source": "prometheus",
        "alert_time": "2026-01-18T10:00:00+08:00",
    }


@pytest.fixture
def sample_ci_data():
    """示例配置项数据"""
    return {
        "name": "测试服务器",
        "identifier": "server-001",
        "ci_type_id": 1,
        "attributes": {
            "ip": "192.168.1.100",
            "os": "Linux",
            "cpu_cores": 8,
            "memory_gb": 32,
        },
    }
