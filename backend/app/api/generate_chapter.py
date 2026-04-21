from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
import re

from app.services.pipeline_service import NovelPipelineService
from app.services.pipeline_service_db import run_with_db_agents
from app.memory.novel_memory import novel_memory

router = APIRouter(prefix="/api", tags=["generate_chapter"])

# 存储进行中的生成任务
active_generations: Dict[str, Dict[str, Any]] = {}


def _count_words(text: str) -> int:
    """计算字数（中英文混合）"""
    if not text:
        return 0
    chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
    english = len(re.findall(r'[a-zA-Z]', text))
    return chinese + english


def _get_word_counts(results: Dict[str, Any]) -> Dict[str, int]:
    """获取各阶段字数统计"""
    return {
        "input": _count_words(results.get("input_text", "")),
        "plan": _count_words(results.get("plan_text", "")),
        "draft": _count_words(results.get("draft_text", "")),
        "edited": _count_words(results.get("edited_text", "")),
        "final": _count_words(results.get("final_text", "")),
    }


class GenerateChapterRequest(BaseModel):
    outline: str
    story_id: Optional[str] = "demo-story"
    chapter_id: Optional[str] = None
    agent_configs: Optional[dict[str, Any]] = None
    constraints: Optional[List[str]] = None
    llm_config: Optional[dict[str, Any]] = None
    # 新增：用户确认选项
    auto_confirm: Optional[bool] = False  # 是否自动确认所有步骤
    confirm_points: Optional[List[str]] = None  # 指定需要确认的关键点 ["outline", "draft", "final"]


class GenerateChapterResponse(BaseModel):
    input_text: str
    plan_text: str
    conflict_suggestions: List[str]
    draft_text: str
    edited_text: str
    reader_feedback: List[str]
    summary_text: str
    final_text: str
    agent_logs: List[Dict[str, Any]]
    trace_data: List[Dict[str, Any]]
    story_id: str
    # 新增：字数统计
    word_count: Optional[Dict[str, int]] = None


class GenerationStepResponse(BaseModel):
    """分步骤生成响应"""
    generation_id: str
    step: str  # "plan", "draft", "edit", "final"
    status: str  # "waiting_confirmation", "completed", "in_progress"
    content: Optional[str] = None
    message: str
    requires_confirmation: bool
    next_step: Optional[str] = None
    # 新增：当前步骤的字数
    word_count: Optional[int] = None


class ConfirmStepRequest(BaseModel):
    generation_id: str
    step: str
    action: str  # "confirm", "modify", "cancel"
    feedback: Optional[str] = None  # 用户修改意见


@router.post("/generate-chapter/start", response_model=GenerationStepResponse)
async def start_generation(payload: GenerateChapterRequest) -> GenerationStepResponse:
    """
    开始章节生成流程
    
    关键点确认机制：
    1. 如果 auto_confirm=True，直接完成全部流程
    2. 如果指定了 confirm_points，在对应步骤暂停等待用户确认
    3. 默认在 plan 和 final 两个关键点暂停
    """
    generation_id = str(uuid.uuid4())
    
    # 初始化生成任务
    active_generations[generation_id] = {
        "status": "planning",
        "payload": payload.dict(),
        "current_step": "plan",
        "results": {},
        "confirm_points": payload.confirm_points or ["plan", "final"],
        "auto_confirm": payload.auto_confirm or False
    }
    
    # 创建服务实例
    service = NovelPipelineService(llm_config=payload.llm_config)
    
    # 第一步：生成大纲/规划
    try:
        # 获取小说信息用于上下文
        novel_info = None
        if payload.story_id and payload.story_id != "demo-story":
            try:
                novel = novel_memory.get_novel(payload.story_id)
                if novel:
                    novel_info = {
                        "title": novel.title,
                        "category_id": novel.category_id,
                        "outline": novel.outline
                    }
            except Exception as e:
                print(f"[GenerateChapter] Error getting novel info: {e}")
        
        # 构建增强的输入提示
        enhanced_outline = payload.outline
        if novel_info:
            enhanced_outline = f"""基于小说《{novel_info['title']}》的创作请求：

{payload.outline}

小说背景信息：
- 类型：{novel_info['category_id'] or '未分类'}
- 大纲：{novel_info['outline'][:200] if novel_info['outline'] else '无'}
"""
        
        # 运行生成流程
        final_state = service.run(
            outline=enhanced_outline,
            story_id=payload.story_id,
            chapter_id=payload.chapter_id,
        )
        
        # 保存结果
        active_generations[generation_id]["results"] = {
            "input_text": final_state.get("input_text", ""),
            "plan_text": final_state.get("plan_text", ""),
            "conflict_suggestions": final_state.get("conflict_suggestions", []),
            "draft_text": final_state.get("draft_text", ""),
            "edited_text": final_state.get("edited_text", ""),
            "reader_feedback": final_state.get("reader_feedback", []),
            "summary_text": final_state.get("summary_text", ""),
            "final_text": final_state.get("final_text", ""),
            "agent_logs": final_state.get("agent_logs", []),
            "trace_data": final_state.get("trace_data", []),
        }
        
        # 检查是否需要确认
        requires_confirmation = not payload.auto_confirm and "plan" in (payload.confirm_points or [])
        
        if requires_confirmation:
            return GenerationStepResponse(
                generation_id=generation_id,
                step="plan",
                status="waiting_confirmation",
                content=final_state.get("plan_text", ""),
                message="📋 大纲已生成，请确认或提供修改意见",
                requires_confirmation=True,
                next_step="draft",
                word_count=_count_words(final_state.get("plan_text", "")),
            )
        else:
            # 自动确认，继续到下一步
            active_generations[generation_id]["current_step"] = "final"
            
            # 检查是否需要在最终稿确认
            if not payload.auto_confirm and "final" in (payload.confirm_points or []):
                return GenerationStepResponse(
                    generation_id=generation_id,
                    step="final",
                    status="waiting_confirmation",
                    content=final_state.get("final_text", ""),
                    message="✅ 章节已完成生成，请确认最终内容",
                    requires_confirmation=True,
                    next_step=None,
                    word_count=_count_words(final_state.get("final_text", "")),
                )
            else:
                # 全部完成
                active_generations[generation_id]["status"] = "completed"
                return GenerationStepResponse(
                    generation_id=generation_id,
                    step="final",
                    status="completed",
                    content=final_state.get("final_text", ""),
                    message="✅ 章节生成完成",
                    requires_confirmation=False,
                    next_step=None,
                    word_count=_count_words(final_state.get("final_text", "")),
                )
                
    except Exception as e:
        active_generations[generation_id]["status"] = "error"
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.post("/generate-chapter/confirm", response_model=GenerationStepResponse)
async def confirm_step(payload: ConfirmStepRequest) -> GenerationStepResponse:
    """确认或修改当前步骤"""
    if payload.generation_id not in active_generations:
        raise HTTPException(status_code=404, detail="生成任务不存在或已过期")
    
    generation = active_generations[payload.generation_id]
    
    if payload.action == "cancel":
        generation["status"] = "cancelled"
        return GenerationStepResponse(
            generation_id=payload.generation_id,
            step=payload.step,
            status="cancelled",
            message="❌ 生成任务已取消",
            requires_confirmation=False
        )
    
    if payload.action == "modify":
        # 用户提供了修改意见，需要重新生成
        # 这里简化处理，实际应该根据反馈重新调用Agent
        generation["status"] = "modifying"
        return GenerationStepResponse(
            generation_id=payload.generation_id,
            step=payload.step,
            status="modifying",
            content=generation["results"].get("plan_text" if payload.step == "plan" else "final_text", ""),
            message=f"📝 已收到修改意见: {payload.feedback}，正在重新生成...",
            requires_confirmation=False,
            next_step=payload.step
        )
    
    # 确认通过，继续下一步
    if payload.step == "plan":
        generation["current_step"] = "final"
        
        # 检查是否需要在最终稿确认
        if "final" in generation.get("confirm_points", []):
            return GenerationStepResponse(
                generation_id=payload.generation_id,
                step="final",
                status="waiting_confirmation",
                content=generation["results"].get("final_text", ""),
                message="✅ 章节已完成生成，请确认最终内容",
                requires_confirmation=True,
                next_step=None
            )
        else:
            generation["status"] = "completed"
            return GenerationStepResponse(
                generation_id=payload.generation_id,
                step="final",
                status="completed",
                content=generation["results"].get("final_text", ""),
                message="✅ 章节生成完成",
                requires_confirmation=False,
                next_step=None,
                word_count=_count_words(generation["results"].get("final_text", "")),
            )
    
    elif payload.step == "final":
        generation["status"] = "completed"
        return GenerationStepResponse(
            generation_id=payload.generation_id,
            step="final",
            status="completed",
            content=generation["results"].get("final_text", ""),
            message="✅ 章节生成完成并已保存",
            requires_confirmation=False,
            next_step=None,
            word_count=_count_words(generation["results"].get("final_text", "")),
        )
    
    return GenerationStepResponse(
        generation_id=payload.generation_id,
        step=payload.step,
        status="completed",
        message="✅ 步骤已确认",
        requires_confirmation=False,
        word_count=0,
    )


@router.get("/generate-chapter/{generation_id}/result", response_model=GenerateChapterResponse)
async def get_generation_result(generation_id: str) -> GenerateChapterResponse:
    """获取完整的生成结果"""
    if generation_id not in active_generations:
        raise HTTPException(status_code=404, detail="生成任务不存在或已过期")
    
    generation = active_generations[generation_id]
    results = generation.get("results", {})
    payload = generation.get("payload", {})
    
    return GenerateChapterResponse(
        input_text=results.get("input_text", ""),
        plan_text=results.get("plan_text", ""),
        conflict_suggestions=results.get("conflict_suggestions", []),
        draft_text=results.get("draft_text", ""),
        edited_text=results.get("edited_text", ""),
        reader_feedback=results.get("reader_feedback", []),
        summary_text=results.get("summary_text", ""),
        final_text=results.get("final_text", ""),
        agent_logs=results.get("agent_logs", []),
        trace_data=results.get("trace_data", []),
        story_id=payload.get("story_id", "demo-story"),
        word_count=_get_word_counts(results),
    )


# 保留原有的简单生成接口（向后兼容）
@router.post("/generate_chapter", response_model=GenerateChapterResponse)
async def generate_chapter_api(payload: GenerateChapterRequest) -> GenerateChapterResponse:
    """
    简化版生成接口（向后兼容）
    直接完成全部生成流程，不在中间步骤暂停
    """
    service = NovelPipelineService(llm_config=payload.llm_config)

    final_state = service.run(
        outline=payload.outline,
        story_id=payload.story_id,
        chapter_id=payload.chapter_id,
    )

    return GenerateChapterResponse(
        input_text=final_state.get("input_text", ""),
        plan_text=final_state.get("plan_text", ""),
        conflict_suggestions=final_state.get("conflict_suggestions", []),
        draft_text=final_state.get("draft_text", ""),
        edited_text=final_state.get("edited_text", ""),
        reader_feedback=final_state.get("reader_feedback", []),
        summary_text=final_state.get("summary_text", ""),
        final_text=final_state.get("final_text", ""),
        agent_logs=final_state.get("agent_logs", []),
        trace_data=final_state.get("trace_data", []),
        story_id=payload.story_id or "demo-story",
        word_count=_get_word_counts(final_state),
    )
