from typing import Any, List, Optional, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.graph import build_full_flow

router = APIRouter(tags=["generate_chapter"])


class GenerateChapterRequest(BaseModel):
    """
    生成章节的请求体。

    说明：
    - outline: 本章大纲/要点。
    - story_id: 可选的故事 ID，后续用于加载 Story Memory。
    - agent_configs: Agent 的行为参数配置。
    - constraints: 全局写作约束。
    - llm_config: 预留字段，前端可以直接填写 LLM 配置。
    """

    outline: str
    story_id: Optional[str] = "demo-story"
    agent_configs: Optional[dict[str, Any]] = None
    constraints: Optional[List[str]] = None
    llm_config: Optional[dict[str, Any]] = None


from app.memory.story_memory import StoryMemory, StoryBible

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
    """
    生成章节的 API 接口。

    使用完整的 LangGraph 多 Agent 流程。
    """
    # 编译流程
    flow = build_full_flow()
    
    # 初始化 Memory
    story_memory = StoryMemory(story_id=payload.story_id or "demo-story", bible=StoryBible())

    # 初始化状态
    initial_state = {
        "input_text": payload.outline,
        "agent_logs": [],
        "trace_data": [],
        "plan_text": "",
        "conflict_suggestions": [],
        "draft_text": "",
        "edited_text": "",
        "reader_feedback": [],
        "summary_text": "",
        "final_text": "",
        "story_memory": story_memory
    }
    
    # 执行流程
    final_state = flow.invoke(initial_state)
    
    return GenerateChapterResponse(
        **final_state,
        story_id=payload.story_id or "demo-story"
    )

