"""
CMDB服务层
配置项管理、关系管理、拓扑计算
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cmdb import CI, CIType, CIRelationship, DataSource
from app.core.cmdb.ci_types import PRESET_CI_TYPES, get_ci_type_by_code


class CITypeService:
    """配置项类型服务"""
    
    async def init_preset_types(self, db: AsyncSession) -> int:
        """初始化预置配置项类型"""
        count = 0
        
        for preset in PRESET_CI_TYPES:
            # 检查是否已存在
            result = await db.execute(
                select(CIType).where(CIType.code == preset.code)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Check if schema is empty and needs hydration
                current_schema = existing.attribute_schema or {}
                has_attributes = current_schema.get("attributes") and len(current_schema["attributes"]) > 0
                
                if not has_attributes:
                    logger.info(f"Hydrating empty schema for existing type: {preset.code}")
                    existing.name = preset.name
                    existing.icon = preset.icon
                    existing.description = preset.description
                    existing.attribute_schema = {
                        "category": preset.category,
                        "attributes": [
                            {
                                "name": attr.name,
                                "label": attr.label,
                                "type": attr.type,
                                "required": attr.required,
                                "default": attr.default,
                                "options": attr.options,
                                "description": attr.description,
                                # UI
                                "group": attr.group,
                                "order": attr.order,
                                "widget": attr.widget,
                                "placeholder": attr.placeholder,
                                "hidden": attr.hidden,
                                "readonly": attr.readonly,
                                # Validation
                                "unique": attr.unique,
                                "regex": attr.regex,
                                "min_val": attr.min_val,
                                "max_val": attr.max_val,
                                # Ref
                                "ref_type": attr.ref_type,
                                "ref_filter": attr.ref_filter,
                            }
                            for attr in preset.attributes
                        ],
                    }
                    existing.updated_at = datetime.now()
                    db.add(existing)
                    count += 1
                else:
                    logger.debug(f"CI type already has attributes, skipping overwrite: {preset.code}")
                continue
            
            # 创建新类型
            ci_type = CIType(
                name=preset.name,
                code=preset.code,
                icon=preset.icon,
                description=preset.description,
                attribute_schema={
                    "category": preset.category,
                    "attributes": [
                        {
                            "name": attr.name,
                            "label": attr.label,
                            "type": attr.type,
                            "required": attr.required,
                            "default": attr.default,
                            "options": attr.options,
                            "description": attr.description,
                            # UI
                            "group": attr.group,
                            "order": attr.order,
                            "widget": attr.widget,
                            "placeholder": attr.placeholder,
                            "hidden": attr.hidden,
                            "readonly": attr.readonly,
                            # Validation
                            "unique": attr.unique,
                            "regex": attr.regex,
                            "min_val": attr.min_val,
                            "max_val": attr.max_val,
                            # Ref
                            "ref_type": attr.ref_type,
                            "ref_filter": attr.ref_filter,
                        }
                        for attr in preset.attributes
                    ],
                },
            )
            db.add(ci_type)
            count += 1
            logger.info(f"Initialized new CI type: {preset.code} - {preset.name}")
        
        await db.commit()
        return count
    
    async def get_all_types(self, db: AsyncSession) -> List[CIType]:
        """获取所有配置项类型"""
        result = await db.execute(select(CIType).order_by(CIType.id))
        return result.scalars().all()
    
    async def get_type_by_code(self, db: AsyncSession, code: str) -> Optional[CIType]:
        """根据编码获取类型"""
        result = await db.execute(
            select(CIType).where(CIType.code == code)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        db: AsyncSession,
        name: str,
        code: str,
        icon: Optional[str] = None,
        description: Optional[str] = None,
        attribute_schema: Optional[Dict[str, Any]] = None,
    ) -> CIType:
        """创建配置项类型"""
        # 检查是否已存在
        existing = await self.get_type_by_code(db, code)
        if existing:
            raise ValueError(f"CI类型编码已存在: {code}")
        
        ci_type = CIType(
            name=name,
            code=code,
            icon=icon,
            description=description,
            attribute_schema=attribute_schema or {"attributes": [], "category": "custom"},
        )
        db.add(ci_type)
        await db.commit()
        await db.refresh(ci_type)
        
        logger.info(f"创建CI类型: {code} - {name}")
        return ci_type
    
    async def update(
        self,
        db: AsyncSession,
        code: str,
        name: Optional[str] = None,
        icon: Optional[str] = None,
        description: Optional[str] = None,
        attribute_schema: Optional[Dict[str, Any]] = None,
    ) -> Optional[CIType]:
        """更新配置项类型"""
        ci_type = await self.get_type_by_code(db, code)
        if not ci_type:
            return None
        
        if name:
            ci_type.name = name
        if icon:
            ci_type.icon = icon
        if description is not None:
            ci_type.description = description
        if attribute_schema is not None:
            ci_type.attribute_schema = attribute_schema
            
        ci_type.updated_at = datetime.now()
        await db.commit()
        await db.refresh(ci_type)
        
        return ci_type
    
    async def delete(self, db: AsyncSession, code: str) -> bool:
        """删除配置项类型"""
        ci_type = await self.get_type_by_code(db, code)
        if not ci_type:
            return False
            
        # 检查是否有关联的配置项
        result = await db.execute(
            select(CI).where(CI.type_id == ci_type.id).limit(1)
        )
        if result.scalar_one_or_none():
            raise ValueError(f"该类型下存在配置项，无法删除: {code}")
        
        await db.delete(ci_type)
        await db.commit()
        return True
    
    async def delete_by_id(self, db: AsyncSession, type_id: int) -> bool:
        """根据ID删除配置项类型"""
        result = await db.execute(
             select(CIType).where(CIType.id == type_id)
        )
        ci_type = result.scalar_one_or_none()
        if not ci_type:
            return False
            
        # 检查是否有关联的配置项
        result = await db.execute(
            select(CI).where(CI.type_id == ci_type.id).limit(1)
        )
        if result.scalar_one_or_none():
            raise ValueError(f"该类型下存在配置项，无法删除 (ID: {type_id})")
        
        await db.delete(ci_type)
        await db.commit()
        return True


class CIService:
    """配置项服务"""
    
    async def _validate_attributes(self, db: AsyncSession, type_code: str, attributes: Dict[str, Any], current_ci_id: Optional[int] = None):
        """校验属性"""
        ci_type = await CITypeService().get_type_by_code(db, type_code)
        if not ci_type:
             # 对于未知的类型，如果是预置的可能在内存中但未初始化的，这里为了简单起见，假设类型已存在DB
             # 实际生产中应先确保CIType已初始化
             logger.warning(f"Validation skipped for unknown type: {type_code}")
             return

        schema_attrs = ci_type.attribute_schema.get("attributes", [])
        if not schema_attrs:
            return

        for attr_schema in schema_attrs:
            key = attr_schema.get("name")
            value = attributes.get(key)
            
            # 1. 必填校验
            if attr_schema.get("required") and value in (None, ""):
                raise ValueError(f"属性 {attr_schema.get('label', key)} ({key}) 不能为空")
            
            if value is not None and value != "":
                # 2. 类型/格式校验
                import re
                regex = attr_schema.get("regex")
                if regex and not re.match(regex, str(value)):
                    raise ValueError(f"属性 {attr_schema.get('label', key)} 格式不正确")
                
                # 3. 数值范围校验
                val_type = attr_schema.get("type")
                if val_type == "number":
                    try:
                        num_val = float(value)
                        min_val = attr_schema.get("min_val")
                        max_val = attr_schema.get("max_val")
                        if min_val is not None and num_val < min_val:
                            raise ValueError(f"属性 {attr_schema.get('label', key)} 不能小于 {min_val}")
                        if max_val is not None and num_val > max_val:
                            raise ValueError(f"属性 {attr_schema.get('label', key)} 不能大于 {max_val}")
                    except ValueError:
                         raise ValueError(f"属性 {attr_schema.get('label', key)} 必须是数字")

                # 4. 唯一性校验
                if attr_schema.get("unique"):
                    # 构建JSON字段查询
                    # PostgreSQL: arrow operator ->> returns text
                    stmt = select(CI).where(
                        and_(
                            CI.type_id == ci_type.id,
                            # 使用 cast 或 func.json_extract_path_text 适配不同数据库，这里假设 PostgreSQL 或 SQLite 支持
                            # SQLAlchemy func.json_extract_path_text(CI.attributes, key) == str(value)
                            CI.attributes[key].astext == str(value) 
                        )
                    )
                    if current_ci_id:
                        stmt = stmt.where(CI.id != current_ci_id)
                    
                    result = await db.execute(stmt)
                    if result.scalar_one_or_none():
                         raise ValueError(f"属性 {attr_schema.get('label', key)} 的值 '{value}' 已存在")


    async def create(
        self,
        db: AsyncSession,
        type_code: str,
        name: str,
        identifier: str,
        attributes: Dict[str, Any] = None,
    ) -> CI:
        """创建配置项"""
        # 获取类型
        ci_type = await CITypeService().get_type_by_code(db, type_code)
        if not ci_type:
            raise ValueError(f"未知的配置项类型: {type_code}")
        
        attributes = attributes or {}
        
        # 属性校验
        await self._validate_attributes(db, type_code, attributes)

        # 检查标识符唯一性
        existing = await self.get_by_identifier(db, identifier)
        if existing:
            raise ValueError(f"配置项标识符已存在: {identifier}")
        
        ci = CI(
            type_id=ci_type.id,
            name=name,
            identifier=identifier,
            status="active",
            attributes=attributes,
        )
        db.add(ci)
        await db.commit()
        await db.refresh(ci)
        
        logger.info(f"创建配置项: {identifier} - {name}")
        return ci

    async def get_by_id(self, db: AsyncSession, ci_id: int) -> Optional[CI]:
        """根据ID获取配置项"""
        result = await db.execute(
            select(CI)
            .options(selectinload(CI.ci_type))
            .where(CI.id == ci_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_identifier(self, db: AsyncSession, identifier: str) -> Optional[CI]:
        """根据标识符获取配置项"""
        result = await db.execute(
            select(CI)
            .options(selectinload(CI.ci_type))
            .where(CI.identifier == identifier)
        )
        return result.scalar_one_or_none()
    
    async def list(
        self,
        db: AsyncSession,
        type_code: Optional[str] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[List[CI], int]:
        """获取配置项列表"""
        query = select(CI).options(selectinload(CI.ci_type))
        count_query = select(CI)
        
        # 类型筛选
        if type_code:
            ci_type = await CITypeService().get_type_by_code(db, type_code)
            if ci_type:
                query = query.where(CI.type_id == ci_type.id)
                count_query = count_query.where(CI.type_id == ci_type.id)
        
        # 状态筛选
        if status:
            query = query.where(CI.status == status)
            count_query = count_query.where(CI.status == status)
        
        # 关键词搜索
        if keyword:
            query = query.where(
                or_(
                    CI.name.contains(keyword),
                    CI.identifier.contains(keyword),
                )
            )
            count_query = count_query.where(
                or_(
                    CI.name.contains(keyword),
                    CI.identifier.contains(keyword),
                )
            )
        
        # 总数
        count_result = await db.execute(count_query)
        total = len(count_result.all())
        
        # 分页
        query = query.offset(offset).limit(limit).order_by(CI.id.desc())
        result = await db.execute(query)
        
        return result.scalars().all(), total

    async def update(
        self,
        db: AsyncSession,
        ci_id: int,
        name: Optional[str] = None,
        status: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Optional[CI]:
        """更新配置项"""
        ci = await self.get_by_id(db, ci_id)
        if not ci:
            return None
        
        if attributes:
            # 合并属性
            new_attributes = {**(ci.attributes or {}), **attributes}
            # 校验完整属性
            await self._validate_attributes(db, ci.ci_type.code, new_attributes, current_ci_id=ci_id)
            ci.attributes = new_attributes

        if name:
            ci.name = name
        if status:
            ci.status = status
        
        ci.updated_at = datetime.now()
        await db.commit()
        await db.refresh(ci)
        
        return ci
    
    async def delete(self, db: AsyncSession, ci_id: int) -> bool:
        """删除配置项"""
        ci = await self.get_by_id(db, ci_id)
        if not ci:
            return False
        
        await db.delete(ci)
        await db.commit()
        return True


class RelationshipService:
    """配置项关系服务"""
    
    RELATION_TYPES = [
        "depends_on",     # 依赖
        "contains",       # 包含
        "connects_to",    # 连接
        "runs_on",        # 运行于
        "deployed_on",    # 部署于
        "belongs_to",     # 属于
    ]
    
    async def create(
        self,
        db: AsyncSession,
        from_ci_id: int,
        to_ci_id: int,
        rel_type: str,
        attributes: Dict[str, Any] = None,
    ) -> CIRelationship:
        """创建关系"""
        if rel_type not in self.RELATION_TYPES:
            raise ValueError(f"未知的关系类型: {rel_type}")
        
        # 检查是否已存在相同关系
        result = await db.execute(
            select(CIRelationship).where(
                and_(
                    CIRelationship.from_ci_id == from_ci_id,
                    CIRelationship.to_ci_id == to_ci_id,
                    CIRelationship.rel_type == rel_type,
                )
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError("关系已存在")
        
        rel = CIRelationship(
            from_ci_id=from_ci_id,
            to_ci_id=to_ci_id,
            rel_type=rel_type,
            attributes=attributes or {},
        )
        db.add(rel)
        await db.commit()
        await db.refresh(rel)
        
        return rel
    
    async def get_relationships(
        self,
        db: AsyncSession,
        ci_id: int,
        direction: str = "both",  # from, to, both
    ) -> Dict[str, List[CIRelationship]]:
        """获取配置项的关系"""
        result = {"upstream": [], "downstream": []}
        
        if direction in ("from", "both"):
            # 上游（指向当前CI的关系）
            query = select(CIRelationship).where(CIRelationship.to_ci_id == ci_id)
            res = await db.execute(query)
            result["upstream"] = res.scalars().all()
        
        if direction in ("to", "both"):
            # 下游（当前CI指向的关系）
            query = select(CIRelationship).where(CIRelationship.from_ci_id == ci_id)
            res = await db.execute(query)
            result["downstream"] = res.scalars().all()
        
        return result
    
    async def delete(self, db: AsyncSession, rel_id: int) -> bool:
        """删除关系"""
        result = await db.execute(
            select(CIRelationship).where(CIRelationship.id == rel_id)
        )
        rel = result.scalar_one_or_none()
        if not rel:
            return False
        
        await db.delete(rel)
        await db.commit()
        return True


class TopologyService:
    """拓扑服务"""
    
    async def get_topology(
        self,
        db: AsyncSession,
        center_ci_id: Optional[int] = None,
        depth: int = 2,
    ) -> Dict[str, Any]:
        """获取拓扑图数据"""
        nodes = []
        edges = []
        visited_ci_ids = set()
        
        if center_ci_id:
            # 以某个CI为中心展示
            await self._traverse_topology(
                db, center_ci_id, depth, nodes, edges, visited_ci_ids
            )
        else:
            # 展示所有CI
            result = await db.execute(
                select(CI).options(selectinload(CI.ci_type)).limit(100)
            )
            cis = result.scalars().all()
            
            for ci in cis:
                nodes.append(self._ci_to_node(ci))
                visited_ci_ids.add(ci.id)
            
            # 获取这些CI之间的关系
            if visited_ci_ids:
                rel_result = await db.execute(
                    select(CIRelationship).where(
                        and_(
                            CIRelationship.from_ci_id.in_(visited_ci_ids),
                            CIRelationship.to_ci_id.in_(visited_ci_ids),
                        )
                    )
                )
                rels = rel_result.scalars().all()
                for rel in rels:
                    edges.append(self._rel_to_edge(rel))
        
        return {"nodes": nodes, "edges": edges}
    
    async def _traverse_topology(
        self,
        db: AsyncSession,
        ci_id: int,
        depth: int,
        nodes: List,
        edges: List,
        visited: set,
    ):
        """递归遍历拓扑"""
        if ci_id in visited or depth < 0:
            return
        
        visited.add(ci_id)
        
        # 获取当前CI
        result = await db.execute(
            select(CI).options(selectinload(CI.ci_type)).where(CI.id == ci_id)
        )
        ci = result.scalar_one_or_none()
        if not ci:
            return
        
        nodes.append(self._ci_to_node(ci))
        
        if depth == 0:
            return
        
        # 获取关系
        rel_service = RelationshipService()
        rels = await rel_service.get_relationships(db, ci_id)
        
        for rel in rels["upstream"]:
            edges.append(self._rel_to_edge(rel))
            await self._traverse_topology(db, rel.from_ci_id, depth - 1, nodes, edges, visited)
        
        for rel in rels["downstream"]:
            edges.append(self._rel_to_edge(rel))
            await self._traverse_topology(db, rel.to_ci_id, depth - 1, nodes, edges, visited)
    
    def _ci_to_node(self, ci: CI) -> Dict:
        """CI转拓扑节点"""
        return {
            "id": ci.id,
            "name": ci.name,
            "identifier": ci.identifier,
            "type": ci.ci_type.code if ci.ci_type else None,
            "type_name": ci.ci_type.name if ci.ci_type else None,
            "icon": ci.ci_type.icon if ci.ci_type else None,
            "status": ci.status,
        }
    
    def _rel_to_edge(self, rel: CIRelationship) -> Dict:
        """关系转拓扑边"""
        return {
            "id": rel.id,
            "source": rel.from_ci_id,
            "target": rel.to_ci_id,
            "type": rel.rel_type,
        }


# 创建全局服务实例
ci_type_service = CITypeService()
ci_service = CIService()
relationship_service = RelationshipService()
topology_service = TopologyService()
