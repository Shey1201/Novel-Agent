"""
Agent Room API - AI编剧室API
整合Agent Reasoning、Discussion、Author Decision等功能
"""

from typing import Any, Dict, Optional, Callable
import traceback
import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.agent_chat_service import AgentChatService
from app.core.ai_config import create_llm_from_config, get_ai_config_from_db

router = APIRouter(prefix="/api/agent", tags=["agent-room"])


# ==================== WebSocket 消息类型 ====================
class AgentMessageType:
    """Agent Room WebSocket 消息类型"""
    AGENT_START = "agent_start"
    AGENT_MESSAGE = "agent_message"
    AGENT_COMPLETE = "agent_complete"
    AGENT_ERROR = "agent_error"
    CONSENSUS_UPDATE = "consensus_update"
    PROGRESS_UPDATE = "progress_update"
    USER_INPUT_REQUIRED = "user_input_required"


# ==================== WebSocket 连接管理器 ====================
class AgentRoomConnectionManager:
    """Agent Room WebSocket 连接管理器"""

    def __init__(self):
        # story_id -> set of WebSockets
        self.active_connections: Dict[str, set] = {}

    async def connect(self, story_id: str, websocket: WebSocket):
        """连接 WebSocket"""
        await websocket.accept()
        if story_id not in self.active_connections:
            self.active_connections[story_id] = set()
        self.active_connections[story_id].add(websocket)

    def disconnect(self, story_id: str, websocket: WebSocket):
        """断开 WebSocket"""
        if story_id in self.active_connections:
            self.active_connections[story_id].discard(websocket)
            if not self.active_connections[story_id]:
                del self.active_connections[story_id]

    async def send_message(self, story_id: str, message: Dict[str, Any]):
        """向指定 story_id 的所有连接发送消息"""
        if story_id not in self.active_connections:
            return
        dead_connections = set()
        for connection in self.active_connections[story_id]:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.add(connection)
        for dead in dead_connections:
            self.disconnect(story_id, dead)

    async def broadcast(self, message: Dict[str, Any]):
        """广播消息到所有连接"""
        for story_id in list(self.active_connections.keys()):
            await self.send_message(story_id, message)


agent_room_manager = AgentRoomConnectionManager()


def create_streaming_callback(story_id: str) -> Callable:
    """创建流式回调函数，用于实时推送 Agent 消息"""
    async def callback(message_type: str, data: Dict[str, Any]):
        """推送消息到 WebSocket"""
        await agent_room_manager.send_message(story_id, {
            "type": message_type,
            "data": data
        })
    return callback

def get_chat_service():
    """每次请求动态创建 AgentChatService，确保读取最新 AI 配置。"""
    ai_config = get_ai_config_from_db()
    print(f"[DEBUG] get_chat_service: ai_config = {ai_config}")
    llm = create_llm_from_config(ai_config)
    print(f"[DEBUG] get_chat_service: llm = {llm}")
    return AgentChatService(llm=llm)


class WordCountRange(BaseModel):
    min: int = 3000
    max: int = 4000


class AgentChatRequest(BaseModel):
    message: str
    story_id: Optional[str] = "demo-story"
    story_name: Optional[str] = None  # 新增：小说名称，供 AI 生成内容时使用
    chapter_id: Optional[str] = None  # 新增：章节ID
    chapter_name: Optional[str] = None  # 新增：章节名称，供 AI 显示用
    word_count_range: Optional[WordCountRange] = None
    # 允许完整透传对话状态，避免丢失 pending_save/context_confirmed 等字段
    conversation_state: Optional[Dict[str, Any]] = None


@router.post("/chat")
async def agent_chat(payload: AgentChatRequest) -> Dict[str, Any]:
    try:
        # 直接透传 conversation_state，保留 pending_save 等关键状态
        state_dict = payload.conversation_state or None

        # 转换 word_count_range 为字典格式
        word_count_dict = None
        if payload.word_count_range:
            word_count_dict = {
                "min": payload.word_count_range.min,
                "max": payload.word_count_range.max
            }

        # 获取 chat_service（会自动使用数据库中的 AI 配置）
        service = get_chat_service()

        # 注意：当前是 async endpoint，但 service.chat 是同步阻塞调用。
        # 必须放到线程池，否则会阻塞事件循环导致请求卡住/超时。
        result = await asyncio.to_thread(
            service.chat,
            payload.message,
            payload.story_id or "demo-story",
            payload.chapter_id,
            payload.chapter_name,
            word_count_dict,
            state_dict,
            payload.story_name,
        )
        return result
    except Exception as e:
        error_msg = f"Error in agent_chat: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return {
            "error": str(e),
            "agent_logs": [
                {
                    "agent": "system",
                    "agent_name": "系统",
                    "message": "❌ 服务器错误",
                    "content": f"处理请求时发生错误: {str(e)}"
                }
            ],
            "final_text": "",
            "final_agent": "system"
        }


# ==================== 流式输出 (SSE) ====================
async def generate_chat_stream(payload: AgentChatRequest):
    """生成流式聊天响应"""
    story_id = payload.story_id or "demo-story"
    state_dict = payload.conversation_state or None

    word_count_dict = None
    if payload.word_count_range:
        word_count_dict = {
            "min": payload.word_count_range.min,
            "max": payload.word_count_range.max
        }

    service = get_chat_service()
    callback = create_streaming_callback(story_id)

    try:
        # 发送开始消息
        await callback(AgentMessageType.AGENT_START, {
            "message": "开始处理请求",
            "story_id": story_id
        })

        # 执行聊天（传入回调）
        result = await service.chat_with_callback(
            payload.message,
            story_id,
            chapter_id=payload.chapter_id,
            chapter_name=payload.chapter_name,
            word_count_range=word_count_dict,
            conversation_state=state_dict,
            story_name=payload.story_name,
            stream_callback=callback
        )

        # 发送完成消息
        await callback(AgentMessageType.AGENT_COMPLETE, {
            "result": result
        })

        # 返回完整结果
        yield f"data: {json.dumps(result, ensure_ascii=False)}\n\n"

    except Exception as e:
        error_msg = f"Error in streaming_chat: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        await callback(AgentMessageType.AGENT_ERROR, {
            "error": str(e)
        })
        yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"


@router.post("/chat/stream")
async def streaming_chat(payload: AgentChatRequest):
    """
    流式聊天接口 - 通过 SSE 实时推送 Agent 消息
    前端可以通过 EventSource 或 fetch ReadableStream 接收
    """
    return StreamingResponse(
        generate_chat_stream(payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ==================== WebSocket 实时通信 ====================
@router.websocket("/ws/{story_id}")
async def agent_room_websocket(websocket: WebSocket, story_id: str):
    """
    Agent Room WebSocket 端点
    - 支持实时推送 Agent 消息
    - 客户端可以订阅特定 story_id 的消息
    """
    await agent_room_manager.connect(story_id, websocket)

    try:
        await websocket.send_json({
            "type": "connected",
            "message": f"已连接到 Agent Room: {story_id}",
            "story_id": story_id
        })

        while True:
            data = await websocket.receive_text()
            msg_data = json.loads(data)
            msg_type = msg_data.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "timestamp": asyncio.get_event_loop().time()})
            elif msg_type == "subscribe":
                # 客户端订阅消息（默认已自动订阅）
                await websocket.send_json({
                    "type": "subscribed",
                    "story_id": story_id
                })
            elif msg_type == "send_message":
                # 客户端通过 WebSocket 发送消息
                message = msg_data.get("message")
                if message:
                    # 创建回调
                    callback = create_streaming_callback(story_id)
                    service = get_chat_service()

                    # 处理消息
                    result = await service.chat_with_callback(
                        message,
                        story_id,
                        chapter_id=msg_data.get("chapter_id"),
                        chapter_name=msg_data.get("chapter_name"),
                        word_count_range=msg_data.get("word_count_range"),
                        conversation_state=msg_data.get("conversation_state"),
                        story_name=msg_data.get("story_name"),
                        stream_callback=callback
                    )

                    # 发送结果
                    await websocket.send_json({
                        "type": "message_result",
                        "data": result
                    })
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}"
                })

    except WebSocketDisconnect:
        agent_room_manager.disconnect(story_id, websocket)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        agent_room_manager.disconnect(story_id, websocket)
