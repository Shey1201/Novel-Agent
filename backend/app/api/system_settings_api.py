"""
System Settings API - 系统设置接口
提供 Token 限制、讨论配置等系统设置的 API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.memory.system_settings import get_system_settings_manager
from app.core.token_budget_manager import get_token_budget_manager
from app.core.discussion_controller import get_discussion_controller
from app.core.agent_cache import get_agent_cache

router = APIRouter(prefix="/api/settings", tags=["system_settings"])


# ============ 请求/响应模型 ============

class TokenSettingsRequest(BaseModel):
    enabled: Optional[bool] = None
    daily_limit: Optional[int] = None
    warning_threshold: Optional[float] = None
    budget_allocation: Optional[Dict[str, float]] = None


class DiscussionSettingsRequest(BaseModel):
    max_rounds: Optional[int] = None
    max_tokens_per_response: Optional[int] = None
    enable_short_mode: Optional[bool] = None
    min_chapter_interval: Optional[int] = None


class CacheSettingsRequest(BaseModel):
    enable_planner_cache: Optional[bool] = None
    enable_conflict_cache: Optional[bool] = None
    enable_consistency_cache: Optional[bool] = None
    ttl_hours: Optional[int] = None


class GenerationSettingsRequest(BaseModel):
    paragraph_length: Optional[int] = None
    reader_interval: Optional[int] = None
    enable_streaming: Optional[bool] = None


# ============ Token 设置接口 ============

@router.get("/token")
async def get_token_settings():
    """获取 Token 设置"""
    manager = get_system_settings_manager()
    settings = manager.get_settings()
    return {
        "enabled": settings.token.enabled,
        "daily_limit": settings.token.daily_limit,
        "warning_threshold": settings.token.warning_threshold,
        "budget_allocation": settings.token.budget_allocation
    }


@router.put("/token")
async def update_token_settings(request: TokenSettingsRequest):
    """更新 Token 设置"""
    manager = get_system_settings_manager()
    
    # 更新设置
    kwargs = request.dict(exclude_unset=True)
    manager.update_token_settings(**kwargs)
    
    # 同步更新 Token Budget Manager
    budget_manager = get_token_budget_manager()
    if request.enabled is not None:
        if request.enabled and request.daily_limit:
            budget_manager.set_daily_limit(request.daily_limit)
        elif not request.enabled:
            budget_manager.set_daily_limit(None)
    elif request.daily_limit is not None and settings.token.enabled:
        budget_manager.set_daily_limit(request.daily_limit)
    
    return {"message": "Token 设置已更新"}


@router.get("/token/status")
async def get_token_status():
    """获取 Token 使用状态"""
    budget_manager = get_token_budget_manager()
    return budget_manager.get_daily_status()


@router.post("/token/reset")
async def reset_daily_token_usage():
    """重置每日 Token 使用"""
    budget_manager = get_token_budget_manager()
    budget_manager.reset_daily_usage()
    return {"message": "每日 Token 使用已重置"}


# ============ 讨论设置接口 ============

@router.get("/discussion")
async def get_discussion_settings():
    """获取讨论设置"""
    manager = get_system_settings_manager()
    settings = manager.get_settings()
    return {
        "max_rounds": settings.discussion.max_rounds,
        "max_tokens_per_response": settings.discussion.max_tokens_per_response,
        "enable_short_mode": settings.discussion.enable_short_mode,
        "min_chapter_interval": settings.discussion.min_chapter_interval
    }


@router.put("/discussion")
async def update_discussion_settings(request: DiscussionSettingsRequest):
    """更新讨论设置"""
    manager = get_system_settings_manager()
    kwargs = request.dict(exclude_unset=True)
    manager.update_discussion_settings(**kwargs)
    return {"message": "讨论设置已更新"}


# ============ 缓存设置接口 ============

@router.get("/cache")
async def get_cache_settings():
    """获取缓存设置"""
    manager = get_system_settings_manager()
    settings = manager.get_settings()
    return {
        "enable_planner_cache": settings.cache.enable_planner_cache,
        "enable_conflict_cache": settings.cache.enable_conflict_cache,
        "enable_consistency_cache": settings.cache.enable_consistency_cache,
        "ttl_hours": settings.cache.ttl_hours
    }


@router.put("/cache")
async def update_cache_settings(request: CacheSettingsRequest):
    """更新缓存设置"""
    manager = get_system_settings_manager()
    kwargs = request.dict(exclude_unset=True)
    manager.update_cache_settings(**kwargs)
    return {"message": "缓存设置已更新"}


@router.get("/cache/stats")
async def get_cache_stats():
    """获取缓存统计"""
    cache = get_agent_cache()
    return cache.get_stats()


@router.post("/cache/clear")
async def clear_cache():
    """清空缓存"""
    cache = get_agent_cache()
    cache.clear()
    return {"message": "缓存已清空"}


# ============ 生成设置接口 ============

@router.get("/generation")
async def get_generation_settings():
    """获取生成设置"""
    manager = get_system_settings_manager()
    settings = manager.get_settings()
    return {
        "paragraph_length": settings.generation.paragraph_length,
        "reader_interval": settings.generation.reader_interval,
        "enable_streaming": settings.generation.enable_streaming
    }


@router.put("/generation")
async def update_generation_settings(request: GenerationSettingsRequest):
    """更新生成设置"""
    manager = get_system_settings_manager()
    kwargs = request.dict(exclude_unset=True)
    manager.update_generation_settings(**kwargs)
    return {"message": "生成设置已更新"}


# ============ 所有设置接口 ============

@router.get("/all")
async def get_all_settings():
    """获取所有设置"""
    manager = get_system_settings_manager()
    settings = manager.get_settings()
    return {
        "token": {
            "enabled": settings.token.enabled,
            "daily_limit": settings.token.daily_limit,
            "warning_threshold": settings.token.warning_threshold,
            "budget_allocation": settings.token.budget_allocation
        },
        "discussion": {
            "max_rounds": settings.discussion.max_rounds,
            "max_tokens_per_response": settings.discussion.max_tokens_per_response,
            "enable_short_mode": settings.discussion.enable_short_mode,
            "min_chapter_interval": settings.discussion.min_chapter_interval
        },
        "cache": {
            "enable_planner_cache": settings.cache.enable_planner_cache,
            "enable_conflict_cache": settings.cache.enable_conflict_cache,
            "enable_consistency_cache": settings.cache.enable_consistency_cache,
            "ttl_hours": settings.cache.ttl_hours
        },
        "generation": {
            "paragraph_length": settings.generation.paragraph_length,
            "reader_interval": settings.generation.reader_interval,
            "enable_streaming": settings.generation.enable_streaming
        }
    }


@router.post("/reset")
async def reset_all_settings():
    """重置所有设置为默认值"""
    manager = get_system_settings_manager()
    manager.reset_to_default()
    return {"message": "所有设置已重置为默认值"}


# ============ 章节生成预算接口 ============

@router.post("/chapter/{chapter_id}/budget")
async def create_chapter_budget(
    chapter_id: str,
    total_budget: int = 15000,
    custom_allocations: Optional[Dict[str, float]] = None
):
    """创建章节 Token 预算"""
    from app.core.token_budget_manager import AgentType
    
    budget_manager = get_token_budget_manager()
    
    # 转换分配比例
    allocations = None
    if custom_allocations:
        allocations = {}
        for key, ratio in custom_allocations.items():
            try:
                agent_type = AgentType(key)
                allocations[agent_type] = ratio
            except ValueError:
                continue
    
    budget = budget_manager.create_chapter_budget(
        chapter_id=chapter_id,
        total_budget=total_budget,
        custom_allocations=allocations
    )
    
    return {
        "chapter_id": chapter_id,
        "total_budget": budget.total_budget,
        "allocations": {
            agent.value: alloc.budget
            for agent, alloc in budget.allocations.items()
        }
    }


@router.get("/chapter/{chapter_id}/budget")
async def get_chapter_budget_report(chapter_id: str):
    """获取章节预算使用报告"""
    budget_manager = get_token_budget_manager()
    report = budget_manager.get_budget_report(chapter_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="章节预算不存在")
    
    return report
