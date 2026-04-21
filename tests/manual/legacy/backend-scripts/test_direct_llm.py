"""直接调用 LLM 测试"""
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

print("=== Direct LLM Test ===", flush=True)

from app.core.llm import get_llm
from langchain_core.messages import HumanMessage

llm = get_llm()
print(f"LLM: {llm}", flush=True)

prompt = "你好，请用一句话回复"
print("Calling LLM...", flush=True)
response = llm.invoke([HumanMessage(content=prompt)])
print(f"Response: {response.content}", flush=True)
print("=== Done ===", flush=True)
