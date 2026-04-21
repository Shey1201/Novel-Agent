"""绕过 PlannerAgent，直接测试底层调用"""
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
from app.memory.agent_memory import AgentMemory
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

print("[1] Getting base LLM...", flush=True)
base_llm = get_llm()

print("[2] Getting config...", flush=True)
agent_memory = AgentMemory()
cfg = agent_memory.get_config("planner")

# 创建带 temperature 的 LLM
api_key = getattr(base_llm, "openai_api_key", None)
if hasattr(api_key, "get_secret_value"):
    api_key = api_key.get_secret_value()

llm = ChatOpenAI(
    model=base_llm.model_name,
    api_key=api_key,
    base_url=base_llm.openai_api_base,
    temperature=cfg.temperature if cfg else 0.7
)
print(f"[3] LLM created: {type(llm)}", flush=True)

# 直接调用 LLM（绕过 Agent）
prompt = """你是一位专业的故事策划师。请根据以下想法创作完整的故事规划：

测试

请一次性提供（用中文）：
1. 故事主题和核心概念
2. 主要角色设定
3. 故事结构
4. 关键情节点
5. 章节规划

确保内容完整。"""

print("[4] Direct LLM invoke...", flush=True)
resp = llm.invoke([HumanMessage(content=prompt)])
print(f"[5] Done! Length: {len(resp.content)}", flush=True)
