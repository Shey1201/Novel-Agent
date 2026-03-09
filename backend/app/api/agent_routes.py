from typing import Any, Dict, Optional
import traceback

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.agent_chat_service import AgentChatService

router = APIRouter(prefix="/api/agent", tags=["agent-room"])
chat_service = AgentChatService()


class WordCountRange(BaseModel):
    min: int = 3000
    max: int = 4000


class ConversationState(BaseModel):
    stage: Optional[str] = None
    workflow_type: Optional[str] = None
    waiting_for_user: bool = False
    accumulated_content: Optional[list] = None


class AgentChatRequest(BaseModel):
    message: str
    story_id: Optional[str] = "demo-story"
    word_count_range: Optional[WordCountRange] = None
    conversation_state: Optional[ConversationState] = None


@router.post("/chat")
async def agent_chat(payload: AgentChatRequest) -> Dict[str, Any]:
    try:
        # 转换 conversation_state 为字典格式
        state_dict = None
        if payload.conversation_state:
            state_dict = {
                "stage": payload.conversation_state.stage,
                "workflow_type": payload.conversation_state.workflow_type,
                "waiting_for_user": payload.conversation_state.waiting_for_user,
                "accumulated_content": payload.conversation_state.accumulated_content or []
            }
        
        # 转换 word_count_range 为字典格式
        word_count_dict = None
        if payload.word_count_range:
            word_count_dict = {
                "min": payload.word_count_range.min,
                "max": payload.word_count_range.max
            }
        
        result = chat_service.chat(
            payload.message, 
            payload.story_id or "demo-story",
            word_count_range=word_count_dict,
            conversation_state=state_dict
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
