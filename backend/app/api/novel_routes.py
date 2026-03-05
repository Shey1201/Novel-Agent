from fastapi import APIRouter, Body, Query
from fastapi.responses import FileResponse

from app.agents.graph import build_full_flow
from app.agents.writing_agent import WritingAgent
from app.agents.editor_agent import EditorAgent
from app.agents.conflict_agent import ConflictAgent
from app.models.novel import ChapterDraft, ChapterDraftResponse
from app.services.chapter_service import save_draft, load_draft, export_to_word

router = APIRouter(prefix="/api/novel", tags=["novel"])


@router.post("/generate")
async def generate_simple(text: str = Body(..., embed=True)) -> dict:
    """
    模块3：调用 LangGraph Flow，对输入文本进行全流程处理。
    """
    flow = build_full_flow()
    initial_state = {
        "input_text": text,
        "agent_logs": [],
        "plan_text": "",
        "conflict_suggestions": [],
        "draft_text": "",
        "edited_text": "",
        "reader_feedback": [],
        "summary_text": "",
        "final_text": ""
    }
    final_state = flow.invoke(initial_state)
    return {"input": text, "result": final_state.get("final_text", "")}


@router.post("/pipeline")
async def run_pipeline(text: str = Body(..., embed=True)) -> dict:
    """
    简单多 Agent 管线：Writing -> Editor -> Conflict。

    注意：当前使用占位逻辑（没有真实 LLM 调用），
    只是为了把前后端完整串起来，方便后续替换为真实模型。
    """
    writing = WritingAgent(llm=None)
    editor = EditorAgent(llm=None)
    conflict = ConflictAgent(llm=None)

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
    """
    模块4：保存章节草稿（当前使用本地文件存储）。
    """
    return save_draft(draft)


@router.get("/draft", response_model=ChapterDraftResponse)
async def get_chapter_draft(
    novel_id: str = Query("demo-novel"),
    chapter_id: str = Query("demo-chapter"),
) -> ChapterDraftResponse:
    """

    模块4：读取章节草稿（当前使用本地文件存储）。
    """
    return load_draft(novel_id, chapter_id)


@router.get("/export/word")
async def export_chapter_to_word(
    novel_id: str = Query("demo-novel"),
    chapter_id: str = Query("demo-chapter"),
) -> FileResponse:
    """
    将指定章节导出为 Word 文档。
    """
    file_path = export_to_word(novel_id, chapter_id)
    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{chapter_id}.docx"
    )

