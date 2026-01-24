"""
文本分片服务
将长文本智能切分为适合检索的片段
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Callable

# LangChain imports
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter as LCRecursiveSplitter
    from langchain_text_splitters import MarkdownHeaderTextSplitter as LCMarkdownSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter as LCRecursiveSplitter
    from langchain.text_splitter import MarkdownHeaderTextSplitter as LCMarkdownSplitter

from loguru import logger


@dataclass
class TextChunk:
    """文本分片"""
    content: str
    index: int
    start_pos: int
    end_pos: int
    metadata: dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TextSplitter:
    """文本分片器基类"""
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separator: str = "\n\n",
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator
        
        # 兼容旧配置的分隔符列表
        self.separators = [
            "\n\n",   # 段落
            "\n",     # 行
            "。",     # 中文句号
            ".",      # 英文句号
            "！",     # 中文感叹号
            "!",      # 英文感叹号
            "？",     # 中文问号
            "?",      # 英文问号
            "；",     # 中文分号
            ";",      # 英文分号
            " ",      # 空格
            "",       # 字符级别
        ]
    
    def split(self, text: str) -> List[TextChunk]:
        """分割文本"""
        raise NotImplementedError

    def _convert_to_chunks(self, text: str, chunks_text: List[str]) -> List[TextChunk]:
        """
        将文本列表转换为带位置信息的TextChunk列表
        注意：LangChain不直接返回位置信息，我们需要根据原文重新定位
        """
        result = []
        current_pos = 0
        
        for i, chunk_text in enumerate(chunks_text):
            # 在当前位置之后查找该片段
            # 注意：由于可能会有重叠，或者分片器可能会修改空白字符，
            # 这种简单的find可能在边缘情况下不完美，但对于大多数情况足够
            start_pos = text.find(chunk_text, current_pos)
            
            # 如果没找到（可能是分片器做了一些微调，如去除首尾空格）
            if start_pos == -1:
                # 尝试从头搜索（防止乱序但不太可能）或模糊匹配
                # 这里简单处理：如果找不到，就重置搜索起点（可能会有误判，但保证能找到）
                start_pos = text.find(chunk_text)
                
            if start_pos == -1:
                # 实在找不到，记录错误但不因中断，使用上一个结束位置
                logger.warning(f"无法在原文中定位切片: {chunk_text[:20]}...")
                start_pos = current_pos
            
            end_pos = start_pos + len(chunk_text)
            
            result.append(TextChunk(
                content=chunk_text,
                index=i,
                start_pos=start_pos,
                end_pos=end_pos,
            ))
            
            # 更新下一次搜索的起始位置
            # 注意需要回退 overlap 的长度，但 LangChain 可能已经处理了
            # 为了保险，我们只保证单调递增，或者设为 start_pos + 1
            # 但考虑到 overlap，其实下一次可能在当前 chunk 内部
            # 所以最好的策略是：下次搜索至少从当前 start_pos + 1 开始
            current_pos = start_pos + 1
            
        return result


class RecursiveTextSplitter(TextSplitter):
    """
    基于 LangChain 的递归文本分片器
    支持 tiktoken 长度计算
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None,
    ):
        super().__init__(chunk_size, chunk_overlap)
        self.separators = separators or self.separators
        
        # 初始化 LangChain 分片器
        try:
            self.lc_splitter = LCRecursiveSplitter.from_tiktoken_encoder(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                encoding_name="cl100k_base", # OpenAI default
                separators=self.separators,
                keep_separator=True
            )
            logger.info("已启用 TikToken 增强的分片器")
        except Exception as e:
            logger.warning(f"TikToken 初始化失败，回退到普通字符计算: {e}")
            self.lc_splitter = LCRecursiveSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=self.separators,
                keep_separator=True
            )
    
    def split(self, text: str) -> List[TextChunk]:
        """使用 LangChain 进行切分"""
        # LangChain 返回的是 Document 对象或 string List
        chunks_text = self.lc_splitter.split_text(text)
        
        logger.debug(f"LangChain 分片完成: 原文{len(text)}字符, 生成{len(chunks_text)}个分片")
        
        # 转换为内部 TextChunk 对象并计算位置
        return self._convert_to_chunks(text, chunks_text)


class MarkdownSplitter(TextSplitter):
    """
    基于 LangChain 的 Markdown 分片器
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
    ):
        super().__init__(chunk_size, chunk_overlap)
        
        # 定义 Header 映射
        self.headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
        ]
        
        self.markdown_splitter = LCMarkdownSplitter(
            headers_to_split_on=self.headers_to_split_on
        )
        
        # 用于再次切分长片段的递归分片器
        self.recursive_splitter = RecursiveTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    def split(self, text: str) -> List[TextChunk]:
        """按Markdown标题切分"""
        # 第一步：按 Header 切分
        md_docs = self.markdown_splitter.split_text(text)
        
        final_chunks_text = []
        md_metadatas = []
        
        # 第二步：检查长度并二次切分
        for doc in md_docs:
            content = doc.page_content
            metadata = doc.metadata
            
            # 如果片段过长，递归切分
            # 注意：这里我们简单判断字符长度，也可以用 token
            if len(content) > self.chunk_size:
                sub_chunks = self.recursive_splitter.split(content)
                for sub in sub_chunks:
                    final_chunks_text.append(sub.content)
                    # 合并 metadata
                    md_metadatas.append({**metadata, **sub.metadata})
            else:
                final_chunks_text.append(content)
                md_metadatas.append(metadata)
        
        # 第三步：计算位置并组装结果
        chunks = self._convert_to_chunks(text, final_chunks_text)
        
        # 补充 metadata
        for chunk, metadata in zip(chunks, md_metadatas):
            chunk.metadata.update(metadata)
            
        return chunks


class SentenceSplitter(RecursiveTextSplitter):
    """
    句子级分片器
    复用 RecursiveTextSplitter，但分隔符优先级调整
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,  # 注意：这里单位统一回字符/token
    ):
        # 优先使用断句符号
        separators = ["\n\n", "。", "！", "？", ".", "!", "?", "\n"]
        super().__init__(
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap,
            separators=separators
        )


def create_splitter(
    splitter_type: str = "recursive",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> TextSplitter:
    """创建分片器"""
    splitters = {
        "recursive": RecursiveTextSplitter,
        "markdown": MarkdownSplitter,
        "sentence": SentenceSplitter,
    }
    
    splitter_class = splitters.get(splitter_type.lower())
    if not splitter_class:
        raise ValueError(f"未知的分片器类型: {splitter_type}")
    
    return splitter_class(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
