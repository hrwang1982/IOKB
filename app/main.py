"""
FastAPI 应用入口
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info(f"Starting {settings.app_name} v0.1.0...")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # 初始化数据库连接
    # 初始化数据库连接
    from app.core.database import init_db, close_db
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    # 初始化Kafka同步管理器
    from app.core.cmdb.kafka import kafka_sync_manager
    await kafka_sync_manager.start()

    # 初始化告警/监控/日志消费者
    from app.core.cmdb.kafka_consumer import kafka_consumer
    import asyncio
    asyncio.create_task(kafka_consumer.start())
    
    yield
    
    # 关闭时
    logger.info("Shutting down...")
    await kafka_sync_manager.stop()
    await kafka_consumer.stop()
    await close_db()
    logger.info("Database connection closed")


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title=settings.app_name,
        description="智能运维知识库系统 - 面向金融行业运维领域的智能化解决方案",
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition", "Content-Length", "Content-Type"],
    )
    
    # 注册路由
    register_routers(app)
    
    return app


def register_routers(app: FastAPI):
    """注册API路由"""
    from app.api import knowledge, cmdb, alert, llm, auth, config, observability
    
    # API v1
    app.include_router(
        auth.router,
        prefix="/api/v1/auth",
        tags=["认证"]
    )
    app.include_router(
        knowledge.router,
        prefix="/api/v1/knowledge",
        tags=["知识库"]
    )
    app.include_router(
        cmdb.router,
        prefix="/api/v1/cmdb",
        tags=["CMDB"]
    )
    app.include_router(
        alert.router,
        prefix="/api/v1/alert",
        tags=["告警"]
    )
    app.include_router(
        llm.router,
        prefix="/api/v1/llm",
        tags=["大模型配置"]
    )
    app.include_router(
        config.router,
        prefix="/api/v1/system",
        tags=["系统配置"]
    )
    app.include_router(
        observability.router,
        prefix="/api/v1/observability",
        tags=["可观测性"]
    )
    
    # 健康检查
    @app.get("/health", tags=["系统"])
    async def health_check():
        return {"status": "ok", "service": settings.app_name}
    
    @app.get("/", tags=["系统"])
    async def root():
        return {
            "name": settings.app_name,
            "version": "0.1.0",
            "description": "智能运维知识库系统"
        }


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
