"""测试 import timing"""
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

print("[1] Importing ChatOpenAI...", flush=True)
from langchain_openai import ChatOpenAI

print("[2] Getting config...", flush=True)
from app.core.llm import _get_ai_config_from_db
config = _get_ai_config_from_db()
print(f"[3] Config: {config}", flush=True)

print("[4] Creating LLM...", flush=True)
llm = ChatOpenAI(
    api_key=config.get("api_key"),
    model=config.get("chat_model"),
    base_url=config.get("base_url"),
    temperature=0.7
)

print("[5] Testing invoke...", flush=True)
from langchain_core.messages import HumanMessage
resp = llm.invoke([HumanMessage(content="hi")])
print(f"[6] Done: {len(resp.content)}", flush=True)
