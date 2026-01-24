"""
向量检索服务
基于Elasticsearch实现向量存储和检索
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from elasticsearch import AsyncElasticsearch
from loguru import logger

from app.config import settings


@dataclass
class SearchResult:
    """搜索结果"""
    id: str
    score: float
    content: str
    metadata: Dict[str, Any]
    document_id: Optional[int] = None
    chunk_index: Optional[int] = None
    kb_id: Optional[int] = None


class ElasticsearchRetriever:
    """Elasticsearch向量检索器"""
    
    def __init__(
        self,
        hosts: List[str] = None,
        index_prefix: str = "skb",
        vector_dimension: int = 1024,
    ):
        self.hosts = hosts or [settings.es_url]
        self.index_prefix = index_prefix or settings.es_index_prefix
        self.vector_dimension = vector_dimension
        self._client: Optional[AsyncElasticsearch] = None
    
    async def get_client(self) -> AsyncElasticsearch:
        """获取ES客户端"""
        if self._client is None:
            use_auth = bool(settings.es_password)
            logger.info(f"初始化ES客户端: hosts={self.hosts}, use_auth={use_auth}")
            self._client = AsyncElasticsearch(
                hosts=self.hosts,
                basic_auth=(settings.es_user, settings.es_password) if use_auth else None,
            )
        return self._client
    
    async def close(self):
        """关闭连接"""
        if self._client:
            await self._client.close()
            self._client = None
    
    def _get_index_name(self, kb_id: int) -> str:
        """获取索引名称"""
        return f"{self.index_prefix}_kb_{kb_id}"
    
    async def create_index(self, kb_id: int) -> bool:
        """创建知识库索引"""
        index_name = self._get_index_name(kb_id)
        client = await self.get_client()
        
        # 检查索引是否存在
        try:
            exists = await client.indices.exists(index=index_name)
            if exists:
                logger.info(f"索引已存在: {index_name}")
                return True
        except Exception as e:
            logger.warning(f"检查索引存在时出错: {type(e).__name__}: {e}")
            if hasattr(e, 'body'):
                logger.warning(f"详情: {e.body}")
            # 假设不存在，继续创建
        
        # 创建索引
        mappings = {
            "properties": {
                "content": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_smart",
                },
                "vector": {
                    "type": "dense_vector",
                    "dims": self.vector_dimension,
                    "index": True,
                    "similarity": "cosine",
                },
                "document_id": {"type": "integer"},
                "chunk_index": {"type": "integer"},
                "kb_id": {"type": "integer"},
                "metadata": {"type": "object", "enabled": False},
                "created_at": {"type": "date"},
            }
        }
        
        settings_body = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "ik_max_word": {
                        "type": "custom",
                        "tokenizer": "ik_max_word",
                    },
                    "ik_smart": {
                        "type": "custom",
                        "tokenizer": "ik_smart",
                    },
                }
            }
        }
        
        try:
            await client.indices.create(
                index=index_name,
                mappings=mappings,
                settings=settings_body,
            )
            logger.info(f"索引创建成功: {index_name}")
            return True
        except Exception as e:
            # 如果IK分词器不存在，使用标准分词器
            logger.warning(f"使用IK分词器创建索引失败，尝试使用标准分词器: {e}")
            mappings["properties"]["content"]["analyzer"] = "standard"
            mappings["properties"]["content"]["search_analyzer"] = "standard"
            del settings_body["analysis"]
            
            try:
                await client.indices.create(
                    index=index_name,
                    mappings=mappings,
                    settings=settings_body,
                )
                logger.info(f"索引创建成功(标准分词器): {index_name}")
                return True
            except Exception as e2:
                logger.error(f"索引创建失败: {type(e2).__name__}: {e2}")
                # 尝试获取更详细的错误信息
                if hasattr(e2, 'body'):
                    logger.error(f"ES错误详情: {e2.body}")
                raise
    
    async def delete_index(self, kb_id: int) -> bool:
        """删除知识库索引"""
        index_name = self._get_index_name(kb_id)
        client = await self.get_client()
        
        if await client.indices.exists(index=index_name):
            await client.indices.delete(index=index_name)
            logger.info(f"索引删除成功: {index_name}")
            return True
        return False
    
    async def index_document(
        self,
        kb_id: int,
        doc_id: str,
        content: str,
        vector: List[float],
        document_id: int,
        chunk_index: int,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """索引文档"""
        index_name = self._get_index_name(kb_id)
        client = await self.get_client()
        
        body = {
            "content": content,
            "vector": vector,
            "document_id": document_id,
            "chunk_index": chunk_index,
            "kb_id": kb_id,
            "metadata": metadata or {},
            "created_at": "now",
        }
        
        result = await client.index(
            index=index_name,
            id=doc_id,
            document=body,
        )
        
        return result["_id"]
    
    async def bulk_index(
        self,
        kb_id: int,
        documents: List[Dict[str, Any]],
    ) -> int:
        """批量索引文档"""
        from datetime import datetime
        
        index_name = self._get_index_name(kb_id)
        client = await self.get_client()
        
        now = datetime.utcnow().isoformat()
        operations = []
        for doc in documents:
            operations.append({"index": {"_index": index_name, "_id": doc["id"]}})
            operations.append({
                "content": doc["content"],
                "vector": doc["vector"],
                "document_id": doc["document_id"],
                "chunk_index": doc["chunk_index"],
                "kb_id": kb_id,
                "metadata": doc.get("metadata", {}),
                "created_at": now,
            })
        
        result = await client.bulk(operations=operations)
        
        success_count = 0
        for item in result["items"]:
            if item["index"]["status"] in [200, 201]:
                success_count += 1
            else:
                logger.error(f"批量索引项失败: {item['index']}")
        
        logger.info(f"批量索引完成: {success_count}/{len(documents)}")
        
        return success_count
    
    async def delete_by_document(self, kb_id: int, document_id: int) -> int:
        """删除文档的所有分片"""
        index_name = self._get_index_name(kb_id)
        client = await self.get_client()
        
        result = await client.delete_by_query(
            index=index_name,
            query={"term": {"document_id": document_id}},
        )
        
        deleted = result.get("deleted", 0)
        logger.info(f"删除文档分片: document_id={document_id}, 删除数量={deleted}")
        
        return deleted
    
    async def search(
        self,
        kb_ids: List[int],
        query_vector: List[float],
        query_text: str = None,
        top_k: int = 10,
        score_threshold: float = 0.5,
        filters: Dict[str, Any] = None,
    ) -> List[SearchResult]:
        """向量检索"""
        client = await self.get_client()
        
        # 构建索引列表
        indices = [self._get_index_name(kb_id) for kb_id in kb_ids]
        
        # 构建查询
        knn = {
            "field": "vector",
            "query_vector": query_vector,
            "k": top_k,
            "num_candidates": top_k * 2,
        }
        
        # 添加过滤条件
        if filters:
            knn["filter"] = {"bool": {"must": []}}
            for key, value in filters.items():
                knn["filter"]["bool"]["must"].append({"term": {key: value}})
        
        # 混合检索：向量 + 关键词
        query_body = {"knn": knn}
        
        if query_text:
            query_body["query"] = {
                "bool": {
                    "should": [
                        {"match": {"content": query_text}},
                    ]
                }
            }
        
        try:
            result = await client.search(
                index=",".join(indices),
                body=query_body,
                size=top_k,
                ignore_unavailable=True,
            )
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
        
        # 解析结果
        hits = result.get("hits", {}).get("hits", [])
        results = []
        
        for hit in hits:
            score = hit.get("_score", 0)
            
            # 过滤低分结果
            if score < score_threshold:
                continue
            
            source = hit.get("_source", {})
            results.append(SearchResult(
                id=hit["_id"],
                score=score,
                content=source.get("content", ""),
                metadata=source.get("metadata", {}),
                document_id=source.get("document_id"),
                chunk_index=source.get("chunk_index"),
                kb_id=source.get("kb_id"),
            ))
        
        logger.debug(f"检索完成: 返回{len(results)}条结果")
        return results
    
    async def hybrid_search(
        self,
        kb_ids: List[int],
        query_vector: List[float],
        query_text: str,
        top_k: int = 10,
        vector_weight: float = 0.7,
        text_weight: float = 0.3,
    ) -> List[SearchResult]:
        """混合检索（向量 + 关键词）"""
        client = await self.get_client()
        indices = [self._get_index_name(kb_id) for kb_id in kb_ids]
        
        # RRF (Reciprocal Rank Fusion) 混合检索
        query_body = {
            "sub_searches": [
                {
                    "query": {
                        "knn": {
                            "field": "vector",
                            "query_vector": query_vector,
                            "k": top_k,
                            "num_candidates": top_k * 2,
                        }
                    }
                },
                {
                    "query": {
                        "match": {
                            "content": query_text
                        }
                    }
                }
            ],
            "rank": {
                "rrf": {
                    "window_size": top_k * 2,
                    "rank_constant": 60,
                }
            }
        }
        
        try:
            result = await client.search(
                index=",".join(indices),
                body=query_body,
                size=top_k,
                ignore_unavailable=True,
            )
        except Exception as e:
            # 如果RRF不支持，回退到普通搜索
            logger.warning(f"RRF搜索失败，回退到普通搜索: {e}")
            return await self.search(kb_ids, query_vector, query_text, top_k)
        
        hits = result.get("hits", {}).get("hits", [])
        results = []
        
        for hit in hits:
            source = hit.get("_source", {})
            results.append(SearchResult(
                id=hit["_id"],
                score=hit.get("_score", 0),
                content=source.get("content", ""),
                metadata=source.get("metadata", {}),
                document_id=source.get("document_id"),
                chunk_index=source.get("chunk_index"),
                kb_id=source.get("kb_id"),
            ))
        
        return results


# 创建全局检索器实例
retriever = ElasticsearchRetriever(
    vector_dimension=settings.embedding_dimension,
)
