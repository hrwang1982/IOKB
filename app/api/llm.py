"""
大模型配置 API
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.auth import oauth2_scheme

router = APIRouter()


# ==================== 数据模型 ====================

class LLMProviderConfig(BaseModel):
    """LLM提供商配置"""
    provider: str  # openai, anthropic, aliyun, baidu, local, custom
    deploy_mode: str = "api"  # api: 调用远程API, local: 本地部署模型
    model_name: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    api_version: Optional[str] = None
    local_url: Optional[str] = None  # 本地部署服务URL
    
    # 参数配置
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 4096
    max_input_tokens: int = 8192
    max_output_tokens: int = 4096
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    
    # 高级配置
    timeout: int = 60
    retry_count: int = 3
    streaming: bool = True
    token_counting: bool = True
    
    
class LLMConfigResponse(BaseModel):
    """LLM配置响应"""
    id: int
    name: str
    provider: str
    model_name: str
    is_default: bool
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EmbeddingConfig(BaseModel):
    """Embedding模型配置"""
    provider: str  # aliyun, openai, local, custom
    deploy_mode: str = "api"  # api: 调用远程API, local: 本地部署模型
    model_name: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    local_url: Optional[str] = None  # 本地部署服务URL
    model_path: Optional[str] = None  # 本地模型路径
    dimension: int = 1024


class RerankConfig(BaseModel):
    """Rerank模型配置"""
    provider: str  # aliyun, local, custom
    deploy_mode: str = "api"  # api: 调用远程API, local: 本地部署模型
    model_name: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    local_url: Optional[str] = None  # 本地部署服务URL
    model_path: Optional[str] = None  # 本地模型路径


class OCRConfig(BaseModel):
    """OCR模型配置"""
    provider: str  # paddleocr, paddleocr_vl, baidu, local, custom
    deploy_mode: str = "local"  # api: 调用远程API, local: 本地部署模型
    model_path: Optional[str] = None  # 本地模型路径
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    local_url: Optional[str] = None  # 本地部署服务URL


class PromptTemplate(BaseModel):
    """Prompt模板"""
    name: str
    description: Optional[str] = None
    template: str
    variables: List[str]


# ==================== LLM 配置管理 ====================

@router.get("/configs", summary="获取LLM配置列表")
async def list_llm_configs(token: str = Depends(oauth2_scheme)):
    """获取所有LLM配置"""
    return {
        "items": [
            {
                "id": 1,
                "name": "通义千问-Turbo",
                "provider": "aliyun",
                "model_name": "qwen-turbo",
                "is_default": True,
                "status": "active"
            }
        ]
    }


@router.post("/configs", response_model=LLMConfigResponse, summary="添加LLM配置")
async def create_llm_config(
    name: str,
    config: LLMProviderConfig,
    token: str = Depends(oauth2_scheme)
):
    """添加新的LLM配置"""
    now = datetime.now()
    return LLMConfigResponse(
        id=1,
        name=name,
        provider=config.provider,
        model_name=config.model_name,
        is_default=False,
        status="active",
        created_at=now,
        updated_at=now
    )


@router.get("/configs/{config_id}", summary="获取LLM配置详情")
async def get_llm_config(config_id: int, token: str = Depends(oauth2_scheme)):
    """获取LLM配置详情（不包含敏感信息）"""
    return {
        "id": config_id,
        "name": "通义千问-Turbo",
        "provider": "aliyun",
        "model_name": "qwen-turbo",
        "api_base": "https://dashscope.aliyuncs.com/api/v1",
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 4096,
        "is_default": True,
        "status": "active"
    }


@router.put("/configs/{config_id}", summary="更新LLM配置")
async def update_llm_config(
    config_id: int,
    config: LLMProviderConfig,
    token: str = Depends(oauth2_scheme)
):
    """更新LLM配置"""
    return {"message": f"配置 {config_id} 已更新"}


@router.delete("/configs/{config_id}", summary="删除LLM配置")
async def delete_llm_config(config_id: int, token: str = Depends(oauth2_scheme)):
    """删除LLM配置"""
    return {"message": f"配置 {config_id} 已删除"}


@router.put("/configs/{config_id}/default", summary="设为默认配置")
async def set_default_config(config_id: int, token: str = Depends(oauth2_scheme)):
    """设置为默认LLM配置"""
    return {"message": f"配置 {config_id} 已设为默认"}


@router.post("/configs/{config_id}/test", summary="测试LLM配置")
async def test_llm_config(config_id: int, token: str = Depends(oauth2_scheme)):
    """测试LLM配置是否可用"""
    # TODO: 实际调用API测试
    return {
        "success": True,
        "message": "连接成功",
        "response_time_ms": 500
    }


# ==================== Embedding 配置 ====================

@router.get("/embedding", summary="获取Embedding配置")
async def get_embedding_config(token: str = Depends(oauth2_scheme)):
    """获取当前Embedding模型配置"""
    return {
        "provider": "aliyun",
        "deploy_mode": "api",
        "model_name": "text-embedding-v3",
        "dimension": 1024,
        "local_url": None,
        "status": "active"
    }


@router.put("/embedding", summary="更新Embedding配置")
async def update_embedding_config(
    config: EmbeddingConfig,
    token: str = Depends(oauth2_scheme)
):
    """
    更新Embedding模型配置
    
    - **deploy_mode**: api(调用远程API) 或 local(本地部署)
    - **local_url**: 本地部署时的服务URL
    """
    return {"message": "Embedding配置已更新"}


@router.post("/embedding/test", summary="测试Embedding配置")
async def test_embedding_config(token: str = Depends(oauth2_scheme)):
    """测试Embedding配置是否可用"""
    return {
        "success": True,
        "message": "连接成功",
        "dimension": 1024
    }


# ==================== Rerank 配置 ====================

@router.get("/rerank", summary="获取Rerank配置")
async def get_rerank_config(token: str = Depends(oauth2_scheme)):
    """获取当前Rerank模型配置"""
    return {
        "provider": "aliyun",
        "deploy_mode": "api",
        "model_name": "gte-rerank",
        "local_url": None,
        "status": "active"
    }


@router.put("/rerank", summary="更新Rerank配置")
async def update_rerank_config(
    config: RerankConfig,
    token: str = Depends(oauth2_scheme)
):
    """
    更新Rerank模型配置
    
    - **deploy_mode**: api(调用远程API) 或 local(本地部署)
    - **local_url**: 本地部署时的服务URL
    """
    return {"message": "Rerank配置已更新"}


@router.post("/rerank/test", summary="测试Rerank配置")
async def test_rerank_config(token: str = Depends(oauth2_scheme)):
    """测试Rerank配置是否可用"""
    return {
        "success": True,
        "message": "连接成功"
    }


# ==================== OCR 配置 ====================

@router.get("/ocr", summary="获取OCR配置")
async def get_ocr_config(token: str = Depends(oauth2_scheme)):
    """获取当前OCR模型配置"""
    return {
        "provider": "paddleocr_vl",
        "deploy_mode": "local",
        "model_path": None,
        "local_url": None,
        "status": "active"
    }


@router.put("/ocr", summary="更新OCR配置")
async def update_ocr_config(
    config: OCRConfig,
    token: str = Depends(oauth2_scheme)
):
    """
    更新OCR模型配置
    
    - **provider**: paddleocr, paddleocr_vl, baidu, local, custom
    - **deploy_mode**: api(调用远程API) 或 local(本地部署)
    - **model_path**: 本地模型文件路径
    - **local_url**: 本地部署服务URL
    """
    return {"message": "OCR配置已更新"}


@router.post("/ocr/test", summary="测试OCR配置")
async def test_ocr_config(token: str = Depends(oauth2_scheme)):
    """测试OCR配置是否可用"""
    return {
        "success": True,
        "message": "OCR服务可用"
    }


# ==================== Prompt 模板管理 ====================

@router.get("/prompts", summary="获取Prompt模板列表")
async def list_prompts(token: str = Depends(oauth2_scheme)):
    """获取所有Prompt模板"""
    return {
        "items": [
            {
                "id": 1,
                "name": "告警分析",
                "description": "用于分析告警的Prompt模板",
                "variables": ["alert_info", "ci_info", "performance_data"]
            },
            {
                "id": 2,
                "name": "知识问答",
                "description": "用于RAG问答的Prompt模板",
                "variables": ["question", "context"]
            }
        ]
    }


@router.get("/prompts/{prompt_id}", summary="获取Prompt模板详情")
async def get_prompt(prompt_id: int, token: str = Depends(oauth2_scheme)):
    """获取Prompt模板详情"""
    return {
        "id": prompt_id,
        "name": "告警分析",
        "description": "用于分析告警的Prompt模板",
        "template": "你是一个专业的IT运维专家...",
        "variables": ["alert_info", "ci_info", "performance_data"]
    }


@router.post("/prompts", summary="创建Prompt模板")
async def create_prompt(
    prompt: PromptTemplate,
    token: str = Depends(oauth2_scheme)
):
    """创建新的Prompt模板"""
    return {"id": 1, "name": prompt.name, "message": "模板创建成功"}


@router.put("/prompts/{prompt_id}", summary="更新Prompt模板")
async def update_prompt(
    prompt_id: int,
    prompt: PromptTemplate,
    token: str = Depends(oauth2_scheme)
):
    """更新Prompt模板"""
    return {"message": f"模板 {prompt_id} 已更新"}


@router.delete("/prompts/{prompt_id}", summary="删除Prompt模板")
async def delete_prompt(prompt_id: int, token: str = Depends(oauth2_scheme)):
    """删除Prompt模板"""
    return {"message": f"模板 {prompt_id} 已删除"}


# ==================== Token 用量统计 ====================

@router.get("/usage", summary="获取Token用量统计")
async def get_token_usage(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    token: str = Depends(oauth2_scheme)
):
    """获取Token使用量统计"""
    return {
        "total_tokens": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "by_model": {},
        "by_day": []
    }
