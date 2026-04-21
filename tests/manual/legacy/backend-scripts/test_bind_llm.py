"""测试 bind() 后的 LLM"""
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
from langchain_core.messages import HumanMessage

print("[1] Getting LLM...", flush=True)
llm = get_llm()
print(f"Original LLM: {type(llm)}", flush=True)

print("[2] Binding temperature...", flush=True)
bound_llm = llm.bind(temperature=0.7)
print(f"Bound LLM: {type(bound_llm)}", flush=True)

print("[3] Testing invoke...", flush=True)
resp = bound_llm.invoke([HumanMessage(content="hi")])
print(f"[4] Done! Length: {len(resp.content)}", flush=True)
