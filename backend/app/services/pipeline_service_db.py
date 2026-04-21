"""
基于数据库 Agent 配置的章节生成流水线

- 从 agents 表读取配置（含 facilitator 与 8 个执行 Agent）
- facilitator 作为协调角色，不参与内容生成；按需调用其余启用的 Agent
- 每个 Agent 调用时注入：agent 配置中的 prompt + skill_memory 的 skills 约束
- 使用各 Agent 的 temperature 配置，并记录各步耗时
"""
import logging
logging.basicConfig(level=logging.WARNING)

from typing import Any, Dict, List, Optional
import time

from app.domain.pipeline_state import build_initial_state, GraphState
from app.memory.story_memory import StoryBible, StoryMemory

# 先创建 memory 实例
from app.memory.agent_memory import AgentMemory
from app.memory.skill_memory import SkillMemory

agent_memory = AgentMemory()
skill_memory = SkillMemory()

# 导入 LLM 模块
from app.core.llm import get_llm
from app.core.ai_config import get_llm_with_fallback

# agent_id -> 默认执行顺序（facilitator 不参与执行）
DEFAULT_EXECUTION_ORDER = [
    "planner",
    "conflict",
    "writer",
    "editor",
    "reader",
    "critic",
    "consistency",
    "summary",
]
FACILITATOR_ID = "facilitator"


def _build_constraints_prefix(story_id: str, agent_id: str) -> str:
    """与 AgentChatService 一致：Agent 配置 prompt + 挂载 skills 约束"""
    parts: List[str] = []
    cfg = agent_memory.get_config(agent_id)
    if cfg and cfg.prompt:
        parts.append(cfg.prompt.strip())
    try:
        sp = skill_memory.build_agent_prompt(story_id, agent_id)
        if sp:
            parts.append(sp.strip())
    except Exception:
        pass
    if not parts:
        return ""
    return "\n\n".join(parts).strip() + "\n\n"


def _get_llm_for_agent(agent_id: str, base_llm: Any) -> Any:
    """按 Agent 配置的 temperature 返回 LLM（无配置则用 base_llm）"""
    # 直接返回 base_llm，跳过配置获取
    return base_llm


def run_with_db_agents(
    outline: str,
    story_id: Optional[str] = None,
    chapter_id: Optional[str] = None,
    llm_config: Optional[Dict[str, Any]] = None,
    execution_order: Optional[List[str]] = None,
) -> Dict[str, Any]:
    print("[run_with_db_agents] START", flush=True)
    """
    使用数据库中的 Agent 配置与 facilitator 协调逻辑执行流水线。

    - 只调用在 DB 中启用且存在于 execution_order 中的 Agent
    - 每个 Agent 使用 DB 的 prompt + skills 约束，并计入耗时
    """
    story_id = story_id or "demo-story"
    order = execution_order or DEFAULT_EXECUTION_ORDER

    # 初始化 LLM
    from langchain_openai import ChatOpenAI
    from app.core.llm import _get_ai_config_from_db
    
    print("[run_with_db_agents] Creating LLM...", flush=True)
    print("[run_with_db_agents] Calling _get_ai_config_from_db...", flush=True)
    config = _get_ai_config_from_db()
    print("[run_with_db_agents] Got config, creating ChatOpenAI...", flush=True)
    
    if llm_config:
        base_llm = ChatOpenAI(
            api_key=llm_config.get("api_key"),
            model=llm_config.get("model", "gpt-4o-mini"),
            base_url=llm_config.get("base_url"),
            temperature=llm_config.get("temperature", 0.7),
        )
    else:
        print("[run_with_db_agents] Checking config.is_active...", flush=True)
        if not config.get("is_active"):
            raise ValueError("AI is not active")
        
        api_key = config.get("api_key")
        chat_model = config.get("chat_model", "deepseek-chat")
        base_url = config.get("base_url")
        
        print(f"[run_with_db_agents] Creating ChatOpenAI: model={chat_model}, base_url={base_url}", flush=True)
        if "deepseek" in chat_model.lower():
            base_llm = ChatOpenAI(
                api_key=api_key,
                model=chat_model,
                base_url=base_url or "https://api.deepseek.com/v1",
                temperature=0.7,
            )
        else:
            base_llm = ChatOpenAI(
                api_key=api_key,
                model=chat_model,
                base_url=base_url,
                temperature=0.7,
            )
        print("[run_with_db_agents] ChatOpenAI created", flush=True)

    # 从 DB 取配置，排除 facilitator，只保留启用的
    print("[run_with_db_agents] Getting all configs...", flush=True)
    all_configs = agent_memory.get_all_configs()
    print(f"[run_with_db_agents] Got {len(all_configs)} configs", flush=True)
    enabled_ids = {c.agent_id for c in all_configs if c.agent_id != FACILITATOR_ID and c.enabled}
    to_run = [a for a in order if a in enabled_ids]
    print(f"[run_with_db_agents] to_run: {to_run}", flush=True)

    print("[run_with_db_agents] Creating memory...", flush=True)
    memory = StoryMemory(story_id=story_id, bible=StoryBible())
    state: Dict[str, Any] = {
        "input_text": outline,
        "plan_text": "",
        "conflict_suggestions": [],
        "draft_text": "",
        "edited_text": "",
        "reader_feedback": [],
        "summary_text": "",
        "final_text": "",
        "agent_logs": [],
        "trace_data": [],
        "story_memory": memory,
        "chapter_id": chapter_id,
    }

    # Agent 类映射（与 graph 一致）
    from app.agents.planner_agent import PlannerAgent
    from app.agents.conflict_agent import ConflictAgent
    from app.agents.writing_agent import WritingAgent
    from app.agents.editor_agent import EditorAgent
    from app.agents.reader_agent import ReaderAgent
    from app.agents.critic_agent import CriticAgent
    from app.agents.consistency_agent import ConsistencyAgent
    from app.agents.summary_agent import SummaryAgent
    from app.agents.base_agent import AgentMode

    agent_classes = {
        "planner": PlannerAgent,
        "conflict": ConflictAgent,
        "writer": WritingAgent,
        "editor": EditorAgent,
        "reader": ReaderAgent,
        "critic": CriticAgent,
        "consistency": ConsistencyAgent,
        "summary": SummaryAgent,
    }

    for agent_id in to_run:
        if agent_id not in agent_classes:
            continue
        prefix = _build_constraints_prefix(story_id, agent_id)
        llm = _get_llm_for_agent(agent_id, base_llm)
        
        # 创建 Agent 实例
        agent_class = agent_classes[agent_id]
        
        # 对于 PlannerAgent，使用简化配置
        if agent_id == "planner":
            agent = agent_class(llm=llm, mode=AgentMode.PLAN_EXECUTE)
        else:
            agent = agent_class(llm=llm)

        # 根据 agent 类型准备输入
        if agent_id == "planner":
            input_text = prefix + state["input_text"]
            t0 = time.time()
            out = agent.run({"text": input_text})
            elapsed = time.time() - t0
            state["plan_text"] = out.get("plan_text", "")
        elif agent_id == "conflict":
            input_text = prefix + (state.get("plan_text") or state["input_text"])
            t0 = time.time()
            out = agent.run({"draft_text": input_text})
            elapsed = time.time() - t0
            state["conflict_suggestions"] = out.get("conflict_suggestions", [])
        elif agent_id == "writer":
            base = (state.get("plan_text") or "") + "\n\n" + "\n".join(state.get("conflict_suggestions", []))
            input_text = prefix + base
            t0 = time.time()
            out = agent.run({"text": input_text})
            elapsed = time.time() - t0
            state["draft_text"] = out.get("draft_text", "")
        elif agent_id == "editor":
            input_text = prefix + state.get("draft_text", "")
            t0 = time.time()
            out = agent.run({"draft_text": input_text, "trace_data": state.get("trace_data", [])})
            elapsed = time.time() - t0
            state["edited_text"] = out.get("edited_text", state.get("draft_text", ""))
        elif agent_id == "reader":
            input_text = prefix + state.get("edited_text", state.get("draft_text", ""))
            t0 = time.time()
            out = agent.run({"draft_text": input_text})
            elapsed = time.time() - t0
            state["reader_feedback"] = out.get("reader_feedback", [])
        elif agent_id == "critic":
            input_text = prefix + state.get("edited_text", state.get("draft_text", ""))
            t0 = time.time()
            agent.run({"text": input_text})
            elapsed = time.time() - t0
        elif agent_id == "consistency":
            input_text = prefix + state.get("edited_text", state.get("draft_text", ""))
            t0 = time.time()
            agent.run({"text": input_text})
            elapsed = time.time() - t0
        elif agent_id == "summary":
            chapter_text = state.get("edited_text") or state.get("draft_text", "")
            # 总结仅针对章节正文，避免把约束当内容
            t0 = time.time()
            state["summary_text"] = agent.run(chapter_text)
            elapsed = time.time() - t0
            state["final_text"] = state.get("edited_text") or state.get("draft_text", "")
        else:
            elapsed = 0

        state["agent_logs"].append({
            "agent": agent_id,
            "message": getattr(agent, "name", agent_id),
            "elapsed_seconds": round(elapsed, 2),
        })

    return state
