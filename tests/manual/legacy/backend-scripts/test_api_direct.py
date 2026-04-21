"""
直接使用 OpenAI SDK 测试 API 响应时间
"""
import os
import time
import openai

print("=" * 60)
print("  Direct API Test - DeepSeek API")
print("=" * 60)

# 从环境变量获取配置
api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL") or "https://api.deepseek.com/v1"

if not api_key:
    # 尝试从 .env 文件读取
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")

print(f"\nAPI Key: {api_key[:10]}..." if api_key else "No API Key found")
print(f"Base URL: {base_url}")

if not api_key:
    print("\nError: No API key found!")
    exit(1)

# 创建客户端
client = openai.OpenAI(api_key=api_key, base_url=base_url)

# 测试 1: 简单的聊天
print("\n1. Test Simple Chat...")
messages = [{"role": "user", "content": "你好，请用一句话介绍自己"}]

start = time.time()
try:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        max_tokens=100
    )
    elapsed = time.time() - start
    print(f"   Time: {elapsed:.2f}s")
    print(f"   Response: {response.choices[0].message.content[:50]}...")
except Exception as e:
    print(f"   Error: {e}")
    elapsed = 0

# 测试 2: 写作任务
print("\n2. Test Writing Task...")
messages = [{"role": "user", "content": "请用100字介绍春天的美景"}]

start = time.time()
try:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        max_tokens=200
    )
    elapsed = time.time() - start
    print(f"   Time: {elapsed:.2f}s")
    print(f"   Response: {response.choices[0].message.content[:100]}...")
except Exception as e:
    print(f"   Error: {e}")

# 测试 3: 规划任务
print("\n3. Test Planning Task...")
messages = [{"role": "user", "content": "请为一个科幻小说设计3个关键情节点"}]

start = time.time()
try:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        max_tokens=300
    )
    elapsed = time.time() - start
    print(f"   Time: {elapsed:.2f}s")
    print(f"   Response: {response.choices[0].message.content[:100]}...")
except Exception as e:
    print(f"   Error: {e}")

# 测试 4: 完整章节生成模拟
print("\n4. Full Chapter Generation Simulation...")
print("   Simulating 5-agent workflow...")

total_start = time.time()

# Agent 1: Planner
messages = [{"role": "user", "content": "写一个关于青春成长的故事大纲，包含主题、角色和结构"}]
start = time.time()
response = client.chat.completions.create(model="deepseek-chat", messages=messages, max_tokens=500)
plan_time = time.time() - start
print(f"   [1] Planner: {plan_time:.2f}s")

# Agent 2: Writer
messages = [{"role": "user", "content": f"根据以下大纲写一个1000字的章节：\n{response.choices[0].message.content[:500]}"}]
start = time.time()
response = client.chat.completions.create(model="deepseek-chat", messages=messages, max_tokens=1500)
write_time = time.time() - start
print(f"   [2] Writer: {write_time:.2f}s")

# Agent 3: Conflict
messages = [{"role": "user", "content": f"分析以下章节，提供冲突增强建议：\n{response.choices[0].message.content[:500]}"}]
start = time.time()
response = client.chat.completions.create(model="deepseek-chat", messages=messages, max_tokens=300)
conflict_time = time.time() - start
print(f"   [3] Conflict: {conflict_time:.2f}s")

# Agent 4: Editor
messages = [{"role": "user", "content": f"编辑并改进以下章节：\n{response.choices[0].message.content[:300]}"}]
start = time.time()
response = client.chat.completions.create(model="deepseek-chat", messages=messages, max_tokens=1500)
edit_time = time.time() - start
print(f"   [4] Editor: {edit_time:.2f}s")

# Agent 5: Summary
messages = [{"role": "user", "content": f"为以下章节写一个50字的摘要：\n{response.choices[0].message.content[:500]}"}]
start = time.time()
response = client.chat.completions.create(model="deepseek-chat", messages=messages, max_tokens=100)
summary_time = time.time() - start
print(f"   [5] Summary: {summary_time:.2f}s")

total_time = time.time() - total_start

print(f"\n{'='*60}")
print(f"  Total Time: {total_time:.2f}s")
print(f"  Breakdown:")
print(f"    Planner:  {plan_time:.2f}s ({plan_time/total_time*100:.1f}%)")
print(f"    Writer:   {write_time:.2f}s ({write_time/total_time*100:.1f}%)")
print(f"    Conflict: {conflict_time:.2f}s ({conflict_time/total_time*100:.1f}%)")
print(f"    Editor:   {edit_time:.2f}s ({edit_time/total_time*100:.1f}%)")
print(f"    Summary:  {summary_time:.2f}s ({summary_time/total_time*100:.1f}%)")
print(f"{'='*60}")