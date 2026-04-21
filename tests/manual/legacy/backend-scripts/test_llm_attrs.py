"""检查 LLM 属性"""
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

llm = get_llm()
print(f"LLM: {llm}", flush=True)
print(f"Has stream: {hasattr(llm, 'stream')}", flush=True)
print(f"Has ainvoke: {hasattr(llm, 'ainvoke')}", flush=True)
print(f"Has invoke: {hasattr(llm, 'invoke')}", flush=True)

# 检查 invoke 是否是绑定方法
import inspect
if hasattr(llm, 'invoke'):
    print(f"invoke is method: {inspect.ismethod(llm.invoke)}", flush=True)
    print(f"invoke is function: {inspect.isfunction(llm.invoke)}", flush=True)
