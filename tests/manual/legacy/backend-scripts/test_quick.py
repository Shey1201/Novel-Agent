import requests
import time

BASE = 'http://127.0.0.1:8000'

print('=== 简化功能测试 ===')

# 测试1: 健康检查
r = requests.get(f'{BASE}/api/health', timeout=10)
print(f'1. 健康检查: {r.status_code} - {r.json().get("status")}')

# 测试2: 冲突分析 (正确格式)
print()
print('2. 冲突分析测试...')
data = {'text': '主角走在黑暗的山洞里，突然发现前方有一只巨大的怪物。'}
r = requests.post(f'{BASE}/api/analysis/conflict/analyze', json=data, timeout=30)
print(f'   状态: {r.status_code}')
if r.status_code == 200:
    result = r.json()
    print(f'   冲突分数: {result.get("score")}')
    print(f'   冲突点: {len(result.get("conflicts", []))} 个')
else:
    print(f'   错误: {r.text[:100]}')

# 测试3: 缓存预热 (正确格式)
print()
print('3. 缓存预热测试...')
data = {'data': {'test_key': 'test_value'}, 'ttl': 3600}
r = requests.post(f'{BASE}/api/cache/warmup', json=data, timeout=10)
print(f'   状态: {r.status_code}')
if r.status_code == 200:
    print(f'   成功')
else:
    print(f'   错误: {r.text[:100]}')

# 测试4: 质量分析
print()
print('4. 质量分析测试...')
data = {'text': '这是一个测试段落。主角走在街上，阳光明媚。他遇到了一个朋友。'}
r = requests.post(f'{BASE}/api/analysis/quality/analyze', json=data, timeout=30)
print(f'   状态: {r.status_code}')
if r.status_code == 200:
    result = r.json()
    print(f'   质量分数: {result.get("overall_score")}')
else:
    print(f'   错误: {r.text[:100]}')

# 测试5: 章节生成
print()
print('5. 章节生成测试...')
data = {'outline': '勇敢的少年在山洞发现神秘力量', 'story_id': 'test-story'}
r = requests.post(f'{BASE}/api/generate_chapter', json=data, timeout=120)
print(f'   状态: {r.status_code}')
if r.status_code == 200:
    result = r.json()
    wc = result.get('word_count', {})
    print(f'   最终字数: {wc.get("final", 0)}')
    print(f'   Agent日志: {len(result.get("agent_logs", []))} 条')
else:
    print(f'   错误: {r.text[:100]}')

print()
print('=== 测试完成 ===')
