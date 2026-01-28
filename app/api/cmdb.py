"""
CMDB 配置管理 API
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import oauth2_scheme
from app.core.database import get_async_session
from app.core.cmdb.service import ci_type_service, ci_service, relationship_service, topology_service

router = APIRouter()


# ==================== 数据模型 ====================

class AttributeSchemaModel(BaseModel):
    """属性Schema模型"""
    name: str
    label: str
    type: str
    required: bool = False
    default: Any = None
    options: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = ""
    
    # UI 展示
    group: Optional[str] = "基本信息"
    order: Optional[int] = 0
    widget: Optional[str] = "input"
    placeholder: Optional[str] = ""
    hidden: Optional[bool] = False
    readonly: Optional[bool] = False
    
    # 数据验证
    unique: Optional[bool] = False
    regex: Optional[str] = ""
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    
    # 引用配置
    ref_type: Optional[str] = ""
    ref_filter: Optional[Dict[str, Any]] = None


class CISchemaDefinition(BaseModel):
    """完整Schema定义"""
    category: Optional[str] = "custom"
    identifier_rule: Optional[str] = None
    attributes: List[AttributeSchemaModel] = []


class CITypeResponse(BaseModel):
    """配置项类型响应"""
    id: int
    name: str
    code: str
    icon: Optional[str] = None
    description: Optional[str] = None
    attribute_schema: Optional[CISchemaDefinition] = None
    
    class Config:
        from_attributes = True


class CITypeCreate(BaseModel):
    """创建配置项类型请求"""
    name: str
    code: str
    icon: Optional[str] = None
    description: Optional[str] = None
    attribute_schema: Optional[CISchemaDefinition] = None


class CITypeUpdate(BaseModel):
    """更新配置项类型请求"""
    name: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    attribute_schema: Optional[CISchemaDefinition] = None


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
    extra_config: Optional[Dict[str, Any]] = None


# ==================== 配置项类型 ====================

@router.get("/types", summary="获取配置项类型列表")
async def list_ci_types(
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme)
):
    """
    获取所有配置项类型
    
    如果数据库中没有类型数据，会自动初始化预置类型
    """
    # 确保预置类型已初始化且Schema完整
    await ci_type_service.init_preset_types(db)
    
    # 从数据库获取所有类型
    ci_types = await ci_type_service.get_all_types(db)
    
    return {
        "items": [
            {
                "id": ct.id,
                "name": ct.name,
                "code": ct.code,
                "icon": ct.icon,
                "description": ct.description,
                "attribute_schema": ct.attribute_schema,
                "category": ct.attribute_schema.get("category") if ct.attribute_schema else None,
            }
            for ct in ci_types
        ]
    }


@router.get("/types/{type_code}", response_model=CITypeResponse, summary="获取配置项类型详情")
async def get_ci_type(
    type_code: str,
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme)
):
    """获取配置项类型详情，包含完整属性Schema"""
    ci_type = await ci_type_service.get_type_by_code(db, type_code)
    
    if not ci_type:
        raise HTTPException(status_code=404, detail=f"配置项类型不存在: {type_code}")
    
    return CITypeResponse(
        id=ci_type.id,
        name=ci_type.name,
        code=ci_type.code,
        icon=ci_type.icon,
        description=ci_type.description,
        attribute_schema=ci_type.attribute_schema
    )


@router.post("/types", response_model=CITypeResponse, summary="创建配置项类型")
async def create_ci_type(
    item: CITypeCreate,
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme)
):
    """创建新的配置项类型"""
    try:
        new_type = await ci_type_service.create(
            db,
            name=item.name,
            code=item.code,
            icon=item.icon,
            description=item.description,
            attribute_schema=item.attribute_schema.model_dump() if item.attribute_schema else None
        )
        return CITypeResponse(
            id=new_type.id,
            name=new_type.name,
            code=new_type.code,
            icon=new_type.icon,
            description=new_type.description,
            attribute_schema=new_type.attribute_schema
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/types/{type_code}", response_model=CITypeResponse, summary="更新配置项类型")
async def update_ci_type(
    type_code: str,
    item: CITypeUpdate,
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme)
):
    """更新配置项类型"""
    updated_type = await ci_type_service.update(
        db,
        code=type_code,
        name=item.name,
        icon=item.icon,
        description=item.description,
        attribute_schema=item.attribute_schema.model_dump() if item.attribute_schema else None
    )
    
    if not updated_type:
        raise HTTPException(status_code=404, detail=f"配置项类型不存在: {type_code}")
    
    return CITypeResponse(
        id=updated_type.id,
        name=updated_type.name,
        code=updated_type.code,
        icon=updated_type.icon,
        description=updated_type.description,
        attribute_schema=updated_type.attribute_schema
    )


@router.delete("/types/id/{type_id}", summary="根据ID删除配置项类型")
async def delete_ci_type_by_id(
    type_id: int,
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme)
):
    """根据ID删除配置项类型"""
    try:
        success = await ci_type_service.delete_by_id(db, type_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Backend: 配置项类型不存在 (ID: {type_id})")
        return {"message": f"类型 ID:{type_id} 已删除"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/types/{type_code}", summary="删除配置项类型")
async def delete_ci_type(
    type_code: str,
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme)
):
    """删除配置项类型"""
    try:
        success = await ci_type_service.delete(db, type_code)
        if not success:
            raise HTTPException(status_code=404, detail=f"配置项类型不存在: {type_code}")
        return {"message": f"类型 {type_code} 已删除"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 配置项管理 ====================

@router.get("/items", summary="获取配置项列表")
async def list_cis(
    type_code: Optional[str] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme)
):
    """
    获取配置项列表
    
    - **type_code**: 可选，按类型筛选
    - **status**: 可选，按状态筛选
    - **keyword**: 可选，搜索关键词
    """
    offset = (page - 1) * size
    cis, total = await ci_service.list(
        db,
        type_code=type_code,
        status=status,
        keyword=keyword,
        offset=offset,
        limit=size
    )
    
    return {
        "items": [
            {
                "id": ci.id,
                "type_id": ci.type_id,
                "type_code": ci.ci_type.code if ci.ci_type else None,
                "type_name": ci.ci_type.name if ci.ci_type else None,
                "name": ci.name,
                "identifier": ci.identifier,
                "status": ci.status,
                "attributes": ci.attributes,
                "created_at": ci.created_at.isoformat() if ci.created_at else None,
                "updated_at": ci.updated_at.isoformat() if ci.updated_at else None,
            }
            for ci in cis
        ],
        "total": total,
        "page": page,
        "size": size
    }


@router.post("/items", response_model=CIResponse, summary="创建配置项")
async def create_ci(
    ci: CICreate,
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme)
):
    """创建新配置项"""
    try:
        new_ci = await ci_service.create(
            db,
            type_code=ci.type_code,
            name=ci.name,
            identifier=ci.identifier,
            attributes=ci.attributes
        )
        return CIResponse(
            id=new_ci.id,
            type_id=new_ci.type_id,
            type_code=new_ci.ci_type.code if new_ci.ci_type else ci.type_code,
            type_name=new_ci.ci_type.name if new_ci.ci_type else "",
            name=new_ci.name,
            identifier=new_ci.identifier,
            status=new_ci.status,
            attributes=new_ci.attributes,
            created_at=new_ci.created_at,
            updated_at=new_ci.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/items/{ci_id}", response_model=CIResponse, summary="获取配置项详情")
async def get_ci(
    ci_id: int,
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme)
):
    """获取配置项详情"""
    ci = await ci_service.get_by_id(db, ci_id)
    
    if not ci:
        raise HTTPException(status_code=404, detail=f"配置项不存在: {ci_id}")
    
    return CIResponse(
        id=ci.id,
        type_id=ci.type_id,
        type_code=ci.ci_type.code if ci.ci_type else None,
        type_name=ci.ci_type.name if ci.ci_type else None,
        name=ci.name,
        identifier=ci.identifier,
        status=ci.status,
        attributes=ci.attributes,
        created_at=ci.created_at,
        updated_at=ci.updated_at
    )


class CIUpdate(BaseModel):
    """更新配置项请求"""
    name: Optional[str] = None
    status: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None


@router.put("/items/{ci_id}", response_model=CIResponse, summary="更新配置项")
async def update_ci(
    ci_id: int,
    ci: CIUpdate,
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme)
):
    """更新配置项"""
    updated_ci = await ci_service.update(
        db,
        ci_id=ci_id,
        name=ci.name,
        status=ci.status,
        attributes=ci.attributes
    )
    
    if not updated_ci:
        raise HTTPException(status_code=404, detail=f"配置项不存在: {ci_id}")
    
    return CIResponse(
        id=updated_ci.id,
        type_id=updated_ci.type_id,
        type_code=updated_ci.ci_type.code if updated_ci.ci_type else ci.type_code,
        type_name=updated_ci.ci_type.name if updated_ci.ci_type else "",
        name=updated_ci.name,
        identifier=updated_ci.identifier,
        status=updated_ci.status,
        attributes=updated_ci.attributes,
        created_at=updated_ci.created_at,
        updated_at=updated_ci.updated_at
    )


@router.delete("/items/batch", summary="批量删除配置项")
async def delete_items_batch(
    ci_ids: List[int],
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme)
):
    """
    批量删除配置项
    """
    count = await ci_service.delete_batch(db, ci_ids)
    
    # logger is not imported in this scope, need to check imports or remove logging if not available
    # Assuming logger is available or I should add import. 
    # Checking imports... loguru is not imported in this file.
    # I will skip logging or use print for now, or add import.
    # Actually, let's add the import to be safe, or just skip logging.
    # The previous code had logger.info, so it might have been missed or available globally?
    # File top imports: from loguru import logger? No, lines 1-15 don't show it.
    # Let's remove logger usage for now to avoid NameError, or better, add the import at the top.
    
    return {"status": "success", "deleted_count": count}


@router.delete("/items/{ci_id}", summary="删除配置项")
async def delete_ci(
    ci_id: int,
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme)
):
    """删除配置项"""
    success = await ci_service.delete(db, ci_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"配置项不存在: {ci_id}")
    
    return {"message": f"配置项 {ci_id} 已删除"}


# ==================== 关系管理 ====================

@router.get("/items/{ci_id}/relationships", summary="获取配置项关系")
async def get_ci_relationships(
    ci_id: int,
    direction: str = Query("both", pattern="^(from|to|both)$"),
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme)
):
    """
    获取配置项的关系列表
    
    - **direction**: from(上游), to(下游), both(双向)
    """
    rels = await relationship_service.get_relationships(db, ci_id, direction)
    return rels


@router.post("/relationships", response_model=RelationshipResponse, summary="创建关系")
async def create_relationship(
    rel: RelationshipCreate,
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme)
):
    """创建配置项之间的关系"""
    try:
        new_rel = await relationship_service.create(
            db,
            from_ci_id=rel.from_ci_id,
            to_ci_id=rel.to_ci_id,
            rel_type=rel.rel_type
        )
        
        # 获取关联的CI名称
        from_ci = await ci_service.get_by_id(db, rel.from_ci_id)
        to_ci = await ci_service.get_by_id(db, rel.to_ci_id)
        
        return RelationshipResponse(
            id=new_rel.id,
            from_ci_id=new_rel.from_ci_id,
            from_ci_name=from_ci.name if from_ci else "",
            to_ci_id=new_rel.to_ci_id,
            to_ci_name=to_ci.name if to_ci else "",
            rel_type=new_rel.rel_type
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/relationships/{rel_id}", summary="删除关系")
async def delete_relationship(
    rel_id: int,
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme)
):
    """删除关系"""
    success = await relationship_service.delete(db, rel_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"关系不存在: {rel_id}")
    
    return {"message": f"关系 {rel_id} 已删除"}


# ==================== 拓扑图 ====================

@router.get("/topology", summary="获取拓扑图数据")
async def get_topology(
    ci_id: Optional[int] = None,
    depth: int = Query(2, ge=1, le=5),
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme)
):
    """
    获取拓扑图数据
    
    - **ci_id**: 可选，以某个CI为中心展示
    - **depth**: 展示深度
    """
    return await topology_service.get_topology(db, ci_id, depth)


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
