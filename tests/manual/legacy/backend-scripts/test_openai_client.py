"""测试 OpenAI 客户端"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
env_path = project_root / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_path)

sys.path.insert(0, str(backend_dir))

print("[1] Creating client...", flush=True)
from openai import OpenAI

client = OpenAI(
    api_key="sk-d85df7d2b9e6473db234b9665c1913f5",
    base_url="https://api.deepseek.com"
)

print("[2] Calling API...", flush=True)
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "hi"}],
    max_tokens=50
)

print(f"[3] Done: {response.choices[0].message.content[:50]}...", flush=True)
