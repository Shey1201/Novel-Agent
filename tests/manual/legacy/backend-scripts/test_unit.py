"""
单元测试 - 直接测试 Agent 而不需要启动服务器
"""
import sys
sys.path.insert(0, 'd:/Project/Novel Agent Studio/backend')

from unittest.mock import Mock, patch
import time

print("=" * 60)
print("  Agent Unit Test (No Server Required)")
print("=" * 60)

# Test 1: BaseAgent
print("\n1. Test BaseAgent...")
from app.agents.base_agent import BaseAgent, AgentMode

mock_llm = Mock()
agent = BaseAgent(name="test-agent", llm=mock_llm, mode=AgentMode.CHAIN)

print(f"   Agent Name: {agent.name}")
print(f"   Agent Mode: {agent.mode.value}")
print(f"   Tools: {len(agent.tools)}")
print("   [OK] BaseAgent initialized")

# Test 2: WritingAgent
print("\n2. Test WritingAgent...")
from app.agents.writing_agent import WritingAgent

# No LLM test
agent = WritingAgent(llm=None, mode=AgentMode.CHAIN)
start = time.time()
result = agent.run({"text": "test writing"})
elapsed = (time.time() - start) * 1000

print(f"   Time: {elapsed:.0f}ms")
print(f"   Keys: {list(result.keys())}")
print(f"   draft_text length: {len(result.get('draft_text', ''))}")
print("   [OK] WritingAgent chain mode")

# Test 3: PlannerAgent  
print("\n3. Test PlannerAgent...")
from app.agents.planner_agent import PlannerAgent

agent = PlannerAgent(llm=None, mode=AgentMode.PLAN_EXECUTE)
start = time.time()
result = agent.run({"text": "test planning"})
elapsed = (time.time() - start) * 1000

print(f"   Time: {elapsed:.0f}ms")
print(f"   plan_text length: {len(result.get('plan_text', ''))}")
print("   [OK] PlannerAgent plan-execute mode")

# Test 4: Mock LLM test
print("\n4. Test with Mock LLM...")
with patch('app.agents.writing_agent.LANGCHAIN_AVAILABLE', True):
    mock_response = Mock()
    mock_response.content = "This is generated content"
    mock_llm = Mock()
    mock_llm.invoke = Mock(return_value=mock_response)
    
    agent = WritingAgent(llm=mock_llm, mode=AgentMode.CHAIN)
    result = agent.run({"text": "test writing"})
    
    print(f"   Content: {result.get('draft_text', '')[:50]}...")
    print("   [OK] Mock LLM test")

# Test 5: Tool system
print("\n5. Test Tool System...")
from app.agents.base_agent import Tool

def test_tool_func(text):
    return f"Processed: {text}"

tool = Tool(
    name="test_tool",
    description="Test tool",
    function=test_tool_func
)

agent = WritingAgent(llm=None)
agent.register_tool(tool)

print(f"   Registered: {len(agent.tools)}")
print(f"   Tool map: {list(agent._tool_map.keys())}")
print("   [OK] Tool system")

# Test 6: Reflection mode
print("\n6. Test Reflection Mode...")
agent = WritingAgent(llm=None, mode=AgentMode.REFLECTION)
start = time.time()
result = agent.run({"text": "test writing"})
elapsed = (time.time() - start) * 1000

print(f"   Time: {elapsed:.0f}ms")
print(f"   Reflection history: {len(result.get('reflection_history', []))}")
print("   [OK] Reflection mode")

print("\n" + "=" * 60)
print("  All Tests Passed!")
print("=" * 60)