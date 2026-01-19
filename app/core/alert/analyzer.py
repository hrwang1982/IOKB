"""
告警分析服务
实现告警与CMDB关联、性能日志数据聚合
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.cmdb.service import ci_service
from app.core.cmdb.es_storage import alert_storage_service, log_storage_service
from app.core.cmdb.influxdb import influxdb_service


@dataclass
class AlertContext:
    """告警上下文"""
    alert: Dict[str, Any]
    ci: Optional[Dict[str, Any]] = None
    related_alerts: List[Dict[str, Any]] = None
    performance_data: List[Dict[str, Any]] = None
    related_logs: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.related_alerts is None:
            self.related_alerts = []
        if self.performance_data is None:
            self.performance_data = []
        if self.related_logs is None:
            self.related_logs = []


class AlertEnricher:
    """告警上下文丰富器"""
    
    def __init__(
        self,
        time_window_minutes: int = 30,  # 关联数据的时间窗口
        max_related_alerts: int = 10,
        max_logs: int = 50,
    ):
        self.time_window_minutes = time_window_minutes
        self.max_related_alerts = max_related_alerts
        self.max_logs = max_logs
    
    async def enrich(
        self,
        alert: Dict[str, Any],
        db_session=None,
    ) -> AlertContext:
        """丰富告警上下文"""
        context = AlertContext(alert=alert)
        
        ci_identifier = alert.get("ci_identifier")
        alert_time = alert.get("alert_time")
        
        if isinstance(alert_time, str):
            try:
                alert_time = datetime.fromisoformat(alert_time.replace("Z", "+00:00"))
            except:
                alert_time = datetime.now()
        elif not isinstance(alert_time, datetime):
            alert_time = datetime.now()
        
        # 时间窗口
        start_time = alert_time - timedelta(minutes=self.time_window_minutes)
        end_time = alert_time + timedelta(minutes=5)  # 告警后5分钟的数据也可能有用
        
        # 1. 关联CMDB配置项
        if ci_identifier and db_session:
            try:
                ci = await ci_service.get_by_identifier(db_session, ci_identifier)
                if ci:
                    context.ci = {
                        "id": ci.id,
                        "name": ci.name,
                        "identifier": ci.identifier,
                        "type": ci.ci_type.code if ci.ci_type else None,
                        "type_name": ci.ci_type.name if ci.ci_type else None,
                        "status": ci.status,
                        "attributes": ci.attributes,
                    }
            except Exception as e:
                logger.warning(f"关联CMDB失败: {ci_identifier}, {e}")
        
        # 2. 获取相关告警（同一CI的近期告警）
        if ci_identifier:
            try:
                related, _ = await alert_storage_service.search_alerts(
                    ci_identifier=ci_identifier,
                    start_time=start_time,
                    end_time=end_time,
                    limit=self.max_related_alerts,
                )
                # 排除当前告警
                current_id = alert.get("alert_id")
                context.related_alerts = [
                    a for a in related 
                    if a.get("alert_id") != current_id
                ]
            except Exception as e:
                logger.warning(f"获取相关告警失败: {e}")
        
        # 3. 获取性能数据
        if ci_identifier:
            try:
                # 查询多个关键指标
                metrics = ["cpu_usage", "memory_usage", "disk_usage", "network_io"]
                perf_data = []
                
                for metric in metrics:
                    try:
                        data = await influxdb_service.query(
                            ci_identifier=ci_identifier,
                            metric_name=metric,
                            start_time=start_time,
                            end_time=end_time,
                            aggregation="mean",
                            window="1m",
                        )
                        if data:
                            perf_data.extend(data)
                    except:
                        pass
                
                context.performance_data = perf_data
            except Exception as e:
                logger.warning(f"获取性能数据失败: {e}")
        
        # 4. 获取相关日志
        if ci_identifier:
            try:
                logs, _ = await log_storage_service.search_logs(
                    ci_identifier=ci_identifier,
                    log_level="error",  # 只获取错误级别的日志
                    start_time=start_time,
                    end_time=end_time,
                    limit=self.max_logs,
                )
                context.related_logs = logs
            except Exception as e:
                logger.warning(f"获取相关日志失败: {e}")
        
        logger.info(
            f"告警上下文丰富完成: ci={ci_identifier}, "
            f"related_alerts={len(context.related_alerts)}, "
            f"perf_points={len(context.performance_data)}, "
            f"logs={len(context.related_logs)}"
        )
        
        return context


class AlertCorrelator:
    """告警关联分析器"""
    
    def __init__(
        self,
        correlation_window_minutes: int = 10,
        min_correlation_score: float = 0.5,
    ):
        self.correlation_window_minutes = correlation_window_minutes
        self.min_correlation_score = min_correlation_score
    
    async def find_correlated_alerts(
        self,
        alert: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """查找关联告警"""
        alert_time = alert.get("alert_time")
        if isinstance(alert_time, str):
            try:
                alert_time = datetime.fromisoformat(alert_time.replace("Z", "+00:00"))
            except:
                alert_time = datetime.now()
        elif not isinstance(alert_time, datetime):
            alert_time = datetime.now()
        
        start_time = alert_time - timedelta(minutes=self.correlation_window_minutes)
        end_time = alert_time + timedelta(minutes=self.correlation_window_minutes)
        
        # 搜索时间窗口内的所有告警
        all_alerts, _ = await alert_storage_service.search_alerts(
            start_time=start_time,
            end_time=end_time,
            limit=100,
        )
        
        # 计算关联度
        correlated = []
        current_id = alert.get("alert_id")
        current_ci = alert.get("ci_identifier")
        current_level = alert.get("level")
        
        for other in all_alerts:
            if other.get("alert_id") == current_id:
                continue
            
            score = self._calculate_correlation(alert, other)
            if score >= self.min_correlation_score:
                correlated.append({
                    **other,
                    "correlation_score": score,
                })
        
        # 按关联度排序
        correlated.sort(key=lambda x: x["correlation_score"], reverse=True)
        
        return correlated
    
    def _calculate_correlation(
        self,
        alert1: Dict,
        alert2: Dict,
    ) -> float:
        """计算两个告警的关联度"""
        score = 0.0
        
        # 同一CI
        if alert1.get("ci_identifier") == alert2.get("ci_identifier"):
            score += 0.4
        
        # 同级别告警
        if alert1.get("level") == alert2.get("level"):
            score += 0.1
        
        # 标题相似
        title1 = alert1.get("title", "").lower()
        title2 = alert2.get("title", "").lower()
        if title1 and title2:
            # 简单的词重叠计算
            words1 = set(title1.split())
            words2 = set(title2.split())
            if words1 and words2:
                overlap = len(words1 & words2) / max(len(words1), len(words2))
                score += overlap * 0.3
        
        # 时间接近度
        time1 = alert1.get("alert_time")
        time2 = alert2.get("alert_time")
        if isinstance(time1, str):
            try:
                time1 = datetime.fromisoformat(time1.replace("Z", "+00:00"))
            except:
                time1 = None
        if isinstance(time2, str):
            try:
                time2 = datetime.fromisoformat(time2.replace("Z", "+00:00"))
            except:
                time2 = None
        
        if time1 and time2:
            diff_seconds = abs((time1 - time2).total_seconds())
            if diff_seconds < 60:
                score += 0.2
            elif diff_seconds < 300:
                score += 0.1
        
        return min(score, 1.0)
    
    async def find_root_cause_candidates(
        self,
        alert_context: AlertContext,
    ) -> List[Dict[str, Any]]:
        """找出可能的根因告警"""
        candidates = []
        
        # 按时间排序，最早的告警更可能是根因
        related = alert_context.related_alerts.copy()
        
        for ra in related:
            # 分析是否可能是根因
            is_candidate = False
            reason = ""
            
            # 1. 更早发生
            ra_time = ra.get("alert_time")
            current_time = alert_context.alert.get("alert_time")
            if ra_time and current_time:
                if isinstance(ra_time, str):
                    ra_time = datetime.fromisoformat(ra_time.replace("Z", "+00:00"))
                if isinstance(current_time, str):
                    current_time = datetime.fromisoformat(current_time.replace("Z", "+00:00"))
                
                if ra_time < current_time:
                    is_candidate = True
                    reason = "发生时间更早"
            
            # 2. 严重级别更高
            level_order = {"critical": 3, "warning": 2, "info": 1}
            ra_level = level_order.get(ra.get("level"), 0)
            current_level = level_order.get(alert_context.alert.get("level"), 0)
            if ra_level > current_level:
                is_candidate = True
                reason = "严重级别更高"
            
            if is_candidate:
                candidates.append({
                    **ra,
                    "root_cause_reason": reason,
                })
        
        return candidates


# 创建全局服务实例
alert_enricher = AlertEnricher()
alert_correlator = AlertCorrelator()
