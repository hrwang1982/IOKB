"""
CMDB配置管理
从YAML配置文件加载配置
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from loguru import logger


@dataclass
class IndexConfigYAML:
    """索引配置"""
    name: str = "default"
    shards: int = 1
    replicas: int = 0
    retention_days: int = 30
    refresh_interval: str = "1s"


@dataclass
class InfluxDBConfigYAML:
    """InfluxDB配置"""
    measurement: str = "ci_metrics"
    batch_size: int = 1000
    flush_interval: int = 10


@dataclass
class KafkaConfigYAML:
    """Kafka消费者配置"""
    batch_size: int = 100
    poll_timeout_ms: int = 1000
    auto_commit: bool = True


@dataclass
class SocketConfigYAML:
    """Socket服务配置"""
    buffer_size: int = 4096
    max_connections: int = 1000
    timeout_seconds: int = 30


@dataclass
class SyncConfigYAML:
    """数据同步配置"""
    default_interval_minutes: int = 60
    batch_size: int = 500
    retry_times: int = 3
    retry_delay_seconds: int = 5


@dataclass
class TopologyConfigYAML:
    """拓扑配置"""
    max_depth: int = 5
    max_nodes: int = 500
    default_layout: str = "dagre"


@dataclass
class RelationshipType:
    """关系类型"""
    code: str
    name: str
    description: str = ""


@dataclass
class CMDBConfig:
    """CMDB完整配置"""
    alert_index: IndexConfigYAML = field(default_factory=IndexConfigYAML)
    log_index: IndexConfigYAML = field(default_factory=IndexConfigYAML)
    influxdb: InfluxDBConfigYAML = field(default_factory=InfluxDBConfigYAML)
    kafka: KafkaConfigYAML = field(default_factory=KafkaConfigYAML)
    socket: SocketConfigYAML = field(default_factory=SocketConfigYAML)
    sync: SyncConfigYAML = field(default_factory=SyncConfigYAML)
    topology: TopologyConfigYAML = field(default_factory=TopologyConfigYAML)
    ci_types_enabled: List[str] = field(default_factory=list)
    relationship_types: List[RelationshipType] = field(default_factory=list)


class CMDBConfigLoader:
    """CMDB配置加载器"""
    
    DEFAULT_CONFIG_PATHS = [
        "config/cmdb.yaml",
        "config/cmdb.yml",
        "../config/cmdb.yaml",
        "/etc/skb/cmdb.yaml",
    ]
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self._config: Optional[CMDBConfig] = None
        self._raw_config: Dict[str, Any] = {}
    
    def _find_config_file(self) -> Optional[str]:
        """查找配置文件"""
        if self.config_path and os.path.exists(self.config_path):
            return self.config_path
        
        # 从项目根目录开始查找
        base_dir = Path(__file__).parent.parent.parent.parent
        
        for path in self.DEFAULT_CONFIG_PATHS:
            full_path = base_dir / path
            if full_path.exists():
                return str(full_path)
        
        return None
    
    def _load_yaml(self) -> Dict[str, Any]:
        """加载YAML配置"""
        config_file = self._find_config_file()
        
        if not config_file:
            logger.warning("未找到CMDB配置文件，使用默认配置")
            return {}
        
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                logger.info(f"加载CMDB配置文件: {config_file}")
                return data or {}
        except Exception as e:
            logger.error(f"加载CMDB配置文件失败: {e}")
            return {}
    
    def _parse_index_config(self, data: Dict) -> IndexConfigYAML:
        """解析索引配置"""
        return IndexConfigYAML(
            name=data.get("name", "default"),
            shards=data.get("shards", 1),
            replicas=data.get("replicas", 0),
            retention_days=data.get("retention_days", 30),
            refresh_interval=data.get("refresh_interval", "1s"),
        )
    
    def load(self) -> CMDBConfig:
        """加载配置"""
        if self._config is not None:
            return self._config
        
        self._raw_config = self._load_yaml()
        
        # 解析各项配置
        alert_index = self._parse_index_config(
            self._raw_config.get("alert_index", {})
        )
        alert_index.name = alert_index.name or "alerts"
        
        log_index = self._parse_index_config(
            self._raw_config.get("log_index", {})
        )
        log_index.name = log_index.name or "logs"
        
        influxdb_data = self._raw_config.get("influxdb", {})
        influxdb = InfluxDBConfigYAML(
            measurement=influxdb_data.get("measurement", "ci_metrics"),
            batch_size=influxdb_data.get("batch_size", 1000),
            flush_interval=influxdb_data.get("flush_interval", 10),
        )
        
        kafka_data = self._raw_config.get("kafka", {})
        kafka = KafkaConfigYAML(
            batch_size=kafka_data.get("batch_size", 100),
            poll_timeout_ms=kafka_data.get("poll_timeout_ms", 1000),
            auto_commit=kafka_data.get("auto_commit", True),
        )
        
        socket_data = self._raw_config.get("socket", {})
        socket = SocketConfigYAML(
            buffer_size=socket_data.get("buffer_size", 4096),
            max_connections=socket_data.get("max_connections", 1000),
            timeout_seconds=socket_data.get("timeout_seconds", 30),
        )
        
        sync_data = self._raw_config.get("sync", {})
        sync = SyncConfigYAML(
            default_interval_minutes=sync_data.get("default_interval_minutes", 60),
            batch_size=sync_data.get("batch_size", 500),
            retry_times=sync_data.get("retry_times", 3),
            retry_delay_seconds=sync_data.get("retry_delay_seconds", 5),
        )
        
        topology_data = self._raw_config.get("topology", {})
        topology = TopologyConfigYAML(
            max_depth=topology_data.get("max_depth", 5),
            max_nodes=topology_data.get("max_nodes", 500),
            default_layout=topology_data.get("default_layout", "dagre"),
        )
        
        # CI类型
        ci_types_data = self._raw_config.get("ci_types", {})
        ci_types_enabled = ci_types_data.get("enabled", [])
        
        # 关系类型
        relationship_types = []
        for rt_data in self._raw_config.get("relationship_types", []):
            relationship_types.append(RelationshipType(
                code=rt_data.get("code", ""),
                name=rt_data.get("name", ""),
                description=rt_data.get("description", ""),
            ))
        
        self._config = CMDBConfig(
            alert_index=alert_index,
            log_index=log_index,
            influxdb=influxdb,
            kafka=kafka,
            socket=socket,
            sync=sync,
            topology=topology,
            ci_types_enabled=ci_types_enabled,
            relationship_types=relationship_types,
        )
        
        return self._config
    
    def reload(self) -> CMDBConfig:
        """重新加载配置"""
        self._config = None
        self._raw_config = {}
        return self.load()
    
    def get_raw_config(self) -> Dict[str, Any]:
        """获取原始配置"""
        if not self._raw_config:
            self._raw_config = self._load_yaml()
        return self._raw_config


# 创建全局配置加载器和配置对象
cmdb_config_loader = CMDBConfigLoader()
cmdb_config = cmdb_config_loader.load()


def get_cmdb_config() -> CMDBConfig:
    """获取CMDB配置"""
    return cmdb_config


def reload_cmdb_config() -> CMDBConfig:
    """重新加载CMDB配置"""
    global cmdb_config
    cmdb_config = cmdb_config_loader.reload()
    return cmdb_config
