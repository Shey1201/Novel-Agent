"""直接导入 LLM 并测试"""
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
os.environ['SUPABASE_URL'] = os.getenv('SUPABASE_URL', '')
os.environ['SUPABASE_SERVICE_KEY'] = os.getenv('SUPABASE_SERVICE_KEY', '')

# 直接从 langchain 导入
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

print("[1] Creating LLM directly...", flush=True)
llm = ChatOpenAI(
    model="deepseek-chat",
    temperature=0.7,
    api_key=os.getenv("DEEPSEEK_API_KEY", ""),
    base_url="https://api.deepseek.com"
)
print("[2] LLM created", flush=True)

print("[3] Testing invoke...", flush=True)
resp = llm.invoke([HumanMessage(content="hello")])
print(f"[4] Done: {len(resp.content)} chars", flush=True)
