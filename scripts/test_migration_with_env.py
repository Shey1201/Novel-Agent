#!/usr/bin/env python3
"""
数据库迁移测试脚本（带环境变量）
"""

import os
import sys

# 设置环境变量
os.environ["SUPABASE_URL"] = "https://wzlzjhclzkrcosvkxsoa.supabase.co"
os.environ["SUPABASE_SERVICE_KEY"] = "sb_publishable_Df5CyfEUF0jIJ8fLUrOYmg_oAle57he"

# 导入并运行原测试
from test_migration import MigrationTester

def main():
    tester = MigrationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
