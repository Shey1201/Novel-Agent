"""
Skill 存储管理模块
"""
import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.skill import Skill, SkillCategory, SkillConstraint, SkillTestResult


class SkillMemory:
    """技能存储管理器"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.skills_dir = self.data_dir / "global" / "skills"
        self.skills_file = self.skills_dir / "skills.json"
        self.categories_file = self.skills_dir / "categories.json"
        
        # 确保目录存在
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化默认数据
        self._init_default_data()
    
    def _init_default_data(self):
        """初始化默认数据"""
        # 初始化默认分类 - 四大基础父分类
        if not self.categories_file.exists():
            default_categories = [
                # === 系统内置分类 (System) ===
                {
                    "id": "cat-system-root",
                    "name": "系统内置",
                    "type": "system",
                    "color": "#ef4444",
                    "is_system": True,
                    "description": "系统默认启用的基础约束，不可删除",
                    "default_agents": ["writer", "editor"],
                    "parent_id": None,
                    "order": 0
                },
                {
                    "id": "cat-safety",
                    "name": "安全合规",
                    "type": "system",
                    "color": "#dc2626",
                    "is_system": True,
                    "description": "禁止血腥、暴力、色情等硬性约束",
                    "default_agents": ["writer", "editor"],
                    "parent_id": "cat-system-root",
                    "order": 0
                },
                {
                    "id": "cat-logic",
                    "name": "基础逻辑",
                    "type": "system",
                    "color": "#ea580c",
                    "is_system": True,
                    "description": "常识一致性、时空因果律等底层规则",
                    "default_agents": ["writer", "editor", "planner"],
                    "parent_id": "cat-system-root",
                    "order": 1
                },
                # === 创作文风分类 (Writing) ===
                {
                    "id": "cat-writing-root",
                    "name": "创作文风",
                    "type": "writing",
                    "color": "#3b82f6",
                    "is_system": True,
                    "description": "管理写作风格和文风的技能分类",
                    "default_agents": ["writer"],
                    "parent_id": None,
                    "order": 1
                },
                {
                    "id": "cat-light-novel",
                    "name": "轻小说类",
                    "type": "writing",
                    "color": "#60a5fa",
                    "is_system": False,
                    "description": "日式轻小说风格",
                    "default_agents": ["writer"],
                    "parent_id": "cat-writing-root",
                    "order": 0
                },
                {
                    "id": "cat-hard-sf",
                    "name": "硬核科幻",
                    "type": "writing",
                    "color": "#818cf8",
                    "is_system": False,
                    "description": "硬科幻文学风格",
                    "default_agents": ["writer"],
                    "parent_id": "cat-writing-root",
                    "order": 1
                },
                {
                    "id": "cat-classical",
                    "name": "古典文学",
                    "type": "writing",
                    "color": "#a78bfa",
                    "is_system": False,
                    "description": "古典文学风格",
                    "default_agents": ["writer"],
                    "parent_id": "cat-writing-root",
                    "order": 2
                },
                # === 领域知识分类 (Domain) ===
                {
                    "id": "cat-domain-root",
                    "name": "领域知识",
                    "type": "domain",
                    "color": "#10b981",
                    "is_system": True,
                    "description": "管理专业领域知识的技能分类",
                    "default_agents": ["writer", "editor"],
                    "parent_id": None,
                    "order": 2
                },
                {
                    "id": "cat-medical",
                    "name": "医学知识",
                    "type": "domain",
                    "color": "#34d399",
                    "is_system": False,
                    "description": "医学专业领域知识",
                    "default_agents": ["writer", "editor"],
                    "parent_id": "cat-domain-root",
                    "order": 0
                },
                {
                    "id": "cat-martial",
                    "name": "武术体系",
                    "type": "domain",
                    "color": "#2dd4bf",
                    "is_system": False,
                    "description": "武术、战斗系统知识",
                    "default_agents": ["writer"],
                    "parent_id": "cat-domain-root",
                    "order": 1
                },
                {
                    "id": "cat-space",
                    "name": "星际航行",
                    "type": "domain",
                    "color": "#5eead4",
                    "is_system": False,
                    "description": "科幻星际航行相关知识",
                    "default_agents": ["writer"],
                    "parent_id": "cat-domain-root",
                    "order": 2
                },
                # === 质量审计分类 (Auditing) ===
                {
                    "id": "cat-auditing-root",
                    "name": "质量审计",
                    "type": "auditing",
                    "color": "#f59e0b",
                    "is_system": True,
                    "description": "管理质量检查和审计的技能分类",
                    "default_agents": ["editor"],
                    "parent_id": None,
                    "order": 3
                },
                {
                    "id": "cat-balance",
                    "name": "战力平衡",
                    "type": "auditing",
                    "color": "#fbbf24",
                    "is_system": False,
                    "description": "战力数值平衡检查",
                    "default_agents": ["editor"],
                    "parent_id": "cat-auditing-root",
                    "order": 0
                },
                {
                    "id": "cat-consistency",
                    "name": "人设一致",
                    "type": "auditing",
                    "color": "#fcd34d",
                    "is_system": False,
                    "description": "角色设定一致性检查",
                    "default_agents": ["editor", "reader"],
                    "parent_id": "cat-auditing-root",
                    "order": 1
                }
            ]
            self._save_categories(default_categories)
        
        # 初始化默认技能
        if not self.skills_file.exists():
            default_skills = [
                {
                    "id": "skill-no-violence",
                    "name": "禁止暴力描写",
                    "description": "禁止过度详细的暴力场景描写",
                    "category_id": "cat-safety",
                    "constraints": [
                        {
                            "id": "constraint-1",
                            "content": "不得详细描写血腥、残忍的暴力场景",
                            "priority": "high",
                            "enabled": True
                        },
                        {
                            "id": "constraint-2",
                            "content": "战斗场景应保持适度，避免过度渲染",
                            "priority": "medium",
                            "enabled": True
                        }
                    ],
                    "target_agents": ["writer", "editor"],
                    "version": "1.0.0",
                    "is_active": True,
                    "is_system": True,
                    "linked_assets": [],
                    "applicable_novels": [],
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                },
                {
                    "id": "skill-no-adult",
                    "name": "禁止色情内容",
                    "description": "禁止任何形式的色情、性暗示内容",
                    "category_id": "cat-safety",
                    "constraints": [
                        {
                            "id": "constraint-3",
                            "content": "禁止露骨的性描写",
                            "priority": "high",
                            "enabled": True
                        },
                        {
                            "id": "constraint-4",
                            "content": "避免过度的性暗示",
                            "priority": "high",
                            "enabled": True
                        }
                    ],
                    "target_agents": ["writer", "editor"],
                    "version": "1.0.0",
                    "is_active": True,
                    "is_system": True,
                    "linked_assets": [],
                    "applicable_novels": [],
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                },
                {
                    "id": "skill-causality",
                    "name": "因果一致性",
                    "description": "确保故事情节符合因果逻辑",
                    "category_id": "cat-logic",
                    "constraints": [
                        {
                            "id": "constraint-5",
                            "content": "事件发展应符合前因后果",
                            "priority": "high",
                            "enabled": True
                        },
                        {
                            "id": "constraint-6",
                            "content": "避免逻辑漏洞和矛盾",
                            "priority": "high",
                            "enabled": True
                        }
                    ],
                    "target_agents": ["writer", "editor", "planner"],
                    "version": "1.0.0",
                    "is_active": True,
                    "is_system": True,
                    "linked_assets": [],
                    "applicable_novels": [],
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            ]
            self._save_skills(default_skills)
    
    def _load_categories(self) -> List[Dict[str, Any]]:
        """加载分类数据"""
        if not self.categories_file.exists():
            return []
        with open(self.categories_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_categories(self, categories: List[Dict[str, Any]]):
        """保存分类数据"""
        with open(self.categories_file, 'w', encoding='utf-8') as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)
    
    def _load_skills(self) -> List[Dict[str, Any]]:
        """加载技能数据"""
        if not self.skills_file.exists():
            return []
        with open(self.skills_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_skills(self, skills: List[Dict[str, Any]]):
        """保存技能数据"""
        with open(self.skills_file, 'w', encoding='utf-8') as f:
            json.dump(skills, f, ensure_ascii=False, indent=2)
    
    # ========== 分类操作 ==========
    
    def get_all_categories(self) -> List[SkillCategory]:
        """获取所有分类"""
        categories_data = self._load_categories()
        return [SkillCategory(**cat) for cat in categories_data]
    
    def get_category_by_id(self, category_id: str) -> Optional[SkillCategory]:
        """根据ID获取分类"""
        categories = self._load_categories()
        for cat in categories:
            if cat["id"] == category_id:
                return SkillCategory(**cat)
        return None
    
    def create_category(self, category: SkillCategory) -> SkillCategory:
        """创建分类"""
        categories = self._load_categories()
        categories.append(category.model_dump())
        self._save_categories(categories)
        return category
    
    def update_category(self, category_id: str, updates: Dict[str, Any]) -> Optional[SkillCategory]:
        """更新分类"""
        categories = self._load_categories()
        for i, cat in enumerate(categories):
            if cat["id"] == category_id:
                categories[i].update(updates)
                self._save_categories(categories)
                return SkillCategory(**categories[i])
        return None
    
    def delete_category(self, category_id: str) -> bool:
        """删除分类，并将该分类下的技能变为未归类"""
        categories = self._load_categories()
        category = next((cat for cat in categories if cat["id"] == category_id), None)
        
        if not category:
            return False
            
        # 系统分类不能删除
        if category.get("is_system", False):
            return False
            
        # 删除分类
        categories = [cat for cat in categories if cat["id"] != category_id]
        self._save_categories(categories)
        
        # 将该分类下的技能变为未归类 (category_id = None)
        skills = self._load_skills()
        updated = False
        for skill in skills:
            if skill.get("category_id") == category_id:
                skill["category_id"] = None
                skill["updated_at"] = datetime.now().isoformat()
                updated = True
        
        if updated:
            self._save_skills(skills)
            
        return True
    
    def move_category(self, category_id: str, new_parent_id: Optional[str], new_order: int) -> bool:
        """移动分类"""
        categories = self._load_categories()
        for cat in categories:
            if cat["id"] == category_id:
                cat["parent_id"] = new_parent_id
                cat["order"] = new_order
                self._save_categories(categories)
                return True
        return False
    
    # ========== 技能操作 ==========
    
    def get_all_skills(self) -> List[Skill]:
        """获取所有技能"""
        skills_data = self._load_skills()
        return [Skill(**skill) for skill in skills_data]
    
    def get_skill_by_id(self, skill_id: str) -> Optional[Skill]:
        """根据ID获取技能"""
        skills = self._load_skills()
        for skill in skills:
            if skill["id"] == skill_id:
                return Skill(**skill)
        return None
    
    def get_skills_by_category(self, category_id: str) -> List[Skill]:
        """获取分类下的所有技能"""
        skills = self._load_skills()
        return [Skill(**skill) for skill in skills if skill["category_id"] == category_id]
    
    def get_skills_by_novel(self, novel_id: str) -> List[Skill]:
        """获取小说挂载的所有技能"""
        skills = self._load_skills()
        return [Skill(**skill) for skill in skills if novel_id in skill.get("applicable_novels", [])]
    
    def create_skill(self, skill: Skill) -> Skill:
        """创建技能"""
        skills = self._load_skills()
        skills.append(skill.model_dump())
        self._save_skills(skills)
        return skill
    
    def update_skill(self, skill_id: str, updates: Dict[str, Any]) -> Optional[Skill]:
        """更新技能"""
        skills = self._load_skills()
        for i, skill in enumerate(skills):
            if skill["id"] == skill_id:
                skill.update(updates)
                skill["updated_at"] = datetime.now().isoformat()
                self._save_skills(skills)
                return Skill(**skill)
        return None
    
    def delete_skill(self, skill_id: str) -> bool:
        """删除技能"""
        skills = self._load_skills()
        original_len = len(skills)
        skills = [skill for skill in skills if skill["id"] != skill_id]
        if len(skills) < original_len:
            self._save_skills(skills)
            return True
        return False
    
    def link_asset_to_skill(self, skill_id: str, asset_id: str) -> bool:
        """关联资产到技能"""
        skills = self._load_skills()
        for skill in skills:
            if skill["id"] == skill_id:
                if asset_id not in skill.get("linked_assets", []):
                    skill["linked_assets"].append(asset_id)
                    self._save_skills(skills)
                return True
        return False
    
    def unlink_asset_from_skill(self, skill_id: str, asset_id: str) -> bool:
        """取消资产关联"""
        skills = self._load_skills()
        for skill in skills:
            if skill["id"] == skill_id:
                if asset_id in skill.get("linked_assets", []):
                    skill["linked_assets"].remove(asset_id)
                    self._save_skills(skills)
                return True
        return False
    
    def mount_skill_to_novel(self, skill_id: str, novel_id: str) -> bool:
        """挂载技能到小说"""
        skills = self._load_skills()
        for skill in skills:
            if skill["id"] == skill_id:
                if novel_id not in skill.get("applicable_novels", []):
                    skill["applicable_novels"].append(novel_id)
                    self._save_skills(skills)
                return True
        return False
    
    def unmount_skill_from_novel(self, skill_id: str, novel_id: str) -> bool:
        """从小说卸载技能"""
        skills = self._load_skills()
        for skill in skills:
            if skill["id"] == skill_id:
                if novel_id in skill.get("applicable_novels", []):
                    skill["applicable_novels"].remove(novel_id)
                    self._save_skills(skills)
                return True
        return False
    
    def test_skill(self, skill_id: str, text: str) -> SkillTestResult:
        """测试技能约束"""
        skill = self.get_skill_by_id(skill_id)
        if not skill:
            return SkillTestResult(passed=False, violations=["技能不存在"], suggestions=[])
        
        violations = []
        suggestions = []
        
        # 简单的规则匹配测试
        for constraint in skill.constraints:
            if not constraint.enabled:
                continue
            
            # 这里可以实现更复杂的规则检查逻辑
            # 目前使用简单的关键词匹配作为示例
            if "禁止" in constraint.content or "不得" in constraint.content:
                # 检查是否包含违规内容
                prohibited_words = ["血腥", "暴力", "色情", "残忍"]
                for word in prohibited_words:
                    if word in text:
                        violations.append(f"违反约束: {constraint.content} (检测到: {word})")
        
        return SkillTestResult(
            passed=len(violations) == 0,
            violations=violations,
            suggestions=suggestions if violations else ["文本符合所有约束规则"]
        )
    
    def get_system_skills(self) -> List[Skill]:
        """获取所有系统技能"""
        skills = self._load_skills()
        return [Skill(**skill) for skill in skills if skill.get("is_system", False)]
    
    def get_active_skills_for_novel(self, novel_id: str) -> List[Skill]:
        """获取小说激活的所有技能（包括系统默认技能）"""
        all_skills = self.get_all_skills()
        active_skills = []
        
        for skill in all_skills:
            # 系统技能默认启用
            if skill.is_system and skill.is_active:
                active_skills.append(skill)
            # 用户挂载的技能
            elif novel_id in skill.applicable_novels and skill.is_active:
                active_skills.append(skill)
        
        return active_skills


# 全局实例
skill_memory = SkillMemory()
