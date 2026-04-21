import requests
import json
BASE = 'http://127.0.0.1:8000'

print('=== 章节生成功能测试 ===')

# 测试生成章节
data = {
    'outline': '一个关于勇敢少年探索神秘山洞的故事',
    'story_id': 'test-story-001'
}

print('发送请求到 /api/generate_chapter...')
r = requests.post(f'{BASE}/api/generate_chapter', json=data, timeout=90)
print(f'状态码: {r.status_code}')

if r.status_code == 200:
    result = r.json()
    print('成功生成章节!')
    word_count = result.get('word_count', {})
    print(f'- 输入字数: {word_count.get("input", 0)}')
    print(f'- 大纲字数: {word_count.get("plan", 0)}')
    print(f'- 草稿字数: {word_count.get("draft", 0)}')
    print(f'- 编辑字数: {word_count.get("edited", 0)}')
    print(f'- 最终字数: {word_count.get("final", 0)}')
    print(f'- Agent日志: {len(result.get("agent_logs", []))} 条')
else:
    print(f'错误: {r.text[:500]}')