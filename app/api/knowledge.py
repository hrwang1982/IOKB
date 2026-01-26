"""
知识库 API
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.api.auth import oauth2_scheme
from app.core.database import get_async_session
from app.models.knowledge import KnowledgeBase, Document, DocumentChunk

router = APIRouter()


# ==================== 数据模型 ====================

class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求"""
    name: str
    description: Optional[str] = None
    

class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""
    id: int
    name: str
    description: Optional[str] = None
    document_count: int = 0
    status: str = "active"
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """文档响应"""
    id: int
    kb_id: int
    filename: str
    file_type: str
    file_size: int
    status: str  # pending, processing, completed, failed
    chunk_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str
    kb_ids: Optional[List[int]] = None
    top_k: int = 10
    score_threshold: float = 0.5


class SearchResult(BaseModel):
    """搜索结果"""
    chunk_id: int
    document_id: int
    document_name: str
    content: str
    score: float
    kb_id: Optional[int] = None
    metadata: Optional[dict] = None


class QARequest(BaseModel):
    """问答请求"""
    question: str
    kb_ids: Optional[List[int]] = None
    top_k: int = 5
    

class QAResponse(BaseModel):
    """问答响应"""
    answer: str
    sources: List[SearchResult]


# ==================== 知识库管理 ====================

@router.get("", summary="获取知识库列表")
async def list_knowledge_bases(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session)
):
    """获取知识库列表"""
    # 计算偏移量
    offset = (page - 1) * size
    
    # 查询知识库列表
    result = await session.execute(
        select(KnowledgeBase)
        .order_by(KnowledgeBase.updated_at.desc())
        .offset(offset)
        .limit(size)
    )
    knowledge_bases = result.scalars().all()
    
    # 查询总数
    count_result = await session.execute(
        select(func.count(KnowledgeBase.id))
    )
    total = count_result.scalar() or 0
    
    # 转换为响应格式
    items = [
        KnowledgeBaseResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description,
            document_count=kb.document_count or 0,
            status=kb.status or "active",
            created_at=kb.created_at,
            updated_at=kb.updated_at
        )
        for kb in knowledge_bases
    ]
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size
    }


@router.post("", response_model=KnowledgeBaseResponse, summary="创建知识库")
async def create_knowledge_base(
    kb: KnowledgeBaseCreate,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session)
):
    """创建新知识库"""
    # 创建知识库对象
    new_kb = KnowledgeBase(
        name=kb.name,
        description=kb.description,
        status="active",
        document_count=0,
        chunk_count=0,
    )
    
    # 添加到数据库
    session.add(new_kb)
    await session.flush()  # 获取自动生成的ID
    await session.refresh(new_kb)  # 刷新获取完整对象
    
    return KnowledgeBaseResponse(
        id=new_kb.id,
        name=new_kb.name,
        description=new_kb.description,
        document_count=new_kb.document_count or 0,
        status=new_kb.status,
        created_at=new_kb.created_at,
        updated_at=new_kb.updated_at
    )


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse, summary="获取知识库详情")
async def get_knowledge_base(
    kb_id: int, 
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session)
):
    """获取知识库详情"""
    result = await session.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    )
    kb = result.scalar_one_or_none()
    
    if not kb:
        raise HTTPException(status_code=404, detail=f"知识库 {kb_id} 不存在")
    
    return KnowledgeBaseResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        document_count=kb.document_count or 0,
        status=kb.status,
        created_at=kb.created_at,
        updated_at=kb.updated_at
    )


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse, summary="更新知识库")
async def update_knowledge_base(
    kb_id: int,
    kb: KnowledgeBaseCreate,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session)
):
    """更新知识库信息"""
    # 查询知识库
    result = await session.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    )
    existing_kb = result.scalar_one_or_none()
    
    if not existing_kb:
        raise HTTPException(status_code=404, detail=f"知识库 {kb_id} 不存在")
    
    # 更新字段
    existing_kb.name = kb.name
    existing_kb.description = kb.description
    existing_kb.updated_at = datetime.now()
    
    await session.flush()
    await session.refresh(existing_kb)
    
    return KnowledgeBaseResponse(
        id=existing_kb.id,
        name=existing_kb.name,
        description=existing_kb.description,
        document_count=existing_kb.document_count or 0,
        status=existing_kb.status,
        created_at=existing_kb.created_at,
        updated_at=existing_kb.updated_at
    )


@router.delete("/{kb_id}", summary="删除知识库")
async def delete_knowledge_base(
    kb_id: int, 
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session)
):
    """删除知识库及其所有文档"""
    # 检查知识库是否存在
    result = await session.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    )
    kb = result.scalar_one_or_none()
    
    if not kb:
        raise HTTPException(status_code=404, detail=f"知识库 {kb_id} 不存在")
    
    # 删除关联的文档分片
    await session.execute(
        delete(DocumentChunk).where(
            DocumentChunk.document_id.in_(
                select(Document.id).where(Document.kb_id == kb_id)
            )
        )
    )
    
    # 删除关联的文档
    await session.execute(
        delete(Document).where(Document.kb_id == kb_id)
    )
    
    # 删除知识库
    await session.delete(kb)
    
    return {"message": f"知识库 {kb_id} 已删除"}


# ==================== 文档管理 ====================

@router.get("/{kb_id}/documents", summary="获取文档列表")
async def list_documents(
    kb_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session)
):
    """获取知识库中的文档列表"""
    # 检查知识库是否存在
    kb_result = await session.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    )
    if not kb_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"知识库 {kb_id} 不存在")
    
    # 计算偏移量
    offset = (page - 1) * size
    
    # 查询文档列表
    result = await session.execute(
        select(Document)
        .where(Document.kb_id == kb_id)
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    documents = result.scalars().all()
    
    # 查询总数
    count_result = await session.execute(
        select(func.count(Document.id)).where(Document.kb_id == kb_id)
    )
    total = count_result.scalar() or 0
    
    # 转换为响应格式
    items = [
        DocumentResponse(
            id=doc.id,
            kb_id=doc.kb_id,
            filename=doc.filename,
            file_type=doc.file_type or "",
            file_size=doc.file_size or 0,
            status=doc.status or "pending",
            chunk_count=doc.chunk_count or 0,
            created_at=doc.created_at
        )
        for doc in documents
    ]
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size
    }


@router.post("/{kb_id}/documents", summary="上传文档")
async def upload_document(
    kb_id: int,
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session)
):
    """
    上传文档到知识库
    
    支持格式：PDF, Word, Excel, Markdown, TXT, 图片等
    """
    from app.services.document_processor import document_processor, process_document_task
    
    # 检查知识库是否存在
    kb_result = await session.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    )
    kb = kb_result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail=f"知识库 {kb_id} 不存在")
    
    results = []
    for file in files:
        # 获取文件类型
        file_type = file.filename.split(".")[-1].lower() if file.filename else "unknown"
        
        # 读取文件内容
        content = await file.read()
        file_size = len(content)
        
        # 保存文件到磁盘
        try:
            file_path = await document_processor.save_file(kb_id, file.filename, content)
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "failed",
                "message": f"文件保存失败: {str(e)}"
            })
            continue
        
        # 创建文档记录
        doc = Document(
            kb_id=kb_id,
            filename=file.filename,
            file_type=file_type,
            file_size=file_size,
            file_path=file_path,
            status="pending",
        )
        session.add(doc)
        await session.flush()  # 获取doc.id
        
        # 异步处理文档
        import asyncio
        asyncio.create_task(process_document_task(doc.id, kb_id, file_path))
        
        results.append({
            "filename": file.filename,
            "status": "pending",
            "message": "文档已上传，正在处理中"
        })
    
    # 更新知识库文档数量
    kb.document_count = (kb.document_count or 0) + len([r for r in results if r["status"] != "failed"])
    
    await session.commit()
    
    return {"uploaded": results}


@router.get("/{kb_id}/documents/{doc_id}", response_model=DocumentResponse, summary="获取文档详情")
async def get_document(
    kb_id: int,
    doc_id: int,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session)
):
    """获取文档详情"""
    result = await session.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.kb_id == kb_id
        )
    )
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail=f"文档 {doc_id} 不存在")
    
    return DocumentResponse(
        id=doc.id,
        kb_id=doc.kb_id,
        filename=doc.filename,
        file_type=doc.file_type or "",
        file_size=doc.file_size or 0,
        status=doc.status or "pending",
        chunk_count=doc.chunk_count or 0,
        created_at=doc.created_at
    )


@router.delete("/{kb_id}/documents/batch", summary="批量删除文档")
async def delete_documents_batch(
    kb_id: int,
    doc_ids: List[int],
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session)
):
    """批量删除文档"""
    # 检查知识库是否存在
    result = await session.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    )
    kb = result.scalar_one_or_none()
    
    if not kb:
        raise HTTPException(status_code=404, detail=f"知识库 {kb_id} 不存在")
    
    if not doc_ids:
        return {"message": "未选择文档", "deleted_count": 0}

    # 查询要删除的文档 (确认属于该KB)
    docs_result = await session.execute(
        select(Document).where(
            Document.id.in_(doc_ids),
            Document.kb_id == kb_id
        )
    )
    docs = docs_result.scalars().all()
    
    if not docs:
        return {"message": "未找到匹配的文档", "deleted_count": 0}
    
    valid_doc_ids = [doc.id for doc in docs]
    
    # 删除关联的分片
    await session.execute(
        delete(DocumentChunk).where(DocumentChunk.document_id.in_(valid_doc_ids))
    )
    
    # 删除文档
    await session.execute(
        delete(Document).where(Document.id.in_(valid_doc_ids))
    )
    
    # 更新知识库文档数量
    deleted_count = len(valid_doc_ids)
    if kb:
        kb.document_count = max(0, (kb.document_count or 0) - deleted_count)
        
    await session.commit()
    
    return {"message": f"已批量删除 {deleted_count} 个文档", "deleted_count": deleted_count}


@router.delete("/{kb_id}/documents/{doc_id}", summary="删除文档")
async def delete_document(
    kb_id: int,
    doc_id: int,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session)
):
    """删除文档"""
    # 查询文档
    result = await session.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.kb_id == kb_id
        )
    )
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail=f"文档 {doc_id} 不存在")
    
    # 删除关联的分片
    await session.execute(
        delete(DocumentChunk).where(DocumentChunk.document_id == doc_id)
    )
    
    # 删除文档
    await session.delete(doc)
    
    # 更新知识库文档数量
    kb_result = await session.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
    )
    kb = kb_result.scalar_one_or_none()
    if kb:
        kb.document_count = max(0, (kb.document_count or 0) - 1)
    
    return {"message": f"文档 {doc_id} 已删除"}





@router.post("/{kb_id}/documents/{doc_id}/reprocess", summary="重新处理文档")
async def reprocess_document(
    kb_id: int,
    doc_id: int,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session)
):
    """重新解析和向量化文档"""
    from app.services.document_processor import document_processor, process_document_task
    import asyncio
    import os
    
    # 查询文档
    result = await session.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.kb_id == kb_id
        )
    )
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail=f"文档 {doc_id} 不存在")
    
    # 检查文件路径是否存在
    if not doc.file_path:
        raise HTTPException(status_code=400, detail="文档没有关联的文件路径，无法重新处理")
    
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=400, detail=f"文档文件 '{doc.filename}' 不存在于服务器")
    
    # 删除旧的切片数据
    await session.execute(
        delete(DocumentChunk).where(DocumentChunk.document_id == doc_id)
    )
    
    # 删除ES中的旧索引数据
    try:
        from app.core.rag import retriever
        # 删除该文档的所有切片索引
        if doc.chunk_count and doc.chunk_count > 0:
            doc_ids_to_delete = [f"{doc_id}_{i}" for i in range(doc.chunk_count)]
            for es_doc_id in doc_ids_to_delete:
                try:
                    await retriever.delete_document(kb_id, es_doc_id)
                except:
                    pass  # 忽略删除失败（可能已不存在）
    except Exception as e:
        logger.warning(f"清理ES索引时出错: {e}")
    
    # 更新状态为处理中，重置切片计数
    doc.status = "processing"
    doc.chunk_count = 0
    doc.updated_at = datetime.now()
    await session.commit()
    
    # 异步触发重新处理任务
    asyncio.create_task(process_document_task(doc.id, kb_id, doc.file_path))
    
    return {"message": "文档正在重新处理中"}


@router.get("/{kb_id}/documents/{doc_id}/chunks", summary="获取文档切片列表")
async def get_document_chunks(
    kb_id: int,
    doc_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取文档的切片列表
    
    返回文档经过RAG处理后的切片数据，包括内容、位置信息等
    """
    # 验证文档存在
    result = await session.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.kb_id == kb_id
        )
    )
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail=f"文档 {doc_id} 不存在")
    
    # 查询切片总数
    count_result = await session.execute(
        select(func.count(DocumentChunk.id)).where(
            DocumentChunk.document_id == doc_id
        )
    )
    total = count_result.scalar() or 0
    
    # 查询切片列表
    result = await session.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == doc_id)
        .order_by(DocumentChunk.chunk_index)
        .offset((page - 1) * size)
        .limit(size)
    )
    chunks = result.scalars().all()
    
    return {
        "items": [
            {
                "id": chunk.id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "content_length": chunk.content_length,
                "doc_metadata": chunk.doc_metadata,
                "created_at": chunk.created_at.isoformat() if chunk.created_at else None,
            }
            for chunk in chunks
        ],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/{kb_id}/documents/{doc_id}/download", summary="下载文档")
async def download_document(
    kb_id: int,
    doc_id: int,
    token: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_async_session)
):
    """
    下载文档原始文件
    """
    from fastapi.responses import FileResponse
    from urllib.parse import quote
    import os
    
    # 验证token（可以通过query参数传递）
    if not token:
        raise HTTPException(status_code=401, detail="未授权")
    
    # 查询文档
    result = await session.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.kb_id == kb_id
        )
    )
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail=f"文档 {doc_id} 不存在")
    
    # 检查文件路径是否存在
    if not doc.file_path:
        raise HTTPException(status_code=404, detail=f"文档 '{doc.filename}' 没有关联的文件路径")
    
    # 检查文件是否存在
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail=f"文档文件 '{doc.filename}' 不存在于服务器")
    
    # 根据文件类型设置media_type
    media_types = {
        "txt": "text/plain; charset=utf-8",
        "pdf": "application/pdf",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xls": "application/vnd.ms-excel",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "md": "text/markdown; charset=utf-8",
        "html": "text/html; charset=utf-8",
    }
    media_type = media_types.get(doc.file_type.lower(), "application/octet-stream")
    
    # 对文件名进行URL编码以支持中文
    encoded_filename = quote(doc.filename)
    
    # 返回文件，设置正确的Content-Disposition
    return FileResponse(
        path=doc.file_path,
        filename=doc.filename,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename=\"{encoded_filename}\"; filename*=UTF-8''{encoded_filename}"
        }
    )


# ==================== 搜索与问答 ====================

@router.post("/search", response_model=List[SearchResult], summary="知识检索")
async def search(
    request: SearchRequest,
    token: str = Depends(oauth2_scheme)
):
    """
    在知识库中进行语义检索
    
    - **query**: 查询内容
    - **kb_ids**: 可选，指定搜索的知识库ID列表
    - **top_k**: 返回结果数量
    - **score_threshold**: 最低相关度阈值
    """
    from app.core.rag import embedding_service, retriever
    
    try:
        # 1. 向量化查询
        query_embedding = await embedding_service.embed(request.query)
        
        # 2. 检索
        kb_ids = request.kb_ids or []
        results = await retriever.search(
            kb_ids=kb_ids,
            query_vector=query_embedding.vector,
            query_text=request.query,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
        )
        
        # 3. 转换为响应格式
        return [
            SearchResult(
                chunk_id=r.chunk_index or 0,
                document_id=r.document_id or 0,
                document_name=r.metadata.get("filename", "") if r.metadata else "",
                content=r.content,
                score=r.score,
                kb_id=r.kb_id,
                metadata=r.metadata,
            )
            for r in results
        ]
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        return []


@router.post("/qa", response_model=QAResponse, summary="知识问答")
async def question_answer(
    request: QARequest,
    token: str = Depends(oauth2_scheme)
):
    """
    基于知识库的智能问答
    
    1. 检索相关知识片段
    2. 使用大模型生成答案
    3. 返回答案及引用来源
    """
    from app.core.rag import rag_service
    
    try:
        kb_ids = request.kb_ids or []
        
        result = await rag_service.answer(
            question=request.question,
            kb_ids=kb_ids,
        )
        
        return QAResponse(
            answer=result.answer,
            sources=[
                SearchResult(
                    chunk_id=s.get("chunk_index", 0),
                    document_id=s.get("document_id", 0),
                    document_name=s.get("metadata", {}).get("filename", "未知文档") if isinstance(s.get("metadata"), dict) else "未知文档",
                    content=s.get("content", ""),
                    score=s.get("score", 0),
                    kb_id=s.get("kb_id"),
                    metadata=s.get("metadata", {}),
                )
                for s in result.sources
            ]
        )
    except Exception as e:
        logger.error(f"问答失败: {e}")
        return QAResponse(
            answer=f"抱歉，处理问题时发生错误: {str(e)}",
            sources=[]
        )

