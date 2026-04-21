"""直接测试 NovelMemory 初始化"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
env_path = project_root / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_path)

sys.path.insert(0, str(backend_dir))

print("[1] Starting...", flush=True)

# 这会触发 NovelMemory
from app.services.pipeline_service_db import run_with_db_agents
print("[2] Done", flush=True)
