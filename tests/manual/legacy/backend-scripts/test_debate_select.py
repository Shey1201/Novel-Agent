"""快速测试优化后的 Debate"""
import sys
from pathlib import Path
import time

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
env_path = project_root / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_path)

sys.path.insert(0, str(backend_dir))

import logging
logging.basicConfig(level=logging.WARNING)

print("=" * 60)
print("快速测试：优化后的 Debate")
print("=" * 60)

# 测试 1：测试 LLM 动态选择 Debate 参与者
from app.services.pipeline_service_facilitator import _select_debate_agents
from app.core.llm import get_llm

llm = get_llm()

test_cases = [
    ("只需要大纲", "第一章：林晓是清华学生...", "planner"),
    ("写作初稿", "林晓在图书馆发现古书...", "writer"),
]

for name, outline, stage in test_cases:
    print(f"\n--- 测试: {name} ({stage}) ---")
    result = _select_debate_agents(
        outline=outline,
        draft_text="这是草稿内容...",
        available_agents=["reader", "critic", "editor"],
        base_llm=llm,
    )
    print(f"选择: {result['selected_agents']}")
    print(f"理由: {result.get('reason', '')}")
