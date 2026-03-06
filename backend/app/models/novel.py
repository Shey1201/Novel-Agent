from typing import List, Optional

from pydantic import BaseModel, Field


class TraceText(BaseModel):
    text: str
    source_agent: str
    revisions: List[str] = Field(default_factory=list)


class ChapterDraft(BaseModel):
    novel_id: str
    chapter_id: str
    content: str


class ChapterDraftResponse(BaseModel):
    novel_id: str
    chapter_id: str
    content: str
    source: str
    trace_data: Optional[List[TraceText]] = None
