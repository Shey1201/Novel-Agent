"""测试不同 temperature"""
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

llm = get_llm()
prompt = "测试"

# 多次调用
for temp in [0.7, 0.8, 0.9, 1.0]:
    print(f"Testing temp={temp}...", flush=True)
    try:
        bound = llm.bind(temperature=temp)
        resp = bound.invoke([HumanMessage(content=prompt)])
        print(f"  OK: {len(resp.content)} chars", flush=True)
    except Exception as e:
        print(f"  Error: {e}", flush=True)

print("Done!", flush=True)
