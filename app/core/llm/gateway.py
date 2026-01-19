"""
大模型调用服务
支持多种LLM提供商和本地部署
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx
from loguru import logger

from app.config import settings


@dataclass
class Message:
    """消息"""
    role: str  # system, user, assistant
    content: str


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    finish_reason: str = ""


class BaseLLM(ABC):
    """LLM基类"""
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        """对话"""
        pass
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> AsyncIterator[str]:
        """流式对话"""
        pass


class AliyunLLM(BaseLLM):
    """阿里云通义千问"""
    
    def __init__(
        self,
        api_key: str = None,
        model_name: str = "qwen-turbo",
        api_base: str = "https://dashscope.aliyuncs.com/api/v1",
    ):
        self.api_key = api_key or settings.llm_api_key
        self.model_name = model_name
        self.api_base = api_base
    
    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        """对话"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.api_base}/services/aigc/text-generation/generation",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "input": {
                        "messages": [{"role": m.role, "content": m.content} for m in messages],
                    },
                    "parameters": {
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "result_format": "message",
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
        
        output = data.get("output", {})
        usage = data.get("usage", {})
        
        content = ""
        if "choices" in output:
            content = output["choices"][0].get("message", {}).get("content", "")
        elif "text" in output:
            content = output["text"]
        
        return LLMResponse(
            content=content,
            model=self.model_name,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            finish_reason=output.get("finish_reason", ""),
        )
    
    async def chat_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> AsyncIterator[str]:
        """流式对话"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.api_base}/services/aigc/text-generation/generation",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "X-DashScope-SSE": "enable",
                },
                json={
                    "model": self.model_name,
                    "input": {
                        "messages": [{"role": m.role, "content": m.content} for m in messages],
                    },
                    "parameters": {
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "result_format": "message",
                        "incremental_output": True,
                    },
                },
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data = json.loads(line[5:])
                        output = data.get("output", {})
                        if "choices" in output:
                            content = output["choices"][0].get("message", {}).get("content", "")
                            if content:
                                yield content


class OpenAILLM(BaseLLM):
    """OpenAI GPT"""
    
    def __init__(
        self,
        api_key: str = None,
        model_name: str = "gpt-4o-mini",
        api_base: str = "https://api.openai.com/v1",
    ):
        self.api_key = api_key or settings.llm_api_key
        self.model_name = model_name
        self.api_base = api_base
    
    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        """对话"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()
        
        choice = data.get("choices", [{}])[0]
        usage = data.get("usage", {})
        
        return LLMResponse(
            content=choice.get("message", {}).get("content", ""),
            model=self.model_name,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            finish_reason=choice.get("finish_reason", ""),
        )
    
    async def chat_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> AsyncIterator[str]:
        """流式对话"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                },
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data:") and line != "data: [DONE]":
                        data = json.loads(line[5:])
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content


class LocalLLM(BaseLLM):
    """本地部署LLM"""
    
    def __init__(
        self,
        local_url: str = None,
        model_name: str = "local-llm",
    ):
        self.local_url = local_url or settings.llm_local_url
        self.model_name = model_name
    
    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        """对话"""
        if not self.local_url:
            raise ValueError("本地LLM服务URL未配置")
        
        # 兼容OpenAI格式的接口
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.local_url}/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()
        
        choice = data.get("choices", [{}])[0]
        usage = data.get("usage", {})
        
        return LLMResponse(
            content=choice.get("message", {}).get("content", ""),
            model=self.model_name,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            finish_reason=choice.get("finish_reason", ""),
        )
    
    async def chat_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> AsyncIterator[str]:
        """流式对话"""
        if not self.local_url:
            raise ValueError("本地LLM服务URL未配置")
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                f"{self.local_url}/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                },
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data:") and line != "data: [DONE]":
                        data = json.loads(line[5:])
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content


class LLMService:
    """LLM服务管理"""
    
    def __init__(self):
        self._llm: Optional[BaseLLM] = None
    
    def get_llm(self) -> BaseLLM:
        """获取LLM实例"""
        if self._llm is not None:
            return self._llm
        
        provider = settings.llm_provider
        deploy_mode = settings.llm_deploy_mode
        
        if deploy_mode == "local":
            self._llm = LocalLLM(
                local_url=settings.llm_local_url,
                model_name=settings.llm_model_name,
            )
        elif provider == "aliyun":
            self._llm = AliyunLLM(
                api_key=settings.llm_api_key,
                model_name=settings.llm_model_name,
                api_base=settings.llm_api_base or "https://dashscope.aliyuncs.com/api/v1",
            )
        elif provider == "openai":
            self._llm = OpenAILLM(
                api_key=settings.llm_api_key,
                model_name=settings.llm_model_name,
                api_base=settings.llm_api_base or "https://api.openai.com/v1",
            )
        else:
            # 默认使用本地服务
            self._llm = LocalLLM(
                local_url=settings.llm_local_url,
                model_name=settings.llm_model_name,
            )
        
        logger.info(f"创建LLM服务: provider={provider}, deploy_mode={deploy_mode}, model={settings.llm_model_name}")
        return self._llm
    
    async def chat(
        self,
        messages: List[Message],
        temperature: float = None,
        max_tokens: int = None,
        **kwargs,
    ) -> LLMResponse:
        """对话"""
        llm = self.get_llm()
        return await llm.chat(
            messages,
            temperature=temperature or settings.llm_temperature,
            max_tokens=max_tokens or settings.llm_max_output_tokens,
            **kwargs,
        )
    
    async def chat_stream(
        self,
        messages: List[Message],
        temperature: float = None,
        max_tokens: int = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """流式对话"""
        llm = self.get_llm()
        async for chunk in llm.chat_stream(
            messages,
            temperature=temperature or settings.llm_temperature,
            max_tokens=max_tokens or settings.llm_max_output_tokens,
            **kwargs,
        ):
            yield chunk


# 创建全局LLM服务实例
llm_service = LLMService()
