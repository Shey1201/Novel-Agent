# -*- coding: utf-8 -*-
import sys
import requests
import json

# Fix stdout encoding
sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

# Test 1: Health
print("=== Test 1: Health ===")
r = requests.get('http://127.0.0.1:8000/api/health')
print(f"Status: {r.status_code}, Response: {r.json()}")

# Test 2: AI Config
print("\n=== Test 2: AI Config ===")
r = requests.get('http://127.0.0.1:8000/api/settings/ai')
print(f"Status: {r.status_code}, Response: {r.json()}")

# Test 3: Novels
print("\n=== Test 3: Novels ===")
r = requests.get('http://127.0.0.1:8000/api/novels')
print(f"Status: {r.status_code}, Response count: {len(r.json())}")

# Test 4: Agent Chat (main test)
print("\n=== Test 4: Agent Chat ===")
story_id = "d342d8c1-2ebc-47ce-8ca1-e1a4882834a6"
r = requests.post('http://127.0.0.1:8000/api/agent/chat', json={
    "message": "hello",
    "story_id": story_id
}, timeout=30)
print(f"Status: {r.status_code}")
try:
    data = r.json()
    print(f"Response keys: {data.keys()}")
    # Print key info
    if 'final_text' in data:
        print(f"final_text: {data['final_text'][:200]}...")
    if 'agent_logs' in data:
        print(f"agent_logs count: {len(data['agent_logs'])}")
except:
    print(f"Response (raw): {r.text[:500]}")

# Test 5: Context Pool Stats
print("\n=== Test 5: Context Pool Stats ===")
try:
    r = requests.get('http://127.0.0.1:8000/api/cache/context-pool/stats')
    print(f"Status: {r.status_code}, Response: {r.json()}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== Test Complete ===")
