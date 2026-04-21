import requests
BASE = 'http://127.0.0.1:8000'

print('=== 服务器运行功能测试 ===')
print()

# 测试1: 健康检查
r = requests.get(f'{BASE}/api/health')
status = r.json().get('status')
print(f'1. 健康检查: {r.status_code} - {status}')

# 测试2: 小说列表
r = requests.get(f'{BASE}/api/novels')
novels = r.json()
print(f'2. 小说列表: {r.status_code} - {len(novels)} 个小说')

# 测试3: Agent配置
r = requests.get(f'{BASE}/api/agents/configs')
agents = r.json()
print(f'3. Agent配置: {r.status_code} - {len(agents)} 个Agent')
for a in agents[:3]:
    print(f'   - {a.get("agent_id")}: {a.get("name")}')

# 测试4: 技能列表
r = requests.get(f'{BASE}/api/skills')
skills = r.json()
print(f'4. 技能列表: {r.status_code} - {len(skills)} 个技能')

# 测试5: 系统设置
r = requests.get(f'{BASE}/api/settings/all')
settings = r.json()
print(f'5. 系统设置: {r.status_code}')
print(f'   - token_enabled: {settings.get("token_enabled")}')
print(f'   - token_daily_limit: {settings.get("token_daily_limit")}')

# 测试6: 资产列表
r = requests.get(f'{BASE}/api/assets/all')
assets = r.json()
print(f'6. 资产列表: {r.status_code} - {len(assets)} 个资产')

# 测试7: 世界设定
r = requests.get(f'{BASE}/api/world/test-story')
print(f'7. 世界设定: {r.status_code}')

# 测试8: 缓存统计
r = requests.get(f'{BASE}/api/cache/stats')
print(f'8. 缓存统计: {r.status_code}')

# 测试9: 消息列表
r = requests.get(f'{BASE}/api/messages')
messages = r.json()
print(f'9. 消息列表: {r.status_code} - {len(messages)} 条消息')

# 测试10: 分类列表
r = requests.get(f'{BASE}/api/categories')
categories = r.json()
print(f'10. 分类列表: {r.status_code} - {len(categories)} 个分类')

print()
print('=== 测试完成 ===')
