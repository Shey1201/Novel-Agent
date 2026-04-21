"""
配置对比测试
"""
import sys
sys.path.insert(0, 'd:/Project/Novel Agent Studio/backend')
from app.agents.smart_coordinator import SmartWorkflowExecutor
import time

print('='*60)
print('  Config Comparison Test')
print('='*60)

# 配置1: 最少 Agent
print('\n[Test 1] Minimal (planner + writer only)')
executor = SmartWorkflowExecutor(story_id='test-1')
result = executor.run('一个冒险故事', agent_sequence=['planner', 'writer'])
total = result['total_time']
print(f'  Time: {total:.1f}s')
print(f'  Agents: {result["agents_executed"]}')

# 配置2: 标准流程
print('\n[Test 2] Standard (planner + writer + editor)')
executor = SmartWorkflowExecutor(story_id='test-2')
result = executor.run('一个冒险故事', agent_sequence=['planner', 'writer', 'editor'])
total2 = result['total_time']
print(f'  Time: {total2:.1f}s')
print(f'  Agents: {result["agents_executed"]}')

# 配置3: 完整流程
print('\n[Test 3] Full (all 6 agents)')
executor = SmartWorkflowExecutor(story_id='test-3')
result = executor.run('一个冒险故事', agent_sequence=['planner', 'conflict', 'writer', 'editor', 'reader', 'summary'])
total3 = result['total_time']
print(f'  Time: {total3:.1f}s')
print(f'  Agents: {result["agents_executed"]}')

print('\n' + '='*60)
print('Summary:')
print('  Minimal: ~' + str(int(total)) + 's (仅生成)')
print('  Standard: ~' + str(int(total2)) + 's (生成+编辑)')  
print('  Full: ~' + str(int(total3)) + 's (完整流程)')
print('='*60)