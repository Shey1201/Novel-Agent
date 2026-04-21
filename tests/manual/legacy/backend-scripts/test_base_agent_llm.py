"""测试 BaseAgent._call_llm 方法"""
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

print("=== Test BaseAgent._call_llm ===", flush=True)

from app.core.llm import get_llm
from app.agents.base_agent import BaseAgent, AgentMode

llm = get_llm()
print(f"LLM: {llm}", flush=True)

# 创建最小化的 Agent
agent = BaseAgent(name="test-agent", llm=llm, mode=AgentMode.CHAIN)
print("Agent created", flush=True)

# 直接调用 _call_llm
print("Calling _call_llm...", flush=True)
result = agent._call_llm("你好，请用一句话回复")
print(f"Result: {result}", flush=True)
print("=== Done ===", flush=True)
