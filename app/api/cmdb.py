"""
CMDB 配置管理 API
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.auth import oauth2_scheme

router = APIRouter()


# ==================== 数据模型 ====================

class CITypeResponse(BaseModel):
    """配置项类型响应"""
    id: int
    name: str
    code: str
    icon: Optional[str] = None
    description: Optional[str] = None
    attribute_schema: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class CICreate(BaseModel):
    """创建配置项请求"""
    type_code: str
    name: str
    identifier: str
    attributes: Optional[Dict[str, Any]] = None


class CIResponse(BaseModel):
    """配置项响应"""
    id: int
    type_id: int
    type_code: str
    type_name: str
    name: str
    identifier: str
    status: str
    attributes: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RelationshipCreate(BaseModel):
    """创建关系请求"""
    from_ci_id: int
    to_ci_id: int
    rel_type: str  # depends_on, contains, connects_to, runs_on


class RelationshipResponse(BaseModel):
    """关系响应"""
    id: int
    from_ci_id: int
    from_ci_name: str
    to_ci_id: int
    to_ci_name: str
    rel_type: str
    
    class Config:
        from_attributes = True


class DataSourceConfig(BaseModel):
    """数据源配置"""
    name: str
    db_type: str  # mysql, postgresql, oracle, sqlserver
    host: str
    port: int
    database: str
    username: str
    password: str
    sync_interval: int = 60  # 分钟
    sync_mode: str = "incremental"  # full, incremental
    table_mappings: Optional[List[Dict[str, Any]]] = None


# ==================== 配置项类型 ====================

@router.get("/types", summary="获取配置项类型列表")
async def list_ci_types(token: str = Depends(oauth2_scheme)):
    """获取所有配置项类型"""
    return {
        "items": [
            {"id": 1, "name": "存储设备", "code": "storage"},
            {"id": 2, "name": "网络设备", "code": "network"},
            {"id": 3, "name": "物理服务器", "code": "server"},
            {"id": 4, "name": "Linux系统", "code": "os_linux"},
            {"id": 5, "name": "Windows系统", "code": "os_windows"},
            {"id": 6, "name": "vCenter集群", "code": "vmware_vcenter"},
            {"id": 7, "name": "ESXi主机", "code": "vmware_esxi"},
            {"id": 8, "name": "虚拟机", "code": "vmware_vm"},
            {"id": 9, "name": "K8s集群", "code": "k8s_cluster"},
            {"id": 10, "name": "K8s节点", "code": "k8s_node"},
            {"id": 11, "name": "K8s Pod", "code": "k8s_pod"},
            {"id": 12, "name": "Docker主机", "code": "docker_host"},
            {"id": 13, "name": "Docker容器", "code": "docker_container"},
            {"id": 14, "name": "中间件", "code": "middleware"},
            {"id": 15, "name": "数据库", "code": "database"},
            {"id": 16, "name": "业务应用", "code": "application"},
        ]
    }


@router.get("/types/{type_code}", response_model=CITypeResponse, summary="获取配置项类型详情")
async def get_ci_type(type_code: str, token: str = Depends(oauth2_scheme)):
    """获取配置项类型详情"""
    return CITypeResponse(
        id=1,
        name="物理服务器",
        code=type_code,
        icon="server",
        description="物理服务器配置项",
        attribute_schema={
            "cpu": {"type": "string", "label": "CPU"},
            "memory": {"type": "string", "label": "内存"},
            "disk": {"type": "string", "label": "磁盘"},
            "ip": {"type": "string", "label": "IP地址"},
        }
    )


# ==================== 配置项管理 ====================

@router.get("/items", summary="获取配置项列表")
async def list_cis(
    type_code: Optional[str] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    token: str = Depends(oauth2_scheme)
):
    """
    获取配置项列表
    
    - **type_code**: 可选，按类型筛选
    - **status**: 可选，按状态筛选
    - **keyword**: 可选，搜索关键词
    """
    return {
        "items": [],
        "total": 0,
        "page": page,
        "size": size
    }


@router.post("/items", response_model=CIResponse, summary="创建配置项")
async def create_ci(ci: CICreate, token: str = Depends(oauth2_scheme)):
    """创建新配置项"""
    now = datetime.now()
    return CIResponse(
        id=1,
        type_id=1,
        type_code=ci.type_code,
        type_name="物理服务器",
        name=ci.name,
        identifier=ci.identifier,
        status="active",
        attributes=ci.attributes,
        created_at=now,
        updated_at=now
    )


@router.get("/items/{ci_id}", response_model=CIResponse, summary="获取配置项详情")
async def get_ci(ci_id: int, token: str = Depends(oauth2_scheme)):
    """获取配置项详情"""
    now = datetime.now()
    return CIResponse(
        id=ci_id,
        type_id=1,
        type_code="server",
        type_name="物理服务器",
        name="示例服务器",
        identifier="server-001",
        status="active",
        attributes={"ip": "192.168.1.1"},
        created_at=now,
        updated_at=now
    )


@router.put("/items/{ci_id}", response_model=CIResponse, summary="更新配置项")
async def update_ci(
    ci_id: int,
    ci: CICreate,
    token: str = Depends(oauth2_scheme)
):
    """更新配置项"""
    now = datetime.now()
    return CIResponse(
        id=ci_id,
        type_id=1,
        type_code=ci.type_code,
        type_name="物理服务器",
        name=ci.name,
        identifier=ci.identifier,
        status="active",
        attributes=ci.attributes,
        created_at=now,
        updated_at=now
    )


@router.delete("/items/{ci_id}", summary="删除配置项")
async def delete_ci(ci_id: int, token: str = Depends(oauth2_scheme)):
    """删除配置项"""
    return {"message": f"配置项 {ci_id} 已删除"}


# ==================== 关系管理 ====================

@router.get("/items/{ci_id}/relationships", summary="获取配置项关系")
async def get_ci_relationships(
    ci_id: int,
    direction: str = Query("both", regex="^(from|to|both)$"),
    token: str = Depends(oauth2_scheme)
):
    """
    获取配置项的关系列表
    
    - **direction**: from(上游), to(下游), both(双向)
    """
    return {"upstream": [], "downstream": []}


@router.post("/relationships", response_model=RelationshipResponse, summary="创建关系")
async def create_relationship(
    rel: RelationshipCreate,
    token: str = Depends(oauth2_scheme)
):
    """创建配置项之间的关系"""
    return RelationshipResponse(
        id=1,
        from_ci_id=rel.from_ci_id,
        from_ci_name="服务器A",
        to_ci_id=rel.to_ci_id,
        to_ci_name="应用B",
        rel_type=rel.rel_type
    )


@router.delete("/relationships/{rel_id}", summary="删除关系")
async def delete_relationship(rel_id: int, token: str = Depends(oauth2_scheme)):
    """删除关系"""
    return {"message": f"关系 {rel_id} 已删除"}


# ==================== 拓扑图 ====================

@router.get("/topology", summary="获取拓扑图数据")
async def get_topology(
    ci_id: Optional[int] = None,
    depth: int = Query(2, ge=1, le=5),
    token: str = Depends(oauth2_scheme)
):
    """
    获取拓扑图数据
    
    - **ci_id**: 可选，以某个CI为中心展示
    - **depth**: 展示深度
    """
    return {
        "nodes": [],
        "edges": []
    }


# ==================== 数据同步 ====================

@router.get("/datasources", summary="获取数据源列表")
async def list_datasources(token: str = Depends(oauth2_scheme)):
    """获取配置的数据源列表"""
    return {"items": []}


@router.post("/datasources", summary="添加数据源")
async def create_datasource(
    config: DataSourceConfig,
    token: str = Depends(oauth2_scheme)
):
    """添加新数据源"""
    return {"id": 1, "name": config.name, "status": "active"}


@router.post("/datasources/{ds_id}/sync", summary="触发数据同步")
async def trigger_sync(ds_id: int, token: str = Depends(oauth2_scheme)):
    """手动触发数据同步"""
    return {"message": "同步任务已启动", "job_id": "sync-001"}


@router.get("/datasources/{ds_id}/status", summary="获取同步状态")
async def get_sync_status(ds_id: int, token: str = Depends(oauth2_scheme)):
    """获取数据源同步状态"""
    return {
        "last_sync_time": datetime.now().isoformat(),
        "status": "success",
        "synced_count": 0,
        "error_count": 0
    }
