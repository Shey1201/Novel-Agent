"""
Analysis API
提供文本分析相关的 API 接口
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.reflexion import get_reflexion_engine, evaluate_text
from app.core.foreshadowing import (
    get_foreshadowing_tracker,
    extract_clues_from_chapter,
    get_active_clues_for_chapter
)
from app.core.conflict_analyzer import (
    analyze_chapter_conflict,
    generate_conflict_heatmap
)
from app.core.text_traceability import (
    get_text_source_info,
    get_traceability_manager
)


router = APIRouter(prefix="/api/analysis", tags=["analysis"])


# ==================== Pydantic Models ====================

class TextAnalysisRequest(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = None
    story_bible: Optional[Dict[str, Any]] = None


class ReflexionResponse(BaseModel):
    original_text: str
    issues: list
    needs_rewrite: bool
    rewrite_type: str
    rewritten_text: Optional[str]
    improvement_summary: str


class ClueExtractionRequest(BaseModel):
    chapter_content: str
    chapter_summary: str
    chapter_number: int


class ClueResponse(BaseModel):
    id: str
    clue: str
    chapter_created: int
    priority: int
    status: str
    expected_resolution: Optional[str]
    related_characters: list


class ConflictAnalysisResponse(BaseModel):
    tension_score: float
    conflict_types: list
    tension_curve: Dict[str, Any]
    conflict_points: list
    suggestions: list
    pacing: Dict[str, Any]
    emotional_arc: list


class HeatmapResponse(BaseModel):
    segments: list
    overall_stats: Dict[str, Any]


class TraceabilityRequest(BaseModel):
    selected_text: str
    document_id: Optional[str] = None


class TraceabilityResponse(BaseModel):
    found: bool
    source: Optional[Dict[str, Any]] = None
    generation_context: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


# ==================== Reflexion API ====================

@router.post("/reflexion/evaluate", response_model=ReflexionResponse)
async def evaluate_text_endpoint(request: TextAnalysisRequest):
    """评估文本质量并生成重写建议"""
    try:
        result = await evaluate_text(
            text=request.text,
            context=request.context or {},
            story_bible=request.story_bible
        )
        
        return ReflexionResponse(
            original_text=result.original_text[:500] + "..." if len(result.original_text) > 500 else result.original_text,
            issues=[
                {
                    "type": issue.type.value,
                    "severity": issue.severity.value,
                    "description": issue.description,
                    "location": issue.location,
                    "suggestion": issue.suggestion
                }
                for issue in result.issues
            ],
            needs_rewrite=result.needs_rewrite,
            rewrite_type=result.rewrite_type,
            rewritten_text=result.rewritten_text,
            improvement_summary=result.improvement_summary
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reflexion/rewrite")
async def rewrite_text_endpoint(request: TextAnalysisRequest):
    """自动重写文本"""
    try:
        engine = get_reflexion_engine()
        result = await engine.evaluate_and_rewrite(
            text=request.text,
            context=request.context or {},
            story_bible=request.story_bible,
            auto_rewrite=True
        )
        
        return {
            "original": result.original_text,
            "rewritten": result.rewritten_text,
            "issues_found": len(result.issues),
            "improvements": result.improvement_summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Foreshadowing API ====================

@router.post("/foreshadowing/extract")
async def extract_clues_endpoint(request: ClueExtractionRequest):
    """从章节提取伏笔"""
    try:
        result = await extract_clues_from_chapter(
            chapter_content=request.chapter_content,
            chapter_summary=request.chapter_summary,
            chapter_number=request.chapter_number
        )
        
        return {
            "chapter_number": result.chapter_number,
            "clues_extracted": len(result.clues),
            "clues": [
                {
                    "id": clue.id,
                    "clue": clue.clue,
                    "priority": clue.priority.value,
                    "priority_label": clue.priority.name,
                    "status": clue.status.value,
                    "expected_resolution": clue.expected_resolution,
                    "related_characters": clue.related_characters,
                    "related_plotlines": clue.related_plotlines,
                    "tags": clue.tags
                }
                for clue in result.clues
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/foreshadowing/active/{chapter_number}")
async def get_active_clues_endpoint(chapter_number: int):
    """获取当前章节的活跃伏笔"""
    try:
        reminders = get_active_clues_for_chapter(chapter_number)
        return {
            "chapter_number": chapter_number,
            "active_clues": len(reminders),
            "reminders": reminders
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/foreshadowing/stats")
async def get_foreshadowing_stats():
    """获取伏笔统计信息"""
    try:
        tracker = get_foreshadowing_tracker()
        stats = tracker.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/foreshadowing/resolve/{clue_id}")
async def resolve_clue_endpoint(clue_id: str, chapter_number: int, notes: str = ""):
    """解决伏笔"""
    try:
        tracker = get_foreshadowing_tracker()
        tracker.resolve_clue(clue_id, chapter_number, notes)
        return {"message": "Clue resolved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Conflict Analysis API ====================

@router.post("/conflict/analyze", response_model=ConflictAnalysisResponse)
async def analyze_conflict_endpoint(request: TextAnalysisRequest):
    """分析章节冲突"""
    try:
        result = await analyze_chapter_conflict(request.text)
        return ConflictAnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conflict/heatmap", response_model=HeatmapResponse)
async def generate_heatmap_endpoint(request: TextAnalysisRequest):
    """生成冲突热力图"""
    try:
        result = await generate_conflict_heatmap(request.text)
        return HeatmapResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conflict/quick-score")
async def quick_conflict_score(request: TextAnalysisRequest):
    """快速获取冲突分数"""
    try:
        result = await analyze_chapter_conflict(request.text)
        return {
            "tension_score": result["tension_score"],
            "conflict_types": result["conflict_types"],
            "curve_type": result["tension_curve"]["curve_type"],
            "total_conflicts": len(result["conflict_points"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Traceability API ====================

@router.post("/traceability/source", response_model=TraceabilityResponse)
async def get_text_source_endpoint(request: TraceabilityRequest):
    """获取文本来源信息"""
    try:
        result = get_text_source_info(request.selected_text)
        
        if not result.get("found"):
            return TraceabilityResponse(
                found=False,
                message=result.get("message", "未找到来源信息")
            )
        
        return TraceabilityResponse(
            found=True,
            source=result.get("source"),
            generation_context=result.get("generation_context")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/traceability/stats")
async def get_traceability_stats():
    """获取溯源统计信息"""
    try:
        manager = get_traceability_manager()
        stats = manager.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Combined Analysis API ====================

@router.post("/comprehensive")
async def comprehensive_analysis(request: TextAnalysisRequest):
    """综合分析 - 一次性获取所有分析结果"""
    try:
        # 并行执行所有分析
        import asyncio
        
        reflexion_task = evaluate_text(
            request.text, request.context or {}, request.story_bible
        )
        conflict_task = analyze_chapter_conflict(request.text)
        
        reflexion_result, conflict_result = await asyncio.gather(
            reflexion_task, conflict_task
        )
        
        return {
            "quality": {
                "needs_rewrite": reflexion_result.needs_rewrite,
                "issues_count": len(reflexion_result.issues),
                "issues": [
                    {
                        "type": i.type.value,
                        "severity": i.severity.value,
                        "description": i.description
                    }
                    for i in reflexion_result.issues[:5]  # 只返回前5个
                ]
            },
            "conflict": {
                "tension_score": conflict_result["tension_score"],
                "curve_type": conflict_result["tension_curve"]["curve_type"],
                "suggestions": conflict_result["suggestions"][:3]  # 只返回前3个建议
            },
            "overall_score": self._calculate_overall_score(
                reflexion_result, conflict_result
            )
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    def _calculate_overall_score(self, reflexion_result, conflict_result):
        """计算综合评分"""
        # 基于问题数量和冲突分数计算
        issue_penalty = len(reflexion_result.issues) * 0.05
        tension_bonus = conflict_result["tension_score"] * 0.3
        
        base_score = 0.7
        score = base_score - issue_penalty + tension_bonus
        
        return round(max(0, min(1, score)), 2)
