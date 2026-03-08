"""
Skill 存储管理模块 - 使用 Supabase
"""
import os
import sys
import subprocess
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.skill import Skill, SkillCategory, SkillConstraint, SkillTestResult

# 尝试导入 supabase，如果没有则使用本地存储作为回退
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    print("[SkillMemory] Failed to import supabase, attempting to install...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase", "-q"])
        from supabase import create_client
        SUPABASE_AVAILABLE = True
        print("[SkillMemory] Supabase installed and imported successfully")
    except Exception as e:
        print(f"[SkillMemory] Failed to install supabase: {e}")
        SUPABASE_AVAILABLE = False


def _process_constraints(raw_constraints: Any) -> List[Dict[str, Any]]:
    """处理从数据库读取的 constraints 数据"""
    if raw_constraints is None:
        return []
    elif isinstance(raw_constraints, dict):
        raw_constraints = [raw_constraints]
    elif not isinstance(raw_constraints, list):
        return []
    
    # 只保留 SkillConstraint 模型需要的字段
    filtered_constraints = []
    for constraint in raw_constraints:
        if isinstance(constraint, dict):
            filtered_constraints.append({
                "id": constraint.get("id"),
                "content": constraint.get("content"),
                "priority": constraint.get("priority"),
                "enabled": constraint.get("enabled", True)
            })
    return filtered_constraints


class SkillMemory:
    """技能存储管理器 - Supabase 版本"""

    def __init__(self):
        self.supabase = None
        self._initialized = False
        self._init_supabase()

    def _init_supabase(self):
        """初始化 Supabase 客户端"""
        if not SUPABASE_AVAILABLE:
            print("Warning: Supabase not available, skill management will be limited")
            return

        # 支持多种环境变量名（本地开发和 Vercel 部署）
        supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

        # 调试日志
        print(f"SkillMemory: Checking Supabase credentials...")
        print(f"  SUPABASE_URL: {'Set' if os.getenv('SUPABASE_URL') else 'Not set'}")
        print(f"  NEXT_PUBLIC_SUPABASE_URL: {'Set' if os.getenv('NEXT_PUBLIC_SUPABASE_URL') else 'Not set'}")
        print(f"  SUPABASE_SERVICE_KEY: {'Set' if os.getenv('SUPABASE_SERVICE_KEY') else 'Not set'}")
        print(f"  SUPABASE_ANON_KEY: {'Set' if os.getenv('SUPABASE_ANON_KEY') else 'Not set'}")
        print(f"  NEXT_PUBLIC_SUPABASE_ANON_KEY: {'Set' if os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY') else 'Not set'}")
        print(f"  Final URL: {'Set' if supabase_url else 'Not set'}")
        print(f"  Final KEY: {'Set' if supabase_key else 'Not set'}")

        if supabase_url and supabase_key:
            try:
                self.supabase = create_client(supabase_url, supabase_key)
                self._initialized = True
                print("SkillMemory: Connected to Supabase successfully")
            except Exception as e:
                print(f"SkillMemory: Error connecting to Supabase: {e}")
                self.supabase = None
                self._initialized = False
        else:
            print("SkillMemory: Warning - Supabase credentials not found, skill management will not work")
            self.supabase = None
            self._initialized = False
    
    def _ensure_connected(self):
        """确保 Supabase 已连接，如果未连接则尝试重新连接"""
        if not self._initialized or self.supabase is None:
            print("SkillMemory: Attempting to reconnect to Supabase...")
            self._init_supabase()
        return self.supabase is not None

    def _get_supabase(self):
        """获取 Supabase 客户端"""
        return self.supabase

    # ========== 分类操作 ==========

    def get_all_categories(self) -> List[SkillCategory]:
        """获取所有分类"""
        print(f"[SkillMemory] get_all_categories called, connected: {self._ensure_connected()}")
        
        if not self._ensure_connected():
            print("[SkillMemory] Error: Cannot fetch categories - Supabase not connected")
            return []

        try:
            print("[SkillMemory] Querying skill_categories from Supabase...")
            response = self.supabase.table("skill_categories").select("*").order("order").execute()
            print(f"[SkillMemory] Fetched {len(response.data) if response.data else 0} raw categories")
            
            if response.data:
                categories = []
                for cat_data in response.data:
                    try:
                        cat = SkillCategory(**cat_data)
                        categories.append(cat)
                    except Exception as e:
                        print(f"[SkillMemory] Error parsing category {cat_data.get('id')}: {e}")
                        print(f"[SkillMemory] Category data: {cat_data}")
                
                print(f"[SkillMemory] Successfully parsed {len(categories)} categories")
                return categories
        except Exception as e:
            print(f"[SkillMemory] Error fetching categories: {e}")
            import traceback
            traceback.print_exc()
        return []

    def get_category_by_id(self, category_id: str) -> Optional[SkillCategory]:
        """根据ID获取分类"""
        if not self.supabase:
            return None

        try:
            response = self.supabase.table("skill_categories").select("*").eq("id", category_id).single().execute()
            if response.data:
                return SkillCategory(**response.data)
        except Exception as e:
            print(f"Error fetching category: {e}")
        return None

    def create_category(self, category: SkillCategory) -> SkillCategory:
        """创建分类"""
        if not self.supabase:
            raise Exception("Supabase not available")

        try:
            data = category.model_dump()
            response = self.supabase.table("skill_categories").insert(data).execute()
            if response.data:
                return SkillCategory(**response.data[0])
        except Exception as e:
            print(f"Error creating category: {e}")
            raise
        return category

    def update_category(self, category_id: str, updates: Dict[str, Any]) -> Optional[SkillCategory]:
        """更新分类"""
        if not self.supabase:
            return None

        try:
            updates["updated_at"] = datetime.now().isoformat()
            response = self.supabase.table("skill_categories").update(updates).eq("id", category_id).execute()
            if response.data:
                return SkillCategory(**response.data[0])
        except Exception as e:
            print(f"Error updating category: {e}")
        return None

    def delete_category(self, category_id: str) -> bool:
        """删除分类，并将该分类下的技能变为未归类"""
        if not self.supabase:
            return False

        try:
            # 检查是否是系统分类
            category = self.get_category_by_id(category_id)
            if category and category.is_system:
                return False

            # 将该分类下的技能变为未归类
            self.supabase.table("skills").update({"category_id": None}).eq("category_id", category_id).execute()

            # 删除分类
            self.supabase.table("skill_categories").delete().eq("id", category_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting category: {e}")
        return False

    def move_category(self, category_id: str, new_parent_id: Optional[str], new_order: int) -> bool:
        """移动分类"""
        if not self.supabase:
            return False

        try:
            self.supabase.table("skill_categories").update({
                "parent_id": new_parent_id,
                "order": new_order
            }).eq("id", category_id).execute()
            return True
        except Exception as e:
            print(f"Error moving category: {e}")
        return False

    # ========== 技能操作 ==========

    def get_all_skills(self) -> List[Skill]:
        """获取所有技能"""
        print(f"[SkillMemory] get_all_skills called, connected: {self._ensure_connected()}")
        
        if not self._ensure_connected():
            print("[SkillMemory] Error: Supabase not connected")
            return []

        try:
            # 获取所有技能
            print("[SkillMemory] Querying skills from Supabase...")
            response = self.supabase.table("skills").select("*").execute()
            print(f"[SkillMemory] Fetched {len(response.data) if response.data else 0} raw skills")
            
            if not response.data:
                return []

            # 组装技能数据（constraints 已从 skills 表的 JSONB 字段中读取）
            skills = []
            for skill_data in response.data:
                skill_id = skill_data.get("id")
                # 确保 constraints 是列表格式
                raw_constraints = skill_data.get("constraints", [])
                if raw_constraints is None:
                    raw_constraints = []
                elif isinstance(raw_constraints, dict):
                    raw_constraints = [raw_constraints]
                elif not isinstance(raw_constraints, list):
                    raw_constraints = []
                
                # 只保留 SkillConstraint 模型需要的字段
                filtered_constraints = []
                for constraint in raw_constraints:
                    if isinstance(constraint, dict):
                        filtered_constraints.append({
                            "id": constraint.get("id"),
                            "content": constraint.get("content"),
                            "priority": constraint.get("priority"),
                            "enabled": constraint.get("enabled", True)
                        })
                
                skill_data["constraints"] = filtered_constraints
                
                try:
                    skill = Skill(**skill_data)
                    skills.append(skill)
                except Exception as e:
                    print(f"[SkillMemory] Error parsing skill {skill_id}: {e}")
                    print(f"[SkillMemory] Skill data: {skill_data}")
            
            print(f"[SkillMemory] Successfully parsed {len(skills)} skills")
            return skills
        except Exception as e:
            print(f"[SkillMemory] Error fetching skills: {e}")
            import traceback
            traceback.print_exc()
        return []

    def get_skill_by_id(self, skill_id: str) -> Optional[Skill]:
        """根据ID获取技能"""
        if not self.supabase:
            return None

        try:
            # 获取技能
            response = self.supabase.table("skills").select("*").eq("id", skill_id).single().execute()
            if not response.data:
                return None

            skill_data = response.data

            # 从 skills 表的 constraints 字段直接读取
            skill_data["constraints"] = _process_constraints(skill_data.get("constraints"))

            return Skill(**skill_data)
        except Exception as e:
            print(f"Error fetching skill: {e}")
        return None

    def get_skills_by_category(self, category_id: str) -> List[Skill]:
        """获取分类下的所有技能"""
        if not self.supabase:
            return []

        try:
            response = self.supabase.table("skills").select("*").eq("category_id", category_id).execute()
            if not response.data:
                return []

            # 组装技能数据（constraints 已从 skills 表的 JSONB 字段中读取）
            skills = []
            for skill_data in response.data:
                skill_data["constraints"] = _process_constraints(skill_data.get("constraints"))
                skills.append(Skill(**skill_data))

            return skills
        except Exception as e:
            print(f"Error fetching skills by category: {e}")
        return []

    def create_skill(self, skill: Skill) -> Skill:
        """创建技能"""
        if not self.supabase:
            raise Exception("Supabase not available")

        try:
            # constraints 现在直接存储在 skills 表的 JSONB 字段中
            skill_data = skill.model_dump()

            # 插入技能（包含 constraints）
            response = self.supabase.table("skills").insert(skill_data).execute()
            if not response.data:
                raise Exception("Failed to create skill")

            return skill
        except Exception as e:
            print(f"Error creating skill: {e}")
            raise

    def update_skill(self, skill_id: str, updates: Dict[str, Any]) -> Optional[Skill]:
        """更新技能"""
        if not self.supabase:
            return None

        try:
            # constraints 现在直接存储在 skills 表的 JSONB 字段中
            updates["updated_at"] = datetime.now().isoformat()
            response = self.supabase.table("skills").update(updates).eq("id", skill_id).execute()
            if not response.data:
                return None

            return self.get_skill_by_id(skill_id)
        except Exception as e:
            print(f"Error updating skill: {e}")
        return None

    def delete_skill(self, skill_id: str) -> bool:
        """删除技能"""
        if not self.supabase:
            return False

        try:
            # constraints 现在直接存储在 skills 表中，删除技能时会自动删除
            self.supabase.table("skills").delete().eq("id", skill_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting skill: {e}")
        return False

    def test_skill(self, skill_id: str, test_text: str) -> SkillTestResult:
        """测试技能"""
        skill = self.get_skill_by_id(skill_id)
        if not skill:
            return SkillTestResult(
                passed=False,
                violations=["技能不存在"],
                suggestions=[]
            )

        violations = []
        suggestions = []

        # 检查每个约束
        for constraint in skill.constraints:
            if not constraint.enabled:
                continue

            # 简单的关键词检查（实际应该使用更复杂的逻辑）
            constraint_keywords = constraint.content.lower()
            test_lower = test_text.lower()

            # 这里可以添加更复杂的约束检查逻辑
            # 目前只是示例实现

        passed = len(violations) == 0

        return SkillTestResult(
            passed=passed,
            violations=violations,
            suggestions=suggestions
        )

    def mount_skill_to_novel(self, skill_id: str, novel_id: str) -> bool:
        """挂载技能到小说"""
        if not self.supabase:
            return False

        try:
            # 获取当前技能
            skill = self.get_skill_by_id(skill_id)
            if not skill:
                return False

            # 更新 applicable_novels 数组
            applicable_novels = skill.applicable_novels or []
            if novel_id not in applicable_novels:
                applicable_novels.append(novel_id)

            self.supabase.table("skills").update({
                "applicable_novels": applicable_novels
            }).eq("id", skill_id).execute()
            return True
        except Exception as e:
            print(f"Error mounting skill to novel: {e}")
        return False

    def unmount_skill_from_novel(self, skill_id: str, novel_id: str) -> bool:
        """从小说卸载技能"""
        if not self.supabase:
            return False

        try:
            # 获取当前技能
            skill = self.get_skill_by_id(skill_id)
            if not skill:
                return False

            # 更新 applicable_novels 数组
            applicable_novels = skill.applicable_novels or []
            if novel_id in applicable_novels:
                applicable_novels.remove(novel_id)

            self.supabase.table("skills").update({
                "applicable_novels": applicable_novels
            }).eq("id", skill_id).execute()
            return True
        except Exception as e:
            print(f"Error unmounting skill from novel: {e}")
        return False

    def get_active_skills_for_novel(self, novel_id: str) -> List[Skill]:
        """获取小说的所有激活技能"""
        if not self.supabase:
            return []

        try:
            response = self.supabase.table("skills").select("*").contains("applicable_novels", [novel_id]).eq("is_active", True).execute()
            if not response.data:
                return []

            # 组装技能数据（constraints 已从 skills 表的 JSONB 字段中读取）
            skills = []
            for skill_data in response.data:
                skill_data["constraints"] = _process_constraints(skill_data.get("constraints"))
                skills.append(Skill(**skill_data))

            return skills
        except Exception as e:
            print(f"Error fetching active skills for novel: {e}")
        return []

    def get_system_skills(self) -> List[Skill]:
        """获取系统默认技能"""
        if not self.supabase:
            return []

        try:
            response = self.supabase.table("skills").select("*").eq("is_system", True).execute()
            if not response.data:
                return []

            # 组装技能数据（constraints 已从 skills 表的 JSONB 字段中读取）
            skills = []
            for skill_data in response.data:
                skill_data["constraints"] = _process_constraints(skill_data.get("constraints"))
                skills.append(Skill(**skill_data))

            return skills
        except Exception as e:
            print(f"Error fetching system skills: {e}")
        return []

    def link_asset_to_skill(self, skill_id: str, asset_id: str) -> bool:
        """关联资产到技能"""
        if not self.supabase:
            return False

        try:
            # 获取当前技能
            skill = self.get_skill_by_id(skill_id)
            if not skill:
                return False

            # 更新 linked_assets 数组
            linked_assets = skill.linked_assets or []
            if asset_id not in linked_assets:
                linked_assets.append(asset_id)

            self.supabase.table("skills").update({
                "linked_assets": linked_assets
            }).eq("id", skill_id).execute()
            return True
        except Exception as e:
            print(f"Error linking asset to skill: {e}")
        return False

    def unlink_asset_from_skill(self, skill_id: str, asset_id: str) -> bool:
        """取消资产关联"""
        if not self.supabase:
            return False

        try:
            # 获取当前技能
            skill = self.get_skill_by_id(skill_id)
            if not skill:
                return False

            # 更新 linked_assets 数组
            linked_assets = skill.linked_assets or []
            if asset_id in linked_assets:
                linked_assets.remove(asset_id)

            self.supabase.table("skills").update({
                "linked_assets": linked_assets
            }).eq("id", skill_id).execute()
            return True
        except Exception as e:
            print(f"Error unlinking asset from skill: {e}")
        return False


# 全局实例
skill_memory = SkillMemory()
