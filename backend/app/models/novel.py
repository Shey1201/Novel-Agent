from typing import List, Optional, Any

from pydantic import BaseModel


class TraceText(BaseModel):
    text: str
    source_agent: str
    revisions: List[str] = []


class ChapterDraft(BaseModel):
    novel_id: str
    chapter_id: str
    content: str


class ChapterDraftResponse(BaseModel):
    novel_id: str
    chapter_id: str
    content: str
    trace_data: Optional[List[TraceText]] = None

