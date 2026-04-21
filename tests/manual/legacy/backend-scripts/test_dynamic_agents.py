"""测试不同用户需求的Agent动态选择"""
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

print("=" * 60)
print("测试不同用户需求的 Agent 动态选择")
print("=" * 60)

from app.services.pipeline_service_facilitator import run_with_facilitator_coordinator, _analyze_user_requirement

test_outline = "第一章：林晓是一个普通的大学生，在图书馆偶然遇到一位神秘的老人..."

# 测试不同的用户需求
test_cases = [
    ("只需要大纲", "帮我生成一个章节大纲"),
    ("只需要写作", "帮我写一章内容"),
    ("写作+编辑", "帮我写一章并编辑修改"),
    ("完整流程", "帮我生成完整的章节内容"),
]

results = []

for name, requirement in test_cases:
    print(f"\n{'='*60}")
    print(f"测试: {name} - 需求: {requirement}")
    print("=" * 60)
    
    # 先分析应该跳过哪些 Agent
    skip_agents = _analyze_user_requirement(requirement)
    print(f"分析结果 - 应跳过: {skip_agents}")
    
    # 运行流程
    result = run_with_facilitator_coordinator(
        outline=test_outline,
        story_id=f"test-{name}",
        chapter_id="chapter-001",
        user_requirement=requirement,
        max_steps=10,
    )
    
    # 统计
    logs = result.get("agent_logs", [])
    total_time = sum(log.get("elapsed_seconds", 0) for log in logs)
    agents_used = [log.get("agent") for log in logs]
    
    results.append({
        "name": name,
        "requirement": requirement,
        "skip_agents": skip_agents,
        "used_agents": agents_used,
        "total_time": total_time,
    })
    
    print(f"\n结果: 使用了 {len(agents_used)} 个 Agent: {agents_used}")
    print(f"总耗时: {total_time:.2f}s")

print("\n" + "=" * 60)
print("测试结果总结")
print("=" * 60)

for r in results:
    print(f"\n【{r['name']}】")
    print(f"  需求: {r['requirement']}")
    print(f"  跳过: {r['skip_agents']}")
    print(f"  使用: {r['used_agents']}")
    print(f"  耗时: {r['total_time']:.2f}s")
