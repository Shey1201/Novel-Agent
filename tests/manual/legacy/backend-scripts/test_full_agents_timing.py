"""完整测试所有 8 个 Agent 的执行时间"""
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
print("完整测试所有 8 个 Agent 的执行时间")
print("=" * 60)

print("\n[1] Importing modules...", flush=True)
from app.services.pipeline_service_db import run_with_db_agents, agent_memory, skill_memory

print("\n[2] 获取所有启用的 Agent 配置...", flush=True)
all_configs = agent_memory.get_all_configs()
enabled_agents = [c.agent_id for c in all_configs if c.enabled and c.agent_id != "facilitator"]
print(f"启用的 Agent: {enabled_agents}")

# 测试用例
test_outline = "第一章：林晓是一个普通的大学生，在图书馆偶然遇到一位神秘的老人..."

print("\n[3] 开始顺序执行所有 Agent...", flush=True)

# 记录每个 Agent 的执行时间
agent_times = {}
total_start = 0

# 按顺序执行每个 Agent
for i, agent_id in enumerate(enabled_agents):
    print(f"\n--- 执行 {agent_id} ({i+1}/{len(enabled_agents)}) ---", flush=True)
    
    if i == 0:
        # 第一个 Agent 需要完整输入
        result = run_with_db_agents(
            outline=test_outline,
            story_id="test-123",
            execution_order=[agent_id]
        )
    else:
        # 后续 Agent 使用前一个的结果
        result = run_with_db_agents(
            outline=test_outline,
            story_id="test-123",
            execution_order=[agent_id]
        )
    
    # 从日志中获取耗时
    logs = result.get("agent_logs", [])
    if logs:
        elapsed = logs[0].get("elapsed_seconds", 0)
        agent_times[agent_id] = elapsed
        print(f"{agent_id}: {elapsed:.2f}s", flush=True)

print("\n" + "=" * 60)
print("测试结果总结")
print("=" * 60)

# 计算总时间
total_time = sum(agent_times.values())

print("\n各 Agent 执行时间:")
for agent, t in agent_times.items():
    pct = (t / total_time * 100) if total_time > 0 else 0
    print(f"  {agent:15s}: {t:6.2f}s ({pct:5.1f}%)")

print(f"\n总耗时: {total_time:.2f}s")
print(f"预计 DeepSeek API 费用: ${total_time / 60 * 0.14:.2f}/分钟 (假设 $0.14/分钟)")
