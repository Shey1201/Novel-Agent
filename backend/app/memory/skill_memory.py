"""
Skill 存储管理模块 - 使用 Supabase
"""
import os
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.skill import Skill, SkillCategory, SkillConstraint, SkillTestResult

# 尝试导入 supabase，如果没有则使用本地存储作为回退
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


class SkillMemory:
    """技能存储管理器 - Supabase 版本"""

    def __init__(self):
        self.supabase: Optional[Client] = None
        self._init_supabase()

    def _init_supabase(self):
        """初始化 Supabase 客户端"""
        if not SUPABASE_AVAILABLE:
            print("Warning: Supabase not available, skill management will be limited")
            return

        # 支持多种环境变量名（本地开发和 Vercel 部署）
        supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

        if supabase_url and supabase_key:
            try:
                self.supabase = create_client(supabase_url, supabase_key)
                print("SkillMemory: Connected to Supabase")
            except Exception as e:
                print(f"Error connecting to Supabase: {e}")
        else:
            print("Warning: Supabase credentials not found")

    def _get_supabase(self) -> Optional[Client]:
        """获取 Supabase 客户端"""
        return self.supabase

    # ========== 分类操作 ==========

    def get_all_categories(self) -> List[SkillCategory]:
        """获取所有分类"""
        if not self.supabase:
            return []

        try:
            response = self.supabase.table("skill_categories").select("*").order("order").execute()
            if response.data:
                return [SkillCategory(**cat) for cat in response.data]
        except Exception as e:
            print(f"Error fetching categories: {e}")
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
        if not self.supabase:
            return []

        try:
            # 获取所有技能
            response = self.supabase.table("skills").select("*").execute()
            if not response.data:
                return []

            # 获取所有约束
            constraints_response = self.supabase.table("skill_constraints").select("*").execute()
            constraints_map = {}
            if constraints_response.data:
                for constraint in constraints_response.data:
                    skill_id = constraint.get("skill_id")
                    if skill_id not in constraints_map:
                        constraints_map[skill_id] = []
                    constraints_map[skill_id].append(constraint)

            # 组装技能数据
            skills = []
            for skill_data in response.data:
                skill_id = skill_data.get("id")
                skill_data["constraints"] = constraints_map.get(skill_id, [])
                skills.append(Skill(**skill_data))

            return skills
        except Exception as e:
            print(f"Error fetching skills: {e}")
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

            # 获取约束
            constraints_response = self.supabase.table("skill_constraints").select("*").eq("skill_id", skill_id).execute()
            skill_data["constraints"] = constraints_response.data or []

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
            if response.data:
                return [Skill(**skill) for skill in response.data]
        except Exception as e:
            print(f"Error fetching skills by category: {e}")
        return []

    def create_skill(self, skill: Skill) -> Skill:
        """创建技能"""
        if not self.supabase:
            raise Exception("Supabase not available")

        try:
            # 分离约束和技能数据
            skill_data = skill.model_dump()
            constraints = skill_data.pop("constraints", [])

            # 插入技能
            response = self.supabase.table("skills").insert(skill_data).execute()
            if not response.data:
                raise Exception("Failed to create skill")

            # 插入约束
            if constraints:
                for constraint in constraints:
                    constraint["skill_id"] = skill.id
                self.supabase.table("skill_constraints").insert(constraints).execute()

            return skill
        except Exception as e:
            print(f"Error creating skill: {e}")
            raise

    def update_skill(self, skill_id: str, updates: Dict[str, Any]) -> Optional[Skill]:
        """更新技能"""
        if not self.supabase:
            return None

        try:
            # 分离约束和其他更新
            constraints = updates.pop("constraints", None)

            # 更新技能
            updates["updated_at"] = datetime.now().isoformat()
            response = self.supabase.table("skills").update(updates).eq("id", skill_id).execute()
            if not response.data:
                return None

            # 如果有约束更新，先删除旧约束再插入新约束
            if constraints is not None:
                self.supabase.table("skill_constraints").delete().eq("skill_id", skill_id).execute()
                if constraints:
                    for constraint in constraints:
                        constraint["skill_id"] = skill_id
                    self.supabase.table("skill_constraints").insert(constraints).execute()

            return self.get_skill_by_id(skill_id)
        except Exception as e:
            print(f"Error updating skill: {e}")
        return None

    def delete_skill(self, skill_id: str) -> bool:
        """删除技能"""
        if not self.supabase:
            return False

        try:
            # 删除约束（级联删除应该会自动处理，但为了安全）
            self.supabase.table("skill_constraints").delete().eq("skill_id", skill_id).execute()

            # 删除技能
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


# 全局实例
skill_memory = SkillMemory()
