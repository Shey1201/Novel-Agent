"""直接测试 PlannerAgent"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
env_path = project_root / ".env"
if env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path)
        print(f"Loaded .env from {env_path}")
    except Exception:
        pass

sys.path.insert(0, str(backend_dir))

import functools
print = functools.partial(print, flush=True)

from app.core.llm import get_llm
from app.core.ai_config import get_llm_with_fallback
from app.agents.planner_agent import PlannerAgent

print("\n=== Testing PlannerAgent ===")
llm = get_llm() or get_llm_with_fallback()
print(f"LLM: {llm}")

agent = PlannerAgent(llm=llm)
print("PlannerAgent created")

input_data = {"text": "一个关于青春成长的故事，主角是高中生。"}
print(f"Running with input: {input_data}")

import time
t0 = time.time()
try:
    result = agent.run(input_data)
    elapsed = time.time() - t0
    print(f"Result: {result}")
    print(f"Time: {elapsed:.2f}s")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Done ===")
