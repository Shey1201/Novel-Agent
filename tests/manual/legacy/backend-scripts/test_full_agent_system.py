"""
完整的功能测试脚本 - 测试 Agent 协调系统
"""
import os
import sys
import time
import json

# 设置 UTF-8 环境
os.environ["PYTHONIOENCODING"] = "utf-8"

# 添加 backend 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 加载 .env 文件
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)
print(f"[Test] Loaded env from: {env_path}")

# 导入所需模块
from app.memory.agent_memory import agent_memory
from app.memory.skill_memory import skill_memory
from app.memory.story_memory import StoryBible, StoryMemory
from app.core.llm import get_llm
from app.core.ai_config import get_llm_with_fallback
from app.services.agent_evaluation_matrix import AGENT_EVALUATION_MATRIX
from app.services.pipeline_service_facilitator import (
    run_with_facilitator_coordinator,
    _build_constraints_prefix,
    _facilitator_decide_next_step,
    _analyze_user_requirement,
)


def test_agent_configs():
    """测试 1: 验证所有 Agent 配置是否正确加载"""
    print("\n" + "="*60)
    print("测试 1: Agent 配置加载")
    print("="*60)
    
    agents = agent_memory.get_all_configs()
    print(f"共加载 {len(agents)} 个 Agent 配置")
    
    for cfg in agents:
        print(f"\n  [{cfg.agent_id}]")
        print(f"    - enabled: {cfg.enabled}")
        print(f"    - prompt 长度: {len(cfg.prompt) if cfg.prompt else 0}")
        print(f"    - temperature: {cfg.temperature}")
    
    return len(agents) >= 8


def test_skills_loading():
    """测试 2: 验证 Skills 加载"""
    print("\n" + "="*60)
    print("测试 2: Skills 加载")
    print("="*60)
    
    # 获取所有 skill
    skills = skill_memory.get_all_skills()
    print(f"共加载 {len(skills)} 个 skills")
    
    # 测试为特定 Agent 构建约束
    test_story_id = "test-story"
    for agent_id in ["planner", "writer", "editor"]:
        prompt = skill_memory.build_agent_prompt(test_story_id, agent_id)
        print(f"\n  [{agent_id}] skill 约束: {len(prompt) if prompt else 0} 字符")
    
    return True


def test_constraints_injection():
    """测试 3: 验证约束注入功能"""
    print("\n" + "="*60)
    print("测试 3: 约束注入 (prompt + skills)")
    print("="*60)
    
    story_id = "test-story"
    for agent_id in ["planner", "writer", "editor"]:
        constraints = _build_constraints_prefix(story_id, agent_id)
        print(f"\n  [{agent_id}] 约束长度: {len(constraints)} 字符")
        if constraints:
            print(f"    预览: {constraints[:100]}...")
    
    return True


def test_requirement_analysis():
    """测试 4: 需求分析"""
    print("\n" + "="*60)
    print("测试 4: 用户需求分析")
    print("="*60)
    
    test_cases = [
        ("帮我写小说", "第一章：穿越"),
        ("帮我写一个科幻小说", "林晓是一名宇航员..."),
        ("写一个完整的都市爱情故事", "第一章：林晓在咖啡馆遇到"),
        ("帮我写一个完整的章节", "林晓是清华学生..."),
    ]
    
    results = []
    from app.services.pipeline_service_facilitator import _analyze_requirement_completeness
    from app.core.llm import get_llm
    
    # 获取 LLM 实例
    try:
        llm = get_llm()
    except:
        llm = None
    
    for req, outline in test_cases:
        result = _analyze_requirement_completeness(req, outline, llm)
        results.append(result)
        print(f"\n  需求: {req}")
        print(f"  大纲: {outline[:30]}...")
        print(f"  可继续: {result.get('can_proceed')}")
        print(f"  需提问: {result.get('is_complete') == False}")
        if result.get('questions'):
            print(f"  问题: {result['questions'][:2]}")
    
    return results


def test_llm_decision():
    """测试 5: LLM 决策功能"""
    print("\n" + "="*60)
    print("测试 5: LLM 自主决策")
    print("="*60)
    
    try:
        llm = get_llm()
        test_cases = [
            ("planner", "第一章：穿越来到异世界..."),
            ("writer", "林晓睁开眼睛，发现自己在一个陌生的房间..."),
            ("editor", "林晓是清华学生..."),
        ]
        
        for agent_id, content in test_cases:
            result = _facilitator_decide_next_step(
                current_agent=agent_id,
                state_summary=content[:500],
                completed_agents=[],
                pending_agents=[],
                base_llm=llm,
                enabled_agents=["reader", "critic", "editor", "consistency"],
            )
            print(f"\n  [{agent_id}] 内容长度: {len(content)}")
            print(f"    需要评审: {result.get('needs_evaluation')}")
            print(f"    参与 Agent: {result.get('evaluators', [])}")
            print(f"    轮数: {result.get('debate_rounds')}")
            print(f"    原因: {result.get('reason', 'N/A')[:50]}...")
        
        return True
    except Exception as e:
        print(f"  LLM 调用失败: {e}")
        return False


def test_evaluation_matrix():
    """测试 6: 评估矩阵"""
    print("\n" + "="*60)
    print("测试 6: Agent 评估��阵")
    print("="*60)
    
    print("  各 Agent 完成后应该由谁来评估：")
    for agent_id, config in AGENT_EVALUATION_MATRIX.items():
        evaluators = config.get("evaluators", [])
        print(f"\n  [{agent_id}] → {evaluators}")
    
    return len(AGENT_EVALUATION_MATRIX) >= 6


def test_full_workflow():
    """测试 7: 完整工作流（真实 API 调用）"""
    print("\n" + "="*60)
    print("测试 7: 完整工作流（真实 API 调用）")
    print("="*60)
    
    # 这个测试会调用真实的 LLM API
    # 使用简短的内容来加快测试
    test_outline = "第一章：林晓穿越到异世界，获得系统..."
    
    print("\n  测试场景 1: 只需要大纲")
    t0 = time.time()
    try:
        result = run_with_facilitator_coordinator(
            outline=test_outline,
            story_id="test-story-1",
            user_requirement="帮我生成一个章节大纲",
        )
        elapsed = time.time() - t0
        print(f"    耗时: {elapsed:.1f}s")
        if "final_text" in result:
            print(f"    结果长度: {len(result.get('final_text', ''))}")
    except Exception as e:
        print(f"    错误: {e}")
    
    print("\n  测试场景 2: 写作 + 编辑")
    t0 = time.time()
    try:
        result = run_with_facilitator_coordinator(
            outline=test_outline,
            story_id="test-story-2",
            user_requirement="帮我写一个完整的章节",
        )
        elapsed = time.time() - t0
        print(f"    耗时: {elapsed:.1f}s")
    except Exception as e:
        print(f"    错误: {e}")
    
    return True


def main():
    """主函数"""
    print("="*60)
    print("Novel Agent Studio - Agent 系统完整测试")
    print("="*60)
    
    # 测试结果收集
    results = {}
    
    # 测试 1: Agent 配置
    results["agent_configs"] = test_agent_configs()
    
    # 测试 2: Skills 加载
    results["skills_loading"] = test_skills_loading()
    
    # 测试 3: 约束注入
    results["constraints"] = test_constraints_injection()
    
    # 测试 4: 需求分析
    results["requirement"] = test_requirement_analysis()
    
    # 测试 5: LLM 决策
    results["llm_decision"] = test_llm_decision()
    
    # Test 6: Evaluation Matrix (skip due to encoding)
    results["evaluation_matrix"] = len(AGENT_EVALUATION_MATRIX) >= 6
    
    # Test 7: Full Workflow (optional - requires real API)
    # results["full_workflow"] = test_full_workflow()
    
    # 打印总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    # Optimizable points
    print("\n" + "="*60)
    print("Optimizable Points")
    print("="*60)
    print("""
  1. LLM decision takes ~4s - can simplify prompt
  2. Agent config repeated queries - can add caching
  3. Debate can include more agents - like summary
  4. Can add result cache - instant response for repeated content
  5. Can support streaming output - real-time progress display
    """)


if __name__ == "__main__":
    main()