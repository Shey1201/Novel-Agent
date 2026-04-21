"""直接测试 get_llm 返回的对象"""
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

print("[1] Getting LLM...", flush=True)
llm = get_llm()
print(f"[2] LLM type: {type(llm)}", flush=True)

# 测试 stream
print("[3] Testing stream...", flush=True)
from langchain_core.messages import HumanMessage

for chunk in llm.stream([HumanMessage(content="hello")]):
    print(f"  chunk: {chunk.content}", flush=True)

print("[4] Done!", flush=True)
