"""
Socket服务
接收告警和监控数据
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from loguru import logger

from app.config import settings


class SocketProtocol(asyncio.Protocol):
    """Socket协议处理"""
    
    def __init__(self, handler: Callable, server: "SocketServer"):
        self.handler = handler
        self.server = server
        self.transport = None
        self.buffer = b""
    
    def connection_made(self, transport):
        """连接建立"""
        self.transport = transport
        peer = transport.get_extra_info("peername")
        logger.info(f"Socket连接建立: {peer}")
        self.server.connection_count += 1
    
    def connection_lost(self, exc):
        """连接断开"""
        peer = self.transport.get_extra_info("peername") if self.transport else "unknown"
        logger.info(f"Socket连接断开: {peer}")
        self.server.connection_count -= 1
    
    def data_received(self, data: bytes):
        """接收数据"""
        self.buffer += data
        
        # 按换行符分割消息
        while b"\n" in self.buffer:
            line, self.buffer = self.buffer.split(b"\n", 1)
            if line:
                asyncio.create_task(self._process_message(line))
    
    async def _process_message(self, data: bytes):
        """处理消息"""
        try:
            message = data.decode("utf-8").strip()
            
            # 尝试解析JSON
            try:
                payload = json.loads(message)
            except json.JSONDecodeError:
                # 非JSON格式，原样传递
                payload = {"raw": message}
            
            # 调用处理器
            response = await self.handler(payload)
            
            # 发送响应
            if response and self.transport:
                response_data = json.dumps(response) + "\n"
                self.transport.write(response_data.encode("utf-8"))
        
        except Exception as e:
            logger.error(f"处理Socket消息失败: {e}")


class SocketServer:
    """Socket服务器"""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
    ):
        self.host = host or settings.socket_host
        self.port = port or settings.socket_port
        self.server = None
        self.connection_count = 0
        self._handlers: Dict[str, Callable] = {}
        self._default_handler: Optional[Callable] = None
    
    def register_handler(self, message_type: str, handler: Callable):
        """注册消息处理器"""
        self._handlers[message_type] = handler
        logger.info(f"注册Socket处理器: {message_type}")
    
    def set_default_handler(self, handler: Callable):
        """设置默认处理器"""
        self._default_handler = handler
    
    async def _handle_message(self, payload: Dict) -> Optional[Dict]:
        """处理消息"""
        msg_type = payload.get("type") or payload.get("message_type", "default")
        handler = self._handlers.get(msg_type, self._default_handler)
        
        if handler:
            return await handler(payload)
        else:
            logger.warning(f"未找到处理器: {msg_type}")
            return {"status": "error", "message": f"Unknown message type: {msg_type}"}
    
    async def start(self):
        """启动服务器"""
        loop = asyncio.get_event_loop()
        
        self.server = await loop.create_server(
            lambda: SocketProtocol(self._handle_message, self),
            self.host,
            self.port,
        )
        
        logger.info(f"Socket服务器启动: {self.host}:{self.port}")
        
        async with self.server:
            await self.server.serve_forever()
    
    async def stop(self):
        """停止服务器"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.server = None
        logger.info("Socket服务器已停止")


# ==================== 默认消息处理器 ====================

async def handle_alert(payload: Dict) -> Dict:
    """处理告警消息"""
    try:
        alert_data = {
            "alert_id": payload.get("alert_id") or payload.get("id"),
            "ci_identifier": payload.get("ci_identifier") or payload.get("host"),
            "level": payload.get("level", "warning"),
            "title": payload.get("title") or payload.get("name"),
            "content": payload.get("content") or payload.get("message"),
            "source": payload.get("source", "socket"),
            "alert_time": payload.get("alert_time") or datetime.now().isoformat(),
        }
        
        logger.info(f"收到Socket告警: {alert_data['alert_id']} - {alert_data['title']}")
        
        # TODO: 保存告警
        
        return {"status": "ok", "message": "Alert received"}
    
    except Exception as e:
        logger.error(f"处理告警失败: {e}")
        return {"status": "error", "message": str(e)}


async def handle_heartbeat(payload: Dict) -> Dict:
    """处理心跳消息"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "server": "skb-socket",
    }


async def handle_metric(payload: Dict) -> Dict:
    """处理指标数据"""
    try:
        metric_data = {
            "ci_identifier": payload.get("ci_identifier") or payload.get("host"),
            "metric_name": payload.get("metric_name") or payload.get("metric"),
            "value": payload.get("value"),
            "timestamp": payload.get("timestamp") or datetime.now().isoformat(),
        }
        
        logger.debug(f"收到指标: {metric_data['ci_identifier']} - {metric_data['metric_name']}")
        
        # TODO: 写入时序数据库
        
        return {"status": "ok"}
    
    except Exception as e:
        logger.error(f"处理指标失败: {e}")
        return {"status": "error", "message": str(e)}


def create_default_socket_server() -> SocketServer:
    """创建默认配置的Socket服务器"""
    server = SocketServer()
    
    # 注册处理器
    server.register_handler("alert", handle_alert)
    server.register_handler("heartbeat", handle_heartbeat)
    server.register_handler("metric", handle_metric)
    server.set_default_handler(handle_alert)  # 默认按告警处理
    
    return server


# 全局Socket服务器实例
socket_server = create_default_socket_server()
