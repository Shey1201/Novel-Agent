"""
Agent Skill Manager: Agent技能管理模块
管理从资产转化的Agent技能和约束
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AgentSkill(BaseModel):
    """Agent技能定义"""
    id: str
    name: str
    description: str
    asset_id: str  # 来源资产ID
    asset_type: str  # 资产类型
    content: str  # 技能内容/约束文本
    target_agents: List[str] = Field(default_factory=list)  # 目标Agent类型
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class NovelSkillMapping(BaseModel):
    """小说与技能的映射关系"""
    novel_id: str
    skill_ids: List[str] = Field(default_factory=list)


class AgentSkillManager:
    """Agent技能管理器"""
    
    DATA_DIR = "data"
    SKILLS_DIR = "agent_skills"
    SKILLS_FILE = "skills.json"
    NOVEL_SKILL_FILE = "novel_skill_mapping.json"
    
    # 支持的Agent类型
    AGENT_TYPES = [
        "writer",      # WritingAgent
        "editor",      # EditorAgent
        "planner",     # PlannerAgent
        "conflict",    # ConflictAgent
        "reader",      # ReaderAgent
        "summary"      # SummaryAgent
    ]
    
    def __init__(self):
        self._skills: Dict[str, AgentSkill] = {}
        self._novel_mappings: Dict[str, NovelSkillMapping] = {}
        self._ensure_directories()
        self._load_data()
    
    def _ensure_directories(self):
        """确保数据目录存在"""
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(os.path.join(self.DATA_DIR, self.SKILLS_DIR), exist_ok=True)
    
    def _get_skills_file_path(self) -> str:
        """获取技能文件路径"""
        return os.path.join(self.DATA_DIR, self.SKILLS_DIR, self.SKILLS_FILE)
    
    def _get_mapping_file_path(self) -> str:
        """获取映射文件路径"""
        return os.path.join(self.DATA_DIR, self.SKILLS_DIR, self.NOVEL_SKILL_FILE)
    
    def _load_data(self):
        """从磁盘加载数据"""
        # 加载技能
        skills_path = self._get_skills_file_path()
        if os.path.exists(skills_path):
            with open(skills_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._skills = {
                    k: AgentSkill(**v) for k, v in data.items()
                }
        
        # 加载映射
        mapping_path = self._get_mapping_file_path()
        if os.path.exists(mapping_path):
            with open(mapping_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._novel_mappings = {
                    k: NovelSkillMapping(**v) for k, v in data.items()
                }
    
    def _save_skills(self):
        """保存技能到磁盘"""
        skills_path = self._get_skills_file_path()
        with open(skills_path, 'w', encoding='utf-8') as f:
            json.dump(
                {k: v.model_dump() for k, v in self._skills.items()},
                f,
                ensure_ascii=False,
                indent=2
            )
    
    def _save_mappings(self):
        """保存映射到磁盘"""
        mapping_path = self._get_mapping_file_path()
        with open(mapping_path, 'w', encoding='utf-8') as f:
            json.dump(
                {k: v.model_dump() for k, v in self._novel_mappings.items()},
                f,
                ensure_ascii=False,
                indent=2
            )
    
    def create_skill_from_asset(
        self,
        skill_id: str,
        skill_name: str,
        description: str,
        asset_id: str,
        asset_type: str,
        asset_content: str,
        target_agents: List[str],
        novel_id: Optional[str] = None
    ) -> AgentSkill:
        """从资产创建Agent技能"""
        # 构建技能内容
        content = self._build_skill_content(asset_type, skill_name, asset_content)
        
        skill = AgentSkill(
            id=skill_id,
            name=skill_name,
            description=description,
            asset_id=asset_id,
            asset_type=asset_type,
            content=content,
            target_agents=target_agents,
            is_active=True
        )
        
        self._skills[skill_id] = skill
        self._save_skills()
        
        # 如果指定了小说，自动关联
        if novel_id:
            self.add_skill_to_novel(skill_id, novel_id)
        
        return skill
    
    def _build_skill_content(self, asset_type: str, name: str, content: str) -> str:
        """构建技能内容文本"""
        templates = {
            "characters": f"""【角色设定约束】
角色名称: {name}
角色描述: {content}

在创作过程中，请确保：
1. 该角色的言行符合上述设定
2. 保持角色性格的一致性
3. 角色的成长变化需要有合理的铺垫
""",
            "worldbuilding": f"""【世界观约束】
设定名称: {name}
设定内容: {content}

在创作过程中，请确保：
1. 严格遵守上述世界观设定
2. 所有情节发展符合世界规则
3. 不出现与设定矛盾的内容
""",
            "factions": f"""【势力设定约束】
势力名称: {name}
势力描述: {content}

在创作过程中，请确保：
1. 该势力的行为符合其设定
2. 势力间的关系保持一致
3. 势力成员的行动符合组织特性
""",
            "locations": f"""【地点设定约束】
地点名称: {name}
地点描述: {content}

在创作过程中，请确保：
1. 地点的地理特征保持一致
2. 场景描写符合地点设定
3. 地点间的距离和关系合理
""",
            "timeline": f"""【时间线约束】
事件名称: {name}
事件描述: {content}

在创作过程中，请确保：
1. 时间顺序符合设定
2. 事件的因果关系清晰
3. 不出现时间线上的矛盾
"""
        }
        
        return templates.get(asset_type, f"【设定约束】\n名称: {name}\n内容: {content}")
    
    def get_skill(self, skill_id: str) -> Optional[AgentSkill]:
        """获取单个技能"""
        return self._skills.get(skill_id)
    
    def get_all_skills(self) -> List[AgentSkill]:
        """获取所有技能"""
        return list(self._skills.values())
    
    def get_skills_by_asset(self, asset_id: str) -> List[AgentSkill]:
        """获取资产的关联技能"""
        return [s for s in self._skills.values() if s.asset_id == asset_id]
    
    def get_skills_by_novel(self, novel_id: str) -> List[AgentSkill]:
        """获取小说的所有技能"""
        mapping = self._novel_mappings.get(novel_id)
        if not mapping:
            return []
        
        return [
            self._skills[sid] for sid in mapping.skill_ids
            if sid in self._skills and self._skills[sid].is_active
        ]
    
    def get_skills_for_agent(self, novel_id: str, agent_type: str) -> List[AgentSkill]:
        """获取指定小说的指定Agent类型的技能"""
        novel_skills = self.get_skills_by_novel(novel_id)
        return [s for s in novel_skills if agent_type in s.target_agents]
    
    def update_skill(self, skill_id: str, updates: Dict) -> Optional[AgentSkill]:
        """更新技能"""
        if skill_id not in self._skills:
            return None
        
        skill = self._skills[skill_id]
        for key, value in updates.items():
            if hasattr(skill, key):
                setattr(skill, key, value)
        
        skill.updated_at = datetime.now().isoformat()
        self._save_skills()
        return skill
    
    def delete_skill(self, skill_id: str) -> bool:
        """删除技能"""
        if skill_id not in self._skills:
            return False
        
        del self._skills[skill_id]
        
        # 从所有小说映射中移除
        for mapping in self._novel_mappings.values():
            if skill_id in mapping.skill_ids:
                mapping.skill_ids.remove(skill_id)
        
        self._save_skills()
        self._save_mappings()
        return True
    
    def add_skill_to_novel(self, skill_id: str, novel_id: str) -> bool:
        """将技能添加到小说"""
        if skill_id not in self._skills:
            return False
        
        if novel_id not in self._novel_mappings:
            self._novel_mappings[novel_id] = NovelSkillMapping(novel_id=novel_id)
        
        mapping = self._novel_mappings[novel_id]
        if skill_id not in mapping.skill_ids:
            mapping.skill_ids.append(skill_id)
            self._save_mappings()
        
        return True
    
    def remove_skill_from_novel(self, skill_id: str, novel_id: str) -> bool:
        """从小说移除技能"""
        if novel_id not in self._novel_mappings:
            return False
        
        mapping = self._novel_mappings[novel_id]
        if skill_id in mapping.skill_ids:
            mapping.skill_ids.remove(skill_id)
            self._save_mappings()
            return True
        
        return False
    
    def toggle_skill_active(self, skill_id: str) -> Optional[bool]:
        """切换技能激活状态"""
        skill = self._skills.get(skill_id)
        if not skill:
            return None
        
        skill.is_active = not skill.is_active
        skill.updated_at = datetime.now().isoformat()
        self._save_skills()
        return skill.is_active
    
    def build_agent_prompt(self, novel_id: str, agent_type: str) -> str:
        """构建Agent的prompt，包含所有相关技能约束"""
        skills = self.get_skills_for_agent(novel_id, agent_type)
        
        if not skills:
            return ""
        
        prompt_parts = ["\n=== 创作约束与设定 ===\n"]
        for skill in skills:
            prompt_parts.append(f"\n{skill.content}\n")
        
        return "\n".join(prompt_parts)


# 全局实例
skill_manager = AgentSkillManager()
