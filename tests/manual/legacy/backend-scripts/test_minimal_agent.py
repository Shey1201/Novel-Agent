"""极简测试 - 绕过所有默认工具"""
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

print("=== Minimal PlannerAgent Test ===", flush=True)

from app.core.llm import get_llm
from app.agents.base_agent import BaseAgent, AgentMode, Tool

llm = get_llm()
print(f"LLM ready", flush=True)

# 手动创建一个最小化的 Agent，不使用 PlannerAgent
class MinimalAgent(BaseAgent):
    def __init__(self, llm):
        # 不调用 super().__init__() 避免工具初始化
        self.name = "minimal-agent"
        self.llm = llm
        self.mode = AgentMode.CHAIN
        self.tools = []
        self._reasoning_history = []
        self._current_context = {}
        self._tool_map = {}
    
    def run(self, input_data):
        prompt = input_data.get("text", "请用一句话回复")
        return {"plan_text": self._call_llm(prompt)}

agent = MinimalAgent(llm)
print("Agent created", flush=True)

print("Running...", flush=True)
result = agent.run({"text": "你好"})
print(f"Result: {result.get('plan_text', '')[:100]}", flush=True)
print("=== Done ===", flush=True)
