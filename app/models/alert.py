"""
告警相关数据模型
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from app.models.user import Base


class Alert(Base):
    """告警表"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(100), unique=True, nullable=False, comment="告警ID")
    ci_id = Column(Integer, ForeignKey("cis.id"), nullable=True)
    level = Column(String(20), nullable=False, comment="告警级别")
    title = Column(String(500), nullable=False, comment="告警标题")
    content = Column(Text, comment="告警内容")
    status = Column(String(20), default="open", comment="告警状态")
    source = Column(String(50), comment="告警来源")
    tags = Column(JSON, comment="标签")
    alert_time = Column(DateTime, nullable=False, comment="告警时间")
    acknowledged_at = Column(DateTime, comment="确认时间")
    acknowledged_by = Column(Integer, ForeignKey("users.id"))
    resolved_at = Column(DateTime, comment="解决时间")
    resolved_by = Column(Integer, ForeignKey("users.id"))
    resolution = Column(Text, comment="解决说明")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    ci = relationship("CI", back_populates="alerts")
    analysis = relationship("AlertAnalysis", back_populates="alert", uselist=False)


class AlertAnalysis(Base):
    """告警分析结果表"""
    __tablename__ = "alert_analyses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False, unique=True)
    fault_summary = Column(Text, comment="故障摘要")
    possible_causes = Column(JSON, comment="可能原因")
    impact_scope = Column(Text, comment="影响范围")
    suggested_actions = Column(JSON, comment="建议措施")
    risk_level = Column(String(20), comment="风险等级")
    related_solutions = Column(JSON, comment="关联的处理方案")
    llm_config_id = Column(Integer, comment="使用的LLM配置")
    analysis_time_ms = Column(Integer, comment="分析耗时(毫秒)")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    alert = relationship("Alert", back_populates="analysis")


class AlertRule(Base):
    """告警规则表"""
    __tablename__ = "alert_rules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="规则名称")
    description = Column(Text, comment="描述")
    condition = Column(JSON, nullable=False, comment="触发条件")
    actions = Column(JSON, comment="触发动作")
    enabled = Column(Integer, default=1, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
