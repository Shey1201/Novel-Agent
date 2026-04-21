"""测试创建 StoryMemory"""
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

print("[1] Importing StoryMemory...", flush=True)
from app.memory.story_memory import StoryBible, StoryMemory
print("[2] Creating StoryBible...", flush=True)
bible = StoryBible()
print("[3] Creating StoryMemory...", flush=True)
memory = StoryMemory(story_id="test", bible=bible)
print(f"[4] Done: {type(memory)}", flush=True)
