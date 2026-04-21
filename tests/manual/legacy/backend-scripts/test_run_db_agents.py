"""测试 run_with_db_agents - 只运行 planner"""
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

print("[1] Importing...", flush=True)
from app.services.pipeline_service_db import run_with_db_agents
print("[2] Imported", flush=True)

print("[3] Running with planner only...", flush=True)
# 只运行 planner
result = run_with_db_agents(
    outline="一个关于青春成长的故事",
    story_id="test-123",
    execution_order=["planner"]
)
print(f"[4] Done! Keys: {list(result.keys())}", flush=True)
print(f"Plan length: {len(result.get('plan_text', ''))}", flush=True)
