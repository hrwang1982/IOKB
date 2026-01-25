"""
CMDB Kafka 数据同步 Worker
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Try importing aiokafka, handle if not installed
try:
    from aiokafka import AIOKafkaConsumer
except ImportError:
    AIOKafkaConsumer = None

from app.core.database import async_session_maker
from app.models.cmdb import DataSource
from app.core.cmdb.service import ci_service
from app.config import settings

class KafkaSyncManager:
    """Kafka 同步管理器"""
    
    _consumers: Dict[int, "KafkaConsumerTask"] = {}
    _running = False
    
    async def start(self):
        """启动管理器"""
        if self._running:
            return
            
        # 确保默认数据源存在
        await self._ensure_default_source()
            
        self._running = True
        logger.info("Starting CMDB Kafka Sync Manager...")
        asyncio.create_task(self._monitor_loop())
    
    async def _ensure_default_source(self):
        """确保默认Kafka数据源配置存在"""
        if not settings.kafka_bootstrap_servers or not settings.cmdb_kafka_topic:
            return

        async with async_session_maker() as db:
            # 检查是否存在
            result = await db.execute(
                select(DataSource).where(
                    DataSource.name == "Default Kafka Source",
                    DataSource.db_type == "kafka"
                )
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                logger.info(f"Auto-creating default Kafka data source: {settings.cmdb_kafka_topic}")
                new_source = DataSource(
                    name="Default Kafka Source",
                    db_type="kafka",
                    host=settings.kafka_bootstrap_servers,
                    database=settings.cmdb_kafka_topic, # Topic stored in database field
                    username="",
                    password="",
                    port=9092, # Default
                    status="active",
                    extra_config={
                        "group_id": settings.cmdb_kafka_group_id
                    }
                )
                db.add(new_source)
                await db.commit()
            else:
                # Update config if changed
                changed = False
                if existing.host != settings.kafka_bootstrap_servers:
                    existing.host = settings.kafka_bootstrap_servers
                    changed = True
                if existing.database != settings.cmdb_kafka_topic:
                    existing.database = settings.cmdb_kafka_topic
                    changed = True
                
                current_group = existing.extra_config.get("group_id") if existing.extra_config else ""
                if current_group != settings.cmdb_kafka_group_id:
                    existing.extra_config = {"group_id": settings.cmdb_kafka_group_id}
                    changed = True
                
                if changed:
                    logger.info("Updating default Kafka data source config from env")
                    await db.commit()
    
    async def stop(self):
        """停止管理器"""
        self._running = False
        for task in self._consumers.values():
            await task.stop()
        self._consumers.clear()
        logger.info("CMDB Kafka Sync Manager stopped.")

    async def _monitor_loop(self):
        """监控循环: 定期检查数据源配置变更"""
        while self._running:
            try:
                await self._refresh_consumers()
            except Exception as e:
                logger.error(f"Error in Kafka monitor loop: {e}")
            await asyncio.sleep(60)  # 每分钟检查一次配置变更

    async def _refresh_consumers(self):
        """刷新消费者任务"""
        async with async_session_maker() as db:
            # 获取所有激活的Kafka数据源
            result = await db.execute(
                select(DataSource).where(
                    DataSource.status == "active",
                    DataSource.db_type == "kafka"
                )
            )
            data_sources = result.scalars().all()
            
            active_ids = {ds.id for ds in data_sources}
            current_ids = set(self._consumers.keys())
            
            # 停止已删除或禁用的源
            for ds_id in current_ids - active_ids:
                logger.info(f"Stopping Kafka consumer for source {ds_id}")
                await self._consumers[ds_id].stop()
                del self._consumers[ds_id]
            
            # 启动或更新源
            for ds in data_sources:
                if ds.id not in self._consumers:
                    logger.info(f"Starting Kafka consumer for source {ds.id} ({ds.name})")
                    task = KafkaConsumerTask(ds.id, ds.host, ds.database, ds.extra_config)
                    await task.start()
                    self._consumers[ds.id] = task
                else:
                    # TODO: 检查配置是否有变，如果有变则重启
                    pass

class KafkaConsumerTask:
    """单个 Kafka 消费任务"""
    
    def __init__(self, source_id: int, bootstrap_servers: str, topic: str, config: Optional[Dict] = None):
        self.source_id = source_id
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.config = config or {}
        self.consumer: Optional[AIOKafkaConsumer] = None
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        if not AIOKafkaConsumer:
            logger.warning("aiokafka not installed, skipping Kafka consumer start")
            return

        self._running = True
        self._task = asyncio.create_task(self._consume_loop())

    async def stop(self):
        self._running = False
        if self.consumer:
            await self.consumer.stop()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _consume_loop(self):
        group_id = self.config.get("group_id", f"cmdb-consumer-{self.source_id}")
        
        try:
            self.consumer = AIOKafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest' # 或者 configurable
            )
            await self.consumer.start()
            logger.info(f"Kafka consumer started for {self.topic}")
            
            async for msg in self.consumer:
                if not self._running:
                    break
                try:
                    await self._process_message(msg.value)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
        except Exception as e:
            logger.error(f"Kafka consumer error: {e}")
        finally:
            if self.consumer:
                await self.consumer.stop()

    async def _process_message(self, data: Dict[str, Any]):
        """处理消息
        Format:
        {
            "op": "update",
            "type_code": "server",
            "identifier": "server-001",
            "data": { ... }
        }
        """
        op = data.get("op")
        type_code = data.get("type_code")
        identifier = data.get("identifier")
        attributes = data.get("data", {})
        
        if not (type_code and identifier):
            logger.warning("Invalid message: missing type_code or identifier")
            return

        async with async_session_maker() as db:
            if op in ("create", "update"):
                # 尝试查找
                existing = await ci_service.get_by_identifier(db, identifier)
                if existing:
                    await ci_service.update(db, existing.id, attributes=attributes)
                    logger.debug(f"Updated CI {identifier} from Kafka")
                else:
                    await ci_service.create(db, type_code, name=identifier, identifier=identifier, attributes=attributes)
                    logger.info(f"Created CI {identifier} from Kafka")
            elif op == "delete":
                existing = await ci_service.get_by_identifier(db, identifier)
                if existing:
                    await ci_service.delete(db, existing.id)
                    logger.info(f"Deleted CI {identifier} from Kafka")

# 全局实例
kafka_sync_manager = KafkaSyncManager()
