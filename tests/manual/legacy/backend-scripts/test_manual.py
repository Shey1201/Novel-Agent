"""手动测试"""
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

# 1. 获取配置
print("[1] Getting config...")
from app.core.llm import _get_ai_config_from_db
config = _get_ai_config_from_db()

# 2. 创建 LLM
print("[2] Creating LLM...")
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(
    api_key=config.get("api_key"),
    model=config.get("chat_model"),
    base_url=config.get("base_url"),
    temperature=0.7
)

# 3. 创建 Agent
print("[3] Creating agent...")
from app.agents.planner_agent import PlannerAgent
agent = PlannerAgent(llm=llm)

# 4. 运行
print("[4] Running agent...")
result = agent.run({"text": "测试"})
print(f"[5] Done! Result length: {len(result.get('plan_text', ''))}", flush=True)
