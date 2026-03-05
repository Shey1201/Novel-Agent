from typing import List, Optional

from pydantic import BaseModel


class Character(BaseModel):
    id: str
    name: str
    role: Optional[str] = None  # 主角 / 反派 / 配角
    description: Optional[str] = None  # 人设描述、性格标签等


class TimelineEvent(BaseModel):
    id: str
    chapter_id: Optional[str] = None
    title: str
    summary: str
    order: int  # 在全局时间线中的顺序


class ChapterSummary(BaseModel):
    chapter_id: str
    title: str
    summary: str
    pov: Optional[str] = None  # 视角角色


class StoryBible(BaseModel):
    world_view: Optional[str] = None  # 世界观 / 规则
    rules: Optional[str] = None  # 写作规则、魔法系统等
    themes: List[str] = []  # 主题标签，如「成长」「复仇」


class StoryMemory(BaseModel):
    """
    Story Memory：用于保持长篇小说的一致性。

    - bible: 整体世界观与设定（Story Bible）
    - characters: 人物卡
    - timeline: 关键事件时间线
    - chapter_summaries: 已完成章节的摘要
    """

    story_id: str
    bible: StoryBible = StoryBible()
    characters: List[Character] = []
    timeline: List[TimelineEvent] = []
    chapter_summaries: List[ChapterSummary] = []

