from typing import List, Optional

from pydantic import BaseModel, Field


class Character(BaseModel):
    id: str
    name: str
    role: Optional[str] = None
    description: Optional[str] = None


class TimelineEvent(BaseModel):
    id: str
    chapter_id: Optional[str] = None
    title: str
    summary: str
    order: int


class ChapterSummary(BaseModel):
    chapter_id: str
    title: str
    summary: str
    pov: Optional[str] = None


class StoryBible(BaseModel):
    world_view: Optional[str] = None
    rules: Optional[str] = None
    themes: List[str] = Field(default_factory=list)


class StoryMemory(BaseModel):
    """Story Memory：用于保持长篇小说的一致性。"""

    story_id: str
    bible: StoryBible = Field(default_factory=StoryBible)
    characters: List[Character] = Field(default_factory=list)
    timeline: List[TimelineEvent] = Field(default_factory=list)
    chapter_summaries: List[ChapterSummary] = Field(default_factory=list)
    world_locked: bool = False
