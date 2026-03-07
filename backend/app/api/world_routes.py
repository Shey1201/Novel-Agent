from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime

from app.memory.story_memory import StoryBible, Character, WorldRule
from app.services.world_service import WorldDebateRequest, WorldService

router = APIRouter(prefix="/api/world", tags=["world"])
world_service = WorldService()


class ApproveWorldRequest(BaseModel):
    story_id: str = "demo-story"
    world_bible: StoryBible


class UpdateStoryBibleRequest(BaseModel):
    """更新 Story Bible 请求"""
    title: Optional[str] = None
    genre: Optional[str] = None
    world_view: Optional[str] = None
    tone: Optional[str] = None
    characters: Optional[List[Character]] = None
    world_rules: Optional[List[WorldRule]] = None
    major_plot_points: Optional[List[str]] = None


class StoryBibleResponse(BaseModel):
    """Story Bible 响应"""
    story_id: str
    title: str = ""
    genre: str = ""
    world_view: str = ""
    tone: str = ""
    characters: List[Character] = Field(default_factory=list)
    world_rules: List[WorldRule] = Field(default_factory=list)
    major_plot_points: List[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.now)


# 内存存储（实际应该使用数据库）
story_bibles: Dict[str, Dict[str, Any]] = {}


@router.post("/debate")
async def debate_world(payload: WorldDebateRequest) -> Dict[str, Any]:
    result = world_service.debate(payload)
    return result.model_dump()


@router.post("/approve")
async def approve_world(payload: ApproveWorldRequest) -> Dict[str, Any]:
    return world_service.approve(payload.story_id, payload.world_bible)


@router.get("/{story_id}")
async def get_world(story_id: str) -> Dict[str, Any]:
    """获取世界设定和 Story Bible"""
    world_data = world_service.get_world(story_id)
    
    # 合并 Story Bible 数据
    if story_id in story_bibles:
        bible_data = story_bibles[story_id]
        world_data["world_bible"] = {
            **world_data.get("world_bible", {}),
            **bible_data
        }
    
    return world_data


@router.put("/{story_id}")
async def update_story_bible(story_id: str, request: UpdateStoryBibleRequest) -> Dict[str, Any]:
    """更新 Story Bible"""
    if story_id not in story_bibles:
        story_bibles[story_id] = {}
    
    # 更新数据
    update_data = request.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now().isoformat()
    
    story_bibles[story_id].update(update_data)
    
    return {
        "success": True,
        "story_id": story_id,
        "data": story_bibles[story_id]
    }


@router.post("/{story_id}/characters")
async def add_character(story_id: str, character: Character) -> Dict[str, Any]:
    """添加角色"""
    if story_id not in story_bibles:
        story_bibles[story_id] = {"characters": []}
    
    if "characters" not in story_bibles[story_id]:
        story_bibles[story_id]["characters"] = []
    
    story_bibles[story_id]["characters"].append(character.model_dump())
    
    return {
        "success": True,
        "character_id": character.id,
        "data": character.model_dump()
    }


@router.delete("/{story_id}/characters/{character_id}")
async def delete_character(story_id: str, character_id: str) -> Dict[str, Any]:
    """删除角色"""
    if story_id not in story_bibles or "characters" not in story_bibles[story_id]:
        raise HTTPException(status_code=404, detail="Story or characters not found")
    
    characters = story_bibles[story_id]["characters"]
    story_bibles[story_id]["characters"] = [
        c for c in characters if c.get("id") != character_id
    ]
    
    return {"success": True, "deleted_id": character_id}


@router.post("/{story_id}/rules")
async def add_world_rule(story_id: str, rule: WorldRule) -> Dict[str, Any]:
    """添加世界规则"""
    if story_id not in story_bibles:
        story_bibles[story_id] = {"world_rules": []}
    
    if "world_rules" not in story_bibles[story_id]:
        story_bibles[story_id]["world_rules"] = []
    
    story_bibles[story_id]["world_rules"].append(rule.model_dump())
    
    return {
        "success": True,
        "rule_id": rule.id,
        "data": rule.model_dump()
    }


@router.delete("/{story_id}/rules/{rule_id}")
async def delete_world_rule(story_id: str, rule_id: str) -> Dict[str, Any]:
    """删除世界规则"""
    if story_id not in story_bibles or "world_rules" not in story_bibles[story_id]:
        raise HTTPException(status_code=404, detail="Story or rules not found")
    
    rules = story_bibles[story_id]["world_rules"]
    story_bibles[story_id]["world_rules"] = [
        r for r in rules if r.get("id") != rule_id
    ]
    
    return {"success": True, "deleted_id": rule_id}
