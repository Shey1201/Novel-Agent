"""
在测试前加载 .env（与 main.py 一致）
"""
import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
project_root = backend_dir.parent
env_path = next((path for path in (backend_dir / ".env", project_root / ".env") if path.exists()), None)

if env_path:
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path)
        print(f"[Test] Loaded .env from {env_path}")
    except Exception as e:
        print(f"[Test] dotenv load failed: {e}")
else:
    print(f"[Test] No .env at {backend_dir / '.env'} or {project_root / '.env'}")

# 确保 backend 在 path 中
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
