"""
Novel Agent Studio v3 - Enhanced LangGraph Workflow
Supports Human-in-the-loop, Reflexion, and Quality Gates
"""

from typing import Any, Dict, Literal, Optional, TypedDict
from enum import Enum

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from app.agents.planner_agent import PlannerAgent
from app.agents.conflict_agent import ConflictAgent
from app.agents.writing_agent import WritingAgent
from app.agents.editor_agent import EditorAgent
from app.agents.reader_agent import ReaderAgent
from app.agents.summary_agent import SummaryAgent
from app.agents.critic_agent import CriticAgent
from app.agents.consistency_agent import ConsistencyAgent
from app.memory.story_memory import ChapterSummary
from app.services.chapter_service import save_memory


class WorkflowStatus(str, Enum):
    """工作流状态"""
    PENDING = "pending"
    PLANNING = "planning"
    HUMAN_REVIEW = "human_review"
    CONFLICT_ANALYSIS = "conflict_analysis"
    WRITING = "writing"
    EDITING = "editing"
    READING = "reading"
    CRITIC_EVAL = "critic_eval"
    REWRITING = "rewriting"
    SUMMARIZING = "summarizing"
    COMPLETED = "completed"
    FAILED = "failed"


class QualityGate(str, Enum):
    """质量检查点结果"""
    PASS = "pass"
    FAIL = "fail"
    NEEDS_IMPROVEMENT = "needs_improvement"


class GraphStateV3(TypedDict):
    """v3 工作流状态"""
    # 输入
    input_text: str
    novel_id: str
    chapter_id: str
    
    # 中间结果
    plan_text: str
    conflict_analysis: Dict[str, Any]
    draft_text: str
    edited_text: str
    reader_feedback: str
    critic_result: Dict[str, Any]
    rewrite_count: int
    
    # 质量评估
    quality_score: float
    logic_consistency: float
    plot_tension: float
    prose_quality: float
    
    # 人类干预
    human_approved: Optional[bool]
    human_feedback: Optional[str]
    
    # 追踪数据
    trace_data: list
    agent_logs: list
    
    # 记忆
    story_memory: Any
    
    # 状态
    status: WorkflowStatus
    current_agent: str
    
    # 错误处理
    error_message: Optional[str]


def _build_agent_input(state: GraphStateV3, agent_type: str, base_input: str) -> str:
    """构建Agent输入，注入上下文"""
    from app.memory.agent_skill_manager import skill_manager
    
    story_id = state.get("novel_id")
    if not story_id:
        return base_input
    
    # 获取技能约束
    skill_prompt = skill_manager.build_agent_prompt(story_id, agent_type)
    
    # 获取相关记忆（RAG）
    memory_context = _get_relevant_memory(state, agent_type)
    
    parts = [base_input]
    if memory_context:
        parts.append(f"\n\n[相关记忆]\n{memory_context}")
    if skill_prompt:
        parts.append(f"\n\n[技能约束]\n{skill_prompt}")
    
    return "\n".join(parts)


def _get_relevant_memory(state: GraphStateV3, agent_type: str) -> str:
    """获取相关记忆（简化版，后续接入完整RAG）"""
    memory = state.get("story_memory")
    if not memory or not memory.chapter_summaries:
        return ""
    
    # 获取最近3章摘要
    recent_summaries = memory.chapter_summaries[-3:]
    summaries_text = "\n".join([
        f"第{i+1}章: {s.summary}"
        for i, s in enumerate(recent_summaries)
    ])
    
    return f"近期剧情摘要:\n{summaries_text}"


# ==================== Agent Nodes ====================

def planner_node(state: GraphStateV3) -> Dict[str, Any]:
    """规划节点"""
    agent = PlannerAgent()
    input_text = _build_agent_input(state, "planner", state["input_text"])
    
    result = agent.run({"text": input_text})
    
    return {
        "plan_text": result["plan_text"],
        "status": WorkflowStatus.HUMAN_REVIEW,
        "current_agent": "planner",
        "agent_logs": state.get("agent_logs", []) + [{
            "agent": "planner",
            "output": result["plan_text"],
            "timestamp": "now"
        }]
    }


def human_review_node(state: GraphStateV3) -> Dict[str, Any]:
    """
    人工审核节点 - Human-in-the-loop
    这是一个中断节点，等待人类输入
    """
    # 检查是否有人类反馈
    if state.get("human_approved") is None:
        # 等待人类输入
        return {
            "status": WorkflowStatus.HUMAN_REVIEW,
            "current_agent": "human",
        }
    
    if state["human_approved"]:
        return {
            "status": WorkflowStatus.CONFLICT_ANALYSIS,
            "current_agent": "conflict",
        }
    else:
        # 人类拒绝，重新规划
        return {
            "status": WorkflowStatus.PLANNING,
            "current_agent": "planner",
            "human_approved": None,  # 重置
            "input_text": f"{state['input_text']}\n\n[人类反馈]\n{state.get('human_feedback', '请重新规划')}",
        }


def conflict_node(state: GraphStateV3) -> Dict[str, Any]:
    """冲突分析节点"""
    agent = ConflictAgent()
    input_text = _build_agent_input(state, "conflict", state["plan_text"])
    
    result = agent.run({"draft_text": input_text})
    
    return {
        "conflict_analysis": {
            "suggestions": result.get("conflict_suggestions", []),
            "tension_score": result.get("tension_score", 0.5),
        },
        "status": WorkflowStatus.WRITING,
        "current_agent": "conflict",
        "agent_logs": state.get("agent_logs", []) + [{
            "agent": "conflict",
            "output": result.get("conflict_suggestions", []),
            "tension_score": result.get("tension_score", 0.5),
        }]
    }


def writing_node(state: GraphStateV3) -> Dict[str, Any]:
    """写作节点"""
    agent = WritingAgent()
    
    base_input = f"[大纲]\n{state['plan_text']}\n\n"
    if state.get("conflict_analysis"):
        base_input += f"[冲突建议]\n{state['conflict_analysis'].get('suggestions', [])}\n\n"
    
    # 如果是重写，添加反馈
    if state.get("rewrite_count", 0) > 0 and state.get("critic_result"):
        base_input += f"[修改建议]\n{state['critic_result'].get('feedback', '')}\n\n"
    
    input_text = _build_agent_input(state, "writer", base_input)
    result = agent.run({"text": input_text})
    
    return {
        "draft_text": result["draft_text"],
        "trace_data": result.get("trace_data", []),
        "status": WorkflowStatus.EDITING,
        "current_agent": "writing",
        "agent_logs": state.get("agent_logs", []) + [{
            "agent": "writing",
            "output_length": len(result["draft_text"]),
            "trace_count": len(result.get("trace_data", [])),
        }]
    }


def editor_node(state: GraphStateV3) -> Dict[str, Any]:
    """编辑节点"""
    agent = EditorAgent()
    input_text = _build_agent_input(state, "editor", state["draft_text"])
    
    result = agent.run({
        "draft_text": input_text,
        "trace_data": state.get("trace_data", []),
    })
    
    return {
        "edited_text": result["edited_text"],
        "trace_data": result.get("trace_data", state.get("trace_data", [])),
        "status": WorkflowStatus.READING,
        "current_agent": "editor",
        "agent_logs": state.get("agent_logs", []) + [{
            "agent": "editor",
            "changes_made": result.get("changes_made", []),
        }]
    }


def reader_node(state: GraphStateV3) -> Dict[str, Any]:
    """读者节点 - 逻辑检查"""
    agent = ReaderAgent()
    input_text = _build_agent_input(state, "reader", state["edited_text"])
    
    result = agent.run({"draft_text": input_text})
    
    # 检查是否有严重逻辑错误
    has_critical_error = result.get("has_critical_error", False)
    
    if has_critical_error:
        return {
            "reader_feedback": result["reader_feedback"],
            "status": WorkflowStatus.REWRITING,
            "current_agent": "reader",
            "rewrite_count": state.get("rewrite_count", 0) + 1,
            "agent_logs": state.get("agent_logs", []) + [{
                "agent": "reader",
                "issue": "critical_error",
                "feedback": result["reader_feedback"],
            }]
        }
    
    return {
        "reader_feedback": result["reader_feedback"],
        "status": WorkflowStatus.CRITIC_EVAL,
        "current_agent": "reader",
        "agent_logs": state.get("agent_logs", []) + [{
            "agent": "reader",
            "issue": "none",
        }]
    }


def critic_node(state: GraphStateV3) -> Dict[str, Any]:
    """评论家节点 - 质量评估"""
    agent = CriticAgent()
    
    result = agent.evaluate(
        chapter=state["edited_text"],
        context={
            "plan": state.get("plan_text"),
            "reader_feedback": state.get("reader_feedback"),
        }
    )
    
    quality_score = result["total_score"]
    
    # 质量检查
    if quality_score < 0.6 and state.get("rewrite_count", 0) < 2:
        # 质量不合格，需要重写
        return {
            "critic_result": result,
            "quality_score": quality_score,
            "logic_consistency": result["breakdown"]["logic_consistency"],
            "plot_tension": result["breakdown"]["plot_tension"],
            "prose_quality": result["breakdown"]["prose_quality"],
            "status": WorkflowStatus.REWRITING,
            "current_agent": "critic",
            "rewrite_count": state.get("rewrite_count", 0) + 1,
            "agent_logs": state.get("agent_logs", []) + [{
                "agent": "critic",
                "score": quality_score,
                "decision": "rewrite",
            }]
        }
    
    return {
        "critic_result": result,
        "quality_score": quality_score,
        "logic_consistency": result["breakdown"]["logic_consistency"],
        "plot_tension": result["breakdown"]["plot_tension"],
        "prose_quality": result["breakdown"]["prose_quality"],
        "status": WorkflowStatus.SUMMARIZING,
        "current_agent": "critic",
        "agent_logs": state.get("agent_logs", []) + [{
            "agent": "critic",
            "score": quality_score,
            "decision": "pass",
        }]
    }


def rewrite_node(state: GraphStateV3) -> Dict[str, Any]:
    """重写节点 - Reflexion"""
    # 准备重写指令
    feedback_parts = []
    
    if state.get("reader_feedback"):
        feedback_parts.append(f"读者反馈: {state['reader_feedback']}")
    
    if state.get("critic_result"):
        feedback_parts.append(f"质量评估: {state['critic_result'].get('feedback', '')}")
    
    rewrite_instruction = "\n".join(feedback_parts)
    
    return {
        "status": WorkflowStatus.WRITING,
        "current_agent": "rewrite",
        "input_text": f"{state['input_text']}\n\n[重写指令]\n{rewrite_instruction}",
        "agent_logs": state.get("agent_logs", []) + [{
            "agent": "rewrite",
            "reason": "quality_check_failed",
            "rewrite_count": state.get("rewrite_count", 0),
        }]
    }


def summary_node(state: GraphStateV3) -> Dict[str, Any]:
    """总结节点"""
    agent = SummaryAgent()
    input_text = state["edited_text"]
    
    summary_result = agent.run(input_text)
    
    # 保存到记忆
    memory = state.get("story_memory")
    if memory:
        new_summary = ChapterSummary(
            chapter_id=state.get("chapter_id", "new-chapter"),
            title="Chapter Summary",
            summary=summary_result,
        )
        memory.chapter_summaries.append(new_summary)
        save_memory(memory)
    
    return {
        "summary_text": summary_result,
        "final_text": state["edited_text"],
        "status": WorkflowStatus.COMPLETED,
        "current_agent": "summary",
        "agent_logs": state.get("agent_logs", []) + [{
            "agent": "summary",
            "summary_length": len(summary_result),
        }]
    }


# ==================== Conditional Edges ====================

def route_after_human_review(state: GraphStateV3) -> Literal["conflict", "planner"]:
    """人工审核后路由"""
    if state.get("human_approved"):
        return "conflict"
    return "planner"


def route_after_reader(state: GraphStateV3) -> Literal["critic", "rewrite"]:
    """读者检查后路由"""
    # 如果有严重错误或者重写次数未超限
    if state.get("rewrite_count", 0) < 2:
        # 这里简化处理，实际应该检查reader的结果
        return "critic"
    return "critic"


def route_after_critic(state: GraphStateV3) -> Literal["summary", "rewrite"]:
    """质量评估后路由"""
    if state.get("quality_score", 0) < 0.6 and state.get("rewrite_count", 0) < 2:
        return "rewrite"
    return "summary"


# ==================== Build Workflow ====================

def build_v3_workflow():
    """构建 v3 工作流"""
    workflow = StateGraph(GraphStateV3)
    
    # 添加节点
    workflow.add_node("planner", planner_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("conflict", conflict_node)
    workflow.add_node("writing", writing_node)
    workflow.add_node("editor", editor_node)
    workflow.add_node("reader", reader_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("rewrite", rewrite_node)
    workflow.add_node("summary", summary_node)
    
    # 设置入口
    workflow.set_entry_point("planner")
    
    # 添加边
    workflow.add_edge("planner", "human_review")
    
    # 条件边：人工审核
    workflow.add_conditional_edges(
        "human_review",
        route_after_human_review,
        {
            "conflict": "conflict",
            "planner": "planner"
        }
    )
    
    workflow.add_edge("conflict", "writing")
    workflow.add_edge("writing", "editor")
    workflow.add_edge("editor", "reader")
    
    # 条件边：读者检查
    workflow.add_conditional_edges(
        "reader",
        route_after_reader,
        {
            "critic": "critic",
            "rewrite": "rewrite"
        }
    )
    
    # 条件边：质量评估
    workflow.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "summary": "summary",
            "rewrite": "rewrite"
        }
    )
    
    workflow.add_edge("rewrite", "writing")
    workflow.add_edge("summary", END)
    
    # 添加检查点（支持中断恢复）
    checkpointer = MemorySaver()
    
    return workflow.compile(checkpointer=checkpointer)


# 全局工作流实例
v3_workflow = build_v3_workflow()
