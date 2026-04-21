"""
性能对比测试 - 比较优化前后的性能
"""
import os
import sys
import time

os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from app.services.pipeline_service_facilitator import (
    _facilitator_decide_next_step,
    _build_constraints_prefix,
    _get_cached_config,
    clear_agent_cache,
)
from app.core.llm import get_llm


def test_llm_decision_performance():
    """测试 LLM 决策性能"""
    print("="*60)
    print("Test: LLM Decision Performance")
    print("="*60)
    
    llm = get_llm()
    
    # 测试1: 短内容 - 应该跳过 LLM 调用
    print("\n[Test 1] Short content (<50 chars) - should skip LLM")
    t0 = time.time()
    result = _facilitator_decide_next_step(
        current_agent="planner",
        state_summary="第一章：穿越",
        completed_agents=[],
        pending_agents=["writer"],
        base_llm=llm,
    )
    elapsed = time.time() - t0
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Should debate: {result.get('should_debate')}")
    print(f"  Reason: {result.get('reason')}")
    
    # 测试2: 长内容 - 应该调用 LLM
    print("\n[Test 2] Long content (>50 chars) - should use LLM")
    long_content = "第一章：林晓穿越到异世界，获得系统。他在陌生的世界中探索，寻找回到原来世界的方法。"
    t0 = time.time()
    result = _facilitator_decide_next_step(
        current_agent="planner",
        state_summary=long_content,
        completed_agents=[],
        pending_agents=["writer"],
        base_llm=llm,
    )
    elapsed = time.time() - t0
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Should debate: {result.get('should_debate')}")
    print(f"  Debate agents: {result.get('debate_agents', [])}")
    print(f"  Reason: {result.get('reason')[:50]}...")
    
    return True


def test_cache_performance():
    """测试缓存性能"""
    print("\n" + "="*60)
    print("Test: Cache Performance")
    print("="*60)
    
    story_id = "test-story"
    agents = ["planner", "writer", "editor", "reader", "critic"]
    
    # 第一次调用 - 无缓存
    print("\n[Test 1] First call - no cache")
    clear_agent_cache()
    t0 = time.time()
    for agent_id in agents:
        _build_constraints_prefix(story_id, agent_id)
    elapsed1 = time.time() - t0
    print(f"  Time: {elapsed1:.3f}s")
    
    # 第二次调用 - 有缓存
    print("\n[Test 2] Second call - with cache")
    t0 = time.time()
    for agent_id in agents:
        _build_constraints_prefix(story_id, agent_id)
    elapsed2 = time.time() - t0
    print(f"  Time: {elapsed2:.3f}s")
    
    # 计算提升
    if elapsed2 > 0:
        improvement = (elapsed1 - elapsed2) / elapsed1 * 100
        print(f"\n  Cache improvement: {improvement:.1f}%")
    
    return True


def test_constraint_injection():
    """测试约束注入"""
    print("\n" + "="*60)
    print("Test: Constraint Injection")
    print("="*60)
    
    story_id = "test-story"
    
    for agent_id in ["planner", "writer", "editor"]:
        constraints = _build_constraints_prefix(story_id, agent_id)
        print(f"\n  [{agent_id}] Length: {len(constraints)} chars")
    
    return True


def main():
    print("="*60)
    print("Performance Optimization Test")
    print("="*60)
    
    # 测试缓存
    test_cache_performance()
    
    # 测试约束注入
    test_constraint_injection()
    
    # 测试 LLM 决策
    test_llm_decision_performance()
    
    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60)


if __name__ == "__main__":
    main()