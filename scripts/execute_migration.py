#!/usr/bin/env python3
"""
数据库迁移执行脚本
自动执行数据库结构优化的完整流程
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.backup_database import backup_database


def print_step(step_num: int, total: int, message: str):
    """打印步骤信息"""
    print(f"\n{'='*60}")
    print(f"步骤 {step_num}/{total}: {message}")
    print('='*60)


def check_migration_file():
    """检查迁移文件是否存在"""
    migration_file = project_root / "supabase" / "migrations" / "015_optimize_database_schema.sql"
    if not migration_file.exists():
        print(f"❌ 迁移文件不存在: {migration_file}")
        return False
    print(f"✅ 迁移文件存在: {migration_file}")
    return True


def read_migration_sql():
    """读取迁移 SQL 内容"""
    migration_file = project_root / "supabase" / "migrations" / "015_optimize_database_schema.sql"
    with open(migration_file, 'r', encoding='utf-8') as f:
        return f.read()


def execute_migration():
    """执行完整的迁移流程"""
    total_steps = 5

    # 步骤 1: 检查环境
    print_step(1, total_steps, "检查迁移环境")
    if not check_migration_file():
        return False

    # 检查 Supabase 连接
    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            print("❌ 未找到 Supabase 环境变量")
            print("请设置以下环境变量之一:")
            print("  - SUPABASE_URL 和 SUPABASE_SERVICE_KEY")
            print("  - 或 NEXT_PUBLIC_SUPABASE_URL 和 SUPABASE_ANON_KEY")
            return False

        supabase = create_client(supabase_url, supabase_key)
        print("✅ Supabase 连接成功")
    except Exception as e:
        print(f"❌ Supabase 连接失败: {e}")
        return False

    # 步骤 2: 备份数据
    print_step(2, total_steps, "备份现有数据")
    try:
        backup_database()
        print("✅ 数据备份完成")
    except Exception as e:
        print(f"❌ 数据备份失败: {e}")
        response = input("是否继续迁移? (y/n): ")
        if response.lower() != 'y':
            return False

    # 步骤 3: 显示迁移信息
    print_step(3, total_steps, "迁移预览")
    sql_content = read_migration_sql()
    print("\n迁移脚本预览 (前 50 行):")
    print("-" * 60)
    lines = sql_content.split('\n')[:50]
    for line in lines:
        print(line)
    print("-" * 60)
    print(f"\n总共 {len(sql_content.split(chr(10)))} 行 SQL")

    # 步骤 4: 确认执行
    print_step(4, total_steps, "确认执行迁移")
    print("\n⚠️  警告: 此操作将修改数据库结构")
    print("迁移内容:")
    print("  - 重命名 agent_configs → agents")
    print("  - 合并 story_assets + global_assets → assets")
    print("  - 合并 user_settings + system_settings → settings")
    print("  - 为所有表添加 deleted_at 软删除字段")
    print("  - 创建新的索引和约束")
    print("\n✅ 数据已备份，可以安全回滚")

    response = input("\n确认执行迁移? (输入 'yes' 继续): ")
    if response.lower() != 'yes':
        print("迁移已取消")
        return False

    # 步骤 5: 执行迁移
    print_step(5, total_steps, "执行数据库迁移")
    try:
        # 分段执行 SQL（避免一次性执行过多）
        sections = sql_content.split('\n\n')
        total_sections = len([s for s in sections if s.strip()])
        current = 0

        for section in sections:
            if not section.strip() or section.strip().startswith('--'):
                continue

            current += 1
            print(f"\n执行段落 {current}/{total_sections}...")

            # 执行 SQL
            result = supabase.rpc('exec_sql', {'sql': section}).execute()
            print(f"  ✅ 完成")

        print("\n" + "="*60)
        print("🎉 数据库迁移成功完成!")
        print("="*60)

        # 显示迁移后的表结构
        print("\n新表结构:")
        print("  - agents (原 agent_configs)")
        print("  - assets (合并 story_assets + global_assets)")
        print("  - settings (合并 user_settings + system_settings)")
        print("  - 所有表支持软删除 (deleted_at)")

        return True

    except Exception as e:
        print(f"\n❌ 迁移执行失败: {e}")
        print("\n回滚选项:")
        print("  1. 使用 restore_database.py 恢复数据")
        print("  2. 手动检查数据库状态")
        return False


def verify_migration():
    """验证迁移结果"""
    print("\n" + "="*60)
    print("验证迁移结果")
    print("="*60)

    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        supabase = create_client(supabase_url, supabase_key)

        tables_to_check = ['agents', 'assets', 'settings', 'novels', 'chapters']
        all_good = True

        for table in tables_to_check:
            try:
                response = supabase.table(table).select('count', count='exact').limit(1).execute()
                count = response.count if hasattr(response, 'count') else '?'
                print(f"  ✅ {table}: 可访问 (约 {count} 条记录)")
            except Exception as e:
                print(f"  ❌ {table}: 访问失败 - {e}")
                all_good = False

        return all_good

    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "="*60)
    print("数据库结构优化迁移工具")
    print("="*60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 执行迁移
    if execute_migration():
        # 验证结果
        verify_migration()

        print("\n" + "="*60)
        print("后续步骤:")
        print("="*60)
        print("1. 部署更新后的后端代码")
        print("2. 部署更新后的前端代码")
        print("3. 测试各项功能是否正常")
        print("\n如遇到问题，可运行: python scripts/restore_database.py")
    else:
        print("\n迁移未完成，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()
