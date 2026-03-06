from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.pipeline_service import NovelPipelineService

router = APIRouter(tags=["generate_chapter"])
pipeline_service = NovelPipelineService()


class GenerateChapterRequest(BaseModel):
    outline: str
    story_id: Optional[str] = "demo-story"
    agent_configs: Optional[dict[str, Any]] = None
    constraints: Optional[List[str]] = None
    llm_config: Optional[dict[str, Any]] = None


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


@router.post("/generate_chapter", response_model=GenerateChapterResponse)
async def generate_chapter_api(payload: GenerateChapterRequest) -> GenerateChapterResponse:
    final_state = pipeline_service.run(
        outline=payload.outline,
        story_id=payload.story_id,
    )

    return GenerateChapterResponse(
        **final_state,
        story_id=payload.story_id or "demo-story",
    )
