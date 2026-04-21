"""深入了解所有 Agent 配置"""
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

from app.memory.agent_memory import agent_memory

# 获取所有 Agent 配置
configs = agent_memory.get_all_configs()

print("=" * 80)
print("数据库中所有 Agent 配置")
print("=" * 80)

for cfg in configs:
    print(f"\n{'='*60}")
    print(f"Agent: {cfg.agent_id}")
    print(f"名称: {cfg.name}")
    print(f"角色: {cfg.role}")
    print(f"人格: {cfg.personality}")
    print(f"温度: {cfg.temperature}")
    print(f"启用: {cfg.enabled}")
    print(f"描述: {cfg.description}")
    print("-" * 60)
    print(f"Prompt (前500字):")
    print(cfg.prompt[:500] if cfg.prompt else "(无)")

print("\n" + "=" * 80)
print("按启用状态分类")
print("=" * 80)

enabled = [c for c in configs if c.enabled]
disabled = [c for c in configs if not c.enabled]

print(f"\n启用的 Agent ({len(enabled)}):")
for c in enabled:
    print(f"  - {c.agent_id}: {c.name}")

print(f"\n禁用的 Agent ({len(disabled)}):")
for c in disabled:
    print(f"  - {c.agent_id}: {c.name}")
