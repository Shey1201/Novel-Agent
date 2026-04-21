"""
简单测试脚本 - 测试 Agent API 响应时间
"""
import requests
import time
import json

BASE_URL = "http://127.0.0.1:8000"

print("=" * 60)
print("  测试 Agent 流程 API")
print("=" * 60)

# 测试健康检查
print("\n1. 测试健康检查...")
try:
    start = time.time()
    r = requests.get(f"{BASE_URL}/api/health", timeout=5)
    elapsed = (time.time() - start) * 1000
    print(f"   状态: {r.status_code}, 耗时: {elapsed:.0f}ms")
    print(f"   返回: {r.json()}")
except Exception as e:
    print(f"   错误: {e}")

# 测试 Agent 聊天
print("\n2. 测试 Agent 聊天...")
payload = {"message": "你好，请帮我写一个开头"}

try:
    start = time.time()
    r = requests.post(
        f"{BASE_URL}/api/agent/chat",
        json=payload,
        timeout=30
    )
    elapsed = (time.time() - start) * 1000
    print(f"   状态: {r.status_code}, 耗时: {elapsed:.0f}ms")
    if r.status_code == 200:
        result = r.json()
        print(f"   回复长度: {len(result.get('response', ''))} 字符")
except Exception as e:
    print(f"   错误: {e}")

# 测试章节生成
print("\n3. 测试章节生成...")
payload = {
    "outline": "一个关于成长的故事",
    "story_id": "test-001",
    "auto_confirm": True
}

try:
    start = time.time()
    r = requests.post(
        f"{BASE_URL}/api/generate_chapter",
        json=payload,
        timeout=120
    )
    elapsed = (time.time() - start) * 1000
    print(f"   状态: {r.status_code}, 耗时: {elapsed:.0f}ms ({elapsed/1000:.1f}秒)")
    
    if r.status_code == 200:
        result = r.json()
        print(f"   Plan 长度: {len(result.get('plan_text', ''))}")
        print(f"   Draft 长度: {len(result.get('draft_text', ''))}")
        print(f"   Final 长度: {len(result.get('final_text', ''))}")
        
        # 打印 agent logs
        logs = result.get("agent_logs", [])
        print(f"\n   Agent 执行日志 ({len(logs)} 个):")
        for log in logs:
            if isinstance(log, dict):
                print(f"     - {log.get('agent', 'unknown')}: {log.get('message', '')}")
except Exception as e:
    print(f"   错误: {e}")

print("\n" + "=" * 60)
print("  测试完成")
print("=" * 60)