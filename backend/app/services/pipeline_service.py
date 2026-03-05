from typing import Optional

from app.agents.graph import build_full_flow
from app.domain.pipeline_state import GraphState, build_initial_state
from app.memory.story_memory import StoryBible, StoryMemory


class NovelPipelineService:
    """统一封装章节生成工作流，避免 API 层重复拼装 state。"""

    def __init__(self):
        self._flow = build_full_flow()

    def run(self, outline: str, story_id: Optional[str] = None) -> GraphState:
        memory = StoryMemory(story_id=story_id or "demo-story", bible=StoryBible())
        initial_state = build_initial_state(input_text=outline, story_memory=memory)
        return self._flow.invoke(initial_state)
