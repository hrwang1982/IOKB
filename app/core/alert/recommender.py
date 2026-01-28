"""
知识库方案推荐服务
基于告警信息从知识库检索相关解决方案
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.rag import rag_service, RAGResult
from app.core.alert.analyzer import AlertContext


@dataclass
class SolutionRecommendation:
    """解决方案推荐"""
    title: str
    content: str
    relevance_score: float
    source_doc_id: Optional[str] = None
    source_doc_name: Optional[str] = None
    category: str = ""  # 方案分类


@dataclass
class RecommendationResult:
    """推荐结果"""
    recommendations: List[SolutionRecommendation]
    rag_answer: Optional[str] = None
    query_used: str = ""
    total_candidates: int = 0


class SolutionRecommender:
    """解决方案推荐器"""
    
    def __init__(
        self,
        max_recommendations: int = 5,
        min_relevance_score: float = 0.5,
        use_rag_answer: bool = True,  # 是否使用RAG生成综合回答
    ):
        self.max_recommendations = max_recommendations
        self.min_relevance_score = min_relevance_score
        self.use_rag_answer = use_rag_answer
    
    async def recommend(
        self,
        context: AlertContext,
        knowledge_base_id: str = None,  # 指定知识库
    ) -> RecommendationResult:
        """根据告警上下文推荐解决方案"""
        # 构建检索查询
        query = self._build_query(context)
        
        recommendations = []
        rag_answer = None
        
        try:
            if self.use_rag_answer:
                # 使用RAG服务获取综合回答和引用来源
                result = await rag_service.answer(
                    question=query,
                    kb_ids=[], # TODO: 指定默认知识库
                )
                
                rag_answer = result.answer
                
                # 从来源构建推荐列表
                for source in result.sources:
                    if source.get("score", 0) >= self.min_relevance_score:
                        recommendations.append(SolutionRecommendation(
                            title=source.get("title", "解决方案"),
                            content=source.get("content", ""),
                            relevance_score=source.get("score", 0),
                            source_doc_id=source.get("document_id"),
                            source_doc_name=source.get("document_name"),
                            category=source.get("category", ""),
                        ))
            else:
                # 仅检索不生成回答
                chunks = await rag_service.retrieve(
                    query=query,
                    top_k=self.max_recommendations * 2,
                )
                
                for chunk in chunks:
                    if chunk.score >= self.min_relevance_score:
                        recommendations.append(SolutionRecommendation(
                            title=chunk.metadata.get("title", "解决方案"),
                            content=chunk.content,
                            relevance_score=chunk.score,
                            source_doc_id=chunk.document_id,
                            source_doc_name=chunk.metadata.get("name"),
                        ))
            
            # 排序并限制数量
            recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
            recommendations = recommendations[:self.max_recommendations]
            
            logger.info(
                f"方案推荐完成: query={query[:50]}..., "
                f"found={len(recommendations)}"
            )
            
        except Exception as e:
            logger.error(f"方案推荐失败: {e}")
        
        return RecommendationResult(
            recommendations=recommendations,
            rag_answer=rag_answer,
            query_used=query,
            total_candidates=len(recommendations),
        )
    
    def _build_query(self, context: AlertContext) -> str:
        """根据告警上下文构建检索查询"""
        parts = []
        
        alert = context.alert
        
        # 告警标题和内容
        title = alert.get("title", "")
        content = alert.get("content", "")
        
        if title:
            parts.append(title)
        if content:
            # 截断过长的内容
            parts.append(content[:300])
        
        # CI类型信息
        if context.ci:
            ci_type = context.ci.get("type_name", "")
            if ci_type:
                parts.append(f"设备类型: {ci_type}")
        
        # 关键词补充
        level = alert.get("level", "")
        if level == "critical":
            parts.append("紧急故障处理")
        
        # 组合查询
        query = " ".join(parts)
        
        # 添加问题解决意图
        query = f"如何解决以下问题: {query}"
        
        return query
    
    async def recommend_by_keywords(
        self,
        keywords: List[str],
        ci_type: str = None,
    ) -> RecommendationResult:
        """根据关键词推荐方案"""
        query_parts = keywords.copy()
        if ci_type:
            query_parts.append(f"设备类型: {ci_type}")
        
        query = " ".join(query_parts)
        
        recommendations = []
        
        try:
            chunks = await rag_service.retrieve(
                query=query,
                top_k=self.max_recommendations * 2,
            )
            
            for chunk in chunks:
                if chunk.score >= self.min_relevance_score:
                    recommendations.append(SolutionRecommendation(
                        title=chunk.metadata.get("title", "解决方案"),
                        content=chunk.content,
                        relevance_score=chunk.score,
                        source_doc_id=chunk.document_id,
                    ))
            
            recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
            recommendations = recommendations[:self.max_recommendations]
            
        except Exception as e:
            logger.error(f"关键词推荐失败: {e}")
        
        return RecommendationResult(
            recommendations=recommendations,
            query_used=query,
        )


class SolutionMatcher:
    """方案匹配器 - 基于规则的快速匹配"""
    
    def __init__(self):
        # 预定义的规则映射
        self.rule_mappings = {
            # 告警关键词 -> 解决方案类别
            "cpu": ["性能优化", "资源扩容"],
            "内存": ["内存优化", "内存泄漏"],
            "磁盘": ["存储扩容", "磁盘清理"],
            "网络": ["网络排查", "连接优化"],
            "超时": ["性能优化", "连接池配置"],
            "连接失败": ["网络排查", "服务恢复"],
            "服务异常": ["服务重启", "日志排查"],
            "宕机": ["紧急恢复", "故障转移"],
        }
    
    def match_categories(self, alert: Dict[str, Any]) -> List[str]:
        """匹配可能的解决方案类别"""
        categories = set()
        
        title = (alert.get("title", "") or "").lower()
        content = (alert.get("content", "") or "").lower()
        text = f"{title} {content}"
        
        for keyword, cats in self.rule_mappings.items():
            if keyword in text:
                categories.update(cats)
        
        return list(categories)
    
    async def quick_match(
        self,
        alert: Dict[str, Any],
    ) -> List[str]:
        """快速匹配，返回建议的解决方案类别"""
        categories = self.match_categories(alert)
        
        if not categories:
            # 默认类别
            level = alert.get("level", "")
            if level == "critical":
                categories = ["紧急处理", "故障恢复"]
            else:
                categories = ["常规排查"]
        
        return categories


# 创建全局服务实例
solution_recommender = SolutionRecommender()
solution_matcher = SolutionMatcher()
