"""
Elasticsearch数据存储服务
告警数据和日志数据分别存储在不同的index中
支持index配置（保存周期、分片等）
配置从 config/cmdb.yaml 读取
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from elasticsearch import AsyncElasticsearch
from loguru import logger

from app.config import settings
from app.core.cmdb.config import cmdb_config, IndexConfigYAML


@dataclass
class IndexConfig:
    """Index配置（兼容旧接口）"""
    name: str
    alias: str = ""
    shards: int = 1
    replicas: int = 0
    retention_days: int = 30  # 保留天数
    refresh_interval: str = "1s"
    
    @classmethod
    def from_yaml_config(cls, yaml_config: IndexConfigYAML) -> "IndexConfig":
        """从YAML配置创建"""
        return cls(
            name=yaml_config.name,
            shards=yaml_config.shards,
            replicas=yaml_config.replicas,
            retention_days=yaml_config.retention_days,
            refresh_interval=yaml_config.refresh_interval,
        )


# 从配置文件加载索引配置
ALERT_INDEX_CONFIG = IndexConfig.from_yaml_config(cmdb_config.alert_index)
LOG_INDEX_CONFIG = IndexConfig.from_yaml_config(cmdb_config.log_index)


class ESDataService:
    """ES数据存储服务"""
    
    def __init__(
        self,
        hosts: List[str] = None,
        index_prefix: str = None,
    ):
        self.hosts = hosts or [settings.es_url]
        self.index_prefix = index_prefix or settings.es_index_prefix
        self._client: Optional[AsyncElasticsearch] = None
    
    async def get_client(self) -> AsyncElasticsearch:
        """获取ES客户端"""
        if self._client is None:
            self._client = AsyncElasticsearch(
                hosts=self.hosts,
                basic_auth=(settings.es_user, settings.es_password) if settings.es_password else None,
            )
        return self._client
    
    async def close(self):
        """关闭连接"""
        if self._client:
            await self._client.close()
            self._client = None
    
    async def create_index(self, config: IndexConfig) -> bool:
        """创建索引"""
        client = await self.get_client()
        index_name = f"{self.index_prefix}-{config.name}"
        
        # 检查是否已存在
        if await client.indices.exists(index=index_name):
            logger.debug(f"索引已存在: {index_name}")
            return True
        
        # 索引设置
        index_settings = {
            "number_of_shards": config.shards,
            "number_of_replicas": config.replicas,
            "refresh_interval": config.refresh_interval,
        }
        
        try:
            await client.indices.create(
                index=index_name,
                settings=index_settings,
            )
            logger.info(f"创建索引成功: {index_name}, shards={config.shards}, replicas={config.replicas}")
            
            # 创建别名
            if config.alias:
                alias_name = f"{self.index_prefix}-{config.alias}"
                await client.indices.put_alias(index=index_name, name=alias_name)
                logger.info(f"创建别名: {alias_name} -> {index_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"创建索引失败: {index_name}, 错误: {e}")
            return False
    
    async def setup_lifecycle_policy(self, config: IndexConfig) -> bool:
        """设置索引生命周期策略"""
        client = await self.get_client()
        policy_name = f"{self.index_prefix}-{config.name}-policy"
        
        policy = {
            "policy": {
                "phases": {
                    "hot": {
                        "actions": {
                            "rollover": {
                                "max_size": "50gb",
                                "max_age": "7d",
                            }
                        }
                    },
                    "warm": {
                        "min_age": "7d",
                        "actions": {
                            "shrink": {"number_of_shards": 1},
                            "forcemerge": {"max_num_segments": 1},
                        }
                    },
                    "delete": {
                        "min_age": f"{config.retention_days}d",
                        "actions": {
                            "delete": {}
                        }
                    }
                }
            }
        }
        
        try:
            await client.ilm.put_lifecycle(name=policy_name, policy=policy["policy"])
            logger.info(f"创建生命周期策略: {policy_name}, 保留{config.retention_days}天")
            return True
        except Exception as e:
            logger.warning(f"创建生命周期策略失败(可能ES版本不支持): {e}")
            return False


class AlertStorageService(ESDataService):
    """告警数据存储服务"""
    
    def __init__(self, config: IndexConfig = None):
        super().__init__()
        self.config = config or ALERT_INDEX_CONFIG
    
    def _get_index_name(self, date: datetime = None) -> str:
        """获取索引名称（按日期分片）"""
        date = date or datetime.now()
        date_str = date.strftime("%Y.%m.%d")
        return f"{self.index_prefix}-{self.config.name}-{date_str}"
    
    async def init_index(self) -> bool:
        """初始化告警索引"""
        client = await self.get_client()
        index_pattern = f"{self.index_prefix}-{self.config.name}-*"
        
        # 创建索引模板
        template_name = f"{self.index_prefix}-alerts-template"
        
        template = {
            "index_patterns": [index_pattern],
            "settings": {
                "number_of_shards": self.config.shards,
                "number_of_replicas": self.config.replicas,
                "refresh_interval": self.config.refresh_interval,
            },
            "mappings": {
                "properties": {
                    "alert_id": {"type": "keyword"},
                    "ci_identifier": {"type": "keyword"},
                    "ci_id": {"type": "integer"},
                    "level": {"type": "keyword"},  # critical, warning, info
                    "title": {"type": "text", "analyzer": "standard"},
                    "content": {"type": "text", "analyzer": "standard"},
                    "source": {"type": "keyword"},
                    "status": {"type": "keyword"},  # open, acknowledged, resolved
                    "tags": {"type": "object", "enabled": False},
                    "alert_time": {"type": "date"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                }
            }
        }
        
        try:
            await client.indices.put_template(name=template_name, body=template)
            logger.info(f"创建告警索引模板: {template_name}")
            
            # 设置生命周期策略
            await self.setup_lifecycle_policy(self.config)
            
            return True
        except Exception as e:
            logger.error(f"初始化告警索引失败: {e}")
            return False
    
    async def save_alert(self, alert_data: Dict[str, Any]) -> str:
        """保存告警"""
        client = await self.get_client()
        
        # 确定索引名称
        alert_time = alert_data.get("alert_time")
        if isinstance(alert_time, str):
            try:
                alert_time = datetime.fromisoformat(alert_time.replace("Z", "+00:00"))
            except:
                alert_time = datetime.now()
        elif not isinstance(alert_time, datetime):
            alert_time = datetime.now()
        
        index_name = self._get_index_name(alert_time)
        
        # 添加时间戳
        alert_data["created_at"] = datetime.now().isoformat()
        if "status" not in alert_data:
            alert_data["status"] = "open"
        
        # 生成文档ID
        doc_id = alert_data.get("alert_id") or f"alert_{datetime.now().timestamp()}"
        
        try:
            result = await client.index(
                index=index_name,
                id=doc_id,
                document=alert_data,
            )
            logger.info(f"保存告警: {doc_id} -> {index_name}")
            return result["_id"]
        except Exception as e:
            logger.error(f"保存告警失败: {e}")
            raise
    
    async def search_alerts(
        self,
        ci_identifier: str = None,
        level: str = None,
        status: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        keyword: str = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[List[Dict], int]:
        """搜索告警"""
        client = await self.get_client()
        
        # 构建查询
        must = []
        
        if ci_identifier:
            must.append({"term": {"ci_identifier": ci_identifier}})
        if level:
            must.append({"term": {"level": level}})
        if status:
            must.append({"term": {"status": status}})
        if keyword:
            must.append({"multi_match": {"query": keyword, "fields": ["title", "content"]}})
        
        # 时间范围
        if start_time or end_time:
            time_range = {}
            if start_time:
                time_range["gte"] = start_time.isoformat()
            if end_time:
                time_range["lte"] = end_time.isoformat()
            must.append({"range": {"alert_time": time_range}})
        
        query = {"bool": {"must": must}} if must else {"match_all": {}}
        
        try:
            result = await client.search(
                index=f"{self.index_prefix}-{self.config.name}-*",
                query=query,
                from_=offset,
                size=limit,
                sort=[{"alert_time": {"order": "desc"}}],
            )
            
            hits = result.get("hits", {})
            total = hits.get("total", {}).get("value", 0)
            alerts = [hit["_source"] for hit in hits.get("hits", [])]
            
            return alerts, total
            
        except Exception as e:
            logger.error(f"搜索告警失败: {e}")
            return [], 0
    
    async def delete_old_data(self, days: int = None) -> int:
        """删除过期数据"""
        client = await self.get_client()
        days = days or self.config.retention_days
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            result = await client.delete_by_query(
                index=f"{self.index_prefix}-{self.config.name}-*",
                query={"range": {"alert_time": {"lt": cutoff_date.isoformat()}}},
            )
            deleted = result.get("deleted", 0)
            logger.info(f"删除过期告警: {deleted}条, 截止日期: {cutoff_date.date()}")
            return deleted
        except Exception as e:
            logger.error(f"删除过期告警失败: {e}")
            return 0


class LogStorageService(ESDataService):
    """日志数据存储服务"""
    
    def __init__(self, config: IndexConfig = None):
        super().__init__()
        self.config = config or LOG_INDEX_CONFIG
    
    def _get_index_name(self, date: datetime = None) -> str:
        """获取索引名称（按日期分片）"""
        date = date or datetime.now()
        date_str = date.strftime("%Y.%m.%d")
        return f"{self.index_prefix}-{self.config.name}-{date_str}"
    
    async def init_index(self) -> bool:
        """初始化日志索引"""
        client = await self.get_client()
        index_pattern = f"{self.index_prefix}-{self.config.name}-*"
        
        # 创建索引模板
        template_name = f"{self.index_prefix}-logs-template"
        
        template = {
            "index_patterns": [index_pattern],
            "settings": {
                "number_of_shards": self.config.shards,
                "number_of_replicas": self.config.replicas,
                "refresh_interval": self.config.refresh_interval,
            },
            "mappings": {
                "properties": {
                    "log_id": {"type": "keyword"},
                    "ci_identifier": {"type": "keyword"},
                    "ci_id": {"type": "integer"},
                    "log_level": {"type": "keyword"},  # debug, info, warning, error, critical
                    "message": {"type": "text", "analyzer": "standard"},
                    "source": {"type": "keyword"},  # 日志来源（文件、应用等）
                    "tags": {"type": "object", "enabled": False},
                    "timestamp": {"type": "date"},
                    "created_at": {"type": "date"},
                }
            }
        }
        
        try:
            await client.indices.put_template(name=template_name, body=template)
            logger.info(f"创建日志索引模板: {template_name}")
            
            # 设置生命周期策略
            await self.setup_lifecycle_policy(self.config)
            
            return True
        except Exception as e:
            logger.error(f"初始化日志索引失败: {e}")
            return False
    
    async def save_log(self, log_data: Dict[str, Any]) -> str:
        """保存日志"""
        client = await self.get_client()
        
        # 确定索引名称
        timestamp = log_data.get("timestamp")
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except:
                timestamp = datetime.now()
        elif not isinstance(timestamp, datetime):
            timestamp = datetime.now()
        
        index_name = self._get_index_name(timestamp)
        
        # 添加创建时间
        log_data["created_at"] = datetime.now().isoformat()
        
        try:
            result = await client.index(
                index=index_name,
                document=log_data,
            )
            return result["_id"]
        except Exception as e:
            logger.error(f"保存日志失败: {e}")
            raise
    
    async def save_logs_batch(self, logs: List[Dict[str, Any]]) -> int:
        """批量保存日志"""
        client = await self.get_client()
        
        operations = []
        for log_data in logs:
            timestamp = log_data.get("timestamp")
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except:
                    timestamp = datetime.now()
            elif not isinstance(timestamp, datetime):
                timestamp = datetime.now()
            
            index_name = self._get_index_name(timestamp)
            log_data["created_at"] = datetime.now().isoformat()
            
            operations.append({"index": {"_index": index_name}})
            operations.append(log_data)
        
        try:
            result = await client.bulk(operations=operations)
            success_count = sum(1 for item in result["items"] if item["index"]["status"] in [200, 201])
            logger.debug(f"批量保存日志: {success_count}/{len(logs)}")
            return success_count
        except Exception as e:
            logger.error(f"批量保存日志失败: {e}")
            return 0
    
    async def search_logs(
        self,
        ci_identifier: str = None,
        log_level: str = None,
        source: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        keyword: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[List[Dict], int]:
        """搜索日志"""
        client = await self.get_client()
        
        must = []
        
        if ci_identifier:
            must.append({"term": {"ci_identifier": ci_identifier}})
        if log_level:
            must.append({"term": {"log_level": log_level}})
        if source:
            must.append({"term": {"source": source}})
        if keyword:
            must.append({"match": {"message": keyword}})
        
        if start_time or end_time:
            time_range = {}
            if start_time:
                time_range["gte"] = start_time.isoformat()
            if end_time:
                time_range["lte"] = end_time.isoformat()
            must.append({"range": {"timestamp": time_range}})
        
        query = {"bool": {"must": must}} if must else {"match_all": {}}
        
        try:
            result = await client.search(
                index=f"{self.index_prefix}-{self.config.name}-*",
                query=query,
                from_=offset,
                size=limit,
                sort=[{"timestamp": {"order": "desc"}}],
            )
            
            hits = result.get("hits", {})
            total = hits.get("total", {}).get("value", 0)
            logs = [hit["_source"] for hit in hits.get("hits", [])]
            
            return logs, total
            
        except Exception as e:
            logger.error(f"搜索日志失败: {e}")
            return [], 0
    
    async def delete_old_data(self, days: int = None) -> int:
        """删除过期数据"""
        client = await self.get_client()
        days = days or self.config.retention_days
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            result = await client.delete_by_query(
                index=f"{self.index_prefix}-{self.config.name}-*",
                query={"range": {"timestamp": {"lt": cutoff_date.isoformat()}}},
            )
            deleted = result.get("deleted", 0)
            logger.info(f"删除过期日志: {deleted}条, 截止日期: {cutoff_date.date()}")
            return deleted
        except Exception as e:
            logger.error(f"删除过期日志失败: {e}")
            return 0


# 创建全局服务实例
alert_storage_service = AlertStorageService()
log_storage_service = LogStorageService()
