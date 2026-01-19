"""
RAG问答服务
整合检索、重排序和大模型生成
"""

from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional

from loguru import logger

from app.core.rag.embedder import embedding_service, EmbeddingResult
from app.core.rag.retriever import retriever, SearchResult
from app.core.rag.reranker import rerank_service, RerankResult
from app.core.llm.gateway import llm_service, Message, LLMResponse


# RAG问答的Prompt模板
RAG_SYSTEM_PROMPT = """你是一个专业的知识库问答助手。请根据以下检索到的上下文信息回答用户的问题。

注意事项：
1. 仅根据提供的上下文信息回答问题，不要编造信息
2. 如果上下文中没有相关信息，请明确告知用户
3. 回答要准确、简洁、专业
4. 适当引用上下文中的关键信息"""

RAG_USER_PROMPT = """上下文信息：
{context}

用户问题：{question}

请根据上下文信息回答用户的问题。"""


@dataclass
class RAGResult:
    """RAG问答结果"""
    answer: str
    sources: List[Dict[str, Any]]
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class RetrievalContext:
    """检索上下文"""
    content: str
    score: float
    document_id: Optional[int] = None
    chunk_index: Optional[int] = None
    metadata: Dict[str, Any] = None


class RAGService:
    """RAG问答服务"""
    
    def __init__(
        self,
        use_rerank: bool = True,
        top_k_retrieve: int = 20,
        top_k_rerank: int = 5,
        score_threshold: float = 0.5,
    ):
        self.use_rerank = use_rerank
        self.top_k_retrieve = top_k_retrieve
        self.top_k_rerank = top_k_rerank
        self.score_threshold = score_threshold
    
    async def retrieve(
        self,
        query: str,
        kb_ids: List[int],
        top_k: int = None,
    ) -> List[RetrievalContext]:
        """检索相关文档"""
        top_k = top_k or self.top_k_retrieve
        
        # 1. 向量化查询
        query_embedding = await embedding_service.embed(query)
        
        # 2. 向量检索
        search_results = await retriever.search(
            kb_ids=kb_ids,
            query_vector=query_embedding.vector,
            query_text=query,
            top_k=top_k,
            score_threshold=self.score_threshold,
        )
        
        if not search_results:
            logger.warning(f"检索无结果: query={query[:50]}...")
            return []
        
        logger.info(f"检索到{len(search_results)}条结果")
        
        # 3. 重排序（可选）
        if self.use_rerank and len(search_results) > 1:
            documents = [r.content for r in search_results]
            rerank_results = await rerank_service.rerank(
                query=query,
                documents=documents,
                top_k=self.top_k_rerank,
            )
            
            # 根据重排序结果重新组织
            reranked = []
            for rr in rerank_results:
                original = search_results[rr.index]
                reranked.append(RetrievalContext(
                    content=original.content,
                    score=rr.score,
                    document_id=original.document_id,
                    chunk_index=original.chunk_index,
                    metadata=original.metadata,
                ))
            
            logger.info(f"重排序后保留{len(reranked)}条结果")
            return reranked
        
        # 不使用重排序，直接返回top_k
        return [
            RetrievalContext(
                content=r.content,
                score=r.score,
                document_id=r.document_id,
                chunk_index=r.chunk_index,
                metadata=r.metadata,
            )
            for r in search_results[:self.top_k_rerank]
        ]
    
    async def answer(
        self,
        question: str,
        kb_ids: List[int],
        system_prompt: str = None,
        temperature: float = 0.7,
    ) -> RAGResult:
        """RAG问答"""
        # 1. 检索相关文档
        contexts = await self.retrieve(question, kb_ids)
        
        if not contexts:
            return RAGResult(
                answer="抱歉，未在知识库中找到相关信息。",
                sources=[],
            )
        
        # 2. 构建上下文
        context_str = self._build_context(contexts)
        
        # 3. 构建消息
        messages = [
            Message(role="system", content=system_prompt or RAG_SYSTEM_PROMPT),
            Message(role="user", content=RAG_USER_PROMPT.format(
                context=context_str,
                question=question,
            )),
        ]
        
        # 4. 调用大模型
        response = await llm_service.chat(messages, temperature=temperature)
        
        # 5. 构建来源
        sources = [
            {
                "content": ctx.content[:200] + "..." if len(ctx.content) > 200 else ctx.content,
                "score": ctx.score,
                "document_id": ctx.document_id,
                "chunk_index": ctx.chunk_index,
            }
            for ctx in contexts
        ]
        
        return RAGResult(
            answer=response.content,
            sources=sources,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
        )
    
    async def answer_stream(
        self,
        question: str,
        kb_ids: List[int],
        system_prompt: str = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """RAG流式问答"""
        # 1. 检索相关文档
        contexts = await self.retrieve(question, kb_ids)
        
        if not contexts:
            yield "抱歉，未在知识库中找到相关信息。"
            return
        
        # 2. 构建上下文
        context_str = self._build_context(contexts)
        
        # 3. 构建消息
        messages = [
            Message(role="system", content=system_prompt or RAG_SYSTEM_PROMPT),
            Message(role="user", content=RAG_USER_PROMPT.format(
                context=context_str,
                question=question,
            )),
        ]
        
        # 4. 流式调用大模型
        async for chunk in llm_service.chat_stream(messages, temperature=temperature):
            yield chunk
    
    def _build_context(self, contexts: List[RetrievalContext]) -> str:
        """构建上下文字符串"""
        parts = []
        for i, ctx in enumerate(contexts):
            parts.append(f"[文档{i + 1}]\n{ctx.content}")
        return "\n\n".join(parts)


# 创建全局RAG服务实例
rag_service = RAGService()
