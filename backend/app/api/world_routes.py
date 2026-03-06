from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from app.memory.story_memory import StoryBible
from app.services.world_service import WorldDebateRequest, WorldService

router = APIRouter(prefix="/api/world", tags=["world"])
world_service = WorldService()


class ApproveWorldRequest(BaseModel):
    story_id: str = "demo-story"
    world_bible: StoryBible


@router.post("/debate")
async def debate_world(payload: WorldDebateRequest) -> Dict[str, Any]:
    result = world_service.debate(payload)
    return result.model_dump()


@router.post("/approve")
async def approve_world(payload: ApproveWorldRequest) -> Dict[str, Any]:
    return world_service.approve(payload.story_id, payload.world_bible)


@router.get("/{story_id}")
async def get_world(story_id: str) -> Dict[str, Any]:
    return world_service.get_world(story_id)
