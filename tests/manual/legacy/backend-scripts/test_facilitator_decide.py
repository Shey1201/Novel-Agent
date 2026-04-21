"""测试新的自主决策逻辑"""
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
from app.core.llm import get_llm

llm = get_llm()

# 测试不同阶段的决策
test_cases = [
    ("planner", {"plan_text": "第一章：林晓发现古书...\n第二章：探索秘密"}),
    ("conflict", {"conflict_text": "主要冲突：林晓 vs 神秘组织", "plan_text": "第一章：林晓发现古书"}),
    ("writer", {"draft_text": "林晓在图书馆翻开那本古书，突然间...", "plan_text": "第一章：林晓发现古书"}),
    ("editor", {"edited_text": "林晓轻轻翻开古书...", "draft_text": "林晓在图书馆翻开那本古书", "plan_text": "第一章"}),
]

print("=" * 60)
print("测试：Facilitator 自主决策")
print("=" * 60)

for agent_id, state in test_cases:
    print(f"\n--- 当前阶段: {agent_id} ---")
    
    summary = _build_state_summary(agent_id, state)
    print(f"状态摘要: {summary[:100]}...")
    
    decision = _facilitator_decide_next_step(
        current_agent=agent_id,
        state_summary=summary,
        completed_agents=["planner"] if agent_id != "planner" else [],
        pending_agents=["writer", "editor"],
        base_llm=llm,
    )
    
    print(f"\n决策结果:")
    print(f"  需要评审: {decision['should_debate']}")
    print(f"  参与Agent: {decision['debate_agents']}")
    print(f"  评审轮数: {decision['debate_rounds']}")
    print(f"  理由: {decision.get('reason', '')}")
