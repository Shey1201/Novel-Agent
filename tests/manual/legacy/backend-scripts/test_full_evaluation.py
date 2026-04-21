# -*- coding: utf-8 -*-
"""
全面测试：评估矩阵 + Facilitator 自主决策 + Debate 性能
"""
import sys
from pathlib import Path
import time

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
env_path = project_root / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_path)

sys.path.insert(0, str(backend_dir))

import logging
logging.basicConfig(level=logging.WARNING)

from app.services.pipeline_service_facilitator import (
    _facilitator_decide_next_step, 
    _build_state_summary,
    _run_debate,
)
from app.services.agent_evaluation_matrix import get_evaluators_for_agent, get_evaluation_config
from app.core.llm import get_llm
from typing import Dict, Any

llm = get_llm()
enabled_agents = ["planner", "conflict", "writer", "editor", "reader", "critic", "consistency", "summary"]

# ========== 测试样例 ==========
TEST_CASES = [
    # 1. Planner
    {
        "name": "Planner - 短大纲",
        "agent_id": "planner",
        "state": {"plan_text": "Chapter 1: Lin Xiao finds ancient book."},
    },
    {
        "name": "Planner - 长大纲",
        "agent_id": "planner", 
        "state": {
            "plan_text": """Chapter 1: Lin Xiao finds ancient book (2000 words)
- Lin Xiao is a Tsinghua student
- Discovers mysterious ancient book in library
- Book emits strange light

Chapter 2: Explore secrets (3000 words)
- Lin Xiao studies the book content
- Discovers hidden text
- Meets mysterious person"""
        },
    },
    {
        "name": "Planner - 复杂大纲",
        "agent_id": "planner",
        "state": {
            "plan_text": """Full book structure: 100 chapters
Main characters: Lin Xiao (male lead), Su Qing (female lead), Mystery Organization
Main plot: Lin Xiao discovers ancient book secrets, fights Mystery Organization
Climax: Chapter 80 Lin Xiao sacrifices
Ending: Chapter 100 world restored
Foreshadowing: Book is alien civilization heritage"""
        },
    },
    
    # 2. Conflict
    {
        "name": "Conflict - 角色冲突",
        "agent_id": "conflict",
        "state": {
            "conflict_text": "Lin Xiao vs Su Qing: Lin Xiao wants to save the world, Su Qing wants to protect Lin Xiao, intense conflict.",
            "plan_text": "Chapter 1: Lin Xiao finds book"
        },
    },
    {
        "name": "Conflict - 势力冲突",
        "agent_id": "conflict",
        "state": {
            "conflict_text": "Heroes vs Mystery Organization: Organization wants to use book to rule world, heroes must stop them.",
            "plan_text": "Full book outline"
        },
    },
    
    # 3. Writer
    {
        "name": "Writer - 短开头",
        "agent_id": "writer",
        "state": {
            "draft_text": "Lin Xiao opened the book, suddenly a light...",
            "plan_text": "Chapter 1: Find book"
        },
    },
    {
        "name": "Writer - 中等开头",
        "agent_id": "writer",
        "state": {
            "draft_text": """Lin Xiao is a junior at Tsinghua University, majoring in history. That afternoon, he found an ancient book in the deepest corner of the library.

The book cover had strange symbols, feeling warm to the touch. Lin Xiao gently opened the pages, suddenly a brilliant light shot from the book, illuminating the entire library.

"What's this?" Lin Xiao was surprised to find his hand glowing, the book's text automatically translating into modern Chinese...""",
            "plan_text": "Chapter 1: Lin Xiao finds mysterious book in library"
        },
    },
    {
        "name": "Writer - 完整章节",
        "agent_id": "writer",
        "state": {
            "draft_text": """Lin Xiao is a top student at Tsinghua. That afternoon, he found an ancient book in the library.

The book cover had strange symbols, seemingly from ancient civilization. Lin Xiao gently opened the pages, suddenly a brilliant light shot from the book.

"What's this?" Lin Xiao was surprised to find his hand glowing, the book's text automatically appearing in his mind.

Just then, the library door opened. A woman in black coat walked in, looking at the book in Lin Xiao's hand with surprise.

"Didn't expect you to find it so fast," the woman said, "It seems fate's gears have started turning."

Lin Xiao looked at her warily: "Who are you? What is this book?"

The woman removed her sunglasses, revealing deep eyes: "I'm Su Qing. As for this book... it concerns the fate of all humanity."

Just then, thunder rolled outside, as if something was about to awaken...""",
            "plan_text": "Chapter 1: Lin Xiao finds book, meets Su Qing"
        },
    },
    {
        "name": "Writer - 修改稿",
        "agent_id": "writer",
        "state": {
            "draft_text": """Lin Xiao gently opened the yellowed pages, suddenly a soft light emanated from the paper, enveloping the entire bookshelf in a warm glow.

"This can't be..." Lin Xiao murmured. As a top history student, he'd seen countless ancient books but never encountered this. The light condensed into text floating in the air, telling an ancient legend about civilization's origin.

Lin Xiao reached out with trembling hands to touch the light text, at that moment his mind flooded with information, as if someone opened a door to another world in his consciousness.

The door opened. A woman in black stood at the entrance, looking at the book in Lin Xiao's hands and floating text with complex eyes.

"We found you," the woman said, "You came earlier than expected.\"""",
            "plan_text": "Chapter 1: Lin Xiao finds book"
        },
    },
    
    # 4. Editor
    {
        "name": "Editor - 初稿修订",
        "agent_id": "editor",
        "state": {
            "edited_text": """Lin Xiao opened the book, light burst out.

He was surprised to find his hand glowing.

"What's happening?" Lin Xiao murmured.

A mysterious woman appeared, talking about fate of humanity.""",
            "draft_text": "Lin Xiao opened book... light... hand glows... woman... fate...",
        },
    },
    {
        "name": "Editor - 终稿修订",
        "agent_id": "editor",
        "state": {
            "edited_text": """Lin Xiao gently opened the yellowed pages, suddenly a soft light emanated from the paper, enveloping the entire bookshelf in a warm glow.

"This can't be..." Lin Xiao murmured. As a top history student, he'd seen countless ancient books but never this. Light text condensed, telling an ancient legend.

Lin Xiao reached out with trembling hands, at that moment his mind flooded with information, as if a door to another world opened in his consciousness.

"We found you." A woman in black pushed open the door, looking at the book and floating text with complex eyes. "You came earlier than expected.\"""",
            "draft_text": """Lin Xiao opened the book, light burst out.
He was surprised to find his hand glowing.
"What's happening?" Lin Xiao murmured.
A mysterious woman appeared, talking about fate.""",
        },
    },
    
    # 5. 特殊情况
    {
        "name": "Writer - 很短内容",
        "agent_id": "writer",
        "state": {
            "draft_text": "Lin Xiao found book.",
            "plan_text": "Chapter 1"
        },
    },
    {
        "name": "Writer - 非常长内容",
        "agent_id": "writer",
        "state": {
            "draft_text": """Chapter 1: Fateful Encounter

Lin Xiao stood at the library entrance, took a deep breath. As a history major top student, he never imagined his life would change dramatically because of an ancient book.

It was an ordinary afternoon. Sunlight streamed through library windows onto bookshelves, the air filled with paper's unique fragrance. Lin Xiao searched history section as usual, his gaze suddenly caught by an ancient book in the corner.

The book had strange symbols on the cover, seemingly very ancient, from thousands of years ago. Lin Xiao curiously reached for it, at the moment of contact, a faint light flashed between the pages.

"Are you okay, classmate?" someone asked.

Only then did Lin Xiao realize he was sweating. He shook his head, quickly opened the book. To his shock, the text automatically translated into modern Chinese, floating in the air!

"What... what's this?" Lin Xiao couldn't believe what he saw.

Just then, the library door opened. A woman in black coat walked in, her gaze fixed directly on the book in Lin Xiao's hands with a hint of surprise.

"Didn't expect you to find it so fast," the woman said, low and mysterious, "It seems fate's gears have started turning."

Lin Xiao looked at her warily: "Who are you? What is this book?"

The woman removed her sunglasses, revealing deep eyes: "I'm Su Qing. As for this book... it concerns the fate of all humanity."

The sky outside suddenly turned dark, as if something was about to awaken. Lin Xiao felt the book in his hands start to heat up, the floating text疯狂闪烁.

"No time to explain," Su Qing grabbed Lin Xiao's wrist, "We must leave immediately!"

Just then, the entire library shook violently, bookshelves started collapsing, countless books fell from the sky. Lin Xiao and Su Qing looked at each other, knowing their peaceful life was over.

(End of chapter, ~2000 words)

Chapter 2: Truth

After an intense chase, Lin Xiao and Su Qing finally shook off their pursuers. They hid in an abandoned warehouse,整理思路.

"What did you mean by fate?" Lin Xiao asked impatiently.

Su Qing sighed, began telling an amazing secret..

(To be continued, ~1500 words)""",
            "plan_text": "Full book 100 chapters outline"
        },
    },
]


def test_facilitator_decision():
    """测试 Facilitator 决策"""
    print("\n" + "=" * 80)
    print("Test 1: Facilitator Autonomous Decision")
    print("=" * 80)
    
    results = []
    
    for i, test in enumerate(TEST_CASES):
        name = test["name"]
        agent_id = test["agent_id"]
        state = test["state"]
        
        t0 = time.time()
        
        # 评估矩阵推荐
        matrix_config = get_evaluation_config(agent_id)
        recommended = get_evaluators_for_agent(agent_id, enabled_agents)
        
        # LLM 决策
        summary = _build_state_summary(agent_id, state)
        decision = _facilitator_decide_next_step(
            current_agent=agent_id,
            state_summary=summary,
            completed_agents=["planner"],
            pending_agents=["writer", "editor"],
            base_llm=llm,
            enabled_agents=enabled_agents,
        )
        
        elapsed = time.time() - t0
        
        match = decision.get("debate_agents", []) == recommended
        results.append({
            "name": name,
            "elapsed": elapsed,
            "match": match,
            "recommended": recommended,
            "decided": decision.get("debate_agents", []),
            "should_debate": decision.get("should_debate"),
        })
        
        content_len = len(state.get('draft_text') or state.get('plan_text') or state.get('edited_text') or '')
        
        print(f"\n[{i+1}] {name}")
        print(f"    Content length: {content_len} chars")
        print(f"    Time: {elapsed:.2f}s")
        print(f"    Matrix: {recommended}")
        print(f"    LLM: {decision.get('debate_agents', [])}")
        print(f"    Debate: {decision.get('should_debate')}")
        reason = decision.get('reason', '')
        print(f"    Reason: {reason[:60]}..." if len(reason) > 60 else f"    Reason: {reason}")
        print(f"    {'MATCH' if match else 'DIFF'}")
    
    # 统计
    avg_time = sum(r["elapsed"] for r in results) / len(results)
    match_count = sum(1 for r in results if r["match"])
    debate_count = sum(1 for r in results if r["should_debate"])
    
    print(f"\n{'='*60}")
    print(f"Statistics:")
    print(f"  Avg time: {avg_time:.2f}s")
    print(f"  Matrix match rate: {match_count}/{len(results)} ({match_count/len(results)*100:.1f}%)")
    print(f"  Need debate: {debate_count}/{len(results)} ({debate_count/len(results)*100:.1f}%)")
    
    return results


def test_debate_performance():
    """测试 Debate 并行执行性能"""
    print("\n" + "=" * 80)
    print("Test 2: Debate Performance")
    print("=" * 80)
    
    test_draft = """Lin Xiao is a history student at Tsinghua. That afternoon, he found an ancient book in the library.

The book cover had strange symbols, seemingly from ancient civilization. Lin Xiao gently opened the pages, suddenly a brilliant light shot from the book.

"What's this?" Lin Xiao was surprised to find his hand glowing, the text automatically translating.

Just then, the library door opened. A woman in black coat walked in: "We found you.\""""
    
    test_outline = "Chapter 1: Lin Xiao finds mysterious book, meets Su Qing."
    
    test_configs = [
        {"name": "1 Agent (editor)", "agents": ["editor"], "rounds": 1},
        {"name": "2 Agents (reader+critic)", "agents": ["reader", "critic"], "rounds": 1},
        {"name": "3 Agents (all)", "agents": ["reader", "critic", "editor"], "rounds": 1},
        {"name": "2 Rounds Debate", "agents": ["reader", "critic", "editor"], "rounds": 2},
    ]
    
    results = []
    
    for config in test_configs:
        print(f"\n[Testing] {config['name']}")
        
        state = {"draft_text": test_draft}
        
        t0 = time.time()
        result = _run_debate(
            draft_text=test_draft,
            outline=test_outline,
            debate_agents=config["agents"],
            max_rounds=config["rounds"],
            state=state,
            story_id="test",
            base_llm=llm,
        )
        
        elapsed = time.time() - t0
        rounds = len(result.get("rounds", []))
        
        results.append({
            "name": config["name"],
            "elapsed": elapsed,
            "rounds": rounds,
            "agents": len(config["agents"]),
        })
        
        print(f"    Time: {elapsed:.2f}s")
        print(f"    Rounds: {rounds}")
        print(f"    Improved length: {len(result.get('improved_text', ''))} chars")
    
    if results:
        baseline = results[2]["elapsed"]
        print(f"\n{'='*60}")
        print(f"Performance (3 Agents 1 round = {baseline:.2f}s baseline):")
        for r in results:
            ratio = r["elapsed"] / baseline if baseline > 0 else 1
            print(f"  {r['name']}: {r['elapsed']:.2f}s ({ratio:.1f}x)")
    
    return results


def test_special_cases():
    """测试特殊情况"""
    print("\n" + "=" * 80)
    print("Test 3: Special Cases")
    print("=" * 80)
    
    cases = [
        {
            "name": "Very short content",
            "agent_id": "writer",
            "state": {"draft_text": "Lin Xiao reads book.", "plan_text": "Chapter 1"},
        },
        {
            "name": "Empty content",
            "agent_id": "writer", 
            "state": {"draft_text": "", "plan_text": ""},
        },
        {
            "name": "Only outline, no draft",
            "agent_id": "writer",
            "state": {"plan_text": "Chapter 1: Lin Xiao finds book"},
        },
    ]
    
    for case in cases:
        name = case["name"]
        agent_id = case["agent_id"]
        state = case["state"]
        
        print(f"\n[{name}]")
        
        try:
            summary = _build_state_summary(agent_id, state)
            print(f"  Summary: {summary[:100]}...")
            
            decision = _facilitator_decide_next_step(
                current_agent=agent_id,
                state_summary=summary,
                completed_agents=["planner"],
                pending_agents=["writer", "editor"],
                base_llm=llm,
                enabled_agents=enabled_agents,
            )
            
            print(f"  Decision: need_debate={decision.get('should_debate')}, agents={decision.get('debate_agents')}")
        except Exception as e:
            print(f"  ERROR: {e}")


def main():
    print("=" * 80)
    print("Full Test: Evaluation Matrix + Facilitator + Debate Performance")
    print("=" * 80)
    
    total_t0 = time.time()
    
    # Test 1
    decision_results = test_facilitator_decision()
    
    # Test 2
    debate_results = test_debate_performance()
    
    # Test 3
    test_special_cases()
    
    total_elapsed = time.time() - total_t0
    
    print("\n" + "=" * 80)
    print("Total Time Analysis")
    print("=" * 80)
    print(f"Total test time: {total_elapsed:.1f}s")
    
    # Optimization suggestions
    print("\n" + "=" * 80)
    print("Optimization Suggestions")
    print("=" * 80)
    
    avg_decision_time = sum(r["elapsed"] for r in decision_results) / len(decision_results)
    avg_debate_time = sum(r["elapsed"] for r in debate_results) / len(debate_results) if debate_results else 0
    
    print(f"""
1. Facilitator decision avg time: {avg_decision_time:.2f}s
   - Called after each agent completes
   - OPTIMIZE: Cache decisions, skip for short content

2. Debate execution avg time: {avg_debate_time:.2f}s
   - Currently using ThreadPoolExecutor parallel
   - OPTIMIZE: Consider async for even faster

3. Total time per agent:
   - Theory min: {avg_decision_time:.2f}s (skip debate)
   - Theory max: {avg_decision_time:.2f}s + {avg_debate_time:.2f}s = {avg_decision_time + avg_debate_time:.2f}s

4. Optimization points:
   - Short content (<200 chars): Skip debate
   - Multiple rounds: Reduce rounds
   - Consistency priority: Must handle consistency issues
   - Cache evaluation matrix
""")


if __name__ == "__main__":
    main()
