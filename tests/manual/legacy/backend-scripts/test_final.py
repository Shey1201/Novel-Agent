import requests

BASE = 'http://127.0.0.1:8000'

print('=== 最终验证 ===')

# 测试1: 健康检查
r = requests.get(f'{BASE}/api/health', timeout=10)
print(f'1. 健康检查: {r.status_code} - {r.json().get("status")}')

# 测试2: 冲突分析
print()
print('2. 冲突分析...')
data = {'text': '主角走在黑暗的山洞里，突然发现前方有一只巨大的怪物。'}
r = requests.post(f'{BASE}/api/analysis/conflict/analyze', json=data, timeout=30)
print(f'   状态: {r.status_code}')
if r.status_code == 200:
    result = r.json()
    print(f'   冲突分数: {result.get("score")}')
else:
    print(f'   错误: {r.text[:100]}')

# 测试3: 缓存预热
print()
print('3. 缓存预热...')
data = {'data': {'test_key': 'test_value'}, 'ttl': 3600}
r = requests.post(f'{BASE}/api/cache/warmup', json=data, timeout=10)
print(f'   状态: {r.status_code}')
if r.status_code == 200:
    result = r.json()
    print(f'   结果: {result.get("message")}')
else:
    print(f'   错误: {r.text[:100]}')

# 测试4: 前瞻分析
print()
print('4. 前瞻分析...')
r = requests.get(f'{BASE}/api/analysis/foreshadowing/stats', timeout=10)
print(f'   状态: {r.status_code}')

# 测试5: Agent配置
print()
print('5. Agent配置...')
r = requests.get(f'{BASE}/api/agents/configs', timeout=10)
print(f'   状态: {r.status_code}')
if r.status_code == 200:
    agents = r.json()
    print(f'   Agent数量: {len(agents)}')

# 测试6: 小说列表
print()
print('6. 小说列表...')
r = requests.get(f'{BASE}/api/novels', timeout=10)
print(f'   状态: {r.status_code}')
if r.status_code == 200:
    novels = r.json()
    print(f'   小说数量: {len(novels)}')

print()
print('=== 验证完成 ===')
