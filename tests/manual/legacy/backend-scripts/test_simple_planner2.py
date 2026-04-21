"""创建不带工具的简化 PlannerAgent"""
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

class SimplePlannerAgent(BaseAgent):
    """简化版 PlannerAgent - 不使用工具"""
    def __init__(self, llm):
        # 不调用 super()，手动设置属性
        self.name = "simple-planner"
        self.llm = llm
        self.mode = AgentMode.PLAN_EXECUTE
        self.tools = []
        self._reasoning_history = []
        self._current_context = {}
        self._tool_map = {}
    
    def run(self, input_data):
        prompt = f"""你是一位专业的故事策划师。请根据以下想法创作完整的故事规划：

{input_data.get('text', '')}

请一次性提供（用中文）：
1. 故事主题和核心概念
2. 主要角色设定
3. 故事结构
4. 关键情节点（至少5个）
5. 章节规划

确保内容完整，可以直接用于后续写作。"""
        
        result = self._call_llm(prompt)
        return {"plan_text": result}

print("[1] Getting LLM...", flush=True)
llm = get_llm()
print("[2] Creating SimplePlannerAgent...", flush=True)
agent = SimplePlannerAgent(llm)
print("[3] Running...", flush=True)
result = agent.run({"text": "一个关于青春成长的故事"})
print(f"[4] Done! Result length: {len(result.get('plan_text', ''))}", flush=True)
