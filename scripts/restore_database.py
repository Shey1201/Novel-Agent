#!/usr/bin/env python3
"""
数据库恢复脚本
从 JSON 备份文件恢复数据
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime

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
    sys.exit(1)


def restore_table(supabase, table_name: str, data: list, dry_run: bool = False) -> bool:
    """恢复单个表"""
    print(f"Restoring {table_name} ({len(data)} rows)...")
    
    if dry_run:
        print(f"  [DRY RUN] Would insert {len(data)} rows")
        return True
    
    try:
        # 分批插入，避免一次性插入过多数据
        batch_size = 100
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            supabase.table(table_name).insert(batch).execute()
        
        print(f"  ✓ Restored {len(data)} rows")
        return True
    except Exception as e:
        print(f"  ✗ Error restoring {table_name}: {e}")
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Restore database from backup")
    parser.add_argument("backup_file", help="Path to backup JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Preview without restoring")
    parser.add_argument("--tables", nargs="+", help="Specific tables to restore")
    args = parser.parse_args()
    
    # 读取备份文件
    backup_path = Path(args.backup_file)
    if not backup_path.exists():
        print(f"Error: Backup file not found: {backup_path}")
        sys.exit(1)
    
    with open(backup_path, "r", encoding="utf-8") as f:
        backup_data = json.load(f)
    
    print("=" * 60)
    print("Database Restore Tool")
    print("=" * 60)
    print(f"Backup file: {backup_path}")
    print(f"Backup timestamp: {backup_data.get('timestamp', 'Unknown')}")
    print(f"Dry run: {args.dry_run}")
    print("=" * 60)
    
    # 创建 Supabase 客户端
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✓ Connected to Supabase")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        sys.exit(1)
    
    # 确定要恢复的表
    tables_to_restore = args.tables or list(backup_data["tables"].keys())
    
    # 恢复数据
    success_count = 0
    fail_count = 0
    
    for table_name in tables_to_restore:
        if table_name not in backup_data["tables"]:
            print(f"⚠ Table {table_name} not found in backup")
            continue
        
        table_data = backup_data["tables"][table_name]
        if restore_table(supabase, table_name, table_data["data"], args.dry_run):
            success_count += 1
        else:
            fail_count += 1
    
    print("=" * 60)
    print("Restore Summary")
    print("=" * 60)
    print(f"Tables processed: {success_count + fail_count}")
    print(f"Success: {success_count}")
    print(f"Failed: {fail_count}")
    
    if args.dry_run:
        print("\n[DRY RUN] No data was actually restored")
        print("Remove --dry-run to perform actual restore")
    else:
        print("\n✓ Restore completed!")


if __name__ == "__main__":
    main()
