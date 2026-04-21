"""对比两个 LLM 对象的差异"""
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
from app.memory.agent_memory import AgentMemory
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

print("[1] get_llm()...", flush=True)
llm1 = get_llm()
print(f"LLM1: model={llm1.model_name}, temp={llm1.temperature}", flush=True)
print(f"  base_url: {getattr(llm1, 'openai_api_base', 'N/A')}", flush=True)

print("[2] Creating LLM via _get_llm_for_agent logic...", flush=True)
agent_memory = AgentMemory()
cfg = agent_memory.get_config("planner")

api_key = getattr(llm1, "openai_api_key", None)
if hasattr(api_key, "get_secret_value"):
    api_key = api_key.get_secret_value()

llm2 = ChatOpenAI(
    model=llm1.model_name,
    api_key=api_key,
    base_url=getattr(llm1, "openai_api_base", None),
    temperature=cfg.temperature if cfg else 0.7
)
print(f"LLM2: model={llm2.model_name}, temp={llm2.temperature}", flush=True)
print(f"  base_url: {getattr(llm2, 'openai_api_base', 'N/A')}", flush=True)

# 测试 LLM1
print("[3] Testing LLM1...", flush=True)
r1 = llm1.invoke([HumanMessage(content="hi")])
print(f"LLM1 OK: {len(r1.content)}", flush=True)

# 测试 LLM2
print("[4] Testing LLM2...", flush=True)
r2 = llm2.invoke([HumanMessage(content="hi")])
print(f"LLM2 OK: {len(r2.content)}", flush=True)
