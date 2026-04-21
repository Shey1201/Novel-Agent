"""检查 API key"""
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
api_key = getattr(llm, "openai_api_key", None)
print(f"api_key type: {type(api_key)}", flush=True)
print(f"api_key value: {api_key}", flush=True)
if hasattr(api_key, "get_secret_value"):
    print(f"get_secret_value: {api_key.get_secret_value()}", flush=True)
