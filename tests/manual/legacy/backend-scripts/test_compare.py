"""对比测试：直接调用 vs 通过 BaseAgent"""
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
from app.core.llm import get_llm
from langchain_core.messages import HumanMessage

llm = get_llm()
print("[2] LLM ready", flush=True)

# 测试1：直接调用
print("[3] Test 1: Direct invoke...", flush=True)
response1 = llm.invoke([HumanMessage(content="hello")])
print(f"[4] Direct result length: {len(response1.content)}", flush=True)

# 测试2：通过 BaseAgent
print("[5] Test 2: Via BaseAgent...", flush=True)
from app.agents.base_agent import BaseAgent
agent = BaseAgent(name="test", llm=llm)
result2 = agent._call_llm("hello")
print(f"[6] BaseAgent result length: {len(result2)}", flush=True)

print("[7] Both tests done!", flush=True)
