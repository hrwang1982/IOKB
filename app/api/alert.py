"""
告警分析 API
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.auth import oauth2_scheme

router = APIRouter()


# ==================== 数据模型 ====================

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db
from app.core.cmdb.es_storage import alert_storage_service, log_storage_service
from app.core.alert.analyzer import alert_enricher
from app.core.alert.llm_analyzer import llm_alert_analyzer
from app.core.alert.recommender import solution_recommender
from app.core.cmdb.influxdb import influxdb_service

class AlertCreate(BaseModel):
    """告警创建请求"""
    alert_id: str
    ci_identifier: str
    level: str  # critical, warning, info
    title: str
    content: str
    source: Optional[str] = None
    tags: Optional[Dict[str, str]] = None


class AlertResponse(BaseModel):
    """告警响应"""
    id: int
    alert_id: str
    ci_id: Optional[int] = None
    ci_name: Optional[str] = None
    level: str
    title: str
    content: str
    status: str  # open, acknowledged, resolved
    source: Optional[str] = None
    tags: Optional[Dict[str, str]] = None
    alert_time: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisResult(BaseModel):
    """分析结果"""
    fault_summary: str
    possible_causes: List[str]
    impact_scope: str
    suggested_actions: List[str]
    risk_level: str  # high, medium, low


class SolutionResult(BaseModel):
    """处理方案"""
    id: int
    title: str
    content: str
    source: str
    relevance_score: float


class AlertAnalysisResponse(BaseModel):
    """告警分析响应"""
    alert_id: str
    analysis: AnalysisResult
    solutions: List[SolutionResult]
    related_performance: Optional[Dict[str, Any]] = None
    related_logs: Optional[List[str]] = None


class PerformanceData(BaseModel):
    """性能数据"""
    ci_identifier: str
    metric_name: str
    value: float
    unit: str
    collect_time: datetime


class LogData(BaseModel):
    """日志数据"""
    ci_identifier: str
    log_level: str
    message: str
    timestamp: datetime


# ==================== 告警管理 ====================

@router.get("", summary="获取告警列表")
async def list_alerts(
    level: Optional[str] = None,
    status: Optional[str] = None,
    ci_identifier: Optional[str] = Query(None, description="配置项标识"),
    ci_id: Optional[int] = None,
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    token: str = Depends(oauth2_scheme)
):
    """
    获取告警列表
    
    - **level**: 可选，按级别筛选 (critical/warning/info)
    - **status**: 可选，按状态筛选 (open/acknowledged/resolved)
    - **ci_identifier**: 可选，按配置项标识筛选
    """
    from app.core.cmdb.es_storage import alert_storage_service
    
    offset = (page - 1) * size
    
    alerts, total = await alert_storage_service.search_alerts(
        ci_identifier=ci_identifier,
        level=level,
        status=status,
        keyword=keyword,
        start_time=start_time,
        end_time=end_time,
        offset=offset,
        limit=size
    )
    
    items = []
    for alert in alerts:
        # 时间戳处理
        alert_time = alert.get("alert_time")
        if isinstance(alert_time, str):
            try:
                alert_time = datetime.fromisoformat(alert_time.replace("Z", "+00:00"))
            except:
                alert_time = datetime.now()
                
        created_at = alert.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except:
                created_at = datetime.now()
                
        items.append(AlertResponse(
            id=0, # ES文档无整型ID，暂填0
            alert_id=alert.get("alert_id") or "",
            ci_id=alert.get("ci_id"),
            ci_name=alert.get("ci_identifier"), # 暂用identifier
            level=alert.get("level", "warning"),
            title=alert.get("title", ""),
            content=alert.get("content", ""),
            status=alert.get("status", "open"),
            source=alert.get("source"),
            tags=alert.get("tags"),
            alert_time=alert_time,
            created_at=created_at
        ))
        
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size
    }


@router.get("/{alert_id}", response_model=AlertResponse, summary="获取告警详情")
async def get_alert(alert_id: str, token: str = Depends(oauth2_scheme)):
    """获取告警详情"""
    # 使用ES客户端直接查询
    client = await alert_storage_service.get_client()
    try:
        result = await client.search(
            index=f"{alert_storage_service.index_prefix}-{alert_storage_service.config.name}-*",
            query={"term": {"alert_id": alert_id}},
            size=1
        )
        hits = result.get("hits", {}).get("hits", [])
        if not hits:
            raise HTTPException(status_code=404, detail=f"告警 {alert_id} 不存在")
            
        alert = hits[0]["_source"]
        
        # 时间处理
        alert_time = alert.get("alert_time")
        if isinstance(alert_time, str):
            try:
                alert_time = datetime.fromisoformat(alert_time.replace("Z", "+00:00"))
            except:
                alert_time = datetime.now()
                
        created_at = alert.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except:
                created_at = datetime.now()

        return AlertResponse(
            id=0,
            alert_id=alert.get("alert_id"),
            ci_id=alert.get("ci_id"),
            ci_name=alert.get("ci_identifier"),
            level=alert.get("level", "warning"),
            title=alert.get("title", ""),
            content=alert.get("content", ""),
            status=alert.get("status", "open"),
            source=alert.get("source"),
            tags=alert.get("tags"),
            alert_time=alert_time,
            created_at=created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        # 如果ES查询失败，尝试返回模拟数据以便演示（在还没有真实数据时）
        # 但既然我们要做真实实现，这里应该抛出错误
        # 为了方便调试，只有在确定是ConnectionError时才mock? 
        # 不，直接报错比较好，让用户知道后端没通
        raise HTTPException(status_code=500, detail=f"查询告警失败: {str(e)}")


@router.put("/{alert_id}/acknowledge", summary="确认告警")
async def acknowledge_alert(alert_id: str, token: str = Depends(oauth2_scheme)):
    """确认告警"""
    return {"message": f"告警 {alert_id} 已确认"}


@router.put("/{alert_id}/resolve", summary="解决告警")
async def resolve_alert(
    alert_id: str,
    resolution: Optional[str] = None,
    token: str = Depends(oauth2_scheme)
):
    """解决告警"""
    return {"message": f"告警 {alert_id} 已解决"}


# ==================== 智能分析 ====================

@router.get("/{alert_id}/analysis", response_model=AlertAnalysisResponse, summary="获取告警分析结果")
async def get_alert_analysis(
    alert_id: str, 
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """获取告警的智能分析结果"""
    # 1. 获取告警数据
    client = await alert_storage_service.get_client()
    result = await client.search(
        index=f"{alert_storage_service.index_prefix}-{alert_storage_service.config.name}-*",
        query={"term": {"alert_id": alert_id}},
        size=1
    )
    hits = result.get("hits", {}).get("hits", [])
    if not hits:
        raise HTTPException(status_code=404, detail="告警不存在")
    alert_data = hits[0]["_source"]
    
    # 2. 丰富上下文
    context = await alert_enricher.enrich(alert_data, db_session=db)
    
    # 3. LLM 分析
    analysis_result = await llm_alert_analyzer.analyze(context)
    
    # 4. 推荐方案
    recommendation = await solution_recommender.recommend(context)
    
    # 5. 为了前端展示，转换格式
    solutions_list = []
    for sol in recommendation.recommendations:
        solutions_list.append(SolutionResult(
            id=0,
            title=sol.title,
            content=sol.content,
            source=sol.source_doc_name or "知识库",
            relevance_score=sol.relevance_score
        ))

    return AlertAnalysisResponse(
        alert_id=alert_data.get("alert_id"),
        analysis=AnalysisResult(
            fault_summary=analysis_result.summary,
            possible_causes=analysis_result.root_causes,
            impact_scope=analysis_result.impact_scope,
            suggested_actions=analysis_result.solutions,
            risk_level="high" if analysis_result.confidence > 0.8 else "medium"
        ),
        solutions=solutions_list,
        # 可以包含关联数据摘要
        related_performance={"count": len(context.performance_data)},
        related_logs=[log.get("message", "")[:50] for log in context.related_logs[:5]]
    )


@router.get("/{alert_id}/solutions", response_model=List[SolutionResult], summary="获取推荐处理方案")
async def get_alert_solutions(
    alert_id: str,
    top_k: int = Query(5, ge=1, le=20),
    token: str = Depends(oauth2_scheme)
):
    """获取告警的推荐处理方案"""
    # 1. 获取告警数据
    client = await alert_storage_service.get_client()
    result = await client.search(
        index=f"{alert_storage_service.index_prefix}-{alert_storage_service.config.name}-*",
        query={"term": {"alert_id": alert_id}},
        size=1
    )
    hits = result.get("hits", {}).get("hits", [])
    if not hits:
        raise HTTPException(status_code=404, detail="告警不存在")
    alert_data = hits[0]["_source"]
    
    # 2. 丰富上下文
    context = await alert_enricher.enrich(alert_data)
    
    # 3. 推荐方案
    # 这里可以创建新的solution_recommender实例如果需要修改参数，或者复用全局
    solution_recommender.max_recommendations = top_k
    recommendation = await solution_recommender.recommend(context)
    
    solutions_list = []
    for i, sol in enumerate(recommendation.recommendations):
        solutions_list.append(SolutionResult(
            id=i+1,
            title=sol.title,
            content=sol.content,
            source=sol.source_doc_name or "知识库",
            relevance_score=sol.relevance_score
        ))
        
    return solutions_list


@router.post("/analyze", response_model=AlertAnalysisResponse, summary="提交告警进行分析")
async def analyze_alert(
    alert: AlertCreate,
    token: str = Depends(oauth2_scheme)
):
    """
    提交告警进行智能分析
    
    用于外部系统调用，实时分析告警
    """
    # TODO: 实现分析逻辑
    return AlertAnalysisResponse(
        alert_id=alert.alert_id,
        analysis=AnalysisResult(
            fault_summary="待分析",
            possible_causes=[],
            impact_scope="待评估",
            suggested_actions=[],
            risk_level="medium"
        ),
        solutions=[]
    )


# ==================== 关联数据 ====================

@router.get("/{alert_id}/performance", summary="获取关联性能数据")
async def get_alert_performance(
    alert_id: str,
    hours: int = Query(1, ge=1, le=24),
    token: str = Depends(oauth2_scheme)
):
    """获取告警关联的性能数据（近N小时）"""
    # 1. 获取告警以知道CI
    client = await alert_storage_service.get_client()
    result = await client.search(
        index=f"{alert_storage_service.index_prefix}-{alert_storage_service.config.name}-*",
        query={"term": {"alert_id": alert_id}},
        size=1
    )
    hits = result.get("hits", {}).get("hits", [])
    if not hits:
        raise HTTPException(status_code=404, detail="告警不存在")
    alert_data = hits[0]["_source"]
    
    ci_identifier = alert_data.get("ci_identifier")
    if not ci_identifier:
        return {"metrics": []}
        
    # 2. 查询InfluxDB
    # 取常用指标
    target_metrics = ["cpu_usage", "memory_usage", "disk_usage", "network_in", "network_out"]
    
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    all_metrics = []
    for metric in target_metrics:
        try:
            data = await influxdb_service.query(
                ci_identifier=ci_identifier,
                metric_name=metric,
                start_time=start_time,
                end_time=end_time,
                aggregation="mean",
                window="5m" # 聚合粒度
            )
            # 格式化一下
            for point in data:
                all_metrics.append({
                    "metric_name": point["metric"],
                    "value": point["value"],
                    "collect_time": point["time"],
                    "ci_identifier": point["ci_identifier"],
                    "unit": "%" if "usage" in metric else ""
                })
        except Exception:
            continue
            
    return {"metrics": all_metrics}


@router.get("/{alert_id}/logs", summary="获取关联日志")
async def get_alert_logs(
    alert_id: str,
    hours: int = Query(1, ge=1, le=24),
    limit: int = Query(100, ge=1, le=1000),
    token: str = Depends(oauth2_scheme)
):
    """获取告警关联的日志数据"""
    # 1. 获取告警
    client = await alert_storage_service.get_client()
    result = await client.search(
        index=f"{alert_storage_service.index_prefix}-{alert_storage_service.config.name}-*",
        query={"term": {"alert_id": alert_id}},
        size=1
    )
    hits = result.get("hits", {}).get("hits", [])
    if not hits:
        raise HTTPException(status_code=404, detail="告警不存在")
    alert_data = hits[0]["_source"]
    
    ci_identifier = alert_data.get("ci_identifier")
    if not ci_identifier:
        return {"logs": []}
        
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    logs, total = await log_storage_service.search_logs(
        ci_identifier=ci_identifier,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    
    return {"logs": logs, "total": total}


@router.get("/{alert_id}/related", summary="获取关联告警")
async def get_related_alerts(
    alert_id: str,
    token: str = Depends(oauth2_scheme)
):
    """获取与当前告警相关的其他告警"""
    return {"related_alerts": []}


# ==================== 嵌入页面 ====================

@router.get("/embed/{alert_id}", summary="嵌入式分析页面")
async def embed_alert_analysis(
    alert_id: str,
    token: Optional[str] = None
):
    """
    提供可嵌入的告警分析页面
    
    支持iframe嵌入到其他系统
    """
    # TODO: 返回HTML页面或重定向到前端页面
    return {"message": "请访问 /embed/alert/{alert_id}?token=xxx"}


# ==================== 统计 ====================

@router.get("/stats/summary", summary="告警统计概览")
async def get_alert_stats(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    token: str = Depends(oauth2_scheme)
):
    """获取告警统计概览"""
    return {
        "total": 0,
        "by_level": {"critical": 0, "warning": 0, "info": 0},
        "by_status": {"open": 0, "acknowledged": 0, "resolved": 0},
        "trend": []
    }
