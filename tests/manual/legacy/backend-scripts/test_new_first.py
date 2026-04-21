"""先测试新 LLM"""
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

print("[1] Creating new LLM first...", flush=True)
agent_memory = AgentMemory()
cfg = agent_memory.get_config("planner")

# 不先调用 get_llm()
api_key = "sk-"  # 填入你的 key
llm2 = ChatOpenAI(
    model="deepseek-chat",
    api_key=api_key,
    base_url="https://api.deepseek.com",
    temperature=0.7
)

print("[2] Testing new LLM...", flush=True)
r2 = llm2.invoke([HumanMessage(content="hi")])
print(f"New LLM OK: {len(r2.content)}", flush=True)
