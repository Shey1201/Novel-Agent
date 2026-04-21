"""尝试使用环境变量中的 API key"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
env_path = project_root / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_path)

sys.path.insert(0, str(backend_dir))

import os

print(f"DEEPSEEK_API_KEY: {os.getenv('DEEPSEEK_API_KEY', 'NOT SET')[:20]}...", flush=True)
print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', 'NOT SET')[:20]}...", flush=True)

# 尝试用环境变量的 key
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

print("[1] Creating LLM with env key...", flush=True)
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY", ""),
    base_url="https://api.deepseek.com",
    temperature=0.7
)

print("[2] Testing invoke...", flush=True)
resp = llm.invoke([HumanMessage(content="hi")])
print(f"[3] OK: {len(resp.content)}", flush=True)
