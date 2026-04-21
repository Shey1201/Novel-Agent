"""简化调试"""
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
from app.memory.agent_memory import AgentMemory

print("[1] Getting LLM...", flush=True)
llm = get_llm()

print("[2] Getting config...", flush=True)
agent_memory = AgentMemory()
cfg = agent_memory.get_config("planner")
print(f"Config temp: {cfg.temperature if cfg else 'None'}", flush=True)

# 创建带 temperature 的 LLM
from langchain_openai import ChatOpenAI
api_key = getattr(llm, "openai_api_key", None)
if hasattr(api_key, "get_secret_value"):
    api_key = api_key.get_secret_value()

agent_llm = ChatOpenAI(
    model=llm.model_name,
    api_key=api_key,
    base_url=llm.openai_api_base,
    temperature=cfg.temperature if cfg else 0.7
)

print("[3] Creating agent...", flush=True)
agent = PlannerAgent(llm=agent_llm)

print("[4] Running...", flush=True)
result = agent.run({"text": "测试"})
print(f"[5] Done! Keys: {result.keys()}", flush=True)
