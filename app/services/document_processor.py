"""
文档处理服务
负责文档的保存、解析、切片、向量化和索引
"""

import asyncio
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_session_context
from app.core.rag import (
    document_parser,
    create_splitter,
    embedding_service,
    retriever,
    TextChunk,
)
from app.models.knowledge import Document, DocumentChunk, KnowledgeBase


class DocumentProcessor:
    """文档处理器"""
    
    def __init__(self):
        self.storage_path = Path(settings.storage_path) / "documents"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.parser = document_parser
        self.splitter = create_splitter(
            splitter_type="recursive",
            chunk_size=500,
            chunk_overlap=50,
        )
    
    def get_document_dir(self, kb_id: int) -> Path:
        """获取知识库文档目录"""
        doc_dir = self.storage_path / str(kb_id)
        doc_dir.mkdir(parents=True, exist_ok=True)
        return doc_dir
    
    async def save_file(
        self,
        kb_id: int,
        filename: str,
        content: bytes,
    ) -> str:
        """
        保存上传的文件
        
        Returns:
            保存后的文件路径
        """
        doc_dir = self.get_document_dir(kb_id)
        
        # 生成唯一文件名避免冲突
        file_ext = Path(filename).suffix
        unique_name = f"{uuid.uuid4().hex}{file_ext}"
        file_path = doc_dir / unique_name
        
        # 写入文件
        file_path.write_bytes(content)
        logger.info(f"文件已保存: {file_path}")
        
        return str(file_path)
    
    async def process_document(
        self,
        doc_id: int,
        kb_id: int,
        file_path: str,
    ):
        """
        处理文档：解析 → 切片 → 向量化 → 索引
        """
        async with get_session_context() as session:
            try:
                # 更新状态为处理中
                await self._update_status(session, doc_id, "processing")
                
                # 1. 解析文档
                logger.info(f"开始解析文档: {file_path}")
                parsed = self.parser.parse(file_path)
                
                if not parsed.text:
                    logger.warning(f"文档解析结果为空: {file_path}")
                    await self._update_status(session, doc_id, "failed", "文档内容为空")
                    return
                
                logger.info(f"文档解析完成, 字符数: {len(parsed.text)}")
                
                # 2. 切片
                chunks = self.splitter.split(parsed.text)
                logger.info(f"文档切片完成, 共 {len(chunks)} 个切片")
                
                if not chunks:
                    await self._update_status(session, doc_id, "failed", "切片结果为空")
                    return
                
                # 3. 向量化
                logger.info("开始向量化...")
                chunk_texts = [c.content for c in chunks]
                embeddings = await embedding_service.embed_batch(chunk_texts)
                logger.info(f"向量化完成, 共 {len(embeddings)} 个向量")
                
                # 4. 确保ES索引存在
                await retriever.create_index(kb_id)
                
                # 5. 批量索引到ES
                es_documents = []
                for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                    es_documents.append({
                        "doc_id": f"{doc_id}_{i}",
                        "content": chunk.content,
                        "vector": emb.vector,
                        "document_id": doc_id,
                        "chunk_index": i,
                        "metadata": {
                            "start_pos": chunk.start_pos,
                            "end_pos": chunk.end_pos,
                        }
                    })
                
                await retriever.bulk_index(kb_id, es_documents)
                logger.info(f"ES索引完成, 共 {len(es_documents)} 条")
                
                # 6. 保存切片到数据库
                for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                    db_chunk = DocumentChunk(
                        document_id=doc_id,
                        chunk_index=i,
                        content=chunk.content,
                        content_length=len(chunk.content),
                        doc_metadata={
                            "token_count": emb.token_count,
                            "start_pos": chunk.start_pos,
                            "end_pos": chunk.end_pos,
                        },
                    )
                    session.add(db_chunk)
                
                # 7. 更新文档状态
                await session.execute(
                    update(Document)
                    .where(Document.id == doc_id)
                    .values(
                        status="completed",
                        chunk_count=len(chunks),
                        file_size=Path(file_path).stat().st_size,
                        updated_at=datetime.now(),
                    )
                )
                
                await session.commit()
                logger.info(f"文档处理完成: doc_id={doc_id}")
                
            except Exception as e:
                logger.error(f"文档处理失败: {e}")
                await session.rollback()
                await self._update_status(session, doc_id, "failed", str(e))
                raise
    
    async def _update_status(
        self,
        session: AsyncSession,
        doc_id: int,
        status: str,
        error_message: str = None,
    ):
        """更新文档状态"""
        values = {
            "status": status,
            "updated_at": datetime.now(),
        }
        if error_message:
            values["error_message"] = error_message
            
        await session.execute(
            update(Document)
            .where(Document.id == doc_id)
            .values(**values)
        )
        await session.commit()


# 创建全局处理器实例
document_processor = DocumentProcessor()


async def process_document_task(doc_id: int, kb_id: int, file_path: str):
    """
    异步处理文档任务
    可以被后台任务或消息队列调用
    """
    try:
        await document_processor.process_document(doc_id, kb_id, file_path)
    except Exception as e:
        logger.error(f"文档处理任务失败: doc_id={doc_id}, error={e}")
