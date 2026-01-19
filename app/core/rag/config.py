"""
RAG模块配置管理
从YAML配置文件加载配置
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from loguru import logger


@dataclass
class ParserConfig:
    """文档解析配置"""
    max_file_size_mb: int = 50
    supported_extensions: List[str] = field(default_factory=lambda: [
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".md", ".txt", ".html"
    ])


@dataclass
class SplitterConfig:
    """文本分片配置"""
    default_type: str = "recursive"
    chunk_size: int = 500
    chunk_overlap: int = 100
    min_chunk_size: int = 50
    separators: List[str] = field(default_factory=lambda: [
        "\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""
    ])


@dataclass
class EmbedderConfig:
    """向量化配置"""
    batch_size: int = 32
    max_retries: int = 3
    retry_delay_seconds: int = 1
    normalize: bool = True


@dataclass
class RetrieverConfig:
    """检索配置"""
    default_top_k: int = 5
    max_top_k: int = 50
    min_score_threshold: float = 0.5
    use_hybrid_search: bool = True
    vector_weight: float = 0.7
    keyword_weight: float = 0.3
    rrf_k: int = 60


@dataclass
class RerankerConfig:
    """重排序配置"""
    enabled: bool = True
    top_n: int = 5
    min_score: float = 0.3


@dataclass
class OCRConfig:
    """OCR配置"""
    languages: List[str] = field(default_factory=lambda: ["ch", "en"])
    use_angle_cls: bool = True
    show_log: bool = False


@dataclass
class MultimodalConfig:
    """多模态配置"""
    video_frames_per_second: float = 0.5
    max_video_frames: int = 10
    image_max_size: int = 2048


@dataclass
class QAConfig:
    """问答配置"""
    use_rerank: bool = True
    context_max_tokens: int = 4000
    stream_enabled: bool = True


@dataclass
class PromptsConfig:
    """Prompt模板配置"""
    system_prompt: str = ""
    user_prompt: str = ""
    no_context_prompt: str = ""


@dataclass
class IndexConfig:
    """知识库索引配置"""
    name_prefix: str = "kb"
    shards: int = 1
    replicas: int = 0
    refresh_interval: str = "1s"


@dataclass
class RAGConfig:
    """RAG模块完整配置"""
    parser: ParserConfig = field(default_factory=ParserConfig)
    splitter: SplitterConfig = field(default_factory=SplitterConfig)
    embedder: EmbedderConfig = field(default_factory=EmbedderConfig)
    retriever: RetrieverConfig = field(default_factory=RetrieverConfig)
    reranker: RerankerConfig = field(default_factory=RerankerConfig)
    ocr: OCRConfig = field(default_factory=OCRConfig)
    multimodal: MultimodalConfig = field(default_factory=MultimodalConfig)
    qa: QAConfig = field(default_factory=QAConfig)
    prompts: PromptsConfig = field(default_factory=PromptsConfig)
    index: IndexConfig = field(default_factory=IndexConfig)


class RAGConfigLoader:
    """RAG配置加载器"""
    
    DEFAULT_CONFIG_PATHS = [
        "config/rag.yaml",
        "config/rag.yml",
        "../config/rag.yaml",
        "/etc/skb/rag.yaml",
    ]
    
    # 默认Prompt模板
    DEFAULT_SYSTEM_PROMPT = """你是一个专业的知识库问答助手。请根据提供的上下文信息回答用户的问题。

规则：
1. 只根据上下文信息回答，不要编造信息
2. 如果上下文信息不足以回答问题，请明确告知用户
3. 回答要准确、简洁、专业
4. 如果引用了具体来源，请标注出处"""

    DEFAULT_USER_PROMPT = """请根据以下上下文信息回答问题。

## 上下文信息
{context}

## 用户问题
{question}

请提供准确、简洁的回答："""

    DEFAULT_NO_CONTEXT_PROMPT = """抱歉，在知识库中未找到与您问题相关的信息。

您的问题是：{question}

建议：
1. 尝试换一种方式描述问题
2. 检查是否有相关文档已上传到知识库
3. 联系管理员确认知识库内容"""

    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self._config: Optional[RAGConfig] = None
        self._raw_config: Dict[str, Any] = {}
    
    def _find_config_file(self) -> Optional[str]:
        """查找配置文件"""
        if self.config_path and os.path.exists(self.config_path):
            return self.config_path
        
        # 从项目根目录开始查找
        base_dir = Path(__file__).parent.parent.parent.parent
        
        for path in self.DEFAULT_CONFIG_PATHS:
            full_path = base_dir / path
            if full_path.exists():
                return str(full_path)
        
        return None
    
    def _load_yaml(self) -> Dict[str, Any]:
        """加载YAML配置"""
        config_file = self._find_config_file()
        
        if not config_file:
            logger.warning("未找到RAG配置文件，使用默认配置")
            return {}
        
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                logger.info(f"加载RAG配置文件: {config_file}")
                return data or {}
        except Exception as e:
            logger.error(f"加载RAG配置文件失败: {e}")
            return {}
    
    def load(self) -> RAGConfig:
        """加载配置"""
        if self._config is not None:
            return self._config
        
        self._raw_config = self._load_yaml()
        
        # 解析各项配置
        parser_data = self._raw_config.get("parser", {})
        parser = ParserConfig(
            max_file_size_mb=parser_data.get("max_file_size_mb", 50),
            supported_extensions=parser_data.get("supported_extensions", [
                ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".md", ".txt", ".html"
            ]),
        )
        
        splitter_data = self._raw_config.get("splitter", {})
        splitter = SplitterConfig(
            default_type=splitter_data.get("default_type", "recursive"),
            chunk_size=splitter_data.get("chunk_size", 500),
            chunk_overlap=splitter_data.get("chunk_overlap", 100),
            min_chunk_size=splitter_data.get("min_chunk_size", 50),
            separators=splitter_data.get("separators", [
                "\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""
            ]),
        )
        
        embedder_data = self._raw_config.get("embedder", {})
        embedder = EmbedderConfig(
            batch_size=embedder_data.get("batch_size", 32),
            max_retries=embedder_data.get("max_retries", 3),
            retry_delay_seconds=embedder_data.get("retry_delay_seconds", 1),
            normalize=embedder_data.get("normalize", True),
        )
        
        retriever_data = self._raw_config.get("retriever", {})
        retriever = RetrieverConfig(
            default_top_k=retriever_data.get("default_top_k", 5),
            max_top_k=retriever_data.get("max_top_k", 50),
            min_score_threshold=retriever_data.get("min_score_threshold", 0.5),
            use_hybrid_search=retriever_data.get("use_hybrid_search", True),
            vector_weight=retriever_data.get("vector_weight", 0.7),
            keyword_weight=retriever_data.get("keyword_weight", 0.3),
            rrf_k=retriever_data.get("rrf_k", 60),
        )
        
        reranker_data = self._raw_config.get("reranker", {})
        reranker = RerankerConfig(
            enabled=reranker_data.get("enabled", True),
            top_n=reranker_data.get("top_n", 5),
            min_score=reranker_data.get("min_score", 0.3),
        )
        
        ocr_data = self._raw_config.get("ocr", {})
        ocr = OCRConfig(
            languages=ocr_data.get("languages", ["ch", "en"]),
            use_angle_cls=ocr_data.get("use_angle_cls", True),
            show_log=ocr_data.get("show_log", False),
        )
        
        multimodal_data = self._raw_config.get("multimodal", {})
        multimodal = MultimodalConfig(
            video_frames_per_second=multimodal_data.get("video_frames_per_second", 0.5),
            max_video_frames=multimodal_data.get("max_video_frames", 10),
            image_max_size=multimodal_data.get("image_max_size", 2048),
        )
        
        qa_data = self._raw_config.get("qa", {})
        qa = QAConfig(
            use_rerank=qa_data.get("use_rerank", True),
            context_max_tokens=qa_data.get("context_max_tokens", 4000),
            stream_enabled=qa_data.get("stream_enabled", True),
        )
        
        prompts_data = self._raw_config.get("prompts", {})
        prompts = PromptsConfig(
            system_prompt=prompts_data.get("system_prompt", self.DEFAULT_SYSTEM_PROMPT),
            user_prompt=prompts_data.get("user_prompt", self.DEFAULT_USER_PROMPT),
            no_context_prompt=prompts_data.get("no_context_prompt", self.DEFAULT_NO_CONTEXT_PROMPT),
        )
        
        index_data = self._raw_config.get("index", {})
        index = IndexConfig(
            name_prefix=index_data.get("name_prefix", "kb"),
            shards=index_data.get("shards", 1),
            replicas=index_data.get("replicas", 0),
            refresh_interval=index_data.get("refresh_interval", "1s"),
        )
        
        self._config = RAGConfig(
            parser=parser,
            splitter=splitter,
            embedder=embedder,
            retriever=retriever,
            reranker=reranker,
            ocr=ocr,
            multimodal=multimodal,
            qa=qa,
            prompts=prompts,
            index=index,
        )
        
        return self._config
    
    def reload(self) -> RAGConfig:
        """重新加载配置"""
        self._config = None
        self._raw_config = {}
        return self.load()
    
    def get_raw_config(self) -> Dict[str, Any]:
        """获取原始配置"""
        if not self._raw_config:
            self._raw_config = self._load_yaml()
        return self._raw_config


# 创建全局配置加载器和配置对象
rag_config_loader = RAGConfigLoader()
rag_config = rag_config_loader.load()


def get_rag_config() -> RAGConfig:
    """获取RAG配置"""
    return rag_config


def reload_rag_config() -> RAGConfig:
    """重新加载RAG配置"""
    global rag_config
    rag_config = rag_config_loader.reload()
    return rag_config
