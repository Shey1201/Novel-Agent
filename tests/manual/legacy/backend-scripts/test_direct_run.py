"""添加调试日志到 _run_plan_execute_mode"""
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

print("[1] Importing...", flush=True)
from app.agents.planner_agent import PlannerAgent
from app.core.llm import get_llm

print("[2] Modules imported", flush=True)

llm = get_llm()
print("[3] LLM ready", flush=True)

print("[4] Creating PlannerAgent...", flush=True)
agent = PlannerAgent(llm=llm)
print("[5] Agent created", flush=True)

print("[6] Calling run()...", flush=True)
# 手动调用内部方法
result = agent._run_plan_execute_mode({"text": "测试"})
print("[7] Done!", flush=True)
