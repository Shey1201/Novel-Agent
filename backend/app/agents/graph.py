from typing import Any, Dict

from langgraph.graph import END, StateGraph

from app.agents.conflict_agent import ConflictAgent
from app.agents.editor_agent import EditorAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.reader_agent import ReaderAgent
from app.agents.summary_agent import SummaryAgent
from app.agents.writing_agent import WritingAgent
from app.domain.pipeline_state import GraphState
from app.memory.story_memory import ChapterSummary
from app.services.chapter_service import save_memory


def planner_node(state: GraphState) -> Dict[str, Any]:
    agent = PlannerAgent()
    result = agent.run({"text": state.get("input_text", "")})
    return {
        "plan_text": result["plan_text"],
        "agent_logs": state.get("agent_logs", []) + [result],
    }


def conflict_node(state: GraphState) -> Dict[str, Any]:
    agent = ConflictAgent()
    result = agent.run({"draft_text": state.get("plan_text", "")})
    return {
        "conflict_suggestions": result["conflict_suggestions"],
        "agent_logs": state.get("agent_logs", []) + [result],
    }


def writing_node(state: GraphState) -> Dict[str, Any]:
    agent = WritingAgent()
    input_text = f"{state.get('plan_text', '')}\n\n[Conflict Suggestions]\n" + "\n".join(
        state.get("conflict_suggestions", [])
    )
    result = agent.run({"text": input_text})
    return {
        "draft_text": result["draft_text"],
        "trace_data": result.get("trace_data", []),
        "agent_logs": state.get("agent_logs", []) + [result],
    }


def editor_node(state: GraphState) -> Dict[str, Any]:
    agent = EditorAgent()
    result = agent.run(
        {
            "draft_text": state.get("draft_text", ""),
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
    result = agent.run({"draft_text": state.get("edited_text", "")})
    return {
        "reader_feedback": result["reader_feedback"],
        "agent_logs": state.get("agent_logs", []) + [result],
    }


def summary_node(state: GraphState) -> Dict[str, Any]:
    agent = SummaryAgent()
    final_text = state.get("edited_text", "")
    summary_result = agent.run(final_text)

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
        "final_text": final_text,
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
