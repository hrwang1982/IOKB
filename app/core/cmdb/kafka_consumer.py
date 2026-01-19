"""
Kafka消费者服务
接收告警、性能、日志数据
- 告警数据存储到 Elasticsearch
- 性能数据存储到 InfluxDB
- 日志数据存储到 Elasticsearch
"""

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from app.config import settings


@dataclass
class KafkaMessage:
    """Kafka消息"""
    topic: str
    partition: int
    offset: int
    key: Optional[str]
    value: Dict[str, Any]
    timestamp: datetime


class BaseMessageHandler(ABC):
    """消息处理器基类"""
    
    @abstractmethod
    async def handle(self, message: KafkaMessage) -> bool:
        """处理消息，返回是否成功"""
        pass


class AlertMessageHandler(BaseMessageHandler):
    """告警消息处理器 - 存储到ES"""
    
    def __init__(self, alert_storage=None):
        self.alert_storage = alert_storage
    
    async def handle(self, message: KafkaMessage) -> bool:
        """处理告警消息"""
        try:
            data = message.value
            
            # 解析告警数据
            alert_data = {
                "alert_id": data.get("alert_id") or data.get("id"),
                "ci_identifier": data.get("ci_identifier") or data.get("host"),
                "level": data.get("level") or data.get("severity", "warning"),
                "title": data.get("title") or data.get("name"),
                "content": data.get("content") or data.get("message"),
                "source": data.get("source", "kafka"),
                "tags": data.get("tags", {}),
                "alert_time": data.get("alert_time") or datetime.now().isoformat(),
            }
            
            logger.info(f"收到告警: {alert_data['alert_id']} - {alert_data['title']}")
            
            # 存储到ES
            if self.alert_storage:
                await self.alert_storage.save_alert(alert_data)
            
            return True
        
        except Exception as e:
            logger.error(f"处理告警消息失败: {e}")
            return False


class PerformanceMessageHandler(BaseMessageHandler):
    """性能数据消息处理器 - 存储到InfluxDB"""
    
    def __init__(self, influxdb_service=None):
        self.influxdb_service = influxdb_service
    
    async def handle(self, message: KafkaMessage) -> bool:
        """处理性能数据消息"""
        try:
            data = message.value
            
            ci_identifier = data.get("ci_identifier") or data.get("host")
            metric_name = data.get("metric_name") or data.get("metric")
            value = data.get("value")
            unit = data.get("unit", "")
            tags = data.get("tags", {})
            timestamp = data.get("timestamp")
            
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except:
                    timestamp = None
            
            logger.debug(f"收到性能数据: {ci_identifier} - {metric_name}")
            
            # 写入InfluxDB
            if self.influxdb_service and value is not None:
                await self.influxdb_service.write_metric(
                    ci_identifier=ci_identifier,
                    metric_name=metric_name,
                    value=float(value),
                    unit=unit,
                    extra_tags=tags,
                    timestamp=timestamp,
                )
            
            return True
        
        except Exception as e:
            logger.error(f"处理性能数据消息失败: {e}")
            return False


class LogMessageHandler(BaseMessageHandler):
    """日志消息处理器 - 存储到ES"""
    
    def __init__(self, log_storage=None):
        self.log_storage = log_storage
    
    async def handle(self, message: KafkaMessage) -> bool:
        """处理日志消息"""
        try:
            data = message.value
            
            # 解析日志数据
            log_data = {
                "ci_identifier": data.get("ci_identifier") or data.get("host"),
                "log_level": data.get("level", "info"),
                "message": data.get("message") or data.get("log"),
                "source": data.get("source", ""),
                "tags": data.get("tags", {}),
                "timestamp": data.get("timestamp") or datetime.now().isoformat(),
            }
            
            logger.debug(f"收到日志: {log_data['ci_identifier']} - {log_data['log_level']}")
            
            # 存储到ES
            if self.log_storage:
                await self.log_storage.save_log(log_data)
            
            return True
        
        except Exception as e:
            logger.error(f"处理日志消息失败: {e}")
            return False


class KafkaConsumer:
    """Kafka消费者"""
    
    def __init__(
        self,
        bootstrap_servers: str = None,
        group_id: str = None,
    ):
        self.bootstrap_servers = bootstrap_servers or settings.kafka_bootstrap_servers
        self.group_id = group_id or settings.kafka_consumer_group
        self._consumer = None
        self._running = False
        self._handlers: Dict[str, BaseMessageHandler] = {}
    
    def register_handler(self, topic: str, handler: BaseMessageHandler):
        """注册消息处理器"""
        self._handlers[topic] = handler
        logger.info(f"注册消息处理器: {topic} -> {handler.__class__.__name__}")
    
    async def _create_consumer(self, topics: List[str]):
        """创建Kafka消费者"""
        try:
            from aiokafka import AIOKafkaConsumer
            
            self._consumer = AIOKafkaConsumer(
                *topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset="latest",
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            )
            await self._consumer.start()
            logger.info(f"Kafka消费者启动成功，订阅主题: {topics}")
            
        except ImportError:
            logger.warning("aiokafka未安装，使用confluent-kafka")
            # 回退到confluent-kafka
            from confluent_kafka import Consumer
            
            conf = {
                "bootstrap.servers": self.bootstrap_servers,
                "group.id": self.group_id,
                "auto.offset.reset": "latest",
            }
            self._consumer = Consumer(conf)
            self._consumer.subscribe(topics)
            logger.info(f"Kafka消费者(confluent)启动成功，订阅主题: {topics}")
    
    async def start(self):
        """启动消费者"""
        topics = list(self._handlers.keys())
        if not topics:
            logger.warning("没有注册任何消息处理器")
            return
        
        await self._create_consumer(topics)
        self._running = True
        
        while self._running:
            try:
                # aiokafka方式
                if hasattr(self._consumer, "getmany"):
                    messages = await self._consumer.getmany(timeout_ms=1000)
                    for tp, msgs in messages.items():
                        for msg in msgs:
                            await self._process_message(msg)
                else:
                    # confluent-kafka方式
                    msg = self._consumer.poll(timeout=1.0)
                    if msg is not None and not msg.error():
                        await self._process_confluent_message(msg)
            
            except Exception as e:
                logger.error(f"消费消息失败: {e}")
                await asyncio.sleep(1)
    
    async def _process_message(self, msg):
        """处理aiokafka消息"""
        topic = msg.topic
        handler = self._handlers.get(topic)
        
        if handler:
            message = KafkaMessage(
                topic=topic,
                partition=msg.partition,
                offset=msg.offset,
                key=msg.key.decode() if msg.key else None,
                value=msg.value,
                timestamp=datetime.fromtimestamp(msg.timestamp / 1000),
            )
            await handler.handle(message)
    
    async def _process_confluent_message(self, msg):
        """处理confluent-kafka消息"""
        topic = msg.topic()
        handler = self._handlers.get(topic)
        
        if handler:
            try:
                value = json.loads(msg.value().decode("utf-8"))
            except:
                value = {"raw": msg.value().decode("utf-8")}
            
            message = KafkaMessage(
                topic=topic,
                partition=msg.partition(),
                offset=msg.offset(),
                key=msg.key().decode() if msg.key() else None,
                value=value,
                timestamp=datetime.now(),
            )
            await handler.handle(message)
    
    async def stop(self):
        """停止消费者"""
        self._running = False
        if self._consumer:
            if hasattr(self._consumer, "stop"):
                await self._consumer.stop()
            else:
                self._consumer.close()
            self._consumer = None
        logger.info("Kafka消费者已停止")


def create_default_consumer() -> KafkaConsumer:
    """创建默认配置的Kafka消费者（集成存储服务）"""
    # 导入存储服务
    from app.core.cmdb.es_storage import alert_storage_service, log_storage_service
    from app.core.cmdb.influxdb import influxdb_service
    
    consumer = KafkaConsumer()
    
    # 注册处理器（集成存储服务）
    consumer.register_handler(
        settings.kafka_alert_topic,
        AlertMessageHandler(alert_storage=alert_storage_service)
    )
    consumer.register_handler(
        settings.kafka_performance_topic,
        PerformanceMessageHandler(influxdb_service=influxdb_service)
    )
    consumer.register_handler(
        settings.kafka_log_topic,
        LogMessageHandler(log_storage=log_storage_service)
    )
    
    return consumer


# 全局消费者实例
kafka_consumer = create_default_consumer()
