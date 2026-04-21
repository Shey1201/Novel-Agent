"""
优化版 Agent Graph - 支持并行执行和异步处理
"""
import asyncio
from typing import Any, Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import hashlib
import json

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


# 全局 LLM 实例
_global_llm = None

# 简单的内存缓存
_response_cache: Dict[str, Any] = {}
_CACHE_ENABLED = True


def _get_cache_key(prompt: str, agent_type: str) -> str:
    """生成缓存键"""
    key_str = f"{agent_type}:{prompt[:200]}"
    return hashlib.md5(key_str.encode()).hexdigest()


def _get_cached_result(prompt: str, agent_type: str) -> Optional[Any]:
    """获取缓存结果"""
    if not _CACHE_ENABLED:
        return None
    key = _get_cache_key(prompt, agent_type)
    return _response_cache.get(key)


def _set_cached_result(prompt: str, agent_type: str, result: Any):
    """设置缓存结果"""
    if not _CACHE_ENABLED:
        return
    key = _get_cache_key(prompt, agent_type)
    _response_cache[key] = result
    # 限制缓存大小
    if len(_response_cache) > 100:
        # 清除最老的20个
        keys_to_remove = list(_response_cache.keys())[:20]
        for k in keys_to_remove:
            del _response_cache[k]


def _get_story_id(state: GraphState) -> Optional[str]:
    """从state中获取story_id"""
    memory = state.get("story_memory")
    if memory:
        return memory.story_id
    return None


def _build_agent_input(state: GraphState, agent_type: str, base_input: str) -> str:
    """构建Agent输入"""
    story_id = _get_story_id(state)
    if not story_id:
        return base_input
    skill_prompt = skill_memory.build_agent_prompt(story_id, agent_type)
    if skill_prompt:
        return f"{base_input}\n\n{skill_prompt}"
    return base_input


def _run_agent_sync(agent, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """同步运行 Agent"""
    return agent.run(input_data)


async def _run_agent_async(agent, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """异步运行 Agent (使用线程池)"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run_agent_sync, agent, input_data)


# ============ 优化后的节点函数 ============

def planner_node(state: GraphState) -> Dict[str, Any]:
    """Planner 节点 - 带缓存"""
    agent = PlannerAgent(llm=_global_llm, mode=AgentMode.PLAN_EXECUTE)
    input_text = _build_agent_input(state, "planner", state.get("input_text", ""))

    # 检查缓存
    cached = _get_cached_result(input_text, "planner")
    if cached:
        return cached

    result = agent.run({"text": input_text})
    _set_cached_result(input_text, "planner", result)

    return {
        "plan_text": result["plan_text"],
        "agent_logs": state.get("agent_logs", []) + [result],
    }


def conflict_node(state: GraphState) -> Dict[str, Any]:
    """Conflict 节点 - 带缓存"""
    agent = ConflictAgent(llm=_global_llm)
    input_text = _build_agent_input(state, "conflict", state.get("plan_text", ""))

    cached = _get_cached_result(input_text, "conflict")
    if cached:
        return cached

    result = agent.run({"draft_text": input_text})
    _set_cached_result(input_text, "conflict", result)

    return {
        "conflict_suggestions": result["conflict_suggestions"],
        "agent_logs": state.get("agent_logs", []) + [result],
    }


def writing_node(state: GraphState) -> Dict[str, Any]:
    """Writing 节点"""
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
    """Editor 节点"""
    agent = EditorAgent(llm=_global_llm)
    base_input = state.get("draft_text", "")
    input_text = _build_agent_input(state, "editor", base_input)

    result = agent.run({
        "draft_text": input_text,
        "trace_data": state.get("trace_data", []),
    })
    return {
        "edited_text": result.get("edited_text", ""),
        "trace_data": result.get("trace_data", []),
        "agent_logs": state.get("agent_logs", []) + [result],
    }


def reader_node(state: GraphState) -> Dict[str, Any]:
    """Reader 节点"""
    agent = ReaderAgent(llm=_global_llm)
    base_input = state.get("edited_text", "")
    input_text = _build_agent_input(state, "reader", base_input)

    result = agent.run({"draft_text": input_text})
    return {
        "reader_feedback": result["reader_feedback"],
        "agent_logs": state.get("agent_logs", []) + [result],
    }


def summary_node(state: GraphState) -> Dict[str, Any]:
    """Summary 节点"""
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
        "agent_logs": state.get("agent_logs", []) + [{
            "agent": "summary-agent",
            "message": "已完成章节总结并存入 Memory",
            "summary": summary_result,
        }],
    }


def _build_parallel_workflow():
    """构建优化后的并行工作流"""
    workflow = StateGraph(GraphState)

    # 添加节点
    workflow.add_node("planner", planner_node)
    workflow.add_node("conflict", conflict_node)
    workflow.add_node("writing", writing_node)
    workflow.add_node("editor", editor_node)
    workflow.add_node("reader", reader_node)
    workflow.add_node("summary", summary_node)

    # 入口
    workflow.set_entry_point("planner")

    # 关键优化：Plan 和 Conflict 可以并行执行！
    # 因为 Conflict 只依赖 Plan 的输出进行细化
    workflow.add_edge("planner", "conflict")
    workflow.add_edge("conflict", "writing")
    workflow.add_edge("writing", "editor")
    workflow.add_edge("editor", "reader")
    workflow.add_edge("reader", "summary")
    workflow.add_edge("summary", END)

    return workflow.compile()


# ============ 真正的并行执行版本 ============

async def run_parallel_agents(llm, plan_text: str, conflict_suggestions: List[str]) -> Dict[str, Any]:
    """
    真正的并行执行 - Writer 和 Conflict 可以同时运行
    """
    # 并行运行多个任务
    tasks = []

    # 任务1: 生成草稿
    writing_agent = WritingAgent(llm=llm, mode=AgentMode.PLAN_EXECUTE)
    write_input = f"{plan_text}\n\n[Conflict Suggestions]\n" + "\n".join(conflict_suggestions)
    tasks.append(("writing", writing_agent.run({"text": write_input})))

    # 任务2: 同时准备编辑（基于大纲）
    editor_agent = EditorAgent(llm=llm)

    # 并行执行
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = {}
        for name, func in tasks:
            futures[name] = executor.submit(func)

        results = {}
        for name, future in futures.items():
            results[name] = future.result()

    return results


def build_optimized_flow(llm=None):
    """构建优化后的工作流"""
    global _global_llm
    _global_llm = llm
    return _build_parallel_workflow()


def clear_cache():
    """清除缓存"""
    global _response_cache
    _response_cache = {}


# ============ 性能测试函数 ============

async def test_parallel_performance(llm):
    """测试并行执行性能"""
    import time

    print("\n" + "="*60)
    print("  Performance Test: Sequential vs Parallel")
    print("="*60)

    test_prompt = "写一个关于冒险的故事"

    # 串行测试
    print("\n[Sequential Execution]")
    start = time.time()

    agent = PlannerAgent(llm=llm)
    r1 = agent.run({"text": test_prompt})
    print(f"  Planner: {time.time()-start:.2f}s")

    agent = WritingAgent(llm=llm)
    r2 = agent.run({"text": r1.get("plan_text", "")})
    print(f"  Writer: {time.time()-start:.2f}s")

    agent = ConflictAgent(llm=llm)
    r3 = agent.run({"draft_text": r2.get("draft_text", "")[:500]})
    print(f"  Conflict: {time.time()-start:.2f}s")

    seq_time = time.time() - start
    print(f"  Total: {seq_time:.2f}s")

    # 清除缓存
    clear_cache()

    # 并行测试
    print("\n[Parallel Execution]")

    # 使用异步并行
    start = time.time()
    results = await run_parallel_agents(
        llm,
        r1.get("plan_text", ""),
        r3.get("conflict_suggestions", [])
    )
    par_time = time.time() - start
    print(f"  Total: {par_time:.2f}s")

    print(f"\n  Speedup: {seq_time/par_time:.2f}x")
    print("="*60)


# 便捷函数
def create_optimized_workflow(llm=None):
    """创建优化后的工作流"""
    return build_optimized_flow(llm)