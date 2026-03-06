from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.agent_chat_service import AgentChatService

router = APIRouter(prefix="/api/agent", tags=["agent-room"])
chat_service = AgentChatService()


class AgentChatRequest(BaseModel):
    message: str
    story_id: Optional[str] = "demo-story"


@router.post("/chat")
async def agent_chat(payload: AgentChatRequest) -> Dict[str, Any]:
    return chat_service.chat(payload.message, payload.story_id or "demo-story")
