from typing import Any, Dict, Optional

from langgraph.graph import END, StateGraph

from app.agents.conflict_agent import ConflictAgent
from app.agents.editor_agent import EditorAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.reader_agent import ReaderAgent
from app.agents.summary_agent import SummaryAgent
from app.agents.writing_agent import WritingAgent
from app.domain.pipeline_state import GraphState
from app.memory.story_memory import ChapterSummary
from app.memory.agent_skill_manager import skill_manager
from app.services.chapter_service import save_memory


def _get_story_id(state: GraphState) -> Optional[str]:
    """从state中获取story_id"""
    memory = state.get("story_memory")
    if memory:
        return memory.story_id
    return None


def _build_agent_input(state: GraphState, agent_type: str, base_input: str) -> str:
    """构建Agent输入，注入资产技能约束"""
    story_id = _get_story_id(state)
    if not story_id:
        return base_input

    # 获取该Agent类型的技能约束
    skill_prompt = skill_manager.build_agent_prompt(story_id, agent_type)

    if skill_prompt:
        return f"{base_input}\n\n{skill_prompt}"
    return base_input


def planner_node(state: GraphState) -> Dict[str, Any]:
    agent = PlannerAgent()
    input_text = _build_agent_input(state, "planner", state.get("input_text", ""))
    result = agent.run({"text": input_text})
    return {
        "plan_text": result["plan_text"],
        "agent_logs": state.get("agent_logs", []) + [result],
    }


def conflict_node(state: GraphState) -> Dict[str, Any]:
    agent = ConflictAgent()
    input_text = _build_agent_input(state, "conflict", state.get("plan_text", ""))
    result = agent.run({"draft_text": input_text})
    return {
        "conflict_suggestions": result["conflict_suggestions"],
        "agent_logs": state.get("agent_logs", []) + [result],
    }


def writing_node(state: GraphState) -> Dict[str, Any]:
    agent = WritingAgent()
    base_input = f"{state.get('plan_text', '')}\n\n[Conflict Suggestions]\n" + "\n".join(
        state.get("conflict_suggestions", [])
    )
    input_text = _build_agent_input(state, "writer", base_input)
    result = agent.run({"text": input_text})
    return {
        "draft_text": result["draft_text"],
        "trace_data": result.get("trace_data", []),
        "agent_logs": state.get("agent_logs", []) + [result],
    }


def editor_node(state: GraphState) -> Dict[str, Any]:
    agent = EditorAgent()
    base_input = state.get("draft_text", "")
    input_text = _build_agent_input(state, "editor", base_input)
    result = agent.run(
        {
            "draft_text": input_text,
            "trace_data": state.get("trace_data", []),
        }
    )
    return {
        "edited_text": result["edited_text"],
        "trace_data": result.get("trace_data", []),
        "agent_logs": state.get("agent_logs", []) + [result],
    }


def reader_node(state: GraphState) -> Dict[str, Any]:
    agent = ReaderAgent()
    base_input = state.get("edited_text", "")
    input_text = _build_agent_input(state, "reader", base_input)
    result = agent.run({"draft_text": input_text})
    return {
        "reader_feedback": result["reader_feedback"],
        "agent_logs": state.get("agent_logs", []) + [result],
    }


def summary_node(state: GraphState) -> Dict[str, Any]:
    agent = SummaryAgent()
    base_input = state.get("edited_text", "")
    input_text = _build_agent_input(state, "summary", base_input)
    summary_result = agent.run(input_text)

    memory = state.get("story_memory")
    if memory:
        new_summary = ChapterSummary(
            chapter_id="new-chapter",
            title="Chapter Summary",
            summary=summary_result,
        )
        memory.chapter_summaries.append(new_summary)
        save_memory(memory)

    return {
        "summary_text": summary_result,
        "final_text": state.get("edited_text", ""),
        "story_memory": memory,
        "agent_logs": state.get("agent_logs", [])
        + [
            {
                "agent": "summary-agent",
                "message": "已完成章节总结并存入 Memory",
                "summary": summary_result,
            }
        ],
    }


def build_full_flow():
    workflow = StateGraph(GraphState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("conflict", conflict_node)
    workflow.add_node("writing", writing_node)
    workflow.add_node("editor", editor_node)
    workflow.add_node("reader", reader_node)
    workflow.add_node("summary", summary_node)

    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "conflict")
    workflow.add_edge("conflict", "writing")
    workflow.add_edge("writing", "editor")
    workflow.add_edge("editor", "reader")
    workflow.add_edge("reader", "summary")
    workflow.add_edge("summary", END)

    return workflow.compile()
