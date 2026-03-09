#!/usr/bin/env python3
"""
检查后端环境变量配置
"""
import os

print("=" * 60)
print("环境变量检查")
print("=" * 60)

# 检查 Supabase 相关环境变量
env_vars = [
    "SUPABASE_URL",
    "NEXT_PUBLIC_SUPABASE_URL",
    "SUPABASE_SERVICE_KEY",
    "SUPABASE_ANON_KEY",
    "NEXT_PUBLIC_SUPABASE_ANON_KEY",
]

print("\nSupabase 环境变量:")
for var in env_vars:
    value = os.getenv(var)
    if value:
        # 只显示前20个字符
        display_value = value[:20] + "..." if len(value) > 20 else value
        print(f"  ✓ {var}: {display_value}")
    else:
        print(f"  ✗ {var}: 未设置")

# 检查关键变量
supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

print("\n" + "=" * 60)
if supabase_url and supabase_key:
    print("✓ 环境变量配置正确")
    print(f"  URL: {supabase_url[:30]}...")
    print(f"  KEY: {'已设置 (' + str(len(supabase_key)) + ' 字符)'}")
else:
    print("✗ 环境变量配置不完整!")
    if not supabase_url:
        print("  - 缺少 SUPABASE_URL 或 NEXT_PUBLIC_SUPABASE_URL")
    if not supabase_key:
        print("  - 缺少 SUPABASE_SERVICE_KEY 或 SUPABASE_ANON_KEY")
    print("\n请在 Railway 中设置以下环境变量:")
    print("  SUPABASE_URL=https://your-project.supabase.co")
    print("  SUPABASE_SERVICE_KEY=your-service-role-key")
print("=" * 60)

# 尝试连接 Supabase
try:
    from supabase import create_client
    if supabase_url and supabase_key:
        print("\n尝试连接 Supabase...")
        supabase = create_client(supabase_url, supabase_key)
        
        # 测试查询
        response = supabase.table("novels").select("count", count="exact").limit(1).execute()
        print(f"✓ 连接成功! 数据库中有 {response.count if hasattr(response, 'count') else '未知'} 本小说")
except Exception as e:
    print(f"\n✗ 连接失败: {e}")
