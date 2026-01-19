"""
CMDB模块单元测试
"""

import pytest
from datetime import datetime


class TestCITypes:
    """CI类型测试"""
    
    def test_preset_ci_types(self):
        """测试预置CI类型"""
        from app.core.cmdb.ci_types import PRESET_CI_TYPES
        
        assert len(PRESET_CI_TYPES) == 16
    
    def test_get_ci_type_by_code(self):
        """测试根据编码获取CI类型"""
        from app.core.cmdb.ci_types import get_ci_type_by_code
        
        ci_type = get_ci_type_by_code("server")
        
        assert ci_type is not None
        assert ci_type.code == "server"
        assert ci_type.name == "物理服务器"
    
    def test_get_ci_type_not_found(self):
        """测试获取不存在的CI类型"""
        from app.core.cmdb.ci_types import get_ci_type_by_code
        
        ci_type = get_ci_type_by_code("nonexistent")
        
        assert ci_type is None
    
    def test_get_ci_types_by_category(self):
        """测试根据分类获取CI类型"""
        from app.core.cmdb.ci_types import PRESET_CI_TYPES
        
        # 直接过滤预置CI类型
        infra_types = [t for t in PRESET_CI_TYPES if t.category == "基础设施"]
        
        assert len(infra_types) > 0
        assert all(t.category == "基础设施" for t in infra_types)


class TestIndexConfig:
    """索引配置测试"""
    
    def test_index_config_creation(self):
        """测试索引配置创建"""
        from app.core.cmdb.es_storage import IndexConfig
        
        config = IndexConfig(
            name="test-index",
            shards=2,
            replicas=1,
            retention_days=30,
        )
        
        assert config.name == "test-index"
        assert config.shards == 2
        assert config.replicas == 1
        assert config.retention_days == 30
    
    def test_index_config_from_yaml(self):
        """测试从YAML配置创建索引配置"""
        from app.core.cmdb.es_storage import IndexConfig
        from app.core.cmdb.config import cmdb_config, IndexConfigYAML
        
        yaml_config = IndexConfigYAML(
            name="test",
            shards=3,
            replicas=0,
            retention_days=7,
        )
        
        config = IndexConfig.from_yaml_config(yaml_config)
        
        assert config.name == "test"
        assert config.shards == 3


class TestTableMapping:
    """表映射测试"""
    
    def test_table_mapping_creation(self):
        """测试表映射创建"""
        from app.core.cmdb.sync import TableMapping
        
        mapping = TableMapping(
            source_table="servers",
            ci_type_code="server",
            identifier_field="hostname",
            field_mappings={  # 正确的字段名
                "hostname": "identifier",
                "ip_address": "ip",
                "os_version": "os",
            },
        )
        
        assert mapping.source_table == "servers"
        assert mapping.ci_type_code == "server"
        assert "hostname" in mapping.field_mappings


class TestKafkaMessage:
    """Kafka消息测试"""
    
    def test_kafka_message_creation(self):
        """测试Kafka消息创建"""
        from app.core.cmdb.kafka_consumer import KafkaMessage
        
        message = KafkaMessage(
            topic="alerts",
            partition=0,
            offset=100,
            key="alert-001",
            value={"title": "Test Alert"},
            timestamp=datetime.now(),
        )
        
        assert message.topic == "alerts"
        assert message.value["title"] == "Test Alert"
