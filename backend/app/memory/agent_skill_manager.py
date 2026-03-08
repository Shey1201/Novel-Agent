"""
Agent Skill Manager: Agent技能管理模块 (Supabase 版本)
管理从资产转化的Agent技能和约束
"""

import os
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# 尝试导入 supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


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
    """Agent技能管理器 - Supabase 版本"""
    
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
        self.supabase: Optional[Client] = None
        self._init_supabase()
    
    def _init_supabase(self):
        """初始化 Supabase 客户端"""
        if not SUPABASE_AVAILABLE:
            print("Warning: Supabase not available, agent skill management will be limited")
            return
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if supabase_url and supabase_key:
            try:
                self.supabase = create_client(supabase_url, supabase_key)
                print("AgentSkillManager: Connected to Supabase")
            except Exception as e:
                print(f"Error connecting to Supabase: {e}")
        else:
            print("Warning: Supabase credentials not found")
    
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
        if not self.supabase:
            raise Exception("Supabase not available")
        
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
        
        try:
            # 保存技能到数据库
            skill_data = {
                "id": skill.id,
                "name": skill.name,
                "description": skill.description,
                "asset_id": skill.asset_id,
                "asset_type": skill.asset_type,
                "content": skill.content,
                "target_agents": skill.target_agents,
                "is_active": skill.is_active,
            }
            self.supabase.table("agent_skills").insert(skill_data).execute()
            
            # 如果指定了小说，自动关联
            if novel_id:
                self.add_skill_to_novel(skill_id, novel_id)
            
            return skill
        except Exception as e:
            print(f"Error creating skill from asset: {e}")
            raise
    
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
        if not self.supabase:
            return None
        
        try:
            response = self.supabase.table("agent_skills").select("*").eq("id", skill_id).single().execute()
            if response.data:
                return AgentSkill(**response.data)
        except Exception as e:
            print(f"Error getting skill: {e}")
        return None
    
    def get_all_skills(self) -> List[AgentSkill]:
        """获取所有技能"""
        if not self.supabase:
            return []
        
        try:
            response = self.supabase.table("agent_skills").select("*").execute()
            if response.data:
                return [AgentSkill(**skill) for skill in response.data]
        except Exception as e:
            print(f"Error getting all skills: {e}")
        return []
    
    def get_skills_by_asset(self, asset_id: str) -> List[AgentSkill]:
        """获取资产的关联技能"""
        if not self.supabase:
            return []
        
        try:
            response = self.supabase.table("agent_skills").select("*").eq("asset_id", asset_id).execute()
            if response.data:
                return [AgentSkill(**skill) for skill in response.data]
        except Exception as e:
            print(f"Error getting skills by asset: {e}")
        return []
    
    def get_skills_by_novel(self, novel_id: str) -> List[AgentSkill]:
        """获取小说的所有技能"""
        if not self.supabase:
            return []
        
        try:
            # 获取小说技能映射
            response = self.supabase.table("novel_skill_mappings").select("skill_id").eq("novel_id", novel_id).execute()
            if not response.data:
                return []
            
            skill_ids = [m["skill_id"] for m in response.data]
            
            # 获取技能详情
            skills = []
            for skill_id in skill_ids:
                skill = self.get_skill(skill_id)
                if skill and skill.is_active:
                    skills.append(skill)
            
            return skills
        except Exception as e:
            print(f"Error getting skills by novel: {e}")
        return []
    
    def get_skills_for_agent(self, novel_id: str, agent_type: str) -> List[AgentSkill]:
        """获取指定小说的指定Agent类型的技能"""
        novel_skills = self.get_skills_by_novel(novel_id)
        return [s for s in novel_skills if agent_type in s.target_agents]
    
    def update_skill(self, skill_id: str, updates: Dict) -> Optional[AgentSkill]:
        """更新技能"""
        if not self.supabase:
            return None
        
        try:
            updates["updated_at"] = datetime.now().isoformat()
            response = self.supabase.table("agent_skills").update(updates).eq("id", skill_id).execute()
            if response.data:
                return AgentSkill(**response.data[0])
        except Exception as e:
            print(f"Error updating skill: {e}")
        return None
    
    def delete_skill(self, skill_id: str) -> bool:
        """删除技能"""
        if not self.supabase:
            return False
        
        try:
            # 删除技能（级联删除会处理映射）
            self.supabase.table("agent_skills").delete().eq("id", skill_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting skill: {e}")
        return False
    
    def add_skill_to_novel(self, skill_id: str, novel_id: str) -> bool:
        """将技能添加到小说"""
        if not self.supabase:
            return False
        
        try:
            mapping_data = {
                "novel_id": novel_id,
                "skill_id": skill_id,
            }
            self.supabase.table("novel_skill_mappings").insert(mapping_data).execute()
            return True
        except Exception as e:
            print(f"Error adding skill to novel: {e}")
        return False
    
    def remove_skill_from_novel(self, skill_id: str, novel_id: str) -> bool:
        """从小说移除技能"""
        if not self.supabase:
            return False
        
        try:
            self.supabase.table("novel_skill_mappings").delete().eq("novel_id", novel_id).eq("skill_id", skill_id).execute()
            return True
        except Exception as e:
            print(f"Error removing skill from novel: {e}")
        return False
    
    def toggle_skill_active(self, skill_id: str) -> Optional[bool]:
        """切换技能激活状态"""
        if not self.supabase:
            return None
        
        try:
            # 获取当前状态
            skill = self.get_skill(skill_id)
            if not skill:
                return None
            
            new_status = not skill.is_active
            self.supabase.table("agent_skills").update({
                "is_active": new_status,
                "updated_at": datetime.now().isoformat()
            }).eq("id", skill_id).execute()
            
            return new_status
        except Exception as e:
            print(f"Error toggling skill active: {e}")
        return None
    
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
