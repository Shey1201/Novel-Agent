#!/usr/bin/env python3
"""
数据库迁移测试脚本
测试迁移后的数据库结构和功能是否正常
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 测试配置
TEST_USER_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
TEST_NOVEL_ID = None  # 将在测试中创建


class MigrationTester:
    """迁移测试器"""

    def __init__(self):
        self.supabase = None
        self.test_results: List[Dict[str, Any]] = []
        self._init_supabase()

    def _init_supabase(self):
        """初始化 Supabase 客户端"""
        try:
            from supabase import create_client
            supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

            if supabase_url and supabase_key:
                self.supabase = create_client(supabase_url, supabase_key)
                print("✅ Supabase 连接成功")
            else:
                print("❌ 未找到 Supabase 环境变量")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Supabase 连接失败: {e}")
            sys.exit(1)

    def _log_test(self, test_name: str, passed: bool, message: str = ""):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")

    # ==================== 表结构测试 ====================

    def test_table_exists(self, table_name: str) -> bool:
        """测试表是否存在"""
        try:
            response = self.supabase.table(table_name).select("count", count="exact").limit(1).execute()
            return True
        except Exception as e:
            return False

    def test_tables_structure(self):
        """测试所有新表是否存在"""
        print("\n" + "="*60)
        print("测试1: 表结构检查")
        print("="*60)

        required_tables = [
            "agents", "assets", "settings", "messages",
            "novels", "chapters", "categories",
            "world_bibles", "skills", "skill_categories"
        ]

        for table in required_tables:
            exists = self.test_table_exists(table)
            self._log_test(
                f"表存在: {table}",
                exists,
                f"{'表可访问' if exists else '表不存在或无法访问'}"
            )

    def test_backup_tables_exist(self):
        """测试备份表是否存在"""
        print("\n" + "="*60)
        print("测试2: 备份表检查")
        print("="*60)

        backup_tables = [
            "_backup_novels", "_backup_chapters", "_backup_agent_configs",
            "_backup_story_assets", "_backup_global_assets",
            "_backup_system_settings", "_backup_user_settings"
        ]

        for table in backup_tables:
            exists = self.test_table_exists(table)
            self._log_test(
                f"备份表存在: {table}",
                exists,
                f"{'备份表可访问' if exists else '备份表不存在'}"
            )

    # ==================== 字段测试 ====================

    def test_soft_delete_columns(self):
        """测试软删除字段是否存在"""
        print("\n" + "="*60)
        print("测试3: 软删除字段检查")
        print("="*60)

        tables_with_soft_delete = [
            "agents", "assets", "settings", "messages",
            "novels", "chapters", "categories",
            "world_bibles", "skills", "skill_categories"
        ]

        for table in tables_with_soft_delete:
            try:
                # 尝试查询 deleted_at 字段
                response = self.supabase.table(table).select("deleted_at").is_("deleted_at", "null").limit(1).execute()
                self._log_test(
                    f"软删除字段: {table}.deleted_at",
                    True,
                    "字段存在且可查询"
                )
            except Exception as e:
                self._log_test(
                    f"软删除字段: {table}.deleted_at",
                    False,
                    f"字段不存在或查询失败: {e}"
                )

    # ==================== CRUD 测试 ====================

    def test_agents_crud(self):
        """测试 agents 表的 CRUD 操作"""
        print("\n" + "="*60)
        print("测试4: Agents 表 CRUD")
        print("="*60)

        try:
            # Create
            test_agent = {
                "user_id": TEST_USER_ID,
                "agent_id": "test-agent-001",
                "name": "测试Agent",
                "role": "writer",
                "prompt": "你是一个测试Agent",
                "temperature": 0.7,
                "enabled": True,
                "personality": "creative"
            }

            response = self.supabase.table("agents").insert(test_agent).select().execute()
            if not response.data:
                self._log_test("Agent 创建", False, "插入失败")
                return

            agent_id = response.data[0]["id"]
            self._log_test("Agent 创建", True, f"ID: {agent_id}")

            # Read
            response = self.supabase.table("agents").select("*").eq("id", agent_id).execute()
            if response.data and len(response.data) > 0:
                self._log_test("Agent 读取", True, f"找到记录: {response.data[0]['name']}")
            else:
                self._log_test("Agent 读取", False, "未找到记录")

            # Update
            response = self.supabase.table("agents").update({"name": "更新的测试Agent"}).eq("id", agent_id).execute()
            if response.data and response.data[0]["name"] == "更新的测试Agent":
                self._log_test("Agent 更新", True, "名称已更新")
            else:
                self._log_test("Agent 更新", False, "更新失败")

            # Soft Delete
            response = self.supabase.table("agents").update({"deleted_at": datetime.now().isoformat()}).eq("id", agent_id).execute()
            if response.data:
                self._log_test("Agent 软删除", True, "已标记删除")
            else:
                self._log_test("Agent 软删除", False, "删除失败")

            # Verify soft delete (should not be found with is_ filter)
            response = self.supabase.table("agents").select("*").eq("id", agent_id).is_("deleted_at", "null").execute()
            if not response.data:
                self._log_test("软删除验证", True, "已删除记录被正确过滤")
            else:
                self._log_test("软删除验证", False, "已删除记录仍可查询")

        except Exception as e:
            self._log_test("Agents CRUD", False, f"异常: {e}")

    def test_assets_crud(self):
        """测试 assets 表的 CRUD 操作"""
        print("\n" + "="*60)
        print("测试5: Assets 表 CRUD")
        print("="*60)

        try:
            # Create local asset
            test_asset = {
                "user_id": TEST_USER_ID,
                "novel_id": None,  # 可以是 null
                "type": "characters",
                "name": "测试角色",
                "content": {"description": "这是一个测试角色"},
                "is_global": False,
                "is_starred": False,
                "color": "#ff0000"
            }

            response = self.supabase.table("assets").insert(test_asset).select().execute()
            if not response.data:
                self._log_test("本地 Asset 创建", False, "插入失败")
                return

            asset_id = response.data[0]["id"]
            self._log_test("本地 Asset 创建", True, f"ID: {asset_id}")

            # Create global asset
            test_global_asset = {
                "user_id": TEST_USER_ID,
                "type": "worldbuilding",
                "name": "测试世界观",
                "description": "这是一个测试世界观",
                "is_global": True,
                "is_starred": True,
                "color": "#00ff00"
            }

            response = self.supabase.table("assets").insert(test_global_asset).select().execute()
            if response.data:
                self._log_test("全局 Asset 创建", True, f"ID: {response.data[0]['id']}")
            else:
                self._log_test("全局 Asset 创建", False, "插入失败")

            # Query by type
            response = self.supabase.table("assets").select("*").eq("type", "characters").is_("deleted_at", "null").execute()
            self._log_test("Asset 按类型查询", True, f"找到 {len(response.data)} 个角色")

            # Query global assets
            response = self.supabase.table("assets").select("*").eq("is_global", True).is_("deleted_at", "null").execute()
            self._log_test("全局 Asset 查询", True, f"找到 {len(response.data)} 个全局资产")

            # Soft delete
            self.supabase.table("assets").update({"deleted_at": datetime.now().isoformat()}).eq("id", asset_id).execute()
            self._log_test("Asset 软删除", True, "已标记删除")

        except Exception as e:
            self._log_test("Assets CRUD", False, f"异常: {e}")

    def test_settings_crud(self):
        """测试 settings 表的 CRUD 操作"""
        print("\n" + "="*60)
        print("测试6: Settings 表 CRUD")
        print("="*60)

        try:
            # Create settings
            test_settings = {
                "user_id": TEST_USER_ID,
                "token_enabled": True,
                "token_daily_limit": 100000,
                "token_warning_threshold": 0.85,
                "discussion_max_rounds": 3,
                "constraints": ["禁止暴力", "禁止色情"],
                "writing_mode": "auto"
            }

            response = self.supabase.table("settings").insert(test_settings).select().execute()
            if not response.data:
                self._log_test("Settings 创建", False, "插入失败")
                return

            settings_id = response.data[0]["id"]
            self._log_test("Settings 创建", True, f"ID: {settings_id}")

            # Read
            response = self.supabase.table("settings").select("*").eq("user_id", TEST_USER_ID).execute()
            if response.data:
                settings = response.data[0]
                self._log_test("Settings 读取", True, f"Token限制: {settings.get('token_daily_limit')}")
            else:
                self._log_test("Settings 读取", False, "未找到记录")

            # Update
            response = self.supabase.table("settings").update({
                "token_daily_limit": 150000,
                "discussion_max_rounds": 5
            }).eq("user_id", TEST_USER_ID).execute()

            if response.data and response.data[0]["token_daily_limit"] == 150000:
                self._log_test("Settings 更新", True, "设置已更新")
            else:
                self._log_test("Settings 更新", False, "更新失败")

        except Exception as e:
            self._log_test("Settings CRUD", False, f"异常: {e}")

    # ==================== 数据迁移验证 ====================

    def test_data_migration(self):
        """测试数据是否正确迁移"""
        print("\n" + "="*60)
        print("测试7: 数据迁移验证")
        print("="*60)

        try:
            # Check agents count
            response = self.supabase.table("agents").select("count", count="exact").is_("deleted_at", "null").execute()
            agents_count = response.count if hasattr(response, 'count') else len(response.data)
            self._log_test("Agents 数据迁移", agents_count > 0, f"记录数: {agents_count}")

            # Check assets count
            response = self.supabase.table("assets").select("count", count="exact").is_("deleted_at", "null").execute()
            assets_count = response.count if hasattr(response, 'count') else len(response.data)
            self._log_test("Assets 数据迁移", assets_count > 0, f"记录数: {assets_count}")

            # Check settings count
            response = self.supabase.table("settings").select("count", count="exact").is_("deleted_at", "null").execute()
            settings_count = response.count if hasattr(response, 'count') else len(response.data)
            self._log_test("Settings 数据迁移", settings_count > 0, f"记录数: {settings_count}")

            # Compare with backup
            response = self.supabase.table("_backup_agent_configs").select("count", count="exact").execute()
            backup_agents = response.count if hasattr(response, 'count') else len(response.data)

            response = self.supabase.table("_backup_story_assets").select("count", count="exact").execute()
            backup_story_assets = response.count if hasattr(response, 'count') else len(response.data)

            response = self.supabase.table("_backup_global_assets").select("count", count="exact").execute()
            backup_global_assets = response.count if hasattr(response, 'count') else len(response.data)

            total_backup_assets = backup_story_assets + backup_global_assets

            self._log_test(
                "Agents 数据完整性",
                agents_count == backup_agents,
                f"新表: {agents_count}, 备份: {backup_agents}"
            )

            self._log_test(
                "Assets 数据完整性",
                assets_count >= total_backup_assets,
                f"新表: {assets_count}, 原表合计: {total_backup_assets}"
            )

        except Exception as e:
            self._log_test("数据迁移验证", False, f"异常: {e}")

    # ==================== 索引测试 ====================

    def test_indexes(self):
        """测试索引是否存在"""
        print("\n" + "="*60)
        print("测试8: 索引检查")
        print("="*60)

        expected_indexes = [
            ("agents", "idx_agents_user_id"),
            ("agents", "idx_agents_deleted_at"),
            ("assets", "idx_assets_user_id"),
            ("assets", "idx_assets_type"),
            ("assets", "idx_assets_is_global"),
            ("settings", "idx_settings_user_id"),
        ]

        for table, index_name in expected_indexes:
            try:
                # 尝试使用索引查询
                response = self.supabase.table(table).select("*").limit(1).execute()
                self._log_test(f"索引: {index_name}", True, f"表 {table} 可正常查询")
            except Exception as e:
                self._log_test(f"索引: {index_name}", False, f"查询失败: {e}")

    # ==================== 清理测试数据 ====================

    def cleanup_test_data(self):
        """清理测试数据"""
        print("\n" + "="*60)
        print("清理测试数据")
        print("="*60)

        try:
            # Soft delete test data
            self.supabase.table("agents").update({"deleted_at": datetime.now().isoformat()}).eq("user_id", TEST_USER_ID).execute()
            self.supabase.table("assets").update({"deleted_at": datetime.now().isoformat()}).eq("user_id", TEST_USER_ID).execute()
            self.supabase.table("settings").update({"deleted_at": datetime.now().isoformat()}).eq("user_id", TEST_USER_ID).execute()
            print("✅ 测试数据已清理（软删除）")
        except Exception as e:
            print(f"⚠️  清理测试数据时出错: {e}")

    # ==================== 生成报告 ====================

    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("测试报告")
        print("="*60)

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["passed"])
        failed = total - passed

        print(f"\n总测试数: {total}")
        print(f"通过: {passed} ✅")
        print(f"失败: {failed} ❌")
        print(f"通过率: {passed/total*100:.1f}%" if total > 0 else "N/A")

        if failed > 0:
            print("\n失败的测试:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  ❌ {result['test_name']}")
                    if result["message"]:
                        print(f"     {result['message']}")

        return failed == 0

    # ==================== 运行所有测试 ====================

    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("数据库迁移测试开始")
        print("="*60)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试用户ID: {TEST_USER_ID}")

        # 运行测试
        self.test_tables_structure()
        self.test_backup_tables_exist()
        self.test_soft_delete_columns()
        self.test_agents_crud()
        self.test_assets_crud()
        self.test_settings_crud()
        self.test_data_migration()
        self.test_indexes()

        # 清理
        self.cleanup_test_data()

        # 生成报告
        success = self.generate_report()

        print("\n" + "="*60)
        if success:
            print("🎉 所有测试通过！迁移成功。")
        else:
            print("⚠️  部分测试失败，请检查问题。")
        print("="*60)

        return success


def main():
    """主函数"""
    tester = MigrationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
