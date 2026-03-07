"""
Cache API
提供缓存管理的 API 接口
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.cache_manager import get_cache_manager, CacheManager
from app.memory.rag_optimizer import get_rag_optimizer


router = APIRouter(prefix="/api/cache", tags=["cache"])


# ==================== Pydantic Models ====================

class CacheStats(BaseModel):
    l1_memory: Dict[str, Any]
    l2_disk: Dict[str, Any]


class CacheClearRequest(BaseModel):
    level: str = "both"  # "l1", "l2", "both"


class CacheWarmupRequest(BaseModel):
    data: Dict[str, Any]
    ttl: int = 3600


class RAGStats(BaseModel):
    avg_query_time_ms: float
    avg_search_time_ms: float
    avg_rerank_time_ms: float
    cache_hit_rate: float
    total_queries: int


# ==================== Cache Management ====================

@router.get("/stats", response_model=CacheStats)
async def get_cache_stats():
    """获取缓存统计信息"""
    cm = get_cache_manager()
    stats = cm.get_stats()
    return CacheStats(**stats)


@router.post("/clear")
async def clear_cache(request: CacheClearRequest):
    """清空缓存"""
    cm = get_cache_manager()
    cm.clear(level=request.level)
    return {"message": f"Cache cleared (level: {request.level})"}


@router.post("/warmup")
async def warmup_cache(request: CacheWarmupRequest):
    """预热缓存"""
    cm = get_cache_manager()
    await cm.warmup(request.data, request.ttl)
    return {
        "message": f"Cache warmed up with {len(request.data)} items",
        "ttl": request.ttl
    }


# ==================== RAG Stats ====================

@router.get("/rag/stats", response_model=RAGStats)
async def get_rag_stats():
    """获取 RAG 统计信息"""
    optimizer = get_rag_optimizer()
    stats = optimizer.get_average_metrics()
    return RAGStats(**stats)


@router.post("/rag/clear")
async def clear_rag_cache():
    """清空 RAG 缓存"""
    optimizer = get_rag_optimizer()
    optimizer.clear_cache()
    return {"message": "RAG cache cleared"}


@router.post("/rag/clear-metrics")
async def clear_rag_metrics():
    """清空 RAG 指标记录"""
    optimizer = get_rag_optimizer()
    optimizer.clear_metrics()
    return {"message": "RAG metrics cleared"}


# ==================== Token Optimizer Stats ====================

@router.get("/token/stats")
async def get_token_optimizer_stats():
    """获取 Token 优化器统计信息"""
    from app.core.token_optimizer import get_token_optimizer
    
    optimizer = get_token_optimizer()
    return {
        "default_budget": optimizer.default_budget,
        "features": [
            "token_estimation",
            "context_compression",
            "budget_management",
            "smart_context_building"
        ]
    }
