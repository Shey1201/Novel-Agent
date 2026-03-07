"""
Yjs WebSocket Server
提供协同编辑的 WebSocket 服务
"""

import asyncio
import json
import logging
from typing import Dict, Set
from dataclasses import dataclass

import websockets
from websockets.server import WebSocketServerProtocol

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DocumentRoom:
    """文档房间"""
    doc_id: str
    clients: Set[WebSocketServerProtocol]
    updates: list
    
    def __init__(self, doc_id: str):
        self.doc_id = doc_id
        self.clients = set()
        self.updates = []


class YjsServer:
    """
    Yjs WebSocket 服务器
    
    实现 Yjs 协议，支持多人协同编辑
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 1234):
        self.host = host
        self.port = port
        self.rooms: Dict[str, DocumentRoom] = {}
        self.client_rooms: Dict[WebSocketServerProtocol, str] = {}
    
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """处理客户端连接"""
        # 从路径中提取文档ID
        # 路径格式: /document-id 或 /?document=document-id
        doc_id = self._extract_doc_id(path)
        
        if not doc_id:
            logger.warning(f"Invalid path: {path}")
            await websocket.close(1000, "Invalid document ID")
            return
        
        logger.info(f"Client connected to document: {doc_id}")
        
        # 加入房间
        await self._join_room(websocket, doc_id)
        
        try:
            async for message in websocket:
                await self._handle_message(websocket, message, doc_id)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected from document: {doc_id}")
        finally:
            await self._leave_room(websocket, doc_id)
    
    def _extract_doc_id(self, path: str) -> str:
        """从路径中提取文档ID"""
        # 移除开头的 /
        path = path.lstrip("/")
        
        # 如果路径为空，返回默认ID
        if not path:
            return "default"
        
        # 处理查询参数
        if "?" in path:
            from urllib.parse import parse_qs, urlparse
            parsed = urlparse(path)
            params = parse_qs(parsed.query)
            if "document" in params:
                return params["document"][0]
            return parsed.path or "default"
        
        return path
    
    async def _join_room(self, websocket: WebSocketServerProtocol, doc_id: str):
        """客户端加入房间"""
        if doc_id not in self.rooms:
            self.rooms[doc_id] = DocumentRoom(doc_id)
        
        room = self.rooms[doc_id]
        room.clients.add(websocket)
        self.client_rooms[websocket] = doc_id
        
        # 发送 awareness 同步消息
        await self._send_awareness_sync(websocket)
        
        # 广播用户加入
        await self._broadcast_user_change(room, websocket, "join")
        
        logger.info(f"Room {doc_id} now has {len(room.clients)} clients")
    
    async def _leave_room(self, websocket: WebSocketServerProtocol, doc_id: str):
        """客户端离开房间"""
        if doc_id in self.rooms:
            room = self.rooms[doc_id]
            room.clients.discard(websocket)
            
            # 广播用户离开
            await self._broadcast_user_change(room, websocket, "leave")
            
            # 如果房间空了，可以选择清理
            if not room.clients:
                logger.info(f"Room {doc_id} is empty, keeping for reconnection")
        
        self.client_rooms.pop(websocket, None)
    
    async def _handle_message(self, websocket: WebSocketServerProtocol, message, doc_id: str):
        """处理消息"""
        if isinstance(message, bytes):
            # 处理二进制消息 (Yjs 更新)
            await self._handle_binary_message(websocket, message, doc_id)
        else:
            # 处理文本消息 (JSON)
            await self._handle_text_message(websocket, message, doc_id)
    
    async def _handle_binary_message(self, websocket: WebSocketServerProtocol, message: bytes, doc_id: str):
        """处理二进制消息"""
        room = self.rooms.get(doc_id)
        if not room:
            return
        
        # 保存更新
        room.updates.append(message)
        
        # 广播给其他客户端
        for client in room.clients:
            if client != websocket and client.open:
                try:
                    await client.send(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")
    
    async def _handle_text_message(self, websocket: WebSocketServerProtocol, message: str, doc_id: str):
        """处理文本消息"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "awareness":
                # 转发 awareness 消息
                await self._broadcast_awareness(websocket, data, doc_id)
            elif msg_type == "query":
                # 处理查询请求
                await self._handle_query(websocket, data, doc_id)
            else:
                logger.warning(f"Unknown message type: {msg_type}")
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON message: {message}")
    
    async def _broadcast_awareness(self, sender: WebSocketServerProtocol, data: dict, doc_id: str):
        """广播 awareness 消息"""
        room = self.rooms.get(doc_id)
        if not room:
            return
        
        message = json.dumps(data)
        
        for client in room.clients:
            if client != sender and client.open:
                try:
                    await client.send(message)
                except Exception as e:
                    logger.error(f"Error broadcasting awareness: {e}")
    
    async def _broadcast_user_change(self, room: DocumentRoom, client: WebSocketServerProtocol, change_type: str):
        """广播用户变化"""
        message = json.dumps({
            "type": "user_change",
            "data": {
                "count": len(room.clients),
                "type": change_type
            }
        })
        
        for c in room.clients:
            if c.open:
                try:
                    await c.send(message)
                except Exception as e:
                    logger.error(f"Error broadcasting user change: {e}")
    
    async def _send_awareness_sync(self, websocket: WebSocketServerProtocol):
        """发送 awareness 同步消息"""
        sync_msg = json.dumps({
            "type": "sync",
            "data": {
                "status": "connected"
            }
        })
        await websocket.send(sync_msg)
    
    async def _handle_query(self, websocket: WebSocketServerProtocol, data: dict, doc_id: str):
        """处理查询请求"""
        query_type = data.get("query")
        
        if query_type == "stats":
            room = self.rooms.get(doc_id)
            if room:
                response = {
                    "type": "query_response",
                    "query": query_type,
                    "data": {
                        "client_count": len(room.clients),
                        "update_count": len(room.updates)
                    }
                }
                await websocket.send(json.dumps(response))
    
    async def start(self):
        """启动服务器"""
        logger.info(f"Starting Yjs WebSocket server on {self.host}:{self.port}")
        
        async with websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10
        ):
            logger.info(f"Yjs WebSocket server started on ws://{self.host}:{self.port}")
            await asyncio.Future()  # 永久运行
    
    def get_room_stats(self, doc_id: str) -> dict:
        """获取房间统计信息"""
        room = self.rooms.get(doc_id)
        if not room:
            return {"exists": False}
        
        return {
            "exists": True,
            "client_count": len(room.clients),
            "update_count": len(room.updates)
        }
    
    def get_all_stats(self) -> dict:
        """获取所有房间统计信息"""
        return {
            doc_id: {
                "client_count": len(room.clients),
                "update_count": len(room.updates)
            }
            for doc_id, room in self.rooms.items()
        }


# 全局服务器实例
_yjs_server: YjsServer = None


def get_yjs_server() -> YjsServer:
    """获取 Yjs 服务器实例"""
    global _yjs_server
    if _yjs_server is None:
        _yjs_server = YjsServer()
    return _yjs_server


async def start_yjs_server(host: str = "0.0.0.0", port: int = 1234):
    """启动 Yjs 服务器"""
    server = YjsServer(host=host, port=port)
    await server.start()


if __name__ == "__main__":
    # 直接运行服务器
    asyncio.run(start_yjs_server())
