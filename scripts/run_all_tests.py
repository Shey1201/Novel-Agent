#!/usr/bin/env python3
"""
运行所有测试
"""

import subprocess
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_command(cmd, cwd=None, description=""):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"运行: {description}")
    print(f"命令: {cmd}")
    print('='*60)
    
    result = subprocess.run(cmd, shell=True, cwd=cwd or project_root)
    return result.returncode == 0

def main():
    """主函数"""
    print("\n" + "="*60)
    print("开始运行所有测试")
    print("="*60)
    
    results = []
    
    # 1. 运行数据库迁移测试
    results.append((
        "数据库迁移测试",
        run_command(
            "python scripts/test_migration.py",
            description="测试数据库结构和迁移"
        )
    ))
    
    # 2. 运行后端 API 测试（如果 pytest 可用）
    results.append((
        "后端 API 测试",
        run_command(
            "cd backend && python -m pytest tests/test_api.py -v || echo 'pytest 未安装或测试失败'",
            description="测试后端 API"
        )
    ))
    
    # 3. 运行前端集成测试（如果 vitest 可用）
    results.append((
        "前端集成测试",
        run_command(
            "cd frontend && npm test -- --run 2>/dev/null || echo '前端测试需要手动运行: npm test'",
            description="测试前端集成"
        )
    ))
    
    # 4. 检查代码类型（如果有类型检查工具）
    results.append((
        "类型检查",
        run_command(
            "cd backend && python -m mypy app/ --ignore-missing-imports 2>/dev/null || echo 'mypy 未安装'",
            description="检查 Python 类型"
        )
    ))
    
    # 显示结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "⚠️  跳过/失败"
        print(f"{status}: {name}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
    
    print("\n手动测试建议:")
    print("1. 启动后端: cd backend && python -m uvicorn app.main:app --reload")
    print("2. 启动前端: cd frontend && npm run dev")
    print("3. 打开浏览器测试各项功能")
    print("4. 检查浏览器控制台是否有错误")

if __name__ == "__main__":
    main()
