"""在 run_with_db_agents 中添加调试"""
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

print("[1] Importing modules...", flush=True)
from app.services.pipeline_service_db import run_with_db_agents, _build_constraints_prefix, _get_llm_for_agent, agent_classes
from app.core.llm import get_llm

print("[2] Getting LLM and building prefix...", flush=True)
llm = get_llm()

prefix = _build_constraints_prefix("test-123", "planner")
print(f"[3] Prefix length: {len(prefix)}", flush=True)

print("[4] Getting LLM for agent...", flush=True)
agent_llm = _get_llm_for_agent("planner", llm)
print(f"[5] Agent LLM: {type(agent_llm)}", flush=True)

print("[6] Creating agent...", flush=True)
agent = agent_classes["planner"](llm=agent_llm)
print(f"[7] Agent: {agent}", flush=True)

print("[8] Calling agent.run()...", flush=True)
out = agent.run({"text": prefix + "一个关于青春成长的故事"})
print(f"[9] Done! Keys: {out.keys()}", flush=True)
