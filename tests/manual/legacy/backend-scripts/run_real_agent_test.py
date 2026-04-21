"""
在真实环境中运行 Agent 测试：连接数据库，使用 facilitator 与 8 个 Agent 配置。

使用方式（在 backend 目录下）：
  python run_real_agent_test.py

要求：
  - 项目根目录有 .env，且配置 SUPABASE_URL、SUPABASE_SERVICE_KEY
  - 可选：OPENAI_API_KEY 或 AI 配置在 settings 表，用于真实 LLM 测试
"""
import os
import sys
from pathlib import Path

# 与 main.py 一致：从项目根加载 .env
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
env_path = project_root / ".env"
if env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path)
        print(f"Loaded .env from {env_path}\n")
    except Exception as e:
        print(f"Warning: could not load .env: {e}\n")
else:
    print(f"Warning: no .env at {env_path}\n")

sys.path.insert(0, str(backend_dir))

# 运行真实 DB 相关测试
import pytest
args = [
    str(backend_dir / "tests" / "integration" / "test_real_db_agents.py"),
    "-v",
    "-s",
    "--tb=short",
]
# 不跑需要真实 LLM 的用例时可加: -k "not test_minimal_flow_with_real_llm"
print("Run: pytest " + " ".join(args))
sys.exit(pytest.main(args))
