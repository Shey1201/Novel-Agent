"""测试不带 tools 的简化 Agent"""
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
from typing import Dict, Any

class SimpleTestAgent(BaseAgent):
    def __init__(self, llm):
        # 不传 tools
        super().__init__(name="test", llm=llm, mode=AgentMode.PLAN_EXECUTE)
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        print("[SimpleTestAgent.run] CALLED", flush=True)
        prompt = f"测试: {input_data.get('text', '')}"
        print("[SimpleTestAgent.run] Calling _call_llm...", flush=True)
        result = self._call_llm(prompt)
        print(f"[SimpleTestAgent.run] Done, len={len(result)}", flush=True)
        return {"result": result}

print("[1] Getting LLM...", flush=True)
llm = get_llm()

print("[2] Creating SimpleTestAgent...", flush=True)
agent = SimpleTestAgent(llm=llm)
print(f"[3] Agent tools: {len(agent.tools)}", flush=True)

print("[4] Calling agent.run()...", flush=True)
result = agent.run({"text": "测试"})
print(f"[5] Done! Result length: {len(result.get('result', ''))}", flush=True)
