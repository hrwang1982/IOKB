"""
仪表盘 API
提供系统概览数据的聚合接口
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.auth import oauth2_scheme
from app.core.database import get_async_session
from app.models.knowledge import KnowledgeBase, Document, QALog
from app.models.cmdb import CI

router = APIRouter()


# ==================== 数据模型 ====================

class RecentAlert(BaseModel):
    """最近告警"""
    id: str
    title: str
    level: str
    time: str
    ci: str


class DashboardSummary(BaseModel):
    """仪表盘概览"""
    pending_alerts: int
    pending_alerts_change: str
    document_count: int
    document_change: str
    ci_count: int
    ci_change: str
    today_qa: int
    today_qa_change: str
    recent_alerts: List[RecentAlert]


# ==================== API 接口 ====================

@router.get("/summary", response_model=DashboardSummary, summary="获取仪表盘概览")
async def get_dashboard_summary(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_session)
):
    """
    获取仪表盘概览数据
    
    包含：
    - 待处理告警数（及变化）
    - 知识库文档数（及变化）
    - 配置项总数（及变化）
    - 今日问答数（及变化）
    - 最近告警列表
    """
    from app.core.cmdb.es_storage import alert_storage_service
    
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    
    # ========== 1. 待处理告警统计 ==========
    pending_alerts = 0
    pending_alerts_yesterday = 0
    recent_alerts_list = []
    
    try:
        client = await alert_storage_service.get_client()
        index_pattern = f"{alert_storage_service.index_prefix}-{alert_storage_service.config.name}-*"
        
        # 当前待处理告警数 (status=open)
        pending_result = await client.count(
            index=index_pattern,
            query={"term": {"status": "open"}}
        )
        pending_alerts = pending_result.get("count", 0)
        
        # 昨日待处理告警数（用于计算变化）
        yesterday_result = await client.count(
            index=index_pattern,
            query={
                "bool": {
                    "must": [
                        {"term": {"status": "open"}},
                        {"range": {"created_at": {"lt": today_start.isoformat()}}}
                    ]
                }
            }
        )
        pending_alerts_yesterday = yesterday_result.get("count", 0)
        
        # 获取最近告警
        recent_result = await client.search(
            index=index_pattern,
            query={"match_all": {}},
            sort=[{"alert_time": {"order": "desc"}}],
            size=5
        )
        hits = recent_result.get("hits", {}).get("hits", [])
        for hit in hits:
            source = hit["_source"]
            alert_time = source.get("alert_time", "")
            # 计算相对时间
            time_str = _format_relative_time(alert_time)
            recent_alerts_list.append(RecentAlert(
                id=source.get("alert_id", ""),
                title=source.get("title", ""),
                level=source.get("level", "info"),
                time=time_str,
                ci=source.get("ci_identifier", "")
            ))
    except Exception:
        # ES 连接失败时使用默认值
        pass
    
    pending_change = pending_alerts - pending_alerts_yesterday
    pending_alerts_change = f"+{pending_change}" if pending_change >= 0 else str(pending_change)
    
    # ========== 2. 知识库文档统计 ==========
    # 当前文档总数
    doc_result = await db.execute(
        select(func.count(Document.id))
    )
    document_count = doc_result.scalar() or 0
    
    # 本周新增文档数
    doc_week_result = await db.execute(
        select(func.count(Document.id)).where(Document.created_at >= week_ago)
    )
    doc_week_count = doc_week_result.scalar() or 0
    document_change = f"+{doc_week_count}" if doc_week_count >= 0 else str(doc_week_count)
    
    # ========== 3. 配置项统计 ==========
    # 当前配置项总数
    ci_result = await db.execute(
        select(func.count(CI.id))
    )
    ci_count = ci_result.scalar() or 0
    
    # 本周新增配置项
    ci_week_result = await db.execute(
        select(func.count(CI.id)).where(CI.created_at >= week_ago)
    )
    ci_week_count = ci_week_result.scalar() or 0
    ci_change = f"+{ci_week_count}" if ci_week_count >= 0 else str(ci_week_count)
    
    # ========== 4. 今日问答统计 ==========
    # 今日问答数
    qa_today_result = await db.execute(
        select(func.count(QALog.id)).where(QALog.created_at >= today_start)
    )
    today_qa = qa_today_result.scalar() or 0
    
    # 昨日问答数
    qa_yesterday_result = await db.execute(
        select(func.count(QALog.id)).where(
            QALog.created_at >= yesterday_start,
            QALog.created_at < today_start
        )
    )
    yesterday_qa = qa_yesterday_result.scalar() or 0
    
    qa_change = today_qa - yesterday_qa
    today_qa_change = f"+{qa_change}" if qa_change >= 0 else str(qa_change)
    
    return DashboardSummary(
        pending_alerts=pending_alerts,
        pending_alerts_change=pending_alerts_change,
        document_count=document_count,
        document_change=document_change,
        ci_count=ci_count,
        ci_change=ci_change,
        today_qa=today_qa,
        today_qa_change=today_qa_change,
        recent_alerts=recent_alerts_list
    )


def _format_relative_time(time_str: str) -> str:
    """格式化相对时间"""
    if not time_str:
        return "未知"
    
    try:
        if isinstance(time_str, str):
            dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        else:
            dt = time_str
        
        # 移除时区信息以便计算
        if dt.tzinfo:
            dt = dt.replace(tzinfo=None)
        
        now = datetime.now()
        diff = now - dt
        
        if diff.total_seconds() < 60:
            return "刚刚"
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}分钟前"
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}小时前"
        else:
            days = int(diff.total_seconds() / 86400)
            return f"{days}天前"
    except Exception:
        return "未知"
