"""
RAG 知识库模块
"""

from app.core.rag.config import (
    rag_config,
    get_rag_config,
    reload_rag_config,
    RAGConfig,
)
from app.core.rag.parser import document_parser, DocumentParser, ParsedContent
from app.core.rag.splitter import create_splitter, TextChunk
from app.core.rag.embedder import embedding_service, EmbeddingResult
from app.core.rag.retriever import retriever, SearchResult
from app.core.rag.reranker import rerank_service, RerankResult
from app.core.rag.ocr import ocr_service, OCRResult
from app.core.rag.qa import rag_service, RAGResult
from app.core.rag.multimodal import (
    multimodal_service,
    ImageUnderstandingResult,
    VideoContentResult,
)

__all__ = [
    "document_parser",
    "DocumentParser",
    "ParsedContent",
    "create_splitter",
    "TextChunk",
    "embedding_service",
    "EmbeddingResult",
    "retriever",
    "SearchResult",
    "rerank_service",
    "RerankResult",
    "ocr_service",
    "OCRResult",
    "rag_service",
    "RAGResult",
    "multimodal_service",
    "ImageUnderstandingResult",
    "VideoContentResult",
]
