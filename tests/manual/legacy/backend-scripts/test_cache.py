import requests
BASE = 'http://127.0.0.1:8000'
print('=== 最终验证 ===')
# 测试1: 健康检查
r = requests.get(f'{BASE}/api/health', timeout=10)
print(f'1. 健康检查: {r.status_code} - {r.json().get("status")}')
# 测试2: 缓存预热
print()
print('2. 缓存预热...')
data = {'data': {'test_key': 'test_value'}, 'ttl': 3600}
r = requests.post(f'{BASE}/api/cache/warmup', json=data, timeout=10)
print(f'   状态: {r.status_code}')
if r.status_code == 200:
    result = r.json()
    print(f'   结果: {result}')
else:
    print(f'   错误: {r.text[:200]}')
print()
print('=== 验证完成 ===')
