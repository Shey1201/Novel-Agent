from typing import Any, Dict, Optional

from app.agents.graph import build_full_flow
from app.domain.pipeline_state import GraphState, build_initial_state
from app.memory.story_memory import StoryBible, StoryMemory
from app.core.llm import get_llm


class NovelPipelineService:
    """统一封装章节生成工作流，避免 API 层重复拼装 state。"""

    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        self._llm = self._init_llm(llm_config)
        self._flow = build_full_flow(self._llm)

    def _init_llm(self, llm_config: Optional[Dict[str, Any]] = None):
        """初始化 LLM，优先使用传入的配置"""
        if llm_config:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                api_key=llm_config.get("api_key"),
                model=llm_config.get("model", "gpt-4o-mini"),
                base_url=llm_config.get("base_url"),
                temperature=llm_config.get("temperature", 0.7),
            )
        return get_llm()

    def run(
        self,
        outline: str,
        story_id: Optional[str] = None,
        chapter_id: Optional[str] = None,
    ) -> GraphState:
        memory = StoryMemory(story_id=story_id or "demo-story", bible=StoryBible())
        initial_state = build_initial_state(
            input_text=outline,
            story_memory=memory,
            chapter_id=chapter_id,
        )
        return self._flow.invoke(initial_state)
