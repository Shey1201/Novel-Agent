"""测试 Debate 模式"""
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

print("=" * 70)
print("测试 Debate 模式")
print("=" * 70)

from app.services.pipeline_service_facilitator import run_with_facilitator_coordinator

test_outline = "第一章：林晓是清华大学的学生，在图书馆偶然发现一本神秘的古书..."

print("\n测试：完整流程 + Debate")
print("=" * 70)

start = time.time()
result = run_with_facilitator_coordinator(
    outline=test_outline,
    story_id="test-debate",
    chapter_id="ch-001",
    user_requirement="帮我写一个完整的章节",
    max_steps=10,
)
elapsed = time.time() - start

logs = result.get("agent_logs", [])
agents_used = [log.get("agent") for log in logs]
agent_time = sum(log.get("elapsed_seconds", 0) for log in logs)

print("\n" + "=" * 70)
print("结果汇总")
print("=" * 70)
print(f"Agent数: {len(agents_used)}")
print(f"Agent列表: {agents_used}")
print(f"Agent耗时: {agent_time:.1f}s")
print(f"总耗时: {elapsed:.1f}s")

# 检查是否有 debate
has_debate = any(log.get("agent") == "debate" for log in logs)
print(f"启用Debate: {has_debate}")
