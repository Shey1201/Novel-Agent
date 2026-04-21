import requests
import time
BASE = 'http://127.0.0.1:8000'

print('=== 正确格式的深度功能测试 ===')
print()

# 测试1: 健康检查
r = requests.get(f'{BASE}/api/health')
print(f'1. 健康检查: {r.status_code} OK')

# 测试2: 章节生成
print()
print('2. 章节生成测试 (带LLM)...')
data = {
    'outline': '一个勇敢的少年在山洞中发现神秘力量的冒险故事',
    'story_id': 'test-func-story'
}
start = time.time()
try:
    r = requests.post(f'{BASE}/api/generate_chapter', json=data, timeout=120)
    elapsed = time.time() - start
    print(f'   状态: {r.status_code}')
    print(f'   耗时: {elapsed:.1f}秒')
    if r.status_code == 200:
        result = r.json()
        wc = result.get('word_count', {})
        print(f'   字数统计:')
        print(f'     - 输入: {wc.get("input", 0)}')
        print(f'     - 大纲: {wc.get("plan", 0)}')
        print(f'     - 草稿: {wc.get("draft", 0)}')
        print(f'     - 编辑: {wc.get("edited", 0)}')
        print(f'     - 最终: {wc.get("final", 0)}')
        print(f'   Agent日志: {len(result.get("agent_logs", []))} 条')
    else:
        print(f'   错误: {r.text[:200]}')
except Exception as e:
    print(f'   错误: {str(e)[:100]}')

# 测试3: 创建小说
print()
print('3. 创建小说测试...')
novel_data = {
    'title': '功能测试小说',
    'description': '这是一本用于功能测试的小说'
}
r = requests.post(f'{BASE}/api/novels', json=novel_data)
print(f'   状态: {r.status_code}')
if r.status_code in [200, 201]:
    novel = r.json()
    novel_id = novel.get('id')
    print(f'   小说ID: {novel_id}')
    
    # 测试4: 获取章节
    print()
    print('4. 获取章节列表...')
    r = requests.get(f'{BASE}/api/novels/{novel_id}/chapters')
    print(f'   状态: {r.status_code}')
    chapters = r.json() if r.status_code == 200 else []
    print(f'   章节数: {len(chapters)}')

# 测试5: 冲突分析 (正确格式)
print()
print('5. 冲突分析测试 (正确格式)...')
# 正确的参数: text 是字符串，不是 chapters 数组
conflict_data = {
    'text': '主角走在黑暗的山洞里，突然发现前方有一只巨大的怪物。主角害怕极了，但他知道必须面对它。他深吸一口气，冲向怪物，与它展开了激烈的战斗。'
}
r = requests.post(f'{BASE}/api/analysis/conflict/analyze', json=conflict_data)
print(f'   状态: {r.status_code}')
if r.status_code == 200:
    result = r.json()
    print(f'   冲突分数: {result.get("score")}')
    print(f'   冲突点数量: {len(result.get("conflicts", []))}')
else:
    print(f'   错误: {r.text[:200]}')

# 测试6: 快速冲突分数
print()
print('6. 快速冲突分数测试...')
conflict_data = {
    'text': '敌人出现了，主角必须战斗。战斗非常激烈，双方都受伤了。最终主角胜利了。'
}
r = requests.post(f'{BASE}/api/analysis/conflict/quick-score', json=conflict_data)
print(f'   状态: {r.status_code}')
if r.status_code == 200:
    result = r.json()
    print(f'   分数: {result}')
else:
    print(f'   错误: {r.text[:200]}')

# 测试7: 缓存预热 (正确格式)
print()
print('7. 缓存预热测试 (正确格式)...')
warmup_data = {
    'data': {'test_key': 'test_value'},
    'ttl': 3600
}
r = requests.post(f'{BASE}/api/cache/warmup', json=warmup_data)
print(f'   状态: {r.status_code}')
if r.status_code == 200:
    result = r.json()
    print(f'   结果: {result}')
else:
    print(f'   错误: {r.text[:200]}')

# 测试8: Agent房间
print()
print('8. Agent房间测试...')
r = requests.get(f'{BASE}/api/agent-room/narrative/report/test-novel')
print(f'   状态: {r.status_code}')

# 测试9: 推理历史
print()
print('9. 推理历史测试...')
r = requests.get(f'{BASE}/api/agent-room/reasoning/history')
print(f'   状态: {r.status_code}')

# 测试10: 前瞻统计
print()
print('10. 前瞻统计测试...')
r = requests.get(f'{BASE}/api/analysis/foreshadowing/stats')
print(f'   状态: {r.status_code}')

# 测试11: 创建技能
print()
print('11. 创建技能测试...')
skill_data = {
    'name': '功能测试技能',
    'description': '这是一个测试技能',
    'category_id': None
}
r = requests.post(f'{BASE}/api/skills', json=skill_data)
print(f'   状态: {r.status_code}')
if r.status_code in [200, 201]:
    skill = r.json()
    skill_id = skill.get('id')
    print(f'   技能ID: {skill_id}')

# 测试12: 质量分析
print()
print('12. 质量分析测试...')
quality_data = {
    'text': '这是一个测试段落。主角走在街上，阳光明媚。他遇到了一个朋友，他们一起去了咖啡馆。'
}
r = requests.post(f'{BASE}/api/analysis/quality/analyze', json=quality_data)
print(f'   状态: {r.status_code}')
if r.status_code == 200:
    result = r.json()
    print(f'   质量分数: {result.get("overall_score")}')
else:
    print(f'   错误: {r.text[:200]}')

print()
print('=== 正确格式的深度功能测试完成 ===')
