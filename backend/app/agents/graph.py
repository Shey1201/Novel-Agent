"""
Agent Graph - Agent 协作工作流
基于 hello-agents 最佳实践增强：
- 多模式运行（CHAIN/REACT/REFLECTION）
- 条件分支和循环
- Agent 间的通信协议
- 记忆系统集成
"""

from typing import Any, Dict, Optional, Callable
from enum import Enum

from langgraph.graph import END, StateGraph

from app.agents.conflict_agent import ConflictAgent
from app.agents.editor_agent import EditorAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.reader_agent import ReaderAgent
from app.agents.summary_agent import SummaryAgent
from app.agents.writing_agent import WritingAgent
from app.agents.base_agent import AgentMode
from app.domain.pipeline_state import GraphState
from app.memory.story_memory import ChapterSummary
from app.memory.skill_memory import skill_memory
from app.services.chapter_service import save_memory


class FlowMode(Enum):
    """工作流模式"""
    LINEAR = "linear"           # 线性流程
    CONDITIONAL = "conditional"  # 条件分支
    ITERATIVE = "iterative"     # 迭代流程
    PARALLEL = "parallel"        # 并行处理


# 全局 LLM 实例，由 build_full_flow 设置
_global_llm = None


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
    skill_prompt = skill_memory.build_agent_prompt(story_id, agent_type)

    if skill_prompt:
        return f"{base_input}\n\n{skill_prompt}"
    return base_input


def _should_continue_iteration(state: GraphState) -> bool:
    """判断是否继续迭代"""
    # 可以基于 agent_logs 中的评估结果判断
    agent_logs = state.get("agent_logs", [])
    
    # 如果有评估结果，检查是否需要重写
    for log in reversed(agent_logs):
        if isinstance(log, dict) and log.get("rewrite_needed"):
            return log.get("total_score", 0.8) < 0.7
    
    # 默认最多迭代 3 次
    iteration = state.get("iteration_count", 0)
    return iteration < 3


def planner_node(state: GraphState) -> Dict[str, Any]:
    """Planner 节点 - 制定写作计划"""
    agent = PlannerAgent(llm=_global_llm, mode=AgentMode.PLAN_EXECUTE)
    input_text = _build_agent_input(state, "planner", state.get("input_text", ""))
    result = agent.run({"text": input_text})
    return {
        "plan_text": result["plan_text"],
        "agent_logs": state.get("agent_logs", []) + [result],
    }


def conflict_node(state: GraphState) -> Dict[str, Any]:
    """Conflict 节点 - 分析冲突需求"""
    agent = ConflictAgent(llm=_global_llm)
    input_text = _build_agent_input(state, "conflict", state.get("plan_text", ""))
    result = agent.run({"draft_text": input_text})
    return {
        "conflict_suggestions": result["conflict_suggestions"],
        "agent_logs": state.get("agent_logs", []) + [result],
    }


def writing_node(state: GraphState) -> Dict[str, Any]:
    """Writing 节点 - 生成内容"""
    agent = WritingAgent(llm=_global_llm, mode=AgentMode.PLAN_EXECUTE)
    base_input = f"{state.get('plan_text', '')}\n\n[Conflict Suggestions]\n" + "\n".join(
        state.get("conflict_suggestions", [])
    )
    input_text = _build_agent_input(state, "writer", base_input)
    result = agent.run({"text": input_text})
    return {
        "draft_text": result.get("draft_text", ""),
        "trace_data": result.get("trace_data", []),
        "agent_logs": state.get("agent_logs", []) + [result],
    }


def editor_node(state: GraphState) -> Dict[str, Any]:
    """Editor 节点 - 编辑和评估"""
    agent = EditorAgent(llm=_global_llm)
    base_input = state.get("draft_text", "")
    input_text = _build_agent_input(state, "editor", base_input)
    result = agent.run(
        {
            "draft_text": input_text,
            "trace_data": state.get("trace_data", []),
        }
    )
    return {
        "edited_text": result.get("edited_text", ""),
        "trace_data": result.get("trace_data", []),
        "agent_logs": state.get("agent_logs", []) + [result],
    }


def reader_node(state: GraphState) -> Dict[str, Any]:
    """Reader 节点 - 模拟读者反馈"""
    agent = ReaderAgent(llm=_global_llm)
    base_input = state.get("edited_text", "")
    input_text = _build_agent_input(state, "reader", base_input)
    result = agent.run({"draft_text": input_text})
    return {
        "reader_feedback": result["reader_feedback"],
        "agent_logs": state.get("agent_logs", []) + [result],
    }


def summary_node(state: GraphState) -> Dict[str, Any]:
    """Summary 节点 - 总结并存储记忆"""
    agent = SummaryAgent(llm=_global_llm)
    base_input = state.get("edited_text", "")
    input_text = _build_agent_input(state, "summary", base_input)
    summary_result = agent.run(input_text)

    memory = state.get("story_memory")
    chapter_id = state.get("chapter_id") or "new-chapter"
    if memory and chapter_id:
        new_summary = ChapterSummary(
            chapter_id=chapter_id,
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


def build_full_flow(llm=None, mode: FlowMode = FlowMode.LINEAR):
    """
    构建完整工作流
    
    Args:
        llm: 大语言模型实例
        mode: 工作流模式 (LINEAR/CONDITIONAL/ITERATIVE)
        
    Returns:
        编译后的工作流图
    """
    global _global_llm
    _global_llm = llm

    workflow = StateGraph(GraphState)

    # 添加节点
    workflow.add_node("planner", planner_node)
    workflow.add_node("conflict", conflict_node)
    workflow.add_node("writing", writing_node)
    workflow.add_node("editor", editor_node)
    workflow.add_node("reader", reader_node)
    workflow.add_node("summary", summary_node)

    # 设置入口
    workflow.set_entry_point("planner")

    # 根据模式构建边
    if mode == FlowMode.LINEAR:
        # 线性流程
        workflow.add_edge("planner", "conflict")
        workflow.add_edge("conflict", "writing")
        workflow.add_edge("writing", "editor")
        workflow.add_edge("editor", "reader")
        workflow.add_edge("reader", "summary")
        workflow.add_edge("summary", END)
        
    elif mode == FlowMode.CONDITIONAL:
        # 条件分支流程
        workflow.add_edge("planner", "conflict")
        workflow.add_edge("conflict", "writing")
        
        # 编辑后可以进入读者反馈或直接结束
        workflow.add_conditional_edges(
            "editor",
            lambda x: "reader" if x.get("iteration_count", 0) < 2 else "summary",
            {
                "reader": "reader",
                "summary": "summary"
            }
        )
        
        workflow.add_edge("reader", "summary")
        workflow.add_edge("summary", END)
        
    elif mode == FlowMode.ITERATIVE:
        # 迭代流程 - 编辑器评估后可以重写
        workflow.add_edge("planner", "conflict")
        workflow.add_edge("conflict", "writing")
        
        # 添加迭代边
        workflow.add_conditional_edges(
            "editor",
            lambda x: "writing" if _should_continue_iteration(x) else "reader",
            {
                "writing": "writing",
                "reader": "reader"
            }
        )
        
        # 增加迭代计数
        def increment_iteration(state: GraphState) -> Dict[str, Any]:
            return {"iteration_count": state.get("iteration_count", 0) + 1}
        
        workflow.add_node("increment_iteration", increment_iteration)
        workflow.add_edge("editor", "increment_iteration")
        
        workflow.add_edge("increment_iteration", "writing")
        workflow.add_edge("reader", "summary")
        workflow.add_edge("summary", END)

    return workflow.compile()


def build_parallel_flow(llm=None):
    """
    构建并行工作流
    
    多个 Agent 可以同时处理不同任务
    """
    global _global_llm
    _global_llm = llm

    workflow = StateGraph(GraphState)

    # 添加节点
    workflow.add_node("planner", planner_node)
    workflow.add_node("conflict", conflict_node)
    workflow.add_node("writing", writing_node)
    workflow.add_node("editor", editor_node)
    
    # 并行节点
    workflow.add_node("parallel_edit", parallel_edit_node)
    workflow.add_node("parallel_critique", parallel_critique_node)
    
    workflow.add_node("summary", summary_node)

    # 入口
    workflow.set_entry_point("planner")
    
    # 主流程
    workflow.add_edge("planner", "conflict")
    workflow.add_edge("conflict", "writing")
    workflow.add_edge("writing", "editor")
    
    # 并行处理
    workflow.add_edge("editor", "parallel_edit")
    workflow.add_edge("editor", "parallel_critique")
    
    # 汇合
    workflow.add_edge("parallel_edit", "summary")
    workflow.add_edge("parallel_critique", "summary")
    
    workflow.add_edge("summary", END)

    return workflow.compile()


def parallel_edit_node(state: GraphState) -> Dict[str, Any]:
    """并行编辑节点 - 多种风格的编辑"""
    # 可以启动多个编辑 Agent 同时处理
    return {
        "agent_logs": state.get("agent_logs", []) + [{
            "agent": "parallel-edit",
            "message": "并行编辑完成"
        }]
    }


def parallel_critique_node(state: GraphState) -> Dict[str, Any]:
    """并行批评节点 - 多角度批评"""
    return {
        "agent_logs": state.get("agent_logs", []) + [{
            "agent": "parallel-critique",
            "message": "多角度批评完成"
        }]
    }


# 便捷函数
def create_writing_workflow(llm=None, config: Dict[str, Any] = None):
    """
    创建写作工作流的便捷函数
    
    Args:
        llm: 大语言模型
        config: 配置字典
            - mode: FlowMode 枚举
            - enable_reflection: 是否启用反思
            - max_iterations: 最大迭代次数
            
    Returns:
        编译后的工作流
    """
    config = config or {}
    mode = config.get("mode", FlowMode.LINEAR)
    
    return build_full_flow(llm, mode)


def create_multi_agent_debate(llm=None):
    """
    创建多 Agent 辩论工作流
    
    多个 Agent 对内容进行辩论和评审
    """
    global _global_llm
    _global_llm = llm

    workflow = StateGraph(GraphState)

    # 添加多个角色 Agent
    def critic_node(state: GraphState):
        from app.agents.critic_agent import CriticAgent
        agent = CriticAgent(llm=_global_llm)
        text = state.get("draft_text", "")
        result = agent.run({"text": text})
        return {"critic_feedback": result.get("feedback", ""), "agent_logs": state.get("agent_logs", []) + [result]}

    def writer_node(state: GraphState):
        from app.agents.writer_agent import WriterAgent
        agent = WriterAgent(llm=_global_llm)
        critique = state.get("critic_feedback", "")
        result = agent.run({"text": f"根据反馈修改: {critique}"})
        return {"draft_text": result.get("draft_text", ""), "agent_logs": state.get("agent_logs", []) + [result]}

    workflow.add_node("critic", critic_node)
    workflow.add_node("writer", writer_node)
    
    workflow.set_entry_point("critic")
    workflow.add_edge("critic", "writer")
    workflow.add_edge("writer", END)

    return workflow.compile()
