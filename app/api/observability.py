"""
Observability API
提供监控指标(Metrics)和日志(Logs)的查询接口
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.auth import oauth2_scheme
from app.core.cmdb.influxdb import influxdb_service
from app.core.cmdb.es_storage import log_storage_service

router = APIRouter()


# ==================== 数据模型 ====================

class MetricPoint(BaseModel):
    """指标数据点"""
    time: datetime
    value: float
    metric: str
    ci_identifier: Optional[str] = None


class MetricsResponse(BaseModel):
    """指标响应"""
    data: List[MetricPoint]


class LogEntry(BaseModel):
    """日志条目"""
    log_id: Optional[str] = None
    ci_identifier: str
    log_level: str
    message: str
    source: Optional[str] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True


class LogsResponse(BaseModel):
    """日志响应"""
    items: List[LogEntry]
    total: int
    page: int
    size: int


# ==================== 指标查询 ====================

@router.get("/metrics", response_model=MetricsResponse, summary="查询性能指标")
async def get_metrics(
    ci_identifier: str = Query(..., description="配置项标识"),
    metric_name: str = Query(..., description="指标名称"),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    hours: int = Query(1, ge=1, le=168, description="若未指定时间范围，查询最近N小时"),
    aggregation: str = Query("mean", description="聚合函数: mean, max, min, sum, count"),
    window: str = Query("1m", description="聚合窗口: 1m, 5m, 1h"),
    token: str = Depends(oauth2_scheme)
):
    """
    查询配置项的性能指标数据
    """
    # 确定时间范围
    if not start_time:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
    
    data = await influxdb_service.query(
        ci_identifier=ci_identifier,
        metric_name=metric_name,
        start_time=start_time,
        end_time=end_time,
        aggregation=aggregation,
        window=window
    )
    
    return MetricsResponse(data=data)


@router.get("/metrics/latest", response_model=MetricsResponse, summary="查询最新指标")
async def get_latest_metrics(
    ci_identifier: str = Query(..., description="配置项标识"),
    metric_names: List[str] = Query(None, description="指定指标名称列表"),
    token: str = Depends(oauth2_scheme)
):
    """
    查询配置项的最新指标数据
    """
    all_data = []
    
    if metric_names:
        for name in metric_names:
            points = await influxdb_service.query_latest(ci_identifier, name)
            all_data.extend(points)
    else:
        # 查询所有
        points = await influxdb_service.query_latest(ci_identifier)
        all_data.extend(points)
        
    return MetricsResponse(data=all_data)


# ==================== 日志查询 ====================

@router.get("/logs", response_model=LogsResponse, summary="查询日志")
async def get_logs(
    ci_identifier: Optional[str] = Query(None, description="配置项标识"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    level: Optional[str] = Query(None, description="日志级别"),
    source: Optional[str] = Query(None, description="日志来源"),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(50, ge=1, le=1000, description="每页数量"),
    token: str = Depends(oauth2_scheme)
):
    """
    查询日志数据
    """
    offset = (page - 1) * size
    
    logs, total = await log_storage_service.search_logs(
        ci_identifier=ci_identifier,
        keyword=keyword,
        log_level=level,
        source=source,
        start_time=start_time,
        end_time=end_time,
        offset=offset,
        limit=size
    )
    
    items = []
    for log in logs:
        # 兼容 timestamp 处理 (可能是字符串或datetime)
        ts = log.get("timestamp")
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except:
                ts = datetime.now()
        
        items.append(LogEntry(
            log_id=log.get("log_id") or "", # 可能是ES生成的ID，不在source里? source里没有_id
            ci_identifier=log.get("ci_identifier", ""),
            log_level=log.get("log_level", "info"),
            message=log.get("message", ""),
            source=log.get("source", ""),
            timestamp=ts
        ))
        
    return LogsResponse(
        items=items,
        total=total,
        page=page,
        size=size
    )
