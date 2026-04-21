"""测试评估矩阵 + LLM 自主决策"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
env_path = project_root / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_path)

sys.path.insert(0, str(backend_dir))

import logging
logging.basicConfig(level=logging.WARNING)

from app.services.pipeline_service_facilitator import _facilitator_decide_next_step, _build_state_summary
from app.services.agent_evaluation_matrix import get_evaluators_for_agent, get_evaluation_config
from app.core.llm import get_llm

llm = get_llm()
enabled_agents = ["planner", "conflict", "writer", "editor", "reader", "critic", "consistency", "summary"]

print("=" * 80)
print("测试：评估矩阵 + LLM 自主决策")
print("=" * 80)

# 测试不同阶段的决策
test_cases = [
    ("planner", {"plan_text": "第一章：林晓发现古书...\n第二章：探索秘密"}),
    ("conflict", {"conflict_text": "主要冲突：林晓 vs 神秘组织", "plan_text": "第一章：林晓发现古书"}),
    ("writer", {"draft_text": "林晓在图书馆翻开那本古书，突然间...", "plan_text": "第一章：林晓发现古书"}),
    ("editor", {"edited_text": "林晓轻轻翻开古书...", "draft_text": "林晓在图书馆翻开那本古书", "plan_text": "第一章"}),
]

for agent_id, state in test_cases:
    print(f"\n{'='*60}")
    print(f"当前阶段: {agent_id}")
    print(f"{'='*60}")
    
    # 评估矩阵推荐
    matrix_config = get_evaluation_config(agent_id)
    recommended = get_evaluators_for_agent(agent_id, enabled_agents)
    print(f"[评估矩阵] 推荐: {recommended} (轮数: {matrix_config.get('default_rounds', 1)})")
    print(f"[评估理由] {matrix_config.get('reasons', {})}")
    
    # LLM 决策
    summary = _build_state_summary(agent_id, state)
    decision = _facilitator_decide_next_step(
        current_agent=agent_id,
        state_summary=summary,
        completed_agents=["planner"] if agent_id != "planner" else [],
        pending_agents=["writer", "editor"],
        base_llm=llm,
        enabled_agents=enabled_agents,
    )
    
    print(f"\n[LLM 决策]")
    print(f"  需要评审: {decision['should_debate']}")
    print(f"  参与Agent: {decision['debate_agents']}")
    print(f"  轮数: {decision['debate_rounds']}")
    print(f"  理由: {decision.get('reason', '')}")
