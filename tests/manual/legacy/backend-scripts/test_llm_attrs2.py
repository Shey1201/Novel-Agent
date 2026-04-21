"""检查 LLM 对象的所有属性"""
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

print("[1] Getting LLM via get_llm...", flush=True)
llm = get_llm()
print(f"[2] LLM: {type(llm)}", flush=True)

# 检查所有属性
print("[3] Checking attrs...", flush=True)
attrs = [a for a in dir(llm) if not a.startswith('_')]
print(f"Public attrs: {attrs}", flush=True)
