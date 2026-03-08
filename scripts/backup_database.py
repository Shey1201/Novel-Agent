#!/usr/bin/env python3
"""
数据库备份脚本
在执行结构优化前，先导出所有数据为 JSON 格式
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加后端路径
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

try:
    from supabase import create_client
except ImportError:
    print("Error: supabase package not installed")
    print("Run: pip install supabase")
    sys.exit(1)

# 获取环境变量
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Supabase credentials not found")
    print("Please set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables")
    sys.exit(1)

# 要备份的表
TABLES = [
    "novels",
    "chapters",
    "categories",
    "agent_configs",
    "story_assets",
    "global_assets",
    "world_bibles",
    "skills",
    "skill_categories",
    "skill_constraints",
    "system_settings",
    "user_settings",
    "messages",
    "asset_versions",
    "novel_asset_mappings",
    "agent_skills",
    "novel_skill_mappings",
]


def backup_table(supabase, table_name: str) -> dict:
    """备份单个表"""
    print(f"Backing up {table_name}...")
    try:
        response = supabase.table(table_name).select("*").execute()
        data = response.data or []
        print(f"  ✓ {len(data)} rows backed up")
        return {
            "table_name": table_name,
            "row_count": len(data),
            "data": data,
        }
    except Exception as e:
        print(f"  ✗ Error backing up {table_name}: {e}")
        return {
            "table_name": table_name,
            "row_count": 0,
            "data": [],
            "error": str(e),
        }


def main():
    """主函数"""
    print("=" * 60)
    print("Database Backup Tool")
    print("=" * 60)
    print(f"Supabase URL: {SUPABASE_URL[:30]}...")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # 创建 Supabase 客户端
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✓ Connected to Supabase")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        sys.exit(1)
    
    # 备份所有表
    backup_data = {
        "timestamp": datetime.now().isoformat(),
        "supabase_url": SUPABASE_URL,
        "tables": {},
    }
    
    total_rows = 0
    for table_name in TABLES:
        result = backup_table(supabase, table_name)
        backup_data["tables"][table_name] = result
        total_rows += result["row_count"]
    
    # 保存备份文件
    backup_dir = Path(__file__).parent.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"database_backup_{timestamp}.json"
    
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    
    print("=" * 60)
    print("Backup Summary")
    print("=" * 60)
    print(f"Total tables: {len(TABLES)}")
    print(f"Total rows: {total_rows}")
    print(f"Backup file: {backup_file}")
    print("=" * 60)
    print("✓ Backup completed successfully!")
    
    # 显示每个表的统计
    print("\nTable Statistics:")
    for table_name, result in backup_data["tables"].items():
        status = "✓" if "error" not in result else "✗"
        print(f"  {status} {table_name}: {result['row_count']} rows")


if __name__ == "__main__":
    main()
