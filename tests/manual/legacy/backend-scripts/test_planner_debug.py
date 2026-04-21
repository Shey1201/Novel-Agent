"""带调试的 PlannerAgent 测试"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
env_path = project_root / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_path)

sys.path.insert(0, str(backend_dir))

# 开启详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

from app.core.llm import get_llm
from app.agents.planner_agent import PlannerAgent
import time

print("=== Testing PlannerAgent with Debug ===")
llm = get_llm()
print(f"LLM ready: {llm}")

agent = PlannerAgent(llm=llm)
print(f"Agent created: {agent.name}, mode: {agent.mode}")

input_data = {"text": "一个关于青春成长的故事"}
print(f"Running agent.run()...")

t0 = time.time()
result = agent.run(input_data)
elapsed = time.time() - t0

print(f"Result: {result}")
print(f"Time: {elapsed:.2f}s")
print("=== Done ===")
