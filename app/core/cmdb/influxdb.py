"""
InfluxDB时序数据服务
存储和查询性能指标数据
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger

from app.config import settings


class InfluxDBService:
    """InfluxDB服务"""
    
    def __init__(
        self,
        url: str = None,
        token: str = None,
        org: str = None,
        bucket: str = None,
    ):
        self.url = url or settings.influxdb_url
        self.token = token or settings.influxdb_token
        self.org = org or settings.influxdb_org
        self.bucket = bucket or settings.influxdb_bucket
        self._client = None
        self._write_api = None
        self._write_api = None
        self._query_api = None
    
    def _format_time(self, dt: datetime) -> str:
        """格式化时间为Flux接受的RFC3339格式"""
        if dt.tzinfo is None:
            # 如果是naive时间，假设为UTC并添加Z
            return dt.isoformat() + "Z"
        return dt.isoformat()
    
    def _get_client(self):
        """获取客户端"""
        if self._client is None:
            try:
                from influxdb_client import InfluxDBClient
                self._client = InfluxDBClient(
                    url=self.url,
                    token=self.token,
                    org=self.org,
                )
                self._write_api = self._client.write_api()
                self._query_api = self._client.query_api()
            except ImportError:
                raise RuntimeError("influxdb-client未安装，请执行: pip install influxdb-client")
        return self._client
    
    async def write_point(
        self,
        measurement: str,
        tags: Dict[str, str],
        fields: Dict[str, Any],
        timestamp: datetime = None,
    ):
        """写入单个数据点"""
        try:
            from influxdb_client import Point
            
            self._get_client()
            
            point = Point(measurement)
            
            for key, value in tags.items():
                point.tag(key, value)
            
            for key, value in fields.items():
                point.field(key, value)
            
            if timestamp:
                point.time(timestamp)
            
            self._write_api.write(bucket=self.bucket, record=point)
            
        except Exception as e:
            logger.error(f"写入InfluxDB失败: {e}")
            raise
    
    async def write_metric(
        self,
        ci_identifier: str,
        metric_name: str,
        value: float,
        unit: str = "",
        extra_tags: Dict[str, str] = None,
        timestamp: datetime = None,
    ):
        """写入指标数据"""
        tags = {
            "ci_identifier": ci_identifier,
            "metric": metric_name,
        }
        if unit:
            tags["unit"] = unit
        if extra_tags:
            tags.update(extra_tags)
        
        fields = {"value": value}
        
        await self.write_point(
            measurement="ci_metrics",
            tags=tags,
            fields=fields,
            timestamp=timestamp,
        )
    
    async def write_batch(
        self,
        points: List[Dict[str, Any]],
    ):
        """批量写入"""
        try:
            from influxdb_client import Point
            
            self._get_client()
            
            records = []
            for p in points:
                point = Point(p.get("measurement", "ci_metrics"))
                
                for key, value in p.get("tags", {}).items():
                    point.tag(key, str(value))
                
                for key, value in p.get("fields", {}).items():
                    point.field(key, value)
                
                if "timestamp" in p:
                    point.time(p["timestamp"])
                
                records.append(point)
            
            self._write_api.write(bucket=self.bucket, record=records)
            logger.debug(f"批量写入 {len(records)} 条数据到InfluxDB")
            
        except Exception as e:
            logger.error(f"批量写入InfluxDB失败: {e}")
            raise
    
    async def query(
        self,
        ci_identifier: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime = None,
        aggregation: str = "mean",  # mean, max, min, sum, count
        window: str = "1m",  # 聚合窗口
    ) -> List[Dict[str, Any]]:
        """查询指标数据"""
        try:
            self._get_client()
            
            end_time = end_time or datetime.now()
            
            # Flux查询语句
            start_str = self._format_time(start_time)
            end_str = self._format_time(end_time)
            
            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: time(v: "{start_str}"), stop: time(v: "{end_str}"))
                |> filter(fn: (r) => r["ci_identifier"] == "{ci_identifier}")
                |> filter(fn: (r) => r["metric"] == "{metric_name}")
                |> aggregateWindow(every: {window}, fn: {aggregation}, createEmpty: false)
                |> yield(name: "{aggregation}")
            '''
            
            tables = self._query_api.query(query)
            
            results = []
            for table in tables:
                for record in table.records:
                    results.append({
                        "time": record.get_time(),
                        "value": record.get_value(),
                        "ci_identifier": record.values.get("ci_identifier"),
                        "metric": record.values.get("metric"),
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"查询InfluxDB失败: {e}")
            raise
    
    async def query_latest(
        self,
        ci_identifier: str,
        metric_name: str = None,
    ) -> List[Dict[str, Any]]:
        """查询最新值"""
        try:
            self._get_client()
            
            metric_filter = ""
            if metric_name:
                metric_filter = f'|> filter(fn: (r) => r["metric"] == "{metric_name}")'
            
            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: -1h)
                |> filter(fn: (r) => r["ci_identifier"] == "{ci_identifier}")
                {metric_filter}
                |> last()
            '''
            
            tables = self._query_api.query(query)
            
            results = []
            for table in tables:
                for record in table.records:
                    results.append({
                        "time": record.get_time(),
                        "value": record.get_value(),
                        "metric": record.values.get("metric"),
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"查询InfluxDB失败: {e}")
            raise
    
    async def get_ci_metrics_summary(
        self,
        ci_identifier: str,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """获取配置项的指标摘要"""
        try:
            self._get_client()
            
            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: -{hours}h)
                |> filter(fn: (r) => r["ci_identifier"] == "{ci_identifier}")
                |> group(columns: ["metric"])
                |> reduce(
                    identity: {{count: 0, sum: 0.0, min: 0.0, max: 0.0}},
                    fn: (r, accumulator) => ({{
                        count: accumulator.count + 1,
                        sum: accumulator.sum + r._value,
                        min: if accumulator.count == 0 then r._value else if r._value < accumulator.min then r._value else accumulator.min,
                        max: if accumulator.count == 0 then r._value else if r._value > accumulator.max then r._value else accumulator.max
                    }})
                )
            '''
            
            tables = self._query_api.query(query)
            
            summary = {}
            for table in tables:
                for record in table.records:
                    metric = record.values.get("metric", "unknown")
                    summary[metric] = {
                        "count": record.values.get("count", 0),
                        "sum": record.values.get("sum", 0),
                        "min": record.values.get("min", 0),
                        "max": record.values.get("max", 0),
                    }
            
            return summary
            
        except Exception as e:
            logger.error(f"获取指标摘要失败: {e}")
            return {}
    
    def close(self):
        """关闭连接"""
        if self._client:
            self._client.close()
            self._client = None
            self._write_api = None
            self._query_api = None


# 创建全局服务实例
influxdb_service = InfluxDBService()
