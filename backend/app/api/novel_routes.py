from fastapi import APIRouter, Body, Query
from fastapi.responses import FileResponse
from typing import Optional

from app.agents.conflict_agent import ConflictAgent
from app.agents.editor_agent import EditorAgent
from app.agents.writing_agent import WritingAgent
from app.models.novel import ChapterDraft, ChapterDraftResponse
from app.services.chapter_service import export_to_word, load_draft, save_draft
from app.services.pipeline_service import NovelPipelineService
from app.core.llm import get_llm

router = APIRouter(prefix="/api/novels", tags=["novels"])


@router.post("/generate")
async def generate_simple(
    text: str = Body(..., embed=True),
    story_id: Optional[str] = Body("demo-story"),
    llm_config: Optional[dict] = Body(None),
) -> dict:
    """简化版章节生成"""
    service = NovelPipelineService(llm_config=llm_config)
    final_state = service.run(outline=text, story_id=story_id)
    return {"input": text, "result": final_state.get("final_text", "")}


@router.post("/pipeline")
async def run_pipeline(
    text: str = Body(..., embed=True),
    llm_config: Optional[dict] = Body(None),
) -> dict:
    """简化流水线：Writing -> Editor -> Conflict"""
    # 获取 LLM 实例
    llm = None
    if llm_config:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            api_key=llm_config.get("api_key"),
            model=llm_config.get("model", "gpt-4o-mini"),
            base_url=llm_config.get("base_url"),
            temperature=llm_config.get("temperature", 0.7),
        )
    else:
        llm = get_llm()

    writing = WritingAgent(llm=llm)
    editor = EditorAgent(llm=llm)
    conflict = ConflictAgent(llm=llm)

    state = {"text": text}
    draft_result = writing.run(state)
    edit_result = editor.run(draft_result)
    conflict_result = conflict.run(edit_result)

    return {
        "input": text,
        "draft_text": draft_result.get("draft_text", ""),
        "edited_text": edit_result.get("edited_text", ""),
        "conflict_suggestions": conflict_result.get("conflict_suggestions", []),
    }


@router.post("/draft", response_model=ChapterDraftResponse)
async def save_chapter_draft(draft: ChapterDraft) -> ChapterDraftResponse:
    return save_draft(draft)


@router.get("/draft", response_model=ChapterDraftResponse)
async def get_chapter_draft(
    novel_id: str = Query("demo-novel"),
    chapter_id: str = Query("demo-chapter"),
) -> ChapterDraftResponse:
    return load_draft(novel_id, chapter_id)


@router.get("/export/word")
async def export_chapter_to_word(
    novel_id: str = Query("demo-novel"),
    chapter_id: str = Query("demo-chapter"),
) -> FileResponse:
    file_path = export_to_word(novel_id, chapter_id)
    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{chapter_id}.docx",
    )
