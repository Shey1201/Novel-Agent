"""测试导入 PlannerAgent"""
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

print("[1] Importing PlannerAgent...", flush=True)
from app.agents.planner_agent import PlannerAgent
print("[2] PlannerAgent imported", flush=True)

print("[3] Getting LLM...", flush=True)
from app.core.llm import get_llm
llm = get_llm()
print("[4] LLM ready", flush=True)

print("[5] Creating PlannerAgent...", flush=True)
agent = PlannerAgent(llm=llm)
print("[6] PlannerAgent created", flush=True)

print("[7] Running agent.run()...", flush=True)
result = agent.run({"text": "测试"})
print("[8] Done!", flush=True)
print(f"Result length: {len(result.get('plan_text', ''))}", flush=True)
