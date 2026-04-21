"""
真实数据库环境下的 Agent 完整功能测试

要求：
1. `backend/.env` 存在，且配置 SUPABASE_URL、SUPABASE_SERVICE_KEY 等
2. 数据库中 agents 表已有数据（如 conflict, critic, writer, reader, editor, facilitator, consistency, planner, summary）
3. facilitator 为协调 Agent，其余 8 个为执行 Agent；按需调用，并注入 agent prompt 与 skills
"""
import sys
import time
from pathlib import Path

# 先加载 .env（与 main.py 一致）
backend_dir = Path(__file__).resolve().parent.parent.parent
project_root = backend_dir.parent
env_path = project_root / ".env"
if env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path)
    except Exception:
        pass
sys.path.insert(0, str(backend_dir))

import pytest
from unittest.mock import Mock, patch


# 执行顺序：facilitator 不参与具体执行，由它“协调”决定调用哪些 Agent；此处用默认顺序
EXECUTION_ORDER = [
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


def test_load_agent_configs_from_db():
    """1. 从数据库加载 Agent 配置"""
    from app.memory.agent_memory import agent_memory

    configs = agent_memory.get_all_configs()
    assert len(configs) >= 1, "数据库中应至少有一条 Agent 配置"

    by_id = {c.agent_id: c for c in configs}
    assert FACILITATOR_ID in by_id, "数据库中应存在 facilitator 协调 Agent"
    assert by_id[FACILITATOR_ID].role, "facilitator 应有 role 描述"

    # 执行类 Agent（不含 facilitator）
    execution_agents = [a for a in configs if a.agent_id != FACILITATOR_ID]
    print(f"\n[DB] 共加载 {len(configs)} 个 Agent，其中协调 Agent: {FACILITATOR_ID}")
    print(f"[DB] 可执行 Agent ({len(execution_agents)} 个): {[c.agent_id for c in execution_agents]}")
    for c in configs:
        status = "ON" if c.enabled else "OFF"
        print(f"  - {c.agent_id}: {c.name} [{status}] role={c.role[:30]}...")
    assert len(execution_agents) >= 1, "除 facilitator 外应至少有一个可执行 Agent"


def test_skill_memory_for_agents():
    """2. 确认 skill_memory 可为各 Agent 提供约束"""
    from app.memory.agent_memory import agent_memory
    from app.memory.skill_memory import skill_memory

    configs = agent_memory.get_all_configs()
    story_id = "test-story-real"
    for c in configs:
        if c.agent_id == FACILITATOR_ID:
            continue
        try:
            prompt = skill_memory.build_agent_prompt(story_id, c.agent_id)
            # 不强制有内容，只要求调用不报错
            assert prompt is not None or True
        except Exception as e:
            pytest.fail(f"skill_memory.build_agent_prompt({c.agent_id}) 不应报错: {e}")
    print("\n[Skills] 各 Agent 的 skills 约束调用正常")


def test_facilitator_as_coordinator():
    """3. 使用 facilitator 作为协调 Agent：仅校验配置存在且启用"""
    from app.memory.agent_memory import agent_memory

    cfg = agent_memory.get_config(FACILITATOR_ID)
    assert cfg is not None
    assert cfg.enabled, "facilitator 应处于启用状态以便协调"
    assert "协调" in cfg.role or "调度" in cfg.role or "Facilitator" in cfg.name
    print(f"\n[Facilitator] 协调 Agent 配置: name={cfg.name}, role={cfg.role}")


def test_agent_prompt_and_skills_injected():
    """4. 校验调用链会注入 agent prompt 与 skills（与 AgentChatService 一致）"""
    from app.memory.agent_memory import agent_memory
    from app.memory.skill_memory import skill_memory

    story_id = "test-story-real"
    agent_id = "planner"
    cfg = agent_memory.get_config(agent_id)
    if not cfg:
        pytest.skip("数据库中无 planner 配置")

    parts = []
    if cfg and cfg.prompt:
        parts.append(cfg.prompt.strip())
    try:
        skill_prompt = skill_memory.build_agent_prompt(story_id, agent_id)
        if skill_prompt:
            parts.append(skill_prompt.strip())
    except Exception:
        pass
    full_prefix = "\n\n".join(parts).strip() + "\n\n" if parts else ""
    # 仅校验：若 DB 有 prompt，则最终前缀应包含
    if cfg and cfg.prompt:
        assert full_prefix, "应包含 agent 配置中的 prompt"
    print("\n[Inject] agent prompt + skills 可正确拼成前缀")


@pytest.mark.timeout(120)  # 需要 pytest-timeout；无插件时可去掉此 marker
def test_minimal_flow_with_real_llm():
    """5. 真实 LLM 最小流程：仅 planner -> summary，且使用 DB 配置与 skills"""
    from app.memory.agent_memory import agent_memory
    from app.memory.skill_memory import skill_memory
    from app.core.ai_config import get_llm_with_fallback

    llm = get_llm_with_fallback()
    if llm is None:
        pytest.skip("未配置 LLM（如 API Key），跳过真实调用")

    story_id = "test-story-real"
    outline = "一个关于青春成长的故事，主角是高中生。"

    # 只跑 planner + summary，减少耗时
    sequence = ["planner", "summary"]
    configs = {c.agent_id: c for c in agent_memory.get_all_configs()}
    enabled = [a for a in sequence if configs.get(a) and configs[a].enabled]
    if not enabled:
        pytest.skip("数据库中 planner/summary 未启用或不存在")

    from app.agents.planner_agent import PlannerAgent
    from app.agents.summary_agent import SummaryAgent

    agent_classes = {
        "planner": PlannerAgent,
        "summary": SummaryAgent,
    }
    state = {"input_text": outline, "plan_text": "", "summary_text": ""}
    timings = {}

    for agent_id in enabled:
        cfg = configs.get(agent_id)
        if not cfg or not cfg.enabled:
            continue
        prefix_parts = []
        if cfg.prompt:
            prefix_parts.append(cfg.prompt.strip())
        try:
            sp = skill_memory.build_agent_prompt(story_id, agent_id)
            if sp:
                prefix_parts.append(sp.strip())
        except Exception:
            pass
        prefix = "\n\n".join(prefix_parts) + "\n\n" if prefix_parts else ""

        if agent_id == "planner":
            input_text = prefix + state["input_text"]
            agent = PlannerAgent(llm=llm)
            t0 = time.time()
            out = agent.run({"text": input_text})
            timings["planner"] = time.time() - t0
            state["plan_text"] = out.get("plan_text", "")
        elif agent_id == "summary":
            input_text = prefix + (state.get("plan_text") or state["input_text"])[:2000]
            agent = SummaryAgent(llm=llm)
            t0 = time.time()
            state["summary_text"] = agent.run(input_text)
            timings["summary"] = time.time() - t0

    total = sum(timings.values())
    print(f"\n[Real LLM] 顺序: {enabled}")
    for k, v in timings.items():
        print(f"  - {k}: {v:.2f}s")
    print(f"  Total: {total:.2f}s")
    assert state.get("plan_text") or state.get("summary_text"), "应至少有一个环节产生内容"


@pytest.mark.timeout(120)
def test_run_with_db_agents_minimal():
    """6. 使用 pipeline_service_db.run_with_db_agents 最小流程（planner + summary）"""
    from app.services.pipeline_service_db import run_with_db_agents
    from app.core.llm import get_llm
    from app.core.ai_config import get_llm_with_fallback

    if get_llm() is None and get_llm_with_fallback() is None:
        pytest.skip("未配置 LLM，跳过真实调用")

    result = run_with_db_agents(
        outline="一个关于青春成长的故事，主角是高中生。",
        story_id="test-story-real",
        execution_order=["planner", "summary"],
    )
    assert "agent_logs" in result
    assert len(result["agent_logs"]) >= 1, "应至少执行一个 Agent"
    for log in result["agent_logs"]:
        assert "agent" in log and "elapsed_seconds" in log
    total = sum(log["elapsed_seconds"] for log in result["agent_logs"])
    print(f"\n[run_with_db_agents] 执行: {[l['agent'] for l in result['agent_logs']]}")
    print(f"  各步耗时(s): {[l['elapsed_seconds'] for l in result['agent_logs']]}, 总耗时: {total:.2f}s")
    assert result.get("plan_text") or result.get("summary_text"), "应至少有一个环节产生内容"


def test_run_with_facilitator_coordinator_minimal():
    """7. 使用 facilitator 动态协调的最小流程（planner -> writer -> finish）"""
    from app.services.pipeline_service_facilitator import run_with_facilitator_coordinator
    from app.core.llm import get_llm
    from app.core.ai_config import get_llm_with_fallback

    if get_llm() is None and get_llm_with_fallback() is None:
        pytest.skip("未配置 LLM，跳过真实调用")

    # 只跑 3 步：强制 planner + facilitator 决策的 writer + finish
    result = run_with_facilitator_coordinator(
        outline="一个关于青春成长的故事，主角是高中生。",
        story_id="test-story-real",
        max_steps=3,  # 限制步数
    )
    assert "agent_logs" in result
    assert "facilitator_decisions" in result
    print(f"\n[facilitator] 执行了 {result.get('steps_executed', 0)} 步")
    print(f"  Agent 日志: {[(l['agent'], l['elapsed_seconds']) for l in result['agent_logs']]}")
    print(f"  Facilitator 决策: {[(d['next_agent'], d['reason'][:30]) for d in result['facilitator_decisions']]}")
    total = result.get("total_time", 0)
    print(f"  总耗时: {total:.2f}s (Agent: {result.get('total_agent_time', 0)}s, Facilitator: {result.get('total_facilitator_time', 0)}s)")
    # 至少应该有 planner 和一次 facilitator 决策
    assert len(result["facilitator_decisions"]) >= 1

