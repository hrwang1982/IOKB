"""
向量化服务
支持多种Embedding提供商和本地部署
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import httpx
from loguru import logger

from app.config import settings


@dataclass
class EmbeddingResult:
    """向量化结果"""
    vector: List[float]
    token_count: int = 0
    model: str = ""


class BaseEmbedder(ABC):
    """Embedding基类"""
    
    @abstractmethod
    async def embed(self, text: str) -> EmbeddingResult:
        """对单个文本进行向量化"""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """批量向量化"""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """向量维度"""
        pass


class AliyunEmbedder(BaseEmbedder):
    """阿里云Embedding服务（OpenAI兼容格式）"""
    
    def __init__(
        self,
        api_key: str = None,
        model_name: str = "text-embedding-v3",
        api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    ):
        self.api_key = api_key or settings.embedding_api_key
        self.model_name = model_name
        self.api_base = api_base
        self._dimension = settings.embedding_dimension
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    async def embed(self, text: str) -> EmbeddingResult:
        """单个文本向量化"""
        results = await self.embed_batch([text])
        return results[0]
    
    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """批量向量化（使用OpenAI兼容格式）"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.api_base}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model_name,
                        "input": texts,
                    },
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as e:
                # 记录详细错误信息
                error_body = e.response.text
                logger.error(f"Embedding API错误: status={e.response.status_code}, body={error_body}")
                raise
        
        results = []
        for item in data.get("data", []):
            results.append(EmbeddingResult(
                vector=item.get("embedding", []),
                token_count=data.get("usage", {}).get("total_tokens", 0) // len(texts),
                model=self.model_name,
            ))
        
        return results


class OpenAIEmbedder(BaseEmbedder):
    """OpenAI Embedding服务"""
    
    def __init__(
        self,
        api_key: str = None,
        model_name: str = "text-embedding-3-small",
        api_base: str = "https://api.openai.com/v1",
    ):
        self.api_key = api_key or settings.embedding_api_key
        self.model_name = model_name
        self.api_base = api_base
        self._dimension = 1536 if "small" in model_name else 3072
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    async def embed(self, text: str) -> EmbeddingResult:
        """单个文本向量化"""
        results = await self.embed_batch([text])
        return results[0]
    
    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """批量向量化"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.api_base}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "input": texts,
                },
            )
            response.raise_for_status()
            data = response.json()
        
        results = []
        for item in data.get("data", []):
            results.append(EmbeddingResult(
                vector=item.get("embedding", []),
                token_count=data.get("usage", {}).get("total_tokens", 0) // len(texts),
                model=self.model_name,
            ))
        
        return results


class LocalEmbedder(BaseEmbedder):
    """本地部署Embedding服务"""
    
    def __init__(
        self,
        local_url: str = None,
        model_name: str = "local-embedding",
        dimension: int = 1024,
    ):
        self.local_url = local_url or settings.embedding_local_url
        self.model_name = model_name
        self._dimension = dimension
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    async def embed(self, text: str) -> EmbeddingResult:
        """单个文本向量化"""
        results = await self.embed_batch([text])
        return results[0]
    
    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """批量向量化"""
        if not self.local_url:
            raise ValueError("本地Embedding服务URL未配置")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.local_url}/embed",
                json={
                    "texts": texts,
                    "model": self.model_name,
                },
            )
            response.raise_for_status()
            data = response.json()
        
        results = []
        embeddings = data.get("embeddings", [])
        
        for emb in embeddings:
            results.append(EmbeddingResult(
                vector=emb,
                token_count=0,
                model=self.model_name,
            ))
        
        return results


class EmbeddingService:
    """Embedding服务管理"""
    
    def __init__(self):
        self._embedder: Optional[BaseEmbedder] = None
    
    def get_embedder(self) -> BaseEmbedder:
        """获取Embedder实例"""
        if self._embedder is not None:
            return self._embedder
        
        # 根据配置创建Embedder
        deploy_mode = settings.embedding_deploy_mode
        provider = settings.embedding_provider
        
        if deploy_mode == "local":
            self._embedder = LocalEmbedder(
                local_url=settings.embedding_local_url,
                model_name=settings.embedding_model_name,
                dimension=settings.embedding_dimension,
            )
        elif provider == "aliyun":
            self._embedder = AliyunEmbedder(
                api_key=settings.embedding_api_key,
                model_name=settings.embedding_model_name,
                api_base=settings.embedding_api_base or "https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
        elif provider == "openai":
            self._embedder = OpenAIEmbedder(
                api_key=settings.embedding_api_key,
                model_name=settings.embedding_model_name,
                api_base=settings.embedding_api_base or "https://api.openai.com/v1",
            )
        else:
            # 默认使用本地服务
            self._embedder = LocalEmbedder(
                local_url=settings.embedding_local_url,
                model_name=settings.embedding_model_name,
                dimension=settings.embedding_dimension,
            )
        
        logger.info(f"创建Embedder: provider={provider}, deploy_mode={deploy_mode}")
        return self._embedder
    
    async def embed(self, text: str) -> EmbeddingResult:
        """对单个文本进行向量化"""
        embedder = self.get_embedder()
        return await embedder.embed(text)
    
    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 10,
    ) -> List[EmbeddingResult]:
        """
        批量向量化
        
        Args:
            texts: 文本列表
            batch_size: 每批处理数量
        """
        embedder = self.get_embedder()
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_results = await embedder.embed_batch(batch)
            results.extend(batch_results)
            logger.debug(f"向量化进度: {min(i + batch_size, len(texts))}/{len(texts)}")
        
        return results
    
    @property
    def dimension(self) -> int:
        """获取向量维度"""
        return self.get_embedder().dimension


# 创建全局服务实例
embedding_service = EmbeddingService()
