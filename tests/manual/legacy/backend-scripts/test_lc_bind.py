"""测试 LangChain 0.3 新 API"""
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

# LangChain 0.3+ API
print("[1] Using bind()...", flush=True)
bound_llm = llm.bind(temperature=0.7)
print("[2] Calling invoke...", flush=True)
resp = bound_llm.invoke([HumanMessage(content="hello")])
print(f"[3] Done: {len(resp.content)}", flush=True)
