"""
Analytics API - 分析和优化相关的 API 接口
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.cache_predictor import get_cache_predictor
from app.core.incremental_cache import get_incremental_cache, get_smart_cache_updater
from app.core.agent_analytics import get_agent_tracker, get_realtime_monitor, AgentAction, AgentActionType
from app.core.user_behavior_logger import get_behavior_logger, UserActionType


router = APIRouter(prefix="/api/analytics", tags=["analytics"])


# ==================== Pydantic Models ====================

class CachePredictionRequest(BaseModel):
    query: str
    novel_id: str


class CachePredictionResponse(BaseModel):
    hit_probability: float
    confidence: float
    suggested_action: str
    similar_queries: list


class IncrementalUpdateRequest(BaseModel):
    key: str
    data: Dict[str, Any]


class AgentActionRequest(BaseModel):
    agent_type: str
    action_type: str
    novel_id: str
    chapter_id: Optional[str] = None
    content_length: int = 0
    quality_score: float = 0.0
    execution_time_ms: int = 0
    tokens_consumed: int = 0
    strategy_used: Optional[str] = None


class UserBehaviorRequest(BaseModel):
    user_id: str
    action_type: str
    session_id: str
    novel_id: Optional[str] = None
    chapter_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# ==================== Cache Prediction API ====================

@router.post("/cache/predict", response_model=CachePredictionResponse)
async def predict_cache_hit(request: CachePredictionRequest):
    """预测缓存命中率"""
    try:
        predictor = get_cache_predictor()
        result = predictor.predict_hit_probability(request.query, request.novel_id)
        
        return CachePredictionResponse(
            hit_probability=result.hit_probability,
            confidence=result.confidence,
            suggested_action=result.suggested_action,
            similar_queries=result.similar_queries
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/record")
async def record_cache_result(
    query: str,
    novel_id: str,
    cache_hit: bool,
    result_quality: float = 1.0
):
    """记录缓存查询结果，用于改进预测"""
    try:
        predictor = get_cache_predictor()
        predictor.record_query_result(query, novel_id, cache_hit, result_quality)
        return {"message": "Cache result recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/prediction-stats")
async def get_prediction_stats():
    """获取缓存预测统计"""
    try:
        predictor = get_cache_predictor()
        return predictor.get_prediction_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Incremental Cache API ====================

@router.post("/incremental-cache/update")
async def incremental_update(request: IncrementalUpdateRequest):
    """增量更新缓存"""
    try:
        updater = get_smart_cache_updater()
        result = updater.smart_update(request.key, request.data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/incremental-cache/{key}")
async def get_cached_data(key: str):
    """获取缓存数据"""
    try:
        cache = get_incremental_cache()
        data = cache.get(key)
        if data is None:
            raise HTTPException(status_code=404, detail="Cache key not found")
        return {"key": key, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/incremental-cache/stats")
async def get_incremental_cache_stats():
    """获取增量缓存统计"""
    try:
        cache = get_incremental_cache()
        return cache.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Agent Analytics API ====================

@router.post("/agent/record-action")
async def record_agent_action(request: AgentActionRequest):
    """记录 Agent 动作"""
    try:
        tracker = get_agent_tracker()
        
        action = AgentAction(
            action_id=f"action_{datetime.now().timestamp()}",
            agent_type=request.agent_type,
            action_type=AgentActionType(request.action_type),
            novel_id=request.novel_id,
            chapter_id=request.chapter_id,
            content_length=request.content_length,
            quality_score=request.quality_score,
            execution_time_ms=request.execution_time_ms,
            tokens_consumed=request.tokens_consumed,
            strategy_used=request.strategy_used
        )
        
        tracker.record_action(action)
        return {"message": "Agent action recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/ranking")
async def get_agent_ranking():
    """获取 Agent 贡献排名"""
    try:
        tracker = get_agent_tracker()
        ranking = tracker.get_agent_ranking()
        
        return {
            "ranking": [
                {
                    "rank": i + 1,
                    "agent_type": c.agent_type,
                    "total_actions": c.total_actions,
                    "average_quality": round(c.average_quality, 3),
                    "efficiency_score": round(c.efficiency_score, 3)
                }
                for i, c in enumerate(ranking[:10])
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/insights/{agent_type}")
async def get_agent_insights(agent_type: str):
    """获取特定 Agent 的深度洞察"""
    try:
        tracker = get_agent_tracker()
        insights = tracker.get_agent_insights(agent_type)
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/full-report")
async def get_agent_full_report():
    """获取 Agent 完整分析报告"""
    try:
        tracker = get_agent_tracker()
        return tracker.generate_full_report()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/session-status")
async def get_session_status():
    """获取当前会话状态"""
    try:
        monitor = get_realtime_monitor()
        return monitor.get_session_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== User Behavior API ====================

@router.post("/behavior/log")
async def log_user_behavior(request: UserBehaviorRequest):
    """记录用户行为"""
    try:
        logger = get_behavior_logger()
        
        logger.log_event(
            user_id=request.user_id,
            action_type=UserActionType(request.action_type),
            session_id=request.session_id,
            novel_id=request.novel_id,
            chapter_id=request.chapter_id,
            metadata=request.metadata
        )
        
        return {"message": "User behavior logged"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/behavior/end-session/{session_id}")
async def end_user_session(session_id: str):
    """结束用户会话"""
    try:
        logger = get_behavior_logger()
        logger.end_session(session_id)
        return {"message": "Session ended"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/behavior/summary/{user_id}")
async def get_user_behavior_summary(user_id: str):
    """获取用户行为摘要"""
    try:
        logger = get_behavior_logger()
        return logger.get_user_behavior_summary(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/behavior/patterns")
async def get_behavior_patterns():
    """获取整体行为模式"""
    try:
        logger = get_behavior_logger()
        return logger.get_behavior_patterns()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/behavior/suggestions")
async def get_optimization_suggestions():
    """获取优化建议"""
    try:
        logger = get_behavior_logger()
        return {"suggestions": logger.generate_optimization_suggestions()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/behavior/export")
async def export_behavior_data(format: str = "json"):
    """导出行为数据"""
    try:
        logger = get_behavior_logger()
        data = logger.export_data(format)
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from datetime import datetime
