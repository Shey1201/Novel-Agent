"""极简测试 PlannerAgent"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
env_path = project_root / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_path)

sys.path.insert(0, str(backend_dir))

# 禁用 DEBUG 日志
import logging
logging.basicConfig(level=logging.WARNING)

print("[1] Importing modules...", flush=True)

from app.core.llm import get_llm
print("[2] LLM loaded", flush=True)

from app.agents.planner_agent import PlannerAgent
print("[3] PlannerAgent imported", flush=True)

llm = get_llm()
print(f"[4] LLM: {llm}", flush=True)

agent = PlannerAgent(llm=llm)
print("[5] Agent created", flush=True)

print("[6] Calling agent.run()...", flush=True)
result = agent.run({"text": "测试故事"})
print(f"[7] Result: {result.get('plan_text', '')[:200]}", flush=True)
print("=== Done ===", flush=True)
