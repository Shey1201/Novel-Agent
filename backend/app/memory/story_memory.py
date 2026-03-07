from typing import List, Optional, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field


class CharacterArc(BaseModel):
    """角色弧线"""
    start_state: str = ""  # 初始状态
    end_state: str = ""    # 最终状态
    key_moments: List[str] = Field(default_factory=list)  # 关键转折点


class CharacterRelationship(BaseModel):
    """角色关系"""
    target_character_id: str
    relationship_type: str  # friend, enemy, family, lover, etc.
    description: str = ""
    strength: float = 0.5  # 0-1, 关系强度


class Character(BaseModel):
    """角色实体 - 完整的人物档案"""
    id: str
    name: str
    aliases: List[str] = Field(default_factory=list)  # 别名/称号
    
    # 基础设定
    age: Optional[int] = None
    gender: Optional[str] = None
    appearance: str = ""  # 外貌描述
    
    # 性格与心理
    personality: str = ""  # 性格特征
    values: List[str] = Field(default_factory=list)  # 价值观
    fears: List[str] = Field(default_factory=list)  # 恐惧
    desires: List[str] = Field(default_factory=list)  # 欲望/动机
    
    # 背景故事
    background: str = ""  # 背景故事
    secrets: List[str] = Field(default_factory=list)  # 秘密
    
    # 能力与限制
    abilities: List[str] = Field(default_factory=list)  # 能力/技能
    weaknesses: List[str] = Field(default_factory=list)  # 弱点/限制
    
    # 动态发展
    current_state: str = ""  # 当前状态
    arc: CharacterArc = Field(default_factory=CharacterArc)  # 角色弧线
    relationships: List[CharacterRelationship] = Field(default_factory=list)  # 关系网络
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # 标签
    tags: List[str] = Field(default_factory=list)


class WorldRule(BaseModel):
    """世界规则"""
    id: str
    name: str
    description: str
    category: str  # magic, physics, society, etc.
    importance: str = "medium"  # low, medium, high, critical
    exceptions: List[str] = Field(default_factory=list)  # 例外情况


class WorldLocation(BaseModel):
    """世界地点"""
    id: str
    name: str
    description: str
    location_type: str  # city, dungeon, forest, etc.
    parent_location: Optional[str] = None  # 上级地点
    significance: str = ""  # 重要性/历史意义
    connected_locations: List[str] = Field(default_factory=list)  # 相连地点


class WorldFaction(BaseModel):
    """世界势力/组织"""
    id: str
    name: str
    description: str
    faction_type: str  # kingdom, guild, cult, etc.
    goals: List[str] = Field(default_factory=list)
    relationships: Dict[str, str] = Field(default_factory=dict)  # 与其他势力的关系


class TimelineEvent(BaseModel):
    """时间线事件"""
    id: str
    chapter_id: Optional[str] = None
    title: str
    summary: str
    order: int
    timestamp: Optional[str] = None  # 故事内时间
    involved_characters: List[str] = Field(default_factory=list)  # 参与角色
    location: Optional[str] = None  # 发生地点
    significance: str = "normal"  # normal, minor, major, critical


class ChapterSummary(BaseModel):
    """章节摘要"""
    chapter_id: str
    title: str
    summary: str
    pov: Optional[str] = None  # 视角角色
    word_count: int = 0
    key_events: List[str] = Field(default_factory=list)
    character_development: Dict[str, str] = Field(default_factory=dict)  # 角色发展
    mood: str = ""  # 章节氛围
    created_at: datetime = Field(default_factory=datetime.now)


class StoryTheme(BaseModel):
    """故事主题"""
    name: str
    description: str
    manifestations: List[str] = Field(default_factory=list)  # 在故事中的体现
    importance: float = 0.5  # 0-1


class StoryBible(BaseModel):
    """
    Story Bible - 故事圣经
    
    包含完整的世界观、角色、情节设定
    作为所有 Agent 的共享知识库
    """
    # 基础信息
    title: str = ""
    genre: str = ""  # 类型：fantasy, sci-fi, romance, etc.
    target_audience: str = ""  # 目标读者
    
    # 世界观
    world_view: str = ""  # 世界观概述
    world_rules: List[WorldRule] = Field(default_factory=list)  # 世界规则
    locations: List[WorldLocation] = Field(default_factory=list)  # 地点
    factions: List[WorldFaction] = Field(default_factory=list)  # 势力
    history: str = ""  # 世界历史
    
    # 主题与基调
    themes: List[StoryTheme] = Field(default_factory=list)
    tone: str = ""  # 整体基调：dark, light, epic, etc.
    
    # 情节结构
    plot_structure: str = ""  # 三幕式、英雄之旅等
    major_plot_points: List[str] = Field(default_factory=list)  # 主要情节点
    ending_type: str = ""  # 结局类型
    
    # 元数据
    version: str = "1.0"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def get_world_rules_text(self) -> str:
        """获取世界规则文本"""
        if not self.world_rules:
            return self.world_view or ""
        
        rules_text = f"世界观:\n{self.world_view}\n\n世界规则:\n"
        for rule in self.world_rules:
            rules_text += f"- {rule.name}: {rule.description}\n"
        return rules_text
    
    def get_character_rules_text(self) -> str:
        """获取角色规则文本"""
        return "角色设定需遵循人物档案中的性格、能力、关系设定"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StoryBible":
        """从字典创建"""
        return cls.model_validate(data)


class StoryMemory(BaseModel):
    """Story Memory：用于保持长篇小说的一致性。"""

    story_id: str
    bible: StoryBible = Field(default_factory=StoryBible)
    characters: List[Character] = Field(default_factory=list)
    timeline: List[TimelineEvent] = Field(default_factory=list)
    chapter_summaries: List[ChapterSummary] = Field(default_factory=list)
    world_locked: bool = False
