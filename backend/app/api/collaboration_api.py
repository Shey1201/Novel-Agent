"""
Collaboration API
提供协同编辑相关的 API 接口
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.collaboration.yjs_server import get_yjs_server


router = APIRouter(prefix="/api/collaboration", tags=["collaboration"])


# ==================== Pydantic Models ====================

class DocumentStats(BaseModel):
    document_id: str
    client_count: int
    update_count: int
    exists: bool


class CollaborationStatus(BaseModel):
    active_documents: int
    total_clients: int
    documents: Dict[str, Dict[str, int]]


class UserInfo(BaseModel):
    name: str
    color: str


# ==================== REST API ====================

@router.get("/stats", response_model=CollaborationStatus)
async def get_collaboration_stats():
    """获取协同编辑整体统计信息"""
    server = get_yjs_server()
    all_stats = server.get_all_stats()
    
    total_clients = sum(stats["client_count"] for stats in all_stats.values())
    
    return CollaborationStatus(
        active_documents=len(all_stats),
        total_clients=total_clients,
        documents=all_stats
    )


@router.get("/stats/{document_id}", response_model=DocumentStats)
async def get_document_stats(document_id: str):
    """获取特定文档的统计信息"""
    server = get_yjs_server()
    stats = server.get_room_stats(document_id)
    
    return DocumentStats(
        document_id=document_id,
        client_count=stats.get("client_count", 0),
        update_count=stats.get("update_count", 0),
        exists=stats.get("exists", False)
    )


@router.get("/documents")
async def list_active_documents():
    """列出所有活跃的文档"""
    server = get_yjs_server()
    stats = server.get_all_stats()
    
    return {
        "documents": [
            {
                "id": doc_id,
                "client_count": info["client_count"],
                "update_count": info["update_count"]
            }
            for doc_id, info in stats.items()
        ]
    }


# ==================== WebSocket ====================

@router.websocket("/ws/{document_id}")
async def collaboration_websocket(websocket: WebSocket, document_id: str):
    """
    协同编辑 WebSocket 端点
    
    此端点将客户端连接到 Yjs WebSocket 服务器
    """
    await websocket.accept()
    
    try:
        # 转发消息到 Yjs 服务器
        # 注意：实际实现中可能需要更复杂的代理逻辑
        await websocket.send_json({
            "type": "info",
            "message": f"Connected to document: {document_id}",
            "websocket_url": f"ws://localhost:1234/{document_id}"
        })
        
        while True:
            data = await websocket.receive_json()
            
            # 处理不同类型的消息
            msg_type = data.get("type")
            
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif msg_type == "get_stats":
                server = get_yjs_server()
                stats = server.get_room_stats(document_id)
                await websocket.send_json({
                    "type": "stats",
                    "data": stats
                })
            else:
                # 转发其他消息
                await websocket.send_json({
                    "type": "echo",
                    "data": data
                })
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
