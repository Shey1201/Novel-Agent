"""测试创建带 temperature 的 LLM"""
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

print("[1] Getting base LLM...", flush=True)
from app.core.llm import get_llm
base_llm = get_llm()

print(f"[2] Base LLM: {type(base_llm)}", flush=True)

# 模拟 _get_llm_for_agent 的代码
print("[3] Getting config...", flush=True)
from app.memory.agent_memory import AgentMemory
agent_memory = AgentMemory()
cfg = agent_memory.get_config("planner")
print(f"[4] Config: {cfg}", flush=True)

if cfg:
    print("[5] Creating new LLM with temperature...", flush=True)
    from langchain_openai import ChatOpenAI
    model = getattr(base_llm, "model_name", None) or getattr(base_llm, "model", None)
    api_key = getattr(base_llm, "openai_api_key", None)
    base_url = getattr(base_llm, "openai_api_base", None)
    print(f"model={model}, api_key={type(api_key)}, base_url={base_url}", flush=True)
    
    if hasattr(api_key, "get_secret_value"):
        api_key = api_key.get_secret_value()
    
    new_llm = ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=float(cfg.temperature),
    )
    print(f"[6] New LLM: {type(new_llm)}", flush=True)
    
    print("[7] Testing invoke...", flush=True)
    from langchain_core.messages import HumanMessage
    resp = new_llm.invoke([HumanMessage(content="hello")])
    print(f"[8] Done! Length: {len(resp.content)}", flush=True)
