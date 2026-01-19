"""
告警模块单元测试
"""

import pytest
from datetime import datetime


class TestAlertContext:
    """告警上下文测试"""
    
    def test_alert_context_creation(self):
        """测试告警上下文创建"""
        from app.core.alert.analyzer import AlertContext
        
        context = AlertContext(
            alert={
                "alert_id": "ALERT001",
                "title": "Test Alert",
            }
        )
        
        assert context.alert["alert_id"] == "ALERT001"
        assert context.related_alerts == []
        assert context.performance_data == []
        assert context.related_logs == []
    
    def test_alert_context_with_data(self):
        """测试带数据的告警上下文"""
        from app.core.alert.analyzer import AlertContext
        
        context = AlertContext(
            alert={"alert_id": "ALERT001"},
            ci={"name": "server-001", "type": "server"},
            related_alerts=[{"alert_id": "ALERT002"}],
            performance_data=[{"metric": "cpu", "value": 80}],
            related_logs=[{"message": "Error occurred"}],
        )
        
        assert context.ci["name"] == "server-001"
        assert len(context.related_alerts) == 1
        assert len(context.performance_data) == 1
        assert len(context.related_logs) == 1


class TestAnalysisResult:
    """分析结果测试"""
    
    def test_analysis_result_creation(self):
        """测试分析结果创建"""
        from app.core.alert.llm_analyzer import AnalysisResult
        
        result = AnalysisResult(
            summary="CPU使用率过高",
            root_causes=["资源不足", "进程异常"],
            impact_scope="单台服务器",
            solutions=["扩容", "重启服务"],
            prevention=["设置告警阈值"],
            raw_response="原始响应内容",
            confidence=0.85,
        )
        
        assert result.summary == "CPU使用率过高"
        assert len(result.root_causes) == 2
        assert result.confidence == 0.85


class TestSolutionRecommendation:
    """方案推荐测试"""
    
    def test_recommendation_creation(self):
        """测试推荐创建"""
        from app.core.alert.recommender import SolutionRecommendation
        
        rec = SolutionRecommendation(
            title="CPU优化方案",
            content="详细内容...",
            relevance_score=0.9,
            source_doc_id="doc001",
        )
        
        assert rec.title == "CPU优化方案"
        assert rec.relevance_score == 0.9


class TestSolutionMatcher:
    """方案匹配器测试"""
    
    def test_match_categories_cpu(self):
        """测试CPU相关匹配"""
        from app.core.alert.recommender import SolutionMatcher
        
        matcher = SolutionMatcher()
        alert = {"title": "CPU使用率过高", "content": "服务器CPU占用90%"}
        
        categories = matcher.match_categories(alert)
        
        assert len(categories) > 0
        assert "性能优化" in categories or "资源扩容" in categories
    
    def test_match_categories_memory(self):
        """测试内存相关匹配"""
        from app.core.alert.recommender import SolutionMatcher
        
        matcher = SolutionMatcher()
        alert = {"title": "内存不足", "content": "服务器内存使用率95%"}
        
        categories = matcher.match_categories(alert)
        
        assert len(categories) > 0
    
    def test_match_categories_network(self):
        """测试网络相关匹配"""
        from app.core.alert.recommender import SolutionMatcher
        
        matcher = SolutionMatcher()
        alert = {"title": "网络连接超时", "content": "连接失败"}
        
        categories = matcher.match_categories(alert)
        
        assert len(categories) > 0


class TestAlertProcessResult:
    """告警处理结果测试"""
    
    def test_process_result_creation(self):
        """测试处理结果创建"""
        from app.core.alert.processor import AlertProcessResult, AlertStatus
        
        result = AlertProcessResult(
            alert={"alert_id": "ALERT001"},
            status=AlertStatus.OPEN,
            process_time_ms=100.5,
        )
        
        assert result.alert["alert_id"] == "ALERT001"
        assert result.status == AlertStatus.OPEN
        assert result.process_time_ms == 100.5
    
    def test_process_result_to_dict(self):
        """测试处理结果转字典"""
        from app.core.alert.processor import AlertProcessResult, AlertStatus
        
        result = AlertProcessResult(
            alert={"alert_id": "ALERT001", "title": "Test"},
            status=AlertStatus.ANALYZING,
            process_time_ms=50.0,
        )
        
        data = result.to_dict()
        
        assert "alert" in data
        assert data["status"] == "analyzing"
        assert data["process_time_ms"] == 50.0


class TestAlertStatus:
    """告警状态测试"""
    
    def test_alert_status_values(self):
        """测试告警状态值"""
        from app.core.alert.processor import AlertStatus
        
        assert AlertStatus.OPEN.value == "open"
        assert AlertStatus.ACKNOWLEDGED.value == "acknowledged"
        assert AlertStatus.RESOLVED.value == "resolved"
        assert AlertStatus.CLOSED.value == "closed"
