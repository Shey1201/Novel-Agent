"""
完整功能测试脚本 - 使用现有的 Agent 系统
"""
import sys
sys.path.insert(0, 'd:/Project/Novel Agent Studio/backend')
import os
import time

# 设置 API
os.environ['OPENAI_API_KEY'] = 'sk-d85df7d2b9e6473db234b9665c1913f5'
os.environ['OPENAI_BASE_URL'] = 'https://api.deepseek.com/v1'

from app.agents.planner_agent import PlannerAgent
from app.agents.writing_agent import WritingAgent
from app.agents.conflict_agent import ConflictAgent
from app.agents.editor_agent import EditorAgent
from app.agents.reader_agent import ReaderAgent
from app.agents.summary_agent import SummaryAgent
from app.agents.base_agent import AgentMode
from app.memory.agent_memory import agent_memory
from app.memory.skill_memory import skill_memory


def test_agent_configs():
    """测试 Agent 配置加载"""
    print("="*60)
    print("  1. Test Agent Configs Loading")
    print("="*60)
    
    try:
        configs = agent_memory.get_all_configs()
        print(f"  Loaded {len(configs)} agent configs:")
        for c in configs:
            status = "ON" if c.enabled else "OFF"
            print(f"    - {c.agent_id}: {c.name} [{status}]")
    except Exception as e:
        print(f"  Warning: {e}")
        print("  Using default configs")


def test_skill_memory():
    """测试 Skill Memory"""
    print("\n" + "="*60)
    print("  2. Test Skill Memory")
    print("="*60)
    
    try:
        # 获取技能
        skills = skill_memory.get_all_skills()
        print(f"  Loaded {len(skills)} skills")
        
        # 获取代理技能
        agent_skills = skill_memory.get_skills_for_agent("test-story", "writer")
        print(f"  Writer agent skills: {len(agent_skills)}")
    except Exception as e:
        print(f"  Warning: {e}")


def test_agent_timing(agent_class, agent_id, input_data, description):
    """测试单个 Agent 的执行时间"""
    print(f"\n  {description}...")
    
    # 检查 Agent 配置
    try:
        config = agent_memory.get_config(agent_id)
        if config and not config.enabled:
            print(f"    Skipped: Agent disabled")
            return None, 0
        if config:
            print(f"    Config: temp={config.temperature}")
    except:
        pass
    
    # 检查 Skill 约束
    try:
        skill_prompt = skill_memory.build_agent_prompt("test-story", agent_id)
        if skill_prompt:
            print(f"    Skill constraint: {len(skill_prompt)} chars")
    except:
        pass
    
    # 执行
    start = time.time()
    agent = agent_class(llm=None)  # 使用模拟 LLM
    result = agent.run(input_data)
    elapsed = time.time() - start
    
    print(f"    Time: {elapsed:.2f}s")
    return result, elapsed


def test_full_workflow():
    """测试完整工作流"""
    print("\n" + "="*60)
    print("  3. Test Full Workflow with All Agents")
    print("="*60)
    
    outline = "一个关于青春成长的故事"
    
    total_start = time.time()
    
    # 1. Planner
    print("\n  [1] Planner Agent")
    result1, t1 = test_agent_timing(
        PlannerAgent, "planner",
        {"text": outline},
        "Planning"
    )
    plan_text = result1.get("plan_text", "") if result1 else ""
    
    # 2. Conflict
    print("\n  [2] Conflict Agent")
    result2, t2 = test_agent_timing(
        ConflictAgent, "conflict",
        {"draft_text": plan_text[:500]},
        "Analyzing conflicts"
    )
    
    # 3. Writer
    print("\n  [3] Writing Agent")
    result3, t3 = test_agent_timing(
        WritingAgent, "writer",
        {"text": plan_text},
        "Writing"
    )
    draft = result3.get("draft_text", "") if result3 else ""
    
    # 4. Editor
    print("\n  [4] Editor Agent")
    result4, t4 = test_agent_timing(
        EditorAgent, "editor",
        {"draft_text": draft[:500]},
        "Editing"
    )
    
    # 5. Reader
    print("\n  [5] Reader Agent")
    result5, t5 = test_agent_timing(
        ReaderAgent, "reader",
        {"draft_text": draft[:500]},
        "Reading feedback"
    )
    
    # 6. Summary
    print("\n  [6] Summary Agent")
    result6, t6 = test_agent_timing(
        SummaryAgent, "summary",
        draft[:500],
        "Summarizing"
    )
    
    total_time = time.time() - total_start
    
    print("\n" + "="*60)
    print("  Summary")
    print("="*60)
    print(f"  Planner:   {t1:.1f}s")
    print(f"  Conflict:  {t2:.1f}s")
    print(f"  Writer:    {t3:.1f}s")
    print(f"  Editor:    {t4:.1f}s")
    print(f"  Reader:    {t5:.1f}s")
    print(f"  Summary:   {t6:.1f}s")
    print(f"  ----------------")
    print(f"  Total:    {total_time:.1f}s")
    print("="*60)


def test_with_real_llm():
    """使用真实 LLM 测试"""
    print("\n" + "="*60)
    print("  4. Test with Real LLM (Planners Only)")
    print("="*60)
    
    import openai
    client = openai.OpenAI(
        api_key='sk-d85df7d2b9e6473db234b9665c1913f5',
        base_url='https://api.deepseek.com/v1'
    )
    
    from app.core.llm import get_llm
    
    # 直接调用 API 测试
    print("\n  Testing real API calls...")
    
    start = time.time()
    response = client.chat.completions.create(
        model='deepseek-chat',
        messages=[{'role': 'user', 'content': '写一个故事大纲'}],
        max_tokens=300
    )
    elapsed = time.time() - start
    
    print(f"  Single API call: {elapsed:.1f}s")
    print(f"  Response: {response.choices[0].message.content[:100]}...")


if __name__ == "__main__":
    test_agent_configs()
    test_skill_memory()
    test_full_workflow()
    test_with_real_llm()