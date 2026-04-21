"""直接测试带 tools 的 LLM 调用"""
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

from app.core.llm import get_llm
from app.agents.planner_agent import PlannerAgent

print("[1] Getting LLM...", flush=True)
llm = get_llm()

print("[2] Creating PlannerAgent...", flush=True)
agent = PlannerAgent(llm=llm)
print(f"[3] Agent tools: {len(agent.tools)}", flush=True)

print("[4] Calling agent.run()...", flush=True)
result = agent.run({"text": "测试"})
print(f"[5] Done! Keys: {result.keys()}", flush=True)
