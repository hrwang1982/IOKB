"""
文本分片服务
将长文本智能切分为适合检索的片段
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Callable

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
    
    def split(self, text: str) -> List[TextChunk]:
        """分割文本"""
        raise NotImplementedError


class RecursiveTextSplitter(TextSplitter):
    """
    递归文本分片器
    按照多级分隔符递归切分，优先保持语义完整性
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None,
    ):
        super().__init__(chunk_size, chunk_overlap)
        self.separators = separators or [
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
        """递归分割文本"""
        chunks = self._recursive_split(text, self.separators)
        
        # 合并小块
        merged_chunks = self._merge_small_chunks(chunks)
        
        # 构建TextChunk对象
        result = []
        current_pos = 0
        for i, chunk_text in enumerate(merged_chunks):
            start_pos = text.find(chunk_text, current_pos)
            if start_pos == -1:
                start_pos = current_pos
            end_pos = start_pos + len(chunk_text)
            
            result.append(TextChunk(
                content=chunk_text,
                index=i,
                start_pos=start_pos,
                end_pos=end_pos,
            ))
            current_pos = start_pos + 1
        
        logger.debug(f"文本分片完成: 原文{len(text)}字符, 生成{len(result)}个分片")
        return result
    
    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """递归分割"""
        if not text:
            return []
        
        # 如果文本已经足够短
        if len(text) <= self.chunk_size:
            return [text]
        
        # 尝试用第一个分隔符切分
        if not separators:
            # 没有分隔符了，强制按长度切分
            return self._split_by_length(text)
        
        separator = separators[0]
        remaining_separators = separators[1:]
        
        if separator:
            parts = text.split(separator)
        else:
            # 空分隔符，按字符切分
            parts = list(text)
        
        result = []
        current_chunk = ""
        
        for part in parts:
            # 如果当前块加上新部分不超过限制
            test_chunk = current_chunk + separator + part if current_chunk else part
            
            if len(test_chunk) <= self.chunk_size:
                current_chunk = test_chunk
            else:
                # 保存当前块
                if current_chunk:
                    result.append(current_chunk)
                
                # 如果单个部分就超过限制，需要进一步切分
                if len(part) > self.chunk_size:
                    sub_chunks = self._recursive_split(part, remaining_separators)
                    result.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = part
        
        # 添加最后一块
        if current_chunk:
            result.append(current_chunk)
        
        return result
    
    def _split_by_length(self, text: str) -> List[str]:
        """按长度切分"""
        result = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk = text[i:i + self.chunk_size]
            if chunk:
                result.append(chunk)
        return result
    
    def _merge_small_chunks(self, chunks: List[str]) -> List[str]:
        """合并过小的块"""
        if not chunks:
            return []
        
        min_chunk_size = self.chunk_size // 4  # 小于四分之一的考虑合并
        result = []
        current_chunk = ""
        
        for chunk in chunks:
            if len(current_chunk) + len(chunk) <= self.chunk_size:
                current_chunk = current_chunk + "\n" + chunk if current_chunk else chunk
            else:
                if current_chunk:
                    result.append(current_chunk)
                current_chunk = chunk
        
        if current_chunk:
            result.append(current_chunk)
        
        return result


class MarkdownSplitter(TextSplitter):
    """
    Markdown文档分片器
    按标题层级切分，保持文档结构
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
    ):
        super().__init__(chunk_size, chunk_overlap)
        self.header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    
    def split(self, text: str) -> List[TextChunk]:
        """按Markdown标题切分"""
        # 找到所有标题
        headers = list(self.header_pattern.finditer(text))
        
        if not headers:
            # 没有标题，使用普通分片
            splitter = RecursiveTextSplitter(self.chunk_size, self.chunk_overlap)
            return splitter.split(text)
        
        sections = []
        for i, match in enumerate(headers):
            level = len(match.group(1))
            title = match.group(2)
            start = match.start()
            end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
            content = text[start:end].strip()
            
            sections.append({
                "level": level,
                "title": title,
                "content": content,
                "start": start,
                "end": end,
            })
        
        # 如果section太长，进一步切分
        result = []
        for section in sections:
            if len(section["content"]) <= self.chunk_size:
                result.append(TextChunk(
                    content=section["content"],
                    index=len(result),
                    start_pos=section["start"],
                    end_pos=section["end"],
                    metadata={
                        "title": section["title"],
                        "level": section["level"],
                    }
                ))
            else:
                # 切分长section
                splitter = RecursiveTextSplitter(self.chunk_size, self.chunk_overlap)
                sub_chunks = splitter.split(section["content"])
                for i, chunk in enumerate(sub_chunks):
                    chunk.metadata["title"] = section["title"]
                    chunk.metadata["level"] = section["level"]
                    chunk.metadata["part"] = i + 1
                    chunk.index = len(result)
                    result.append(chunk)
        
        return result


class SentenceSplitter(TextSplitter):
    """
    句子级分片器
    按句子边界切分，适合需要精确语义的场景
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 1,  # overlap用句子数表示
    ):
        super().__init__(chunk_size, chunk_overlap)
        self.sentence_endings = re.compile(r'[。！？.!?\n]+')
    
    def split(self, text: str) -> List[TextChunk]:
        """按句子切分"""
        # 切分成句子
        sentences = self.sentence_endings.split(text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return []
        
        result = []
        current_chunk = []
        current_length = 0
        current_start = 0
        
        for sentence in sentences:
            if current_length + len(sentence) <= self.chunk_size:
                current_chunk.append(sentence)
                current_length += len(sentence) + 1  # +1 for separator
            else:
                # 保存当前块
                if current_chunk:
                    chunk_text = "。".join(current_chunk) + "。"
                    result.append(TextChunk(
                        content=chunk_text,
                        index=len(result),
                        start_pos=current_start,
                        end_pos=current_start + len(chunk_text),
                    ))
                    current_start += len(chunk_text)
                
                # 开始新块（带overlap）
                if self.chunk_overlap > 0 and len(current_chunk) > self.chunk_overlap:
                    current_chunk = current_chunk[-self.chunk_overlap:]
                    current_length = sum(len(s) + 1 for s in current_chunk)
                else:
                    current_chunk = []
                    current_length = 0
                
                current_chunk.append(sentence)
                current_length += len(sentence) + 1
        
        # 添加最后一块
        if current_chunk:
            chunk_text = "。".join(current_chunk) + "。"
            result.append(TextChunk(
                content=chunk_text,
                index=len(result),
                start_pos=current_start,
                end_pos=current_start + len(chunk_text),
            ))
        
        return result


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
