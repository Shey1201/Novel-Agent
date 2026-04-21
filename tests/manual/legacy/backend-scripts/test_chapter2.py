import requests
import json
BASE = 'http://127.0.0.1:8000'

# 测试章节生成
data = {'outline': '少年发现神秘山洞', 'story_id': 'test-1'}
r = requests.post(f'{BASE}/api/generate_chapter', json=data, timeout=60)
print(f'章节生成: {r.status_code}')

if r.status_code == 200:
    result = r.json()
    wc = result.get('word_count', {})
    print(f'输入: {wc.get("input", 0)} 字')
    print(f'大纲: {wc.get("plan", 0)} 字')
    print(f'草稿: {wc.get("draft", 0)} 字')
    print(f'编辑: {wc.get("edited", 0)} 字')
    print(f'最终: {wc.get("final", 0)} 字')
    print(f'Agent日志: {len(result.get("agent_logs", []))} 条')
elif r.status_code == 500:
    print(f'错误: {r.text[:200]}')