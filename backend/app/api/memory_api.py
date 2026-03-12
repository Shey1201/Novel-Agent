"""
Memory API - 历史记忆侧边栏后端接口
提供 StoryMemory 的读取和编辑功能
与 chapter_service 统一使用 story_memory.json，避免双文件不同步。
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.chapter_service import load_memory, save_memory
from app.memory.story_memory import StoryMemory, StoryBible, Character, ChapterSummary, TimelineEvent

router = APIRouter(prefix="/api/memory", tags=["memory"])


# ==================== Pydantic Models ====================

class CharacterInput(BaseModel):
    """角色输入模型"""
    id: Optional[str] = None
    name: str
    aliases: List[str] = Field(default_factory=list)
    age: Optional[int] = None
    gender: Optional[str] = None
    appearance: str = ""
    personality: str = ""
    background: str = ""
    current_state: str = ""
    tags: List[str] = Field(default_factory=list)


class ChapterSummaryInput(BaseModel):
    """章节摘要输入模型"""
    chapter_id: str
    title: str
    summary: str
    pov: Optional[str] = None
    word_count: int = 0
    key_events: List[str] = Field(default_factory=list)
    mood: str = ""


class MemoryResponse(BaseModel):
    """记忆响应模型"""
    success: bool
    message: str = ""
    data: Optional[Dict[str, Any]] = None


# ==================== 工具函数（统一使用 story_memory.json）====================

def load_story_memory(story_id: str) -> Dict[str, Any]:
    """加载故事记忆为 API 用 Dict，来源：story_memory.json（与 agent/写作链路一致）"""
    memory = load_memory(story_id)
    if memory is None:
        return _default_memory_dict(story_id)
    data = memory.model_dump()
    # 兼容前端可能使用的字段
    data.setdefault("unresolved_clues", [])
    return data


def _default_memory_dict(story_id: str) -> Dict[str, Any]:
    """默认空记忆 Dict"""
    return {
        "story_id": story_id,
        "bible": StoryBible().model_dump(),
        "characters": [],
        "timeline": [],
        "chapter_summaries": [],
        "world_locked": False,
        "unresolved_clues": [],
    }


def save_story_memory(story_id: str, memory_data: Dict[str, Any]):
    """保存故事记忆：写入 story_memory.json（与 chapter_service 一致）"""
    memory = load_memory(story_id)
    if memory is None:
        memory = StoryMemory(story_id=story_id, bible=StoryBible())
    # 只更新 API 允许的字段，避免覆盖未传字段
    if "bible" in memory_data and memory_data["bible"]:
        memory.bible = StoryBible.model_validate(memory_data["bible"])
    if "characters" in memory_data:
        memory.characters = [Character.model_validate(c) for c in memory_data["characters"]]
    if "timeline" in memory_data:
        memory.timeline = [TimelineEvent.model_validate(t) for t in memory_data["timeline"]]
    if "chapter_summaries" in memory_data:
        memory.chapter_summaries = [ChapterSummary.model_validate(s) for s in memory_data["chapter_summaries"]]
    if "world_locked" in memory_data:
        memory.world_locked = bool(memory_data["world_locked"])
    if "unresolved_clues" in memory_data:
        memory.unresolved_clues = list(memory_data["unresolved_clues"])
    save_memory(memory)


# ==================== API Endpoints ====================

@router.get("/{story_id}")
async def get_story_memory(story_id: str) -> MemoryResponse:
    """
    获取故事记忆
    """
    try:
        memory_data = load_story_memory(story_id)
        return MemoryResponse(
            success=True,
            message="获取成功",
            data=memory_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{story_id}/characters")
async def get_characters(story_id: str) -> MemoryResponse:
    """
    获取所有角色
    """
    try:
        memory_data = load_story_memory(story_id)
        characters = memory_data.get("characters", [])
        return MemoryResponse(
            success=True,
            message=f"获取到 {len(characters)} 个角色",
            data={"characters": characters}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{story_id}/characters")
async def add_character(story_id: str, character: CharacterInput) -> MemoryResponse:
    """
    添加新角色
    """
    try:
        memory_data = load_story_memory(story_id)
        
        # 生成角色ID
        import uuid
        char_id = character.id or f"char-{uuid.uuid4().hex[:8]}"
        
        new_character = {
            "id": char_id,
            "name": character.name,
            "aliases": character.aliases,
            "age": character.age,
            "gender": character.gender,
            "appearance": character.appearance,
            "personality": character.personality,
            "background": character.background,
            "current_state": character.current_state,
            "tags": character.tags,
            "abilities": [],
            "weaknesses": [],
            "secrets": [],
            "values": [],
            "fears": [],
            "desires": [],
            "relationships": [],
            "arc": {
                "start_state": "",
                "end_state": "",
                "key_moments": []
            }
        }
        
        memory_data.setdefault("characters", []).append(new_character)
        save_story_memory(story_id, memory_data)
        
        return MemoryResponse(
            success=True,
            message=f"角色 {character.name} 添加成功",
            data={"character": new_character}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{story_id}/characters/{character_id}")
async def update_character(
    story_id: str,
    character_id: str,
    character: CharacterInput
) -> MemoryResponse:
    """
    更新角色信息
    """
    try:
        memory_data = load_story_memory(story_id)
        
        characters = memory_data.get("characters", [])
        for i, char in enumerate(characters):
            if char.get("id") == character_id:
                # 更新角色信息
                characters[i].update({
                    "name": character.name,
                    "aliases": character.aliases,
                    "age": character.age,
                    "gender": character.gender,
                    "appearance": character.appearance,
                    "personality": character.personality,
                    "background": character.background,
                    "current_state": character.current_state,
                    "tags": character.tags
                })
                save_story_memory(story_id, memory_data)
                return MemoryResponse(
                    success=True,
                    message=f"角色 {character.name} 更新成功",
                    data={"character": characters[i]}
                )
        
        raise HTTPException(status_code=404, detail="角色不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{story_id}/characters/{character_id}")
async def delete_character(story_id: str, character_id: str) -> MemoryResponse:
    """
    删除角色
    """
    try:
        memory_data = load_story_memory(story_id)
        
        characters = memory_data.get("characters", [])
        original_count = len(characters)
        characters = [c for c in characters if c.get("id") != character_id]
        
        if len(characters) == original_count:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        memory_data["characters"] = characters
        save_story_memory(story_id, memory_data)
        
        return MemoryResponse(
            success=True,
            message="角色删除成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{story_id}/summaries")
async def get_chapter_summaries(story_id: str) -> MemoryResponse:
    """
    获取章节摘要列表
    """
    try:
        memory_data = load_story_memory(story_id)
        summaries = memory_data.get("chapter_summaries", [])
        return MemoryResponse(
            success=True,
            message=f"获取到 {len(summaries)} 个章节摘要",
            data={"summaries": summaries}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{story_id}/summaries")
async def add_chapter_summary(
    story_id: str,
    summary: ChapterSummaryInput
) -> MemoryResponse:
    """
    添加章节摘要
    """
    try:
        memory_data = load_story_memory(story_id)
        
        from datetime import datetime
        new_summary = {
            "chapter_id": summary.chapter_id,
            "title": summary.title,
            "summary": summary.summary,
            "pov": summary.pov,
            "word_count": summary.word_count,
            "key_events": summary.key_events,
            "mood": summary.mood,
            "character_development": {},
            "created_at": datetime.now().isoformat()
        }
        
        memory_data.setdefault("chapter_summaries", []).append(new_summary)
        save_story_memory(story_id, memory_data)
        
        return MemoryResponse(
            success=True,
            message=f"章节摘要 {summary.title} 添加成功",
            data={"summary": new_summary}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{story_id}/bible")
async def get_story_bible(story_id: str) -> MemoryResponse:
    """
    获取故事圣经
    """
    try:
        memory_data = load_story_memory(story_id)
        bible = memory_data.get("bible", {})
        return MemoryResponse(
            success=True,
            message="获取成功",
            data={"bible": bible}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{story_id}/bible")
async def update_story_bible(
    story_id: str,
    bible_data: Dict[str, Any]
) -> MemoryResponse:
    """
    更新故事圣经
    """
    try:
        memory_data = load_story_memory(story_id)
        memory_data["bible"] = bible_data
        save_story_memory(story_id, memory_data)
        
        return MemoryResponse(
            success=True,
            message="故事圣经更新成功",
            data={"bible": bible_data}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{story_id}/status")
async def get_memory_status(story_id: str) -> MemoryResponse:
    """
    获取记忆系统状态
    """
    try:
        memory_data = load_story_memory(story_id)
        
        return MemoryResponse(
            success=True,
            message="获取成功",
            data={
                "story_id": story_id,
                "character_count": len(memory_data.get("characters", [])),
                "chapter_summary_count": len(memory_data.get("chapter_summaries", [])),
                "timeline_event_count": len(memory_data.get("timeline", [])),
                "world_locked": memory_data.get("world_locked", False),
                "storage_type": "story_memory"  # 统一使用 story_memory.json
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
