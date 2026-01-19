"""
Rerank重排序服务
对检索结果进行重排序，提高相关性
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

import httpx
from loguru import logger

from app.config import settings


@dataclass
class RerankResult:
    """重排序结果"""
    index: int
    score: float
    text: str


class BaseReranker(ABC):
    """Reranker基类"""
    
    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 10,
    ) -> List[RerankResult]:
        """重排序"""
        pass


class AliyunReranker(BaseReranker):
    """阿里云Rerank服务"""
    
    def __init__(
        self,
        api_key: str = None,
        model_name: str = "gte-rerank",
        api_base: str = "https://dashscope.aliyuncs.com/api/v1",
    ):
        self.api_key = api_key or settings.rerank_api_key
        self.model_name = model_name
        self.api_base = api_base
    
    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 10,
    ) -> List[RerankResult]:
        """重排序"""
        if not documents:
            return []
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_base}/services/rerank/text-rerank/text-rerank",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "input": {
                        "query": query,
                        "documents": documents,
                    },
                    "parameters": {
                        "top_n": min(top_k, len(documents)),
                        "return_documents": True,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
        
        results = []
        for item in data.get("output", {}).get("results", []):
            results.append(RerankResult(
                index=item.get("index", 0),
                score=item.get("relevance_score", 0.0),
                text=item.get("document", {}).get("text", documents[item.get("index", 0)]),
            ))
        
        return results


class LocalReranker(BaseReranker):
    """本地部署Rerank服务"""
    
    def __init__(
        self,
        local_url: str = None,
        model_name: str = "local-rerank",
    ):
        self.local_url = local_url or settings.rerank_local_url
        self.model_name = model_name
    
    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 10,
    ) -> List[RerankResult]:
        """重排序"""
        if not self.local_url:
            raise ValueError("本地Rerank服务URL未配置")
        
        if not documents:
            return []
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.local_url}/rerank",
                json={
                    "query": query,
                    "documents": documents,
                    "top_k": min(top_k, len(documents)),
                },
            )
            response.raise_for_status()
            data = response.json()
        
        results = []
        for item in data.get("results", []):
            results.append(RerankResult(
                index=item.get("index", 0),
                score=item.get("score", 0.0),
                text=item.get("text", documents[item.get("index", 0)]),
            ))
        
        return results


class RerankService:
    """Rerank服务管理"""
    
    def __init__(self):
        self._reranker: Optional[BaseReranker] = None
    
    def get_reranker(self) -> BaseReranker:
        """获取Reranker实例"""
        if self._reranker is not None:
            return self._reranker
        
        provider = settings.rerank_provider
        deploy_mode = settings.rerank_deploy_mode
        
        if deploy_mode == "local":
            self._reranker = LocalReranker(
                local_url=settings.rerank_local_url,
                model_name=settings.rerank_model_name,
            )
        elif provider == "aliyun":
            self._reranker = AliyunReranker(
                api_key=settings.rerank_api_key,
                model_name=settings.rerank_model_name,
                api_base=settings.rerank_api_base or "https://dashscope.aliyuncs.com/api/v1",
            )
        else:
            # 默认使用本地服务
            self._reranker = LocalReranker(
                local_url=settings.rerank_local_url,
                model_name=settings.rerank_model_name,
            )
        
        logger.info(f"创建Reranker: provider={provider}, deploy_mode={deploy_mode}")
        return self._reranker
    
    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 10,
    ) -> List[RerankResult]:
        """重排序"""
        reranker = self.get_reranker()
        return await reranker.rerank(query, documents, top_k)


# 创建全局Rerank服务实例
rerank_service = RerankService()
