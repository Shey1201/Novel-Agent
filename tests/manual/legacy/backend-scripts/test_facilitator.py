"""测试 facilitator 协调器的决策流程"""
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

print("=" * 60)
print("测试 Facilitator 协调器的决策流程")
print("=" * 60)

print("\n[1] Importing facilitator module...", flush=True)
from app.services.pipeline_service_facilitator import run_with_facilitator_coordinator

print("\n[2] 运行完整工作流 (带 facilitator 协调)...", flush=True)

test_outline = "第一章：林晓是一个普通的大学生，在图书馆偶然遇到一位神秘的老人..."
story_id = "test-facilitator-123"

# 运行完整流程
result = run_with_facilitator_coordinator(
    outline=test_outline,
    story_id=story_id,
    chapter_id="chapter-001",
    max_steps=15,
)

print("\n" + "=" * 60)
print("Facilitator 决策结果")
print("=" * 60)

# 打印 facilitator 决策
decisions = result.get("facilitator_decisions", [])
print("\nFacilitator 决策流程:")
for i, d in enumerate(decisions):
    print(f"  Step {i+1}: {d.get('next_agent', '?')} - {d.get('reason', '')} ({d.get('elapsed_seconds', 0):.2f}s)")

# 打印各 Agent 执行日志
logs = result.get("agent_logs", [])
print("\nAgent 执行日志:")
for log in logs:
    print(f"  - {log.get('agent')}: {log.get('message')} ({log.get('elapsed_seconds', 0):.2f}s)")

# 计算总耗时
total_time = sum(log.get("elapsed_seconds", 0) for log in logs)
facilitator_time = sum(d.get("elapsed_seconds", 0) for d in decisions)

print(f"\n总 Agent 执行时间: {total_time:.2f}s")
print(f"Facilitator 决策时间: {facilitator_time:.2f}s")
print(f"总耗时: {total_time + facilitator_time:.2f}s")

# 打印最终结果
final_text = result.get("final_text", "")
summary_text = result.get("summary_text", "")
print(f"\n最终文本长度: {len(final_text)} 字符")
print(f"摘要长度: {len(summary_text)} 字符")
