"""
文档解析服务
支持 PDF、Word、Excel、Markdown、TXT、HTML 等格式
"""

import hashlib
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from loguru import logger


class FileType(str, Enum):
    """支持的文件类型"""
    PDF = "pdf"
    WORD_DOC = "doc"
    WORD_DOCX = "docx"
    EXCEL_XLS = "xls"
    EXCEL_XLSX = "xlsx"
    MARKDOWN = "md"
    TXT = "txt"
    HTML = "html"
    JSON = "json"
    YAML = "yaml"
    XML = "xml"
    # 图片类型（需要OCR）
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    TIFF = "tiff"
    BMP = "bmp"


@dataclass
class ParsedContent:
    """解析后的内容"""
    text: str
    metadata: Dict[str, Any]
    pages: Optional[List[Dict[str, Any]]] = None  # 按页/段落分组的内容
    tables: Optional[List[Dict[str, Any]]] = None  # 提取的表格
    images: Optional[List[Dict[str, Any]]] = None  # 提取的图片信息


@dataclass
class DocumentChunk:
    """文档分片"""
    content: str
    index: int
    metadata: Dict[str, Any]
    start_char: int = 0
    end_char: int = 0


class BaseParser(ABC):
    """解析器基类"""
    
    @abstractmethod
    def parse(self, file_path: str) -> ParsedContent:
        """解析文件"""
        pass
    
    @abstractmethod
    def supports(self, file_type: FileType) -> bool:
        """是否支持该文件类型"""
        pass


class PDFParser(BaseParser):
    """PDF解析器"""
    
    def supports(self, file_type: FileType) -> bool:
        return file_type == FileType.PDF
    
    def parse(self, file_path: str) -> ParsedContent:
        """解析PDF文件"""
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(file_path)
            pages = []
            full_text = []
            tables = []
            images = []
            
            for page_num, page in enumerate(doc):
                # 提取文本
                page_text = page.get_text()
                full_text.append(page_text)
                
                pages.append({
                    "page_num": page_num + 1,
                    "text": page_text,
                    "width": page.rect.width,
                    "height": page.rect.height,
                })
                
                # 提取图片信息
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    images.append({
                        "page": page_num + 1,
                        "index": img_index,
                        "xref": img[0],
                    })
            
            doc.close()
            
            metadata = {
                "file_path": file_path,
                "file_type": "pdf",
                "page_count": len(pages),
                "image_count": len(images),
            }
            
            return ParsedContent(
                text="\n\n".join(full_text),
                metadata=metadata,
                pages=pages,
                tables=tables,
                images=images,
            )
            
        except Exception as e:
            logger.error(f"PDF解析失败: {file_path}, 错误: {e}")
            raise


class WordParser(BaseParser):
    """Word文档解析器"""
    
    def supports(self, file_type: FileType) -> bool:
        return file_type in [FileType.WORD_DOC, FileType.WORD_DOCX]
    
    def parse(self, file_path: str) -> ParsedContent:
        """解析Word文件"""
        try:
            from docx import Document
            
            doc = Document(file_path)
            paragraphs = []
            full_text = []
            tables = []
            
            # 提取段落
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text)
                    paragraphs.append({
                        "text": para.text,
                        "style": para.style.name if para.style else None,
                    })
            
            # 提取表格
            for table_idx, table in enumerate(doc.tables):
                table_data = []
                for row in table.rows:
                    row_data = [cell.text for cell in row.cells]
                    table_data.append(row_data)
                tables.append({
                    "index": table_idx,
                    "data": table_data,
                })
            
            metadata = {
                "file_path": file_path,
                "file_type": "docx",
                "paragraph_count": len(paragraphs),
                "table_count": len(tables),
            }
            
            return ParsedContent(
                text="\n\n".join(full_text),
                metadata=metadata,
                pages=paragraphs,
                tables=tables,
            )
            
        except Exception as e:
            logger.error(f"Word解析失败: {file_path}, 错误: {e}")
            raise


class ExcelParser(BaseParser):
    """Excel解析器"""
    
    def supports(self, file_type: FileType) -> bool:
        return file_type in [FileType.EXCEL_XLS, FileType.EXCEL_XLSX]
    
    def parse(self, file_path: str) -> ParsedContent:
        """解析Excel文件"""
        try:
            import openpyxl
            
            wb = openpyxl.load_workbook(file_path, data_only=True)
            sheets = []
            full_text = []
            tables = []
            
            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                sheet_data = []
                
                for row in sheet.iter_rows(values_only=True):
                    # 过滤空行
                    if any(cell is not None for cell in row):
                        row_text = [str(cell) if cell is not None else "" for cell in row]
                        sheet_data.append(row_text)
                        full_text.append("\t".join(row_text))
                
                if sheet_data:
                    sheets.append({
                        "name": sheet_name,
                        "rows": len(sheet_data),
                    })
                    tables.append({
                        "sheet": sheet_name,
                        "data": sheet_data,
                    })
            
            wb.close()
            
            metadata = {
                "file_path": file_path,
                "file_type": "xlsx",
                "sheet_count": len(sheets),
            }
            
            return ParsedContent(
                text="\n".join(full_text),
                metadata=metadata,
                pages=sheets,
                tables=tables,
            )
            
        except Exception as e:
            logger.error(f"Excel解析失败: {file_path}, 错误: {e}")
            raise


class MarkdownParser(BaseParser):
    """Markdown解析器"""
    
    def supports(self, file_type: FileType) -> bool:
        return file_type == FileType.MARKDOWN
    
    def parse(self, file_path: str) -> ParsedContent:
        """解析Markdown文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 按标题分割
            sections = []
            current_section = {"title": "", "content": [], "level": 0}
            
            for line in content.split("\n"):
                if line.startswith("#"):
                    # 保存当前section
                    if current_section["content"]:
                        sections.append({
                            "title": current_section["title"],
                            "text": "\n".join(current_section["content"]),
                            "level": current_section["level"],
                        })
                    # 开始新section
                    level = len(line) - len(line.lstrip("#"))
                    title = line.lstrip("#").strip()
                    current_section = {"title": title, "content": [], "level": level}
                else:
                    current_section["content"].append(line)
            
            # 添加最后一个section
            if current_section["content"]:
                sections.append({
                    "title": current_section["title"],
                    "text": "\n".join(current_section["content"]),
                    "level": current_section["level"],
                })
            
            metadata = {
                "file_path": file_path,
                "file_type": "markdown",
                "section_count": len(sections),
            }
            
            return ParsedContent(
                text=content,
                metadata=metadata,
                pages=sections,
            )
            
        except Exception as e:
            logger.error(f"Markdown解析失败: {file_path}, 错误: {e}")
            raise


class TextParser(BaseParser):
    """纯文本解析器"""
    
    def supports(self, file_type: FileType) -> bool:
        return file_type in [FileType.TXT, FileType.JSON, FileType.YAML, FileType.XML]
    
    def parse(self, file_path: str) -> ParsedContent:
        """解析文本文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 获取文件扩展名
            ext = Path(file_path).suffix.lstrip(".")
            
            metadata = {
                "file_path": file_path,
                "file_type": ext,
                "char_count": len(content),
                "line_count": content.count("\n") + 1,
            }
            
            return ParsedContent(
                text=content,
                metadata=metadata,
            )
            
        except Exception as e:
            logger.error(f"文本解析失败: {file_path}, 错误: {e}")
            raise


class HTMLParser(BaseParser):
    """HTML解析器"""
    
    def supports(self, file_type: FileType) -> bool:
        return file_type == FileType.HTML
    
    def parse(self, file_path: str) -> ParsedContent:
        """解析HTML文件"""
        try:
            from html.parser import HTMLParser as StdHTMLParser
            
            class TextExtractor(StdHTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text_parts = []
                    self.skip_tags = {"script", "style", "head"}
                    self.current_skip = False
                
                def handle_starttag(self, tag, attrs):
                    if tag in self.skip_tags:
                        self.current_skip = True
                
                def handle_endtag(self, tag):
                    if tag in self.skip_tags:
                        self.current_skip = False
                
                def handle_data(self, data):
                    if not self.current_skip:
                        text = data.strip()
                        if text:
                            self.text_parts.append(text)
            
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            extractor = TextExtractor()
            extractor.feed(html_content)
            
            text = "\n".join(extractor.text_parts)
            
            metadata = {
                "file_path": file_path,
                "file_type": "html",
                "char_count": len(text),
            }
            
            return ParsedContent(
                text=text,
                metadata=metadata,
            )
            
        except Exception as e:
            logger.error(f"HTML解析失败: {file_path}, 错误: {e}")
            raise


class DocumentParser:
    """文档解析服务"""
    
    def __init__(self):
        self.parsers: List[BaseParser] = [
            PDFParser(),
            WordParser(),
            ExcelParser(),
            MarkdownParser(),
            TextParser(),
            HTMLParser(),
        ]
    
    def get_file_type(self, file_path: str) -> Optional[FileType]:
        """获取文件类型"""
        ext = Path(file_path).suffix.lstrip(".").lower()
        try:
            return FileType(ext)
        except ValueError:
            return None
    
    def get_parser(self, file_type: FileType) -> Optional[BaseParser]:
        """获取对应的解析器"""
        for parser in self.parsers:
            if parser.supports(file_type):
                return parser
        return None
    
    def parse(self, file_path: str) -> ParsedContent:
        """解析文档"""
        file_type = self.get_file_type(file_path)
        if not file_type:
            raise ValueError(f"不支持的文件类型: {file_path}")
        
        parser = self.get_parser(file_type)
        if not parser:
            raise ValueError(f"未找到对应的解析器: {file_type}")
        
        logger.info(f"开始解析文档: {file_path}, 类型: {file_type}")
        result = parser.parse(file_path)
        logger.info(f"文档解析完成: {file_path}, 字符数: {len(result.text)}")
        
        return result
    
    def compute_hash(self, file_path: str) -> str:
        """计算文件哈希"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def needs_ocr(self, file_type: FileType) -> bool:
        """是否需要OCR"""
        return file_type in [
            FileType.PNG, FileType.JPG, FileType.JPEG,
            FileType.TIFF, FileType.BMP
        ]


# 创建全局解析器实例
document_parser = DocumentParser()
