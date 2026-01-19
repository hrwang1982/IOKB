"""
告警处理服务
整合告警分析、方案推荐的完整工作流
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.alert.analyzer import (
    AlertEnricher,
    AlertCorrelator,
    AlertContext,
    alert_enricher,
    alert_correlator,
)
from app.core.alert.llm_analyzer import (
    LLMAlertAnalyzer,
    AnalysisResult,
    llm_alert_analyzer,
)
from app.core.alert.recommender import (
    SolutionRecommender,
    RecommendationResult,
    solution_recommender,
    solution_matcher,
)


class AlertStatus(Enum):
    """告警状态"""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    ANALYZING = "analyzing"
    RESOLVED = "resolved"
    CLOSED = "closed"


@dataclass
class AlertProcessResult:
    """告警处理结果"""
    alert: Dict[str, Any]
    context: Optional[AlertContext] = None
    analysis: Optional[AnalysisResult] = None
    recommendations: Optional[RecommendationResult] = None
    correlated_alerts: List[Dict[str, Any]] = None
    root_cause_candidates: List[Dict[str, Any]] = None
    status: AlertStatus = AlertStatus.OPEN
    process_time_ms: float = 0
    
    def __post_init__(self):
        if self.correlated_alerts is None:
            self.correlated_alerts = []
        if self.root_cause_candidates is None:
            self.root_cause_candidates = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "alert": self.alert,
            "context": {
                "ci": self.context.ci if self.context else None,
                "related_alerts_count": len(self.context.related_alerts) if self.context else 0,
                "performance_data_count": len(self.context.performance_data) if self.context else 0,
                "related_logs_count": len(self.context.related_logs) if self.context else 0,
            } if self.context else None,
            "analysis": {
                "summary": self.analysis.summary,
                "root_causes": self.analysis.root_causes,
                "impact_scope": self.analysis.impact_scope,
                "solutions": self.analysis.solutions,
                "prevention": self.analysis.prevention,
                "confidence": self.analysis.confidence,
            } if self.analysis else None,
            "recommendations": [
                {
                    "title": r.title,
                    "content": r.content[:200] + "..." if len(r.content) > 200 else r.content,
                    "relevance_score": r.relevance_score,
                    "source_doc_name": r.source_doc_name,
                }
                for r in (self.recommendations.recommendations if self.recommendations else [])
            ],
            "rag_answer": self.recommendations.rag_answer if self.recommendations else None,
            "correlated_alerts_count": len(self.correlated_alerts),
            "root_cause_candidates": [
                {
                    "alert_id": rc.get("alert_id"),
                    "title": rc.get("title"),
                    "reason": rc.get("root_cause_reason"),
                }
                for rc in self.root_cause_candidates[:3]  # 最多3个
            ],
            "status": self.status.value,
            "process_time_ms": self.process_time_ms,
        }


class AlertProcessor:
    """告警处理器"""
    
    def __init__(
        self,
        enricher: AlertEnricher = None,
        correlator: AlertCorrelator = None,
        analyzer: LLMAlertAnalyzer = None,
        recommender: SolutionRecommender = None,
    ):
        self.enricher = enricher or alert_enricher
        self.correlator = correlator or alert_correlator
        self.analyzer = analyzer or llm_alert_analyzer
        self.recommender = recommender or solution_recommender
    
    async def process(
        self,
        alert: Dict[str, Any],
        db_session=None,
        skip_analysis: bool = False,
        skip_recommendations: bool = False,
    ) -> AlertProcessResult:
        """处理告警的完整流程"""
        start_time = datetime.now()
        
        result = AlertProcessResult(
            alert=alert,
            status=AlertStatus.ANALYZING,
        )
        
        try:
            # 1. 丰富告警上下文
            logger.info(f"开始处理告警: {alert.get('alert_id')}")
            result.context = await self.enricher.enrich(alert, db_session)
            
            # 2. 查找关联告警
            result.correlated_alerts = await self.correlator.find_correlated_alerts(alert)
            
            # 3. 查找根因候选
            if result.context:
                result.root_cause_candidates = await self.correlator.find_root_cause_candidates(
                    result.context
                )
            
            # 4. 大模型分析（可选）
            if not skip_analysis and result.context:
                result.analysis = await self.analyzer.analyze(result.context)
            
            # 5. 方案推荐（可选）
            if not skip_recommendations and result.context:
                result.recommendations = await self.recommender.recommend(result.context)
            
            result.status = AlertStatus.OPEN
            
        except Exception as e:
            logger.error(f"处理告警失败: {e}")
            result.status = AlertStatus.OPEN
        
        # 计算处理时间
        end_time = datetime.now()
        result.process_time_ms = (end_time - start_time).total_seconds() * 1000
        
        logger.info(
            f"告警处理完成: {alert.get('alert_id')}, "
            f"耗时={result.process_time_ms:.0f}ms"
        )
        
        return result
    
    async def quick_process(
        self,
        alert: Dict[str, Any],
    ) -> Dict[str, Any]:
        """快速处理（仅规则匹配，不调用LLM）"""
        start_time = datetime.now()
        
        # 快速匹配解决方案类别
        categories = await solution_matcher.quick_match(alert)
        
        # 查找关联告警
        correlated = await self.correlator.find_correlated_alerts(alert)
        
        end_time = datetime.now()
        process_time = (end_time - start_time).total_seconds() * 1000
        
        return {
            "alert_id": alert.get("alert_id"),
            "suggested_categories": categories,
            "correlated_alerts_count": len(correlated),
            "correlated_alerts": [
                {"alert_id": a.get("alert_id"), "title": a.get("title")}
                for a in correlated[:5]
            ],
            "process_time_ms": process_time,
        }
    
    async def batch_process(
        self,
        alerts: List[Dict[str, Any]],
        db_session=None,
        skip_analysis: bool = True,  # 批处理默认跳过LLM分析
    ) -> List[AlertProcessResult]:
        """批量处理告警"""
        results = []
        
        for alert in alerts:
            result = await self.process(
                alert,
                db_session=db_session,
                skip_analysis=skip_analysis,
            )
            results.append(result)
        
        return results


# 创建全局处理器实例
alert_processor = AlertProcessor()
