"""快速测试 LLM 是否可用"""
import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
env_path = project_root / ".env"
if env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path)
    except Exception:
        pass

sys.path.insert(0, str(backend_dir))

from app.core.llm import get_llm
from app.core.ai_config import get_llm_with_fallback
import time

print("Testing LLM...")

# 尝试获取 LLM
llm = get_llm()
if llm is None:
    print("get_llm() returned None, trying get_llm_with_fallback()...")
    llm = get_llm_with_fallback()

if llm is None:
    print("ERROR: No LLM available")
    sys.exit(1)

print(f"LLM available: {llm}")

# 简单调用测试
try:
    from langchain_core.messages import HumanMessage
    t0 = time.time()
    response = llm.invoke([HumanMessage(content="你好，请回复'测试成功'")])
    elapsed = time.time() - t0
    print(f"LLM response: {response.content if hasattr(response, 'content') else response}")
    print(f"Time: {elapsed:.2f}s")
except Exception as e:
    print(f"LLM call failed: {e}")
    import traceback
    traceback.print_exc()
