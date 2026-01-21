"""
知识库相关数据模型
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON, Float
from sqlalchemy.orm import relationship

from app.models.user import Base


class KnowledgeBase(Base):
    """知识库表"""
    __tablename__ = "knowledge_bases"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="知识库名称")
    description = Column(Text, comment="描述")
    status = Column(String(20), default="active", comment="状态")
    document_count = Column(Integer, default=0, comment="文档数量")
    chunk_count = Column(Integer, default=0, comment="分片数量")
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    documents = relationship("Document", back_populates="knowledge_base")


class Document(Base):
    """文档表"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    filename = Column(String(500), nullable=False, comment="文件名")
    file_type = Column(String(20), comment="文件类型")
    file_size = Column(Integer, comment="文件大小(字节)")
    file_path = Column(String(1000), comment="存储路径")
    content_hash = Column(String(64), comment="内容哈希")
    status = Column(String(20), default="pending", comment="处理状态")
    chunk_count = Column(Integer, default=0, comment="分片数量")
    error_message = Column(Text, comment="错误信息")
    doc_metadata = Column(JSON, comment="元数据")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document")


class DocumentChunk(Base):
    """文档分片表"""
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False, comment="分片索引")
    content = Column(Text, nullable=False, comment="分片内容")
    content_length = Column(Integer, comment="内容长度")
    doc_metadata = Column(JSON, comment="元数据")
    embedding_id = Column(String(100), comment="向量存储ID")
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    document = relationship("Document", back_populates="chunks")


class LLMConfig(Base):
    """LLM配置表"""
    __tablename__ = "llm_configs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="配置名称")
    provider = Column(String(50), nullable=False, comment="提供商")
    model_name = Column(String(100), nullable=False, comment="模型名称")
    api_key_encrypted = Column(String(500), comment="加密后的API Key")
    api_base = Column(String(500), comment="API端点")
    api_version = Column(String(50), comment="API版本")
    temperature = Column(Float, default=0.7)
    top_p = Column(Float, default=0.9)
    max_tokens = Column(Integer, default=4096)
    max_input_tokens = Column(Integer, default=8192)
    max_output_tokens = Column(Integer, default=4096)
    is_default = Column(Integer, default=0, comment="是否默认")
    status = Column(String(20), default="active")
    extra_config = Column(JSON, comment="其他配置")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class PromptTemplate(Base):
    """Prompt模板表"""
    __tablename__ = "prompt_templates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="模板名称")
    description = Column(String(500), comment="描述")
    template = Column(Text, nullable=False, comment="模板内容")
    variables = Column(JSON, comment="变量列表")
    category = Column(String(50), comment="分类")
    is_system = Column(Integer, default=0, comment="是否系统模板")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
