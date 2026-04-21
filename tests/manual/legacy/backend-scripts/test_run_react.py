"""测试 BaseAgent.run_react - 手动模拟"""
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

from app.core.llm import get_llm
from app.agents.base_agent import BaseAgent, AgentMode

print("[1] Creating agent...", flush=True)
llm = get_llm()
agent = BaseAgent(name="test", llm=llm, mode=AgentMode.CHAIN)

print("[2] Calling run()...", flush=True)
# BaseAgent.run() 会抛出 NotImplementedError
try:
    result = agent.run({"text": "test"})
    print(f"[3] Result: {result}", flush=True)
except NotImplementedError as e:
    print(f"[3] Expected error: {e}", flush=True)

# 测试 run_react
print("[4] Calling run_react...", flush=True)
result2 = agent.run_react(
    input_data={"text": "test"},
    max_steps=1,
    stop_on_success=True
)
print(f"[5] Done! Keys: {result2.keys()}", flush=True)
