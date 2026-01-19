"""
集成测试
测试模块间的协作
"""

import pytest
import pytest_asyncio
from datetime import datetime


class TestAuthIntegration:
    """认证模块集成测试"""
    
    @pytest.mark.asyncio
    async def test_user_registration_and_login(self, db_session, sample_user_data):
        """测试用户注册和登录流程"""
        from app.auth.user_service import user_service
        
        # 创建用户
        user = await user_service.create(
            db=db_session,
            username=sample_user_data["username"],
            password=sample_user_data["password"],
            email=sample_user_data["email"],
            display_name=sample_user_data["display_name"],
        )
        
        assert user is not None
        assert user.username == sample_user_data["username"]
        
        # 登录
        result = await user_service.authenticate(
            db=db_session,
            username=sample_user_data["username"],
            password=sample_user_data["password"],
        )
        
        assert result is not None
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["user"]["username"] == sample_user_data["username"]
    
    @pytest.mark.asyncio
    async def test_user_login_wrong_password(self, db_session, sample_user_data):
        """测试错误密码登录"""
        from app.auth.user_service import user_service
        
        # 创建用户
        await user_service.create(
            db=db_session,
            username=sample_user_data["username"],
            password=sample_user_data["password"],
            email=sample_user_data["email"],
        )
        
        # 使用错误密码登录
        result = await user_service.authenticate(
            db=db_session,
            username=sample_user_data["username"],
            password="WrongPassword",
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_user_password_change(self, db_session, sample_user_data):
        """测试修改密码"""
        from app.auth.user_service import user_service
        
        # 创建用户
        user = await user_service.create(
            db=db_session,
            username=sample_user_data["username"],
            password=sample_user_data["password"],
            email=sample_user_data["email"],
        )
        
        # 修改密码
        new_password = "NewPassword456"
        result = await user_service.change_password(
            db=db_session,
            user_id=user.id,
            old_password=sample_user_data["password"],
            new_password=new_password,
        )
        
        assert result is True
        
        # 使用新密码登录
        login_result = await user_service.authenticate(
            db=db_session,
            username=sample_user_data["username"],
            password=new_password,
        )
        
        assert login_result is not None


class TestTokenFlow:
    """令牌流程测试"""
    
    def test_token_create_verify_refresh(self):
        """测试令牌创建-验证-刷新流程"""
        from app.auth.jwt import JWTService
        
        jwt_service = JWTService(
            secret_key="test-secret",
            access_token_expire_minutes=30,
            refresh_token_expire_days=7,
        )
        
        # 创建令牌对
        tokens = jwt_service.create_token_pair(
            user_id="1",
            username="testuser",
            roles=["admin"],
            permissions=["kb:read"],
        )
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        
        # 验证访问令牌
        payload = jwt_service.verify_token(tokens["access_token"])
        assert payload is not None
        assert payload.username == "testuser"
        
        # 刷新令牌
        new_tokens = jwt_service.refresh_access_token(
            refresh_token=tokens["refresh_token"],
            roles=["admin"],
        )
        
        assert new_tokens is not None
        assert "access_token" in new_tokens
        
        # 验证新的访问令牌
        new_payload = jwt_service.verify_token(new_tokens["access_token"])
        assert new_payload is not None
        assert new_payload.username == "testuser"


class TestAlertProcessingFlow:
    """告警处理流程测试"""
    
    @pytest.mark.asyncio
    async def test_alert_enrichment(self, sample_alert_data):
        """测试告警上下文丰富"""
        from app.core.alert.analyzer import AlertEnricher
        
        enricher = AlertEnricher(
            time_window_minutes=30,
            max_related_alerts=5,
        )
        
        # 丰富告警上下文（无数据库连接时）
        context = await enricher.enrich(sample_alert_data, db_session=None)
        
        assert context is not None
        assert context.alert == sample_alert_data
        # 无数据库时，CI为空
        assert context.ci is None
    
    @pytest.mark.asyncio
    async def test_alert_correlation(self, sample_alert_data):
        """测试告警关联"""
        from app.core.alert.analyzer import AlertCorrelator
        
        correlator = AlertCorrelator(
            correlation_window_minutes=10,
            min_correlation_score=0.5,
        )
        
        # 计算告警关联度
        score = correlator._calculate_correlation(
            sample_alert_data,
            {
                "alert_id": "ALERT002",
                "ci_identifier": "server-001",  # 相同CI
                "level": "warning",
                "title": "CPU使用率告警",  # 相似标题
            },
        )
        
        # 同一CI应该有较高关联度
        assert score >= 0.4
    
    @pytest.mark.asyncio
    async def test_quick_match(self, sample_alert_data):
        """测试快速匹配"""
        from app.core.alert.recommender import SolutionMatcher
        
        matcher = SolutionMatcher()
        categories = await matcher.quick_match(sample_alert_data)
        
        assert len(categories) > 0
        assert isinstance(categories, list)


class TestConfigIntegration:
    """配置集成测试"""
    
    def test_all_configs_loadable(self):
        """测试所有配置都可加载"""
        from app.core.cmdb.config import cmdb_config
        from app.core.alert.config import alert_config
        from app.core.rag.config import rag_config
        from app.auth.config import auth_config
        
        assert cmdb_config is not None
        assert alert_config is not None
        assert rag_config is not None
        assert auth_config is not None
    
    def test_config_consistency(self):
        """测试配置一致性"""
        from app.core.alert.config import alert_config
        from app.core.rag.config import rag_config
        
        # 告警分析器使用的日志数应该合理
        assert alert_config.llm_analyzer.max_logs <= alert_config.enricher.max_logs
        
        # RAG检索数应该合理
        assert rag_config.retriever.default_top_k <= rag_config.retriever.max_top_k
