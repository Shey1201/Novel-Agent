import requests
import time
BASE = 'http://127.0.0.1:8000'

print('=== 深度功能测试 ===')
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

# 测试5: 创建技能
print()
print('5. 创建技能测试...')
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

# 测试6: 缓存预热
print()
print('6. 缓存预热测试...')
r = requests.post(f'{BASE}/api/cache/warmup')
print(f'   状态: {r.status_code}')

# 测试7: 分析API
print()
print('7. 冲突分析测试...')
analysis_data = {
    'chapters': [
        {'title': '第1章', 'content': '主角发现了山洞'},
        {'title': '第2章', 'content': '主角获得了力量'}
    ]
}
r = requests.post(f'{BASE}/api/analysis/conflict/analyze', json=analysis_data)
print(f'   状态: {r.status_code}')

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

# 测试10: 分析统计
print()
print('10. 前瞻统计测试...')
r = requests.get(f'{BASE}/api/analysis/foreshadowing/stats')
print(f'   状态: {r.status_code}')

print()
print('=== 深度功能测试完成 ===')
