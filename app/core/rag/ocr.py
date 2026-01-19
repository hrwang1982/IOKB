"""
OCR服务
支持PaddleOCR、PaddleOCR-VL和本地部署
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from app.config import settings


@dataclass
class OCRResult:
    """OCR识别结果"""
    text: str
    confidence: float = 0.0
    boxes: Optional[List[Dict[str, Any]]] = None  # 文字位置信息
    

class BaseOCR(ABC):
    """OCR基类"""
    
    @abstractmethod
    async def recognize(self, image_path: str) -> OCRResult:
        """识别图片中的文字"""
        pass
    
    @abstractmethod
    async def recognize_bytes(self, image_bytes: bytes) -> OCRResult:
        """识别图片字节流中的文字"""
        pass


class PaddleOCRService(BaseOCR):
    """PaddleOCR服务（本地）"""
    
    def __init__(self, use_gpu: bool = False, lang: str = "ch"):
        self.use_gpu = use_gpu
        self.lang = lang
        self._ocr = None
    
    def _get_ocr(self):
        """懒加载OCR实例"""
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR
                self._ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang=self.lang,
                    show_log=False,
                )
            except ImportError:
                raise RuntimeError("PaddleOCR未安装，请执行: pip install paddlepaddle paddleocr")
        return self._ocr
    
    async def recognize(self, image_path: str) -> OCRResult:
        """识别图片"""
        ocr = self._get_ocr()
        result = ocr.ocr(image_path, cls=True)
        
        return self._parse_result(result)
    
    async def recognize_bytes(self, image_bytes: bytes) -> OCRResult:
        """识别图片字节流"""
        import io
        from PIL import Image
        import numpy as np
        
        image = Image.open(io.BytesIO(image_bytes))
        image_array = np.array(image)
        
        ocr = self._get_ocr()
        result = ocr.ocr(image_array, cls=True)
        
        return self._parse_result(result)
    
    def _parse_result(self, result: List) -> OCRResult:
        """解析OCR结果"""
        if not result or not result[0]:
            return OCRResult(text="", confidence=0.0, boxes=[])
        
        texts = []
        boxes = []
        total_confidence = 0.0
        count = 0
        
        for line in result[0]:
            box = line[0]
            text = line[1][0]
            confidence = line[1][1]
            
            texts.append(text)
            boxes.append({
                "text": text,
                "box": box,
                "confidence": confidence,
            })
            total_confidence += confidence
            count += 1
        
        avg_confidence = total_confidence / count if count > 0 else 0.0
        
        return OCRResult(
            text="\n".join(texts),
            confidence=avg_confidence,
            boxes=boxes,
        )


class LocalOCRService(BaseOCR):
    """本地部署OCR服务（通过HTTP调用）"""
    
    def __init__(self, local_url: str = None):
        self.local_url = local_url or settings.ocr_local_url
    
    async def recognize(self, image_path: str) -> OCRResult:
        """识别图片文件"""
        if not self.local_url:
            raise ValueError("本地OCR服务URL未配置")
        
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        return await self.recognize_bytes(image_bytes)
    
    async def recognize_bytes(self, image_bytes: bytes) -> OCRResult:
        """识别图片字节流"""
        if not self.local_url:
            raise ValueError("本地OCR服务URL未配置")
        
        import base64
        image_base64 = base64.b64encode(image_bytes).decode()
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.local_url}/ocr",
                json={"image": image_base64},
            )
            response.raise_for_status()
            data = response.json()
        
        return OCRResult(
            text=data.get("text", ""),
            confidence=data.get("confidence", 0.0),
            boxes=data.get("boxes"),
        )


class BaiduOCRService(BaseOCR):
    """百度OCR服务"""
    
    def __init__(self, api_key: str = None, secret_key: str = None):
        self.api_key = api_key or settings.ocr_api_key
        self.secret_key = secret_key
        self._access_token = None
    
    async def _get_access_token(self) -> str:
        """获取访问令牌"""
        if self._access_token:
            return self._access_token
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://aip.baidubce.com/oauth/2.0/token",
                params={
                    "grant_type": "client_credentials",
                    "client_id": self.api_key,
                    "client_secret": self.secret_key,
                },
            )
            response.raise_for_status()
            data = response.json()
            self._access_token = data["access_token"]
        
        return self._access_token
    
    async def recognize(self, image_path: str) -> OCRResult:
        """识别图片"""
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        return await self.recognize_bytes(image_bytes)
    
    async def recognize_bytes(self, image_bytes: bytes) -> OCRResult:
        """识别图片字节流"""
        import base64
        
        access_token = await self._get_access_token()
        image_base64 = base64.b64encode(image_bytes).decode()
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic",
                params={"access_token": access_token},
                data={"image": image_base64},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            data = response.json()
        
        texts = []
        for word in data.get("words_result", []):
            texts.append(word.get("words", ""))
        
        return OCRResult(
            text="\n".join(texts),
            confidence=0.9,
        )


class AliyunOCRService(BaseOCR):
    """阿里云OCR服务"""
    
    def __init__(
        self,
        api_key: str = None,
        api_base: str = "https://ocr-api.cn-hangzhou.aliyuncs.com",
    ):
        self.api_key = api_key or settings.ocr_api_key
        self.api_base = api_base
    
    async def recognize(self, image_path: str) -> OCRResult:
        """识别图片"""
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        return await self.recognize_bytes(image_bytes)
    
    async def recognize_bytes(self, image_bytes: bytes) -> OCRResult:
        """识别图片字节流"""
        import base64
        
        image_base64 = base64.b64encode(image_bytes).decode()
        
        # 使用阿里云通义千问VL模型进行OCR（更强大的文字识别）
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "qwen-vl-ocr",
                    "input": {
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"image": f"data:image/png;base64,{image_base64}"},
                                    {"text": "请识别并提取图片中的所有文字内容，按原文格式输出，不要添加任何解释。"},
                                ],
                            }
                        ],
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
        
        output = data.get("output", {})
        content = ""
        
        if "choices" in output:
            content = output["choices"][0].get("message", {}).get("content", [])
            if isinstance(content, list):
                content = content[0].get("text", "") if content else ""
        elif "text" in output:
            content = output["text"]
        
        return OCRResult(
            text=content,
            confidence=0.95,
            metadata={"model": "qwen-vl-ocr"},
        )


class OCRService:
    """OCR服务管理"""
    
    def __init__(self):
        self._ocr: Optional[BaseOCR] = None
    
    def get_ocr(self) -> BaseOCR:
        """获取OCR实例"""
        if self._ocr is not None:
            return self._ocr
        
        provider = settings.ocr_provider
        deploy_mode = settings.ocr_deploy_mode
        
        if deploy_mode == "local" and settings.ocr_local_url:
            self._ocr = LocalOCRService(local_url=settings.ocr_local_url)
        elif provider == "aliyun":
            self._ocr = AliyunOCRService(api_key=settings.ocr_api_key)
        elif provider in ["paddleocr", "paddleocr_vl"]:
            self._ocr = PaddleOCRService()
        elif provider == "baidu":
            self._ocr = BaiduOCRService()
        else:
            # 默认使用PaddleOCR
            self._ocr = PaddleOCRService()
        
        logger.info(f"创建OCR服务: provider={provider}, deploy_mode={deploy_mode}")
        return self._ocr
    
    async def recognize(self, image_path: str) -> OCRResult:
        """识别图片"""
        ocr = self.get_ocr()
        return await ocr.recognize(image_path)
    
    async def recognize_bytes(self, image_bytes: bytes) -> OCRResult:
        """识别图片字节流"""
        ocr = self.get_ocr()
        return await ocr.recognize_bytes(image_bytes)


# 创建全局OCR服务实例
ocr_service = OCRService()
