from typing import Any, Dict, List, TypedDict

from app.memory.story_memory import StoryMemory


class GraphState(TypedDict):
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
    story_memory: StoryMemory


def build_initial_state(input_text: str, story_memory: StoryMemory) -> GraphState:
    return {
        "input_text": input_text,
        "agent_logs": [],
        "trace_data": [],
        "plan_text": "",
        "conflict_suggestions": [],
        "draft_text": "",
        "edited_text": "",
        "reader_feedback": [],
        "summary_text": "",
        "final_text": "",
        "story_memory": story_memory,
    }
