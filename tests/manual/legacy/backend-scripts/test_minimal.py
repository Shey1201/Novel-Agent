"""最小化测试"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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

print("[1] Importing run_with_db_agents...", flush=True)
from app.services.pipeline_service_db import run_with_db_agents
print("[2] Imported", flush=True)

print("[3] Running...", flush=True)
result = run_with_db_agents(
    outline="测试故事",
    story_id="test",
    execution_order=["planner"]
)
print(f"[4] Done! plan_text length: {len(result.get('plan_text', ''))}", flush=True)
