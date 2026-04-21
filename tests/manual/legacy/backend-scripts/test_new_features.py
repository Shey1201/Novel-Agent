"""
测试新功能 - 评分系统、递归生成、Reflection 模式
"""
import os
import sys
import time

os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from app.services.agent_scoring_system import AgentScoringSystem, get_scoring_system
from app.services.recursive_content_generator import RecursiveContentGenerator, create_recursive_generator
from app.services.reflection_agent import ReflectionAgent, create_reflection_agent
from app.core.llm import get_llm


def test_scoring_system():
    """测试评分系统"""
    print("="*60)
    print("Test 1: Scoring System")
    print("="*60)
    
    # 获取 LLM
    llm = get_llm()
    scoring = get_scoring_system(llm)
    
    # 测试内容
    test_contents = [
        ("短内容", "这是第一章。"),
        ("中等内容", "第一章：林晓穿越到异世界。这是一个充满挑战的新世界。他需要在这里生存下去。\
            他遇到了很多困难，但他没有放弃。\
            最终，他成为了这个世界的英雄。"),
        ("长内容", """第一章：林晓穿越到异世界

林晓是一名普通的大学生。有一天，他突然穿越到了一个新的世界。这个世界充满了魔法和怪物。

他开始探索这个陌生的地方。首先，他遇到了一位善良的老人。老人告诉他关于这个世界的基本情况。然后，他开始学习魔法。

经过长时间的训练，林晓终于成为了一名强大的法师。他开始挑战这个世界的最强的怪物。最终，他拯救了整个世界。

这个故事告诉我们，只要不放弃，就一定能够成功。"""),
    ]
    
    for name, content in test_contents:
        print(f"\n--- Testing: {name} ({len(content)} chars) ---")
        
        # 评分
        result = scoring.check_and_score(content, "writer")
        
        print(f"  Score: {result['score']}/100 ({result['grade']})")
        print(f"  Passed: {result['passed']}")
        print(f"  Needs revision: {result['needs_revision']}")
        print(f"  Needs rewrite: {result['needs_rewrite']}")
        print(f"  Dimensions:")
        for dim, score in result['review_details'].items():
            print(f"    - {dim}: {score}")
    
    return True


def test_recursive_generator():
    """测试递归内容生成"""
    print("\n" + "="*60)
    print("Test 2: Recursive Content Generator")
    print("="*60)
    
    # 获取 LLM
    llm = get_llm()
    
    # 创建生成器
    generator = create_recursive_generator(llm=llm)
    
    # 测试生成
    topic = "都市爱情故事"
    context = {
        "description": "讲述都市年轻人的爱情故事",
        "target": "年轻读者",
    }
    
    print(f"\n--- Generating: {topic} ---")
    t0 = time.time()
    
    # 生成内容树（只生成 1 层以加快测试）
    root = generator.generate(topic, context, max_depth=1)
    
    elapsed = time.time() - t0
    print(f"\n  Time: {elapsed:.1f}s")
    print(f"  Root title: {root.title}")
    print(f"  Root content length: {len(root.content)}")
    print(f"  Word count: {root.count_words()}")
    print(f"  Children: {len(root.children)}")
    
    return True


def test_reflection_agent():
    """测试 Reflection 模式"""
    print("\n" + "="*60)
    print("Test 3: Reflection Agent")
    print("="*60)
    
    # 获取 LLM
    llm = get_llm()
    
    # 创建 Reflection Agent
    reflection = create_reflection_agent(llm=llm, max_iterations=2)
    
    # 测试
    prompt = """请帮我写一段小说开头，主题是穿越到异世界。

要求：
- 主角穿越到异世界
- 异世界有魔法和怪物
- 主角获得系统或金手指
"""
    
    print(f"\n--- Generating with Reflection ---")
    t0 = time.time()
    
    result = reflection.generate_and_refine(prompt)
    
    elapsed = time.time() - t0
    print(f"\n  Time: {elapsed:.1f}s")
    print(f"  Iterations: {result.iteration_count}")
    print(f"  Original length: {len(result.original_content)}")
    print(f"  Improved length: {len(result.improved_content)}")
    print(f"  Improvements made: {len(result.improvements_made)}")
    
    if result.improvements_made:
        print("\n  Improvements:")
        for imp in result.improvements_made:
            print(f"    - {imp}")
    
    return True


def main():
    print("="*60)
    print("New Features Test")
    print("="*60)
    
    results = {}
    
    # 测试 1: 评分系统
    try:
        results["scoring"] = test_scoring_system()
    except Exception as e:
        print(f"  Error: {e}")
        results["scoring"] = False
    
    # 测试 2: 递归生成（可能耗时较长）
    # try:
    #     results["recursive"] = test_recursive_generator()
    # except Exception as e:
    #     print(f"  Error: {e}")
    #     results["recursive"] = False
    
    # 测试 3: Reflection 模式
    try:
        results["reflection"] = test_reflection_agent()
    except Exception as e:
        print(f"  Error: {e}")
        results["reflection"] = False
    
    # 总结
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    passed = sum(1 for v in results.values() if v)
    for name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {name}: {status}")
    print(f"\nTotal: {passed}/{len(results)} passed")


if __name__ == "__main__":
    main()
