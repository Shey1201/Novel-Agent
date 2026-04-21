"""测试 AI 需求分析功能"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
env_path = project_root / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_path)

sys.path.insert(0, str(backend_dir))

print("测试 AI 需求分析功能...")

from app.services.pipeline_service_facilitator import _analyze_requirement_completeness
from app.memory.agent_memory import agent_memory
from app.core.llm import get_llm

# 获取 LLM
llm = get_llm()

print("=" * 60)

# 测试用例
test_cases = [
    ("帮我写小说", ""),
    ("帮我写一个科幻小说", "林晓是一名宇航员..."),
    ("写一个都市爱情故事", "第一章：林晓在咖啡馆遇到神秘男子..."),
    ("帮我写一个完整的章节", "主角林晓是清华大学的学生，意外获得了外星科技..."),
]

for req, outline in test_cases:
    print(f"\n--- 需求: '{req}' ---")
    print(f"--- 大纲: '{outline[:40]}...' ---")
    
    result = _analyze_requirement_completeness(req, outline, llm=llm)
    
    print(f"\n完整度: {'OK' if result['is_complete'] else 'NO'}")
    print(f"分析: {result.get('analysis', '')}")
    print(f"可继续: {'OK' if result['can_proceed'] else 'NO'}")
    
    if result['questions']:
        print("\n需要提问:")
        for i, q in enumerate(result['questions'], 1):
            print(f"  {i}. {q}")
