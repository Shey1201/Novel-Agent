# -*- coding: utf-8 -*-
import sys
import requests

sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

base = 'http://127.0.0.1:8000'
tests = [
    ("GET", "/api/health", None),
    ("GET", "/api/settings/ai", None),
    ("GET", "/api/novels", None),
    ("GET", "/api/agents/configs", None),
    ("GET", "/api/skills", None),
    ("GET", "/api/categories", None),
    ("GET", "/api/memory/d342d8c1-2ebc-47ce-8ca1-e1a4882834a6", None),
]

print("=== Extended API Tests ===\n")
for method, path, body in tests:
    try:
        if method == "GET":
            r = requests.get(f"{base}{path}", timeout=10)
        else:
            r = requests.post(f"{base}{path}", json=body, timeout=10)
        
        status = "✅" if r.status_code < 400 else "❌"
        print(f"{status} {method} {path}")
        print(f"   Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict):
                print(f"   Keys: {list(data.keys())[:5]}")
            elif isinstance(data, list):
                print(f"   Count: {len(data)}")
        print()
    except Exception as e:
        print(f"❌ {method} {path}: {str(e)[:50]}\n")
