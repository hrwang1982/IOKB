"""
系统配置管理 API
用于读取和保存系统配置文件
"""

import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()

# 配置文件目录
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"

# 允许编辑的配置文件白名单
ALLOWED_CONFIG_FILES = {
    "cmdb": "cmdb.yaml",
    "alert": "alert.yaml",
    "rag": "rag.yaml",
    "auth": "auth.yaml",
}


class ConfigFileInfo(BaseModel):
    """配置文件信息"""
    name: str
    code: str
    path: str
    description: str


class ConfigFileContent(BaseModel):
    """配置文件内容"""
    code: str
    name: str
    path: str
    content: str


class ConfigUpdateRequest(BaseModel):
    """更新配置请求"""
    content: str


# 配置文件描述信息
CONFIG_DESCRIPTIONS = {
    "cmdb": {
        "name": "CMDB 配置",
        "description": "CMDB模块配置，包含CI类型、数据源、Kafka等配置",
    },
    "alert": {
        "name": "告警配置",
        "description": "告警分析模块配置，包含严重程度、分析策略等",
    },
    "rag": {
        "name": "RAG 配置",
        "description": "RAG知识库配置，包含embedding、chunk等参数",
    },
    "auth": {
        "name": "认证配置",
        "description": "认证授权配置，包含JWT、LDAP、SSO等配置",
    },
}


@router.get("/configs", summary="获取配置文件列表")
async def list_config_files() -> list[ConfigFileInfo]:
    """获取所有可编辑的配置文件列表"""
    configs = []
    for code, filename in ALLOWED_CONFIG_FILES.items():
        file_path = CONFIG_DIR / filename
        if file_path.exists():
            info = CONFIG_DESCRIPTIONS.get(code, {})
            configs.append(ConfigFileInfo(
                code=code,
                name=info.get("name", filename),
                path=f"config/{filename}",
                description=info.get("description", ""),
            ))
    return configs


@router.get("/configs/{config_code}", summary="获取配置文件内容")
async def get_config_file(config_code: str) -> ConfigFileContent:
    """读取指定配置文件的内容"""
    if config_code not in ALLOWED_CONFIG_FILES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置文件 '{config_code}' 不存在"
        )
    
    filename = ALLOWED_CONFIG_FILES[config_code]
    file_path = CONFIG_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置文件 {filename} 不存在"
        )
    
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"读取配置文件失败: {str(e)}"
        )
    
    info = CONFIG_DESCRIPTIONS.get(config_code, {})
    return ConfigFileContent(
        code=config_code,
        name=info.get("name", filename),
        path=f"config/{filename}",
        content=content,
    )


@router.put("/configs/{config_code}", summary="更新配置文件")
async def update_config_file(
    config_code: str,
    request: ConfigUpdateRequest,
) -> dict:
    """
    更新指定配置文件的内容
    
    注意：修改配置后需要重启相应服务才能生效
    """
    if config_code not in ALLOWED_CONFIG_FILES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置文件 '{config_code}' 不存在"
        )
    
    filename = ALLOWED_CONFIG_FILES[config_code]
    file_path = CONFIG_DIR / filename
    
    # 验证YAML格式
    try:
        import yaml
        yaml.safe_load(request.content)
    except yaml.YAMLError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"YAML格式错误: {str(e)}"
        )
    
    # 备份原文件
    backup_path = file_path.with_suffix(".yaml.bak")
    if file_path.exists():
        try:
            backup_path.write_text(file_path.read_text(encoding="utf-8"), encoding="utf-8")
        except Exception:
            pass  # 备份失败不阻止保存
    
    # 保存新内容
    try:
        file_path.write_text(request.content, encoding="utf-8")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存配置文件失败: {str(e)}"
        )
    
    return {
        "message": "配置保存成功",
        "path": f"config/{filename}",
        "backup": f"config/{filename}.bak" if backup_path.exists() else None,
    }


@router.post("/configs/{config_code}/validate", summary="验证配置文件")
async def validate_config_file(
    config_code: str,
    request: ConfigUpdateRequest,
) -> dict:
    """验证配置文件的YAML格式是否正确"""
    try:
        import yaml
        yaml.safe_load(request.content)
        return {"valid": True, "message": "YAML格式正确"}
    except yaml.YAMLError as e:
        return {
            "valid": False,
            "message": f"YAML格式错误: {str(e)}",
            "error": str(e),
        }


@router.post("/configs/{config_code}/restore", summary="恢复配置文件")
async def restore_config_file(config_code: str) -> dict:
    """从备份恢复配置文件"""
    if config_code not in ALLOWED_CONFIG_FILES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置文件 '{config_code}' 不存在"
        )
    
    filename = ALLOWED_CONFIG_FILES[config_code]
    file_path = CONFIG_DIR / filename
    backup_path = file_path.with_suffix(".yaml.bak")
    
    if not backup_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="备份文件不存在"
        )
    
    try:
        backup_content = backup_path.read_text(encoding="utf-8")
        file_path.write_text(backup_content, encoding="utf-8")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"恢复失败: {str(e)}"
        )
    
    return {"message": "配置已从备份恢复"}
