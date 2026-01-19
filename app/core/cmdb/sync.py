"""
数据库同步服务
从外部数据库抽取数据同步到CMDB
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings


class DatabaseConnector:
    """数据库连接器"""
    
    def __init__(
        self,
        db_type: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
    ):
        self.db_type = db_type
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self._engine = None
    
    def get_connection_url(self) -> str:
        """获取连接URL"""
        drivers = {
            "mysql": "mysql+aiomysql",
            "postgresql": "postgresql+asyncpg",
            "oracle": "oracle+cx_oracle_async",
            "sqlserver": "mssql+aioodbc",
        }
        driver = drivers.get(self.db_type, "mysql+aiomysql")
        return f"{driver}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    async def connect(self):
        """建立连接"""
        if self._engine is None:
            url = self.get_connection_url()
            self._engine = create_async_engine(url, echo=False)
        return self._engine
    
    async def close(self):
        """关闭连接"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
    
    async def execute_query(self, sql: str, params: Dict = None) -> List[Dict]:
        """执行查询"""
        engine = await self.connect()
        async with engine.connect() as conn:
            result = await conn.execute(text(sql), params or {})
            rows = result.fetchall()
            columns = result.keys()
            return [dict(zip(columns, row)) for row in rows]
    
    async def test_connection(self) -> bool:
        """测试连接"""
        try:
            engine = await self.connect()
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False


class TableMapping:
    """表映射配置"""
    
    def __init__(
        self,
        source_table: str,
        ci_type_code: str,
        field_mappings: Dict[str, str],  # {ci_field: source_field}
        identifier_field: str,
        name_field: str,
        filter_condition: Optional[str] = None,
    ):
        self.source_table = source_table
        self.ci_type_code = ci_type_code
        self.field_mappings = field_mappings
        self.identifier_field = identifier_field
        self.name_field = name_field
        self.filter_condition = filter_condition
    
    def build_select_sql(self) -> str:
        """构建查询SQL"""
        # 获取需要查询的字段
        fields = list(set(
            list(self.field_mappings.values()) + 
            [self.identifier_field, self.name_field]
        ))
        fields_str = ", ".join(fields)
        
        sql = f"SELECT {fields_str} FROM {self.source_table}"
        if self.filter_condition:
            sql += f" WHERE {self.filter_condition}"
        
        return sql
    
    def map_row_to_ci(self, row: Dict) -> Dict:
        """将数据行映射为CI数据"""
        attributes = {}
        for ci_field, source_field in self.field_mappings.items():
            if source_field in row:
                attributes[ci_field] = row[source_field]
        
        return {
            "identifier": str(row.get(self.identifier_field, "")),
            "name": str(row.get(self.name_field, "")),
            "type_code": self.ci_type_code,
            "attributes": attributes,
        }


class DataSyncService:
    """数据同步服务"""
    
    def __init__(self):
        self._connectors: Dict[int, DatabaseConnector] = {}
    
    def get_connector(self, datasource_id: int, config: Dict) -> DatabaseConnector:
        """获取或创建数据库连接器"""
        if datasource_id not in self._connectors:
            self._connectors[datasource_id] = DatabaseConnector(
                db_type=config["db_type"],
                host=config["host"],
                port=config["port"],
                database=config["database"],
                username=config["username"],
                password=config["password"],
            )
        return self._connectors[datasource_id]
    
    async def sync_datasource(
        self,
        datasource_id: int,
        config: Dict,
        mappings: List[TableMapping],
        ci_service,  # CIService实例
        db_session: AsyncSession,
    ) -> Dict[str, int]:
        """同步数据源"""
        connector = self.get_connector(datasource_id, config)
        
        stats = {
            "total": 0,
            "created": 0,
            "updated": 0,
            "failed": 0,
        }
        
        for mapping in mappings:
            try:
                # 执行查询
                sql = mapping.build_select_sql()
                logger.info(f"开始同步表: {mapping.source_table}")
                rows = await connector.execute_query(sql)
                
                stats["total"] += len(rows)
                
                # 处理每条记录
                for row in rows:
                    try:
                        ci_data = mapping.map_row_to_ci(row)
                        
                        # 检查是否已存在
                        existing = await ci_service.get_by_identifier(
                            db_session, ci_data["identifier"]
                        )
                        
                        if existing:
                            # 更新
                            await ci_service.update(
                                db_session,
                                existing.id,
                                name=ci_data["name"],
                                attributes=ci_data["attributes"],
                            )
                            stats["updated"] += 1
                        else:
                            # 创建
                            await ci_service.create(
                                db_session,
                                type_code=ci_data["type_code"],
                                name=ci_data["name"],
                                identifier=ci_data["identifier"],
                                attributes=ci_data["attributes"],
                            )
                            stats["created"] += 1
                    
                    except Exception as e:
                        logger.error(f"处理记录失败: {row}, 错误: {e}")
                        stats["failed"] += 1
                
                logger.info(f"表 {mapping.source_table} 同步完成: {len(rows)} 条")
            
            except Exception as e:
                logger.error(f"同步表 {mapping.source_table} 失败: {e}")
        
        return stats
    
    async def close_all(self):
        """关闭所有连接"""
        for connector in self._connectors.values():
            await connector.close()
        self._connectors.clear()


class SyncScheduler:
    """同步调度器"""
    
    def __init__(self):
        self._running = False
        self._tasks: Dict[int, asyncio.Task] = {}
    
    async def start_sync_job(
        self,
        datasource_id: int,
        interval_minutes: int,
        sync_func,
    ):
        """启动同步任务"""
        if datasource_id in self._tasks:
            logger.warning(f"数据源 {datasource_id} 已有同步任务在运行")
            return
        
        async def job():
            while self._running:
                try:
                    await sync_func()
                except Exception as e:
                    logger.error(f"同步任务执行失败: {e}")
                
                await asyncio.sleep(interval_minutes * 60)
        
        self._running = True
        self._tasks[datasource_id] = asyncio.create_task(job())
        logger.info(f"启动数据源 {datasource_id} 同步任务，间隔 {interval_minutes} 分钟")
    
    async def stop_sync_job(self, datasource_id: int):
        """停止同步任务"""
        if datasource_id in self._tasks:
            self._tasks[datasource_id].cancel()
            del self._tasks[datasource_id]
            logger.info(f"停止数据源 {datasource_id} 同步任务")
    
    async def stop_all(self):
        """停止所有任务"""
        self._running = False
        for task in self._tasks.values():
            task.cancel()
        self._tasks.clear()


# 创建全局服务实例
data_sync_service = DataSyncService()
sync_scheduler = SyncScheduler()
