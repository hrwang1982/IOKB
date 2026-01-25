"""
CMDB相关数据模型
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from app.models.user import Base


class CIType(Base):
    """配置项类型表"""
    __tablename__ = "ci_types"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="类型名称")
    code = Column(String(50), unique=True, nullable=False, comment="类型编码")
    icon = Column(String(50), comment="图标")
    description = Column(String(500), comment="描述")
    attribute_schema = Column(JSON, comment="属性Schema定义")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    cis = relationship("CI", back_populates="ci_type")


class CI(Base):
    """配置项表"""
    __tablename__ = "cis"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    type_id = Column(Integer, ForeignKey("ci_types.id"), nullable=False)
    name = Column(String(200), nullable=False, comment="配置项名称")
    identifier = Column(String(100), unique=True, nullable=False, comment="唯一标识")
    status = Column(String(20), default="active", comment="状态")
    attributes = Column(JSON, comment="扩展属性")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    ci_type = relationship("CIType", back_populates="cis")
    alerts = relationship("Alert", back_populates="ci")
    from_relationships = relationship("CIRelationship", foreign_keys="CIRelationship.from_ci_id", back_populates="from_ci")
    to_relationships = relationship("CIRelationship", foreign_keys="CIRelationship.to_ci_id", back_populates="to_ci")


class CIRelationship(Base):
    """配置项关系表"""
    __tablename__ = "ci_relationships"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_ci_id = Column(Integer, ForeignKey("cis.id"), nullable=False)
    to_ci_id = Column(Integer, ForeignKey("cis.id"), nullable=False)
    rel_type = Column(String(50), nullable=False, comment="关系类型")
    attributes = Column(JSON, comment="关系属性")
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    from_ci = relationship("CI", foreign_keys=[from_ci_id], back_populates="from_relationships")
    to_ci = relationship("CI", foreign_keys=[to_ci_id], back_populates="to_relationships")


class DataSource(Base):
    """数据源配置表"""
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="数据源名称")
    db_type = Column(String(20), nullable=False, comment="数据库类型")
    host = Column(String(200), nullable=False)
    port = Column(Integer, nullable=False)
    database = Column(String(100), nullable=False)
    username = Column(String(100))
    password_encrypted = Column(String(500), comment="加密后的密码")
    sync_interval = Column(Integer, default=60, comment="同步间隔(分钟)")
    sync_mode = Column(String(20), default="incremental", comment="同步模式")
    table_mappings = Column(JSON, comment="表映射配置")
    extra_config = Column(JSON, comment="额外配置(Kafka GroupID, SASL等)")
    status = Column(String(20), default="active")
    last_sync_time = Column(DateTime, comment="最后同步时间")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
