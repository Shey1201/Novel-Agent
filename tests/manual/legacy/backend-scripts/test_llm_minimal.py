"""最小化 LLM 调用测试"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
env_path = project_root / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_path)

sys.path.insert(0, str(backend_dir))

from app.core.llm import get_llm
from langchain_core.messages import HumanMessage
import time

print("=== Minimal LLM Test ===")
llm = get_llm()
print(f"LLM: {llm}")

# 直接调用，不经过 Agent
print("Calling LLM directly...")
t0 = time.time()
try:
    resp = llm.invoke([HumanMessage(content="你好，请用一句话回复")])
    print(f"Response: {resp.content}")
    print(f"Time: {time.time()-t0:.2f}s")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("=== Done ===")
