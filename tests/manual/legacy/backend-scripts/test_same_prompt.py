"""测试相同 prompt"""
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
from app.agents.base_agent import BaseAgent
from langchain_core.messages import HumanMessage

llm = get_llm()

# 用 PlannerAgent 相同的 prompt
prompt = """你是一位专业的故事策划师。请根据以下想法创作完整的故事规划：

测试

请一次性提供（用中文）：
1. 故事主题和核心概念
2. 主要角色设定（主角、配角）及背景
3. 故事结构（开端、发展、高潮、结局）
4. 关键情节点（至少5个）
5. 章节规划（10章左右的大纲）
6. 世界观设定要点

确保内容完整，可以直接用于后续写作。"""

print(f"Prompt length: {len(prompt)}", flush=True)

# 直接调用
print("Test 1: Direct invoke...", flush=True)
resp = llm.invoke([HumanMessage(content=prompt)])
print(f"Direct result: {len(resp.content)} chars", flush=True)

# 通过 BaseAgent
print("Test 2: Via BaseAgent...", flush=True)
agent = BaseAgent(name="test", llm=llm)
result = agent._call_llm(prompt)
print(f"BaseAgent result: {len(result)} chars", flush=True)

print("Done!", flush=True)
