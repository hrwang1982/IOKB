"""
多模态处理服务
支持图片理解和视频内容提取
"""

import base64
import io
import os
import tempfile
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from app.config import settings


@dataclass
class ImageUnderstandingResult:
    """图片理解结果"""
    description: str
    tags: List[str] = None
    objects: List[Dict[str, Any]] = None
    text: Optional[str] = None  # OCR提取的文字
    metadata: Dict[str, Any] = None


@dataclass
class VideoContentResult:
    """视频内容提取结果"""
    description: str
    duration: float = 0.0
    frames: List[Dict[str, Any]] = None  # 关键帧信息
    transcription: Optional[str] = None  # 语音转文字
    metadata: Dict[str, Any] = None


class BaseImageUnderstanding(ABC):
    """图片理解基类"""
    
    @abstractmethod
    async def understand(self, image_path: str) -> ImageUnderstandingResult:
        """理解图片内容"""
        pass
    
    @abstractmethod
    async def understand_bytes(self, image_bytes: bytes) -> ImageUnderstandingResult:
        """理解图片字节流"""
        pass


class AliyunVLModel(BaseImageUnderstanding):
    """阿里云通义千问VL多模态模型"""
    
    def __init__(
        self,
        api_key: str = None,
        model_name: str = "qwen-vl-max",
        api_base: str = "https://dashscope.aliyuncs.com/api/v1",
    ):
        self.api_key = api_key or settings.llm_api_key
        self.model_name = model_name
        self.api_base = api_base
    
    async def understand(self, image_path: str) -> ImageUnderstandingResult:
        """理解图片文件"""
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        return await self.understand_bytes(image_bytes)
    
    async def understand_bytes(self, image_bytes: bytes) -> ImageUnderstandingResult:
        """理解图片字节流"""
        image_base64 = base64.b64encode(image_bytes).decode()
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.api_base}/services/aigc/multimodal-generation/generation",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "input": {
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"image": f"data:image/png;base64,{image_base64}"},
                                    {"text": "请详细描述这张图片的内容，包括：1.主要内容和场景 2.图中的文字（如果有）3.关键对象和元素。请用中文回答。"},
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
        
        return ImageUnderstandingResult(
            description=content,
            metadata={"model": self.model_name},
        )


class OpenAIVisionModel(BaseImageUnderstanding):
    """OpenAI GPT-4 Vision模型"""
    
    def __init__(
        self,
        api_key: str = None,
        model_name: str = "gpt-4o",
        api_base: str = "https://api.openai.com/v1",
    ):
        self.api_key = api_key or settings.llm_api_key
        self.model_name = model_name
        self.api_base = api_base
    
    async def understand(self, image_path: str) -> ImageUnderstandingResult:
        """理解图片文件"""
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        return await self.understand_bytes(image_bytes)
    
    async def understand_bytes(self, image_bytes: bytes) -> ImageUnderstandingResult:
        """理解图片字节流"""
        image_base64 = base64.b64encode(image_bytes).decode()
        
        # 检测图片类型
        if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            media_type = "image/png"
        elif image_bytes[:2] == b'\xff\xd8':
            media_type = "image/jpeg"
        else:
            media_type = "image/png"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{media_type};base64,{image_base64}",
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": "请详细描述这张图片的内容，包括：1.主要内容和场景 2.图中的文字（如果有）3.关键对象和元素。请用中文回答。",
                                },
                            ],
                        }
                    ],
                    "max_tokens": 2048,
                },
            )
            response.raise_for_status()
            data = response.json()
        
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        return ImageUnderstandingResult(
            description=content,
            metadata={"model": self.model_name},
        )


class LocalVLModel(BaseImageUnderstanding):
    """本地部署的VL多模态模型"""
    
    def __init__(
        self,
        local_url: str = None,
        model_name: str = "local-vl",
    ):
        self.local_url = local_url or settings.llm_local_url
        self.model_name = model_name
    
    async def understand(self, image_path: str) -> ImageUnderstandingResult:
        """理解图片文件"""
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        return await self.understand_bytes(image_bytes)
    
    async def understand_bytes(self, image_bytes: bytes) -> ImageUnderstandingResult:
        """理解图片字节流"""
        if not self.local_url:
            raise ValueError("本地VL模型服务URL未配置")
        
        image_base64 = base64.b64encode(image_bytes).decode()
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{self.local_url}/v1/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                                {"type": "text", "text": "请详细描述这张图片的内容。"},
                            ],
                        }
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()
        
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        return ImageUnderstandingResult(
            description=content,
            metadata={"model": self.model_name},
        )


class VideoContentExtractor:
    """视频内容提取器"""
    
    def __init__(
        self,
        image_model: BaseImageUnderstanding = None,
        frames_per_second: float = 0.5,  # 每秒提取帧数
        max_frames: int = 10,  # 最大帧数
    ):
        self.image_model = image_model
        self.frames_per_second = frames_per_second
        self.max_frames = max_frames
    
    async def extract(self, video_path: str) -> VideoContentResult:
        """提取视频内容"""
        try:
            import cv2
        except ImportError:
            raise RuntimeError("opencv-python未安装，请执行: pip install opencv-python")
        
        # 打开视频
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        # 计算采样间隔
        sample_interval = int(fps / self.frames_per_second) if self.frames_per_second > 0 else int(fps)
        
        # 提取关键帧
        frames = []
        frame_idx = 0
        
        while len(frames) < self.max_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                break
            
            # 编码为JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            frames.append({
                "index": frame_idx,
                "time": frame_idx / fps if fps > 0 else 0,
                "bytes": frame_bytes,
            })
            
            frame_idx += sample_interval
            if frame_idx >= frame_count:
                break
        
        cap.release()
        
        logger.info(f"从视频提取了{len(frames)}个关键帧, 时长={duration:.1f}秒")
        
        # 使用图片模型理解每个关键帧
        frame_descriptions = []
        if self.image_model:
            for i, frame in enumerate(frames):
                try:
                    result = await self.image_model.understand_bytes(frame["bytes"])
                    frame_descriptions.append({
                        "index": frame["index"],
                        "time": frame["time"],
                        "description": result.description,
                    })
                except Exception as e:
                    logger.warning(f"第{i}帧理解失败: {e}")
        
        # 汇总描述
        description = self._summarize_frames(frame_descriptions)
        
        return VideoContentResult(
            description=description,
            duration=duration,
            frames=frame_descriptions,
            metadata={
                "frame_count": frame_count,
                "fps": fps,
                "analyzed_frames": len(frame_descriptions),
            },
        )
    
    def _summarize_frames(self, frame_descriptions: List[Dict]) -> str:
        """汇总帧描述"""
        if not frame_descriptions:
            return "无法分析视频内容"
        
        parts = ["视频内容分析：\n"]
        for fd in frame_descriptions:
            time_str = f"{fd['time']:.1f}秒"
            parts.append(f"[{time_str}] {fd['description'][:200]}")
        
        return "\n\n".join(parts)


class ASRService:
    """ASR语音识别服务"""
    
    def __init__(self):
        self.api_key = settings.asr_api_key or settings.llm_api_key
        self.model_name = settings.asr_model_name
        self.provider = settings.asr_provider
    
    async def transcribe(self, audio_path: str) -> str:
        """转写音频文件"""
        if self.provider == "aliyun":
            return await self._transcribe_aliyun(audio_path)
        # TODO: 支持其他 provider
        return await self._transcribe_aliyun(audio_path)
    
    async def _transcribe_aliyun(self, audio_path: str) -> str:
        """使用阿里云 DashScope 进行转写"""
        import dashscope
        from http import HTTPStatus
        
        dashscope.api_key = self.api_key
        
        try:
            # 这里的调用通常是同步阻塞的，需放入 executor
            loop = asyncio.get_running_loop()
            
            def _run_recognition():
                abs_audio_path = os.path.abspath(audio_path)
                file_ext = Path(abs_audio_path).suffix.lstrip('.')
                
                # Fix: Override invalid local model name for Aliyun Cloud API
                # fun-asr-mtl is for local deployment, not supported by public API
                real_model_name = self.model_name
                if self.model_name == "fun-asr-mtl":
                    logger.warning(f"检测到本地模型名称 {self.model_name}，但在使用云端API。自动切换为 paraformer-realtime-v2")
                    real_model_name = "paraformer-realtime-v2"
                
                logger.debug(f"[ASR DEBUG] Using Recognition.call with file: {abs_audio_path}, model: {real_model_name}")
                
                # Recognition __init__ requires: model, callback, format, sample_rate
                # callback=None is accepted based on logs
                recognizer = dashscope.audio.asr.Recognition(
                    model=real_model_name,
                    format=file_ext,
                    sample_rate=16000, # Default to 16k
                    callback=None
                )
                
                # Do NOT pass model/format again to call(), it causes "multiple values" error
                response = recognizer.call(
                    file=abs_audio_path
                )
                
                logger.debug(f"[ASR DEBUG] Recognition Response: {response}")
                
                if response.status_code == HTTPStatus.OK:
                    return response.output
                else:
                    raise RuntimeError(f"ASR Recognition Failed: {response.code} {response.message}")

            response = await loop.run_in_executor(None, _run_recognition)
            
            if response:
                # Recognition response parsing
                text = ""
                if "sentences" in response:
                    for sentence in response["sentences"]:
                        text += sentence.get("text", "")
                elif "sentence" in response: 
                    for sentence in response["sentence"]:
                        text += sentence.get("text", "")
                elif "text" in response: 
                    text += response["text"]
                elif hasattr(response, "text") and response.text:
                    text += response.text
                
                logger.debug(f"[ASR DEBUG] Extracted Text: {text}")
                return text
            else:
                logger.warning(f"ASR返回空响应: {response}")
                return ""
                
        except Exception as e:
            logger.error(f"ASR转写异常: {e}")
            raise


class MultimodalService:
    """多模态服务管理"""
    
    def __init__(self):
        self._image_model: Optional[BaseImageUnderstanding] = None
        self._video_extractor: Optional[VideoContentExtractor] = None
        self._asr_service: Optional[ASRService] = None
    
    def get_image_model(self) -> BaseImageUnderstanding:
        """获取图片理解模型"""
        if self._image_model is not None:
            return self._image_model
        
        # 使用VL专属配置，如果未配置则回退到LLM配置
        provider = settings.vl_provider if settings.vl_provider else settings.llm_provider
        deploy_mode = settings.vl_deploy_mode if settings.vl_deploy_mode else settings.llm_deploy_mode
        api_key = settings.vl_api_key if settings.vl_api_key else settings.llm_api_key
        model_name = settings.vl_model_name if settings.vl_model_name else "qwen-vl-max"
        local_url = settings.vl_local_url if settings.vl_local_url else settings.llm_local_url
        api_base = settings.vl_api_base
        
        if deploy_mode == "local":
            self._image_model = LocalVLModel(
                local_url=local_url,
                model_name=model_name,
            )
        elif provider == "aliyun":
            # Ensure we use the native API base for Aliyun provider
            # The setting might be pointing to OpenAI compatible endpoint (compatible-mode/v1)
            native_api_base = "https://dashscope.aliyuncs.com/api/v1"
            use_base = api_base if api_base and "compatible-mode" not in api_base else native_api_base
            
            self._image_model = AliyunVLModel(
                api_key=api_key,
                model_name=model_name,
                api_base=use_base,
            )
        elif provider == "openai":
            self._image_model = OpenAIVisionModel(
                api_key=api_key,
                model_name=model_name if model_name != "qwen-vl-max" else "gpt-4o",
                api_base=api_base or "https://api.openai.com/v1",
            )
        else:
            self._image_model = LocalVLModel(local_url=local_url)
        
        logger.info(f"创建图片理解模型: provider={provider}, deploy_mode={deploy_mode}, model={model_name}")
        return self._image_model
    
    def get_asr_service(self) -> ASRService:
        """获取ASR服务"""
        if self._asr_service is None:
            self._asr_service = ASRService()
        return self._asr_service

    def get_video_extractor(self) -> VideoContentExtractor:
        """获取视频提取器"""
        if self._video_extractor is None:
            self._video_extractor = VideoContentExtractor(
                image_model=self.get_image_model(),
            )
        return self._video_extractor
    
    async def understand_image(self, image_path: str) -> ImageUnderstandingResult:
        """理解图片"""
        model = self.get_image_model()
        return await model.understand(image_path)
    
    async def understand_image_bytes(self, image_bytes: bytes) -> ImageUnderstandingResult:
        """理解图片字节流"""
        model = self.get_image_model()
        return await model.understand_bytes(image_bytes)
    
    async def transcribe_audio(self, audio_path: str) -> str:
        """转写音频"""
        asr = self.get_asr_service()
        return await asr.transcribe(audio_path)

    async def extract_video_content(self, video_path: str) -> VideoContentResult:
        """提取视频内容（包含视觉理解和语音转写）"""
        extractor = self.get_video_extractor()
        
        # 1. 提取视觉内容
        video_result = await extractor.extract(video_path)
        
        # 2. 提取并转写语音
        try:
            # 使用 moviepy 提取音频临时文件
            # 兼容 moviepy v1.x 和 v2.x
            try:
                from moviepy import VideoFileClip
            except ImportError:
                try:
                    import moviepy.editor as mp
                    VideoFileClip = mp.VideoFileClip
                except ImportError:
                    raise ImportError("Could not import moviepy. Please install it with `pip install moviepy`")
            
            temp_audio = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            temp_audio.close()
            
            # 由于可能没有安装 moviepy，我们需要做好异常处理
            # 并且 moviepy 依赖 ffmpeg
            
            # 使用 run_in_executor 运行音频提取
            def _extract_audio():
                clip = VideoFileClip(video_path)
                if clip.audio:
                    # Fix: Force mono audio (nchannels=1) as some ASR models (like Paraformer) require it
                    clip.audio.write_audiofile(
                        temp_audio.name, 
                        logger=None,
                        nchannels=1, 
                        codec='libmp3lame'
                    )
                    clip.close()  # V2.x best practice
                    return True
                clip.close()
                return False

            loop = asyncio.get_running_loop()
            has_audio = await loop.run_in_executor(None, _extract_audio)
            
            if has_audio:
                logger.info(f"视频音频已提取: {temp_audio.name}")
                transcription = await self.transcribe_audio(temp_audio.name)
                video_result.transcription = transcription
            
            # 清理临时文件
            os.unlink(temp_audio.name)
                
        except ImportError:
            logger.warning("未安装 moviepy，跳过视频语音转写")
        except Exception as e:
            logger.warning(f"视频语音转写失败: {e}")
            if os.path.exists(temp_audio.name):
                os.unlink(temp_audio.name)
        
        return video_result
    
    async def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        处理多模态文件
        自动识别文件类型并处理
        """
        ext = Path(file_path).suffix.lower()
        
        # 图片类型
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff']:
            result = await self.understand_image(file_path)
            return {
                "type": "image",
                "description": result.description,
                "text": result.text,
                "metadata": result.metadata,
            }
        
        # 视频类型
        elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']:
            result = await self.extract_video_content(file_path)
            # 合并描述和语音文本
            full_text = f"{result.description}\n\n[语音转写]\n{result.transcription or '无语音内容'}"
            return {
                "type": "video",
                "description": full_text,  # 为了兼容 parser 接口，这里放全部内容
                "duration": result.duration,
                "transcription": result.transcription,
                "metadata": result.metadata,
            }
        
        # 音频类型
        elif ext in ['.mp3', '.wav', '.m4a', '.flac', '.aac']:
            transcription = await self.transcribe_audio(file_path)
            return {
                "type": "audio",
                "description": transcription,
                "metadata": {"file_type": "audio"},
            }
        
        else:
            raise ValueError(f"不支持的文件类型: {ext}")


# 创建全局多模态服务实例
multimodal_service = MultimodalService()
