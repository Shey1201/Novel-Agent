"""
真实 API 测试 - 调用 DeepSeek API 测试 Agent 流程
"""
import sys
sys.path.insert(0, 'd:/Project/Novel Agent Studio/backend')

import time
from app.agents.writing_agent import WritingAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.conflict_agent import ConflictAgent
from app.agents.editor_agent import EditorAgent
from app.agents.summary_agent import SummaryAgent

# 初始化真实 LLM
from app.core.llm import get_llm

print("=" * 60)
print("  Real API Test - Agent Flow with DeepSeek")
print("=" * 60)

# 获取真实的 LLM
print("\n1. Initializing LLM...")
try:
    llm = get_llm()
    print(f"   LLM Model: {llm.model_name if hasattr(llm, 'model_name') else 'unknown'}")
    print(f"   [OK] LLM initialized")
except Exception as e:
    print(f"   Error: {e}")
    exit(1)

# 测试 1: PlannerAgent
print("\n2. Test PlannerAgent...")
agent = PlannerAgent(llm=llm)

start = time.time()
result = agent.run({"text": "写一个关于青春成长的故事"})
elapsed = time.time() - start

print(f"   Time: {elapsed:.2f}s")
print(f"   Plan length: {len(result.get('plan_text', ''))} chars")
print(f"   Preview: {result.get('plan_text', '')[:100]}...")
print("   [OK] PlannerAgent done")

# 测试 2: WritingAgent
print("\n3. Test WritingAgent...")
agent = WritingAgent(llm=llm)

start = time.time()
result = agent.run({
    "text": "主角是一名高中生，在面对高考和家庭期望的压力下，逐渐找到自己的人生方向。"
})
elapsed = time.time() - start

print(f"   Time: {elapsed:.2f}s")
print(f"   Draft length: {len(result.get('draft_text', ''))} chars")
print(f"   Preview: {result.get('draft_text', '')[:100]}...")
print("   [OK] WritingAgent done")

# 测试 3: ConflictAgent
print("\n4. Test ConflictAgent...")
agent = ConflictAgent(llm=llm)

start = time.time()
result = agent.run({
    "draft_text": result.get('draft_text', '')[:500]
})
elapsed = time.time() - start

print(f"   Time: {elapsed:.2f}s")
print(f"   Suggestions: {len(result.get('conflict_suggestions', []))} items")
for i, s in enumerate(result.get('conflict_suggestions', [])[:2], 1):
    print(f"     {i}. {s[:50]}...")
print("   [OK] ConflictAgent done")

# 测试 4: EditorAgent
print("\n5. Test EditorAgent...")
agent = EditorAgent(llm=llm)

start = time.time()
result = agent.run({
    "draft_text": "这是测试草稿" * 50
})
elapsed = time.time() - start

print(f"   Time: {elapsed:.2f}s")
print(f"   Edited length: {len(result.get('edited_text', ''))} chars")
print("   [OK] EditorAgent done")

# 测试 5: SummaryAgent
print("\n6. Test SummaryAgent...")
agent = SummaryAgent(llm=llm)

start = time.time()
result = agent.run("这是一个测试章节内容。" * 30)
elapsed = time.time() - start

print(f"   Time: {elapsed:.2f}s")
print(f"   Summary length: {len(result)} chars")
print(f"   Preview: {result[:100]}...")
print("   [OK] SummaryAgent done")

# 测试完整流程
print("\n" + "=" * 60)
print("  Full Workflow Test")
print("=" * 60)

total_start = time.time()

# 1. Plan
agent = PlannerAgent(llm=llm)
start = time.time()
plan_result = agent.run({"text": "一个关于冒险的故事"})
plan_time = time.time() - start
print(f"\n[1] Planner: {plan_time:.2f}s")

# 2. Write
agent = WritingAgent(llm=llm)
start = time.time()
write_result = agent.run({"text": plan_result.get('plan_text', '')})
write_time = time.time() - start
print(f"[2] Writing: {write_time:.2f}s")

# 3. Conflict
agent = ConflictAgent(llm=llm)
start = time.time()
conflict_result = agent.run({"draft_text": write_result.get('draft_text', '')[:500]})
conflict_time = time.time() - start
print(f"[3] Conflict: {conflict_time:.2f}s")

# 4. Edit
agent = EditorAgent(llm=llm)
start = time.time()
edit_result = agent.run({"draft_text": write_result.get('draft_text', '')})
edit_time = time.time() - start
print(f"[4] Editor: {edit_time:.2f}s")

# 5. Summary
agent = SummaryAgent(llm=llm)
start = time.time()
summary_result = agent.run(edit_result.get('edited_text', ''))
summary_time = time.time() - start
print(f"[5] Summary: {summary_time:.2f}s")

total_time = time.time() - total_start

print(f"\n{'='*60}")
print(f"  Total Time: {total_time:.2f}s")
print(f"  Breakdown:")
print(f"    Planner:  {plan_time:.2f}s ({plan_time/total_time*100:.1f}%)")
print(f"    Writing:  {write_time:.2f}s ({write_time/total_time*100:.1f}%)")
print(f"    Conflict: {conflict_time:.2f}s ({conflict_time/total_time*100:.1f}%)")
print(f"    Editor:   {edit_time:.2f}s ({edit_time/total_time*100:.1f}%)")
print(f"    Summary:  {summary_time:.2f}s ({summary_time/total_time*100:.1f}%)")
print(f"{'='*60}")