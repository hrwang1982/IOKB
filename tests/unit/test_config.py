"""
配置模块单元测试
"""

import pytest
from pathlib import Path


class TestCMDBConfig:
    """CMDB配置测试"""
    
    def test_config_load(self):
        """测试配置加载"""
        from app.core.cmdb.config import cmdb_config
        
        assert cmdb_config is not None
        assert cmdb_config.alert_index is not None
        assert cmdb_config.log_index is not None
    
    def test_alert_index_config(self):
        """测试告警索引配置"""
        from app.core.cmdb.config import cmdb_config
        
        assert cmdb_config.alert_index.name == "alerts"
        assert cmdb_config.alert_index.shards >= 1
        assert cmdb_config.alert_index.retention_days > 0
    
    def test_log_index_config(self):
        """测试日志索引配置"""
        from app.core.cmdb.config import cmdb_config
        
        assert cmdb_config.log_index.name == "logs"
        assert cmdb_config.log_index.shards >= 1


class TestAlertConfig:
    """告警配置测试"""
    
    def test_config_load(self):
        """测试配置加载"""
        from app.core.alert.config import alert_config
        
        assert alert_config is not None
        assert alert_config.enricher is not None
        assert alert_config.llm_analyzer is not None
    
    def test_enricher_config(self):
        """测试丰富器配置"""
        from app.core.alert.config import alert_config
        
        assert alert_config.enricher.time_window_minutes > 0
        assert alert_config.enricher.max_related_alerts > 0
    
    def test_prompts_config(self):
        """测试Prompt配置"""
        from app.core.alert.config import alert_config
        
        assert len(alert_config.prompts.system_prompt) > 0
        assert len(alert_config.prompts.user_prompt) > 0
        assert "{question}" in alert_config.prompts.user_prompt or "{content}" in alert_config.prompts.user_prompt


class TestRAGConfig:
    """RAG配置测试"""
    
    def test_config_load(self):
        """测试配置加载"""
        from app.core.rag.config import rag_config
        
        assert rag_config is not None
        assert rag_config.splitter is not None
        assert rag_config.retriever is not None
    
    def test_splitter_config(self):
        """测试分片配置"""
        from app.core.rag.config import rag_config
        
        assert rag_config.splitter.chunk_size > 0
        assert rag_config.splitter.chunk_overlap >= 0
        assert rag_config.splitter.chunk_overlap < rag_config.splitter.chunk_size
    
    def test_retriever_config(self):
        """测试检索配置"""
        from app.core.rag.config import rag_config
        
        assert rag_config.retriever.default_top_k > 0
        assert 0 <= rag_config.retriever.min_score_threshold <= 1


class TestAuthConfig:
    """Auth配置测试"""
    
    def test_config_load(self):
        """测试配置加载"""
        from app.auth.config import auth_config
        
        assert auth_config is not None
        assert auth_config.jwt is not None
        assert auth_config.password is not None
    
    def test_jwt_config(self):
        """测试JWT配置"""
        from app.auth.config import auth_config
        
        assert auth_config.jwt.algorithm in ["HS256", "HS384", "HS512", "RS256"]
        assert auth_config.jwt.access_token_expire_minutes > 0
    
    def test_password_config(self):
        """测试密码策略配置"""
        from app.auth.config import auth_config
        
        assert auth_config.password.min_length >= 6


class TestConfigReload:
    """配置热重载测试"""
    
    def test_cmdb_config_reload(self):
        """测试CMDB配置重载"""
        from app.core.cmdb.config import reload_cmdb_config, cmdb_config
        
        old_shards = cmdb_config.alert_index.shards
        new_config = reload_cmdb_config()
        
        assert new_config is not None
        assert new_config.alert_index.shards == old_shards  # 配置未变
    
    def test_alert_config_reload(self):
        """测试告警配置重载"""
        from app.core.alert.config import reload_alert_config
        
        new_config = reload_alert_config()
        assert new_config is not None
    
    def test_rag_config_reload(self):
        """测试RAG配置重载"""
        from app.core.rag.config import reload_rag_config
        
        new_config = reload_rag_config()
        assert new_config is not None
    
    def test_auth_config_reload(self):
        """测试Auth配置重载"""
        from app.auth.config import reload_auth_config
        
        new_config = reload_auth_config()
        assert new_config is not None
