import json
from pathlib import Path
from docx import Document

from app.models.novel import ChapterDraft, ChapterDraftResponse

# 本地文件根目录：backend/data
DATA_DIR = Path(__file__).resolve().parents[2] / "data"


from app.memory.story_memory import StoryMemory

def _draft_path(novel_id: str, chapter_id: str) -> Path:
    novel_dir = DATA_DIR / novel_id
    novel_dir.mkdir(parents=True, exist_ok=True)
    return novel_dir / f"{chapter_id}.json"


def _memory_path(story_id: str) -> Path:
    story_dir = DATA_DIR / story_id
    story_dir.mkdir(parents=True, exist_ok=True)
    return story_dir / "story_memory.json"




def _memory_component_paths(story_id: str) -> dict[str, Path]:
    story_dir = DATA_DIR / story_id
    story_dir.mkdir(parents=True, exist_ok=True)
    return {
        "world": story_dir / "world.json",
        "characters": story_dir / "characters.json",
        "timeline": story_dir / "timeline.json",
    }

def save_memory(memory: StoryMemory):
    path = _memory_path(memory.story_id)
    path.write_text(memory.model_dump_json(indent=2), encoding="utf-8")

    components = _memory_component_paths(memory.story_id)
    components["world"].write_text(json.dumps(memory.bible.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    components["characters"].write_text(json.dumps([c.model_dump() for c in memory.characters], ensure_ascii=False, indent=2), encoding="utf-8")
    components["timeline"].write_text(json.dumps([t.model_dump() for t in memory.timeline], ensure_ascii=False, indent=2), encoding="utf-8")


def load_memory(story_id: str) -> StoryMemory:
    path = _memory_path(story_id)
    if path.exists():
        return StoryMemory.model_validate_json(path.read_text(encoding="utf-8"))
    return None


def save_draft(draft: ChapterDraft) -> ChapterDraftResponse:
    path = _draft_path(draft.novel_id, draft.chapter_id)
    payload = {
        "novel_id": draft.novel_id,
        "chapter_id": draft.chapter_id,
        "content": draft.content,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return ChapterDraftResponse(
        novel_id=draft.novel_id,
        chapter_id=draft.chapter_id,
        content=draft.content,
        source="file",
    )


def load_draft(novel_id: str, chapter_id: str) -> ChapterDraftResponse:
    path = _draft_path(novel_id, chapter_id)
    if path.exists():
        try:
            data = json.loads(path.read_bytes())
            content = data.get("content", "")
        except Exception:
            content = ""
    else:
        content = ""

    return ChapterDraftResponse(
        novel_id=novel_id,
        chapter_id=chapter_id,
        content=content,
        source="file" if content else "empty",
    )


def export_to_word(novel_id: str, chapter_id: str) -> str:
    draft = load_draft(novel_id, chapter_id)
    document = Document()
    document.add_paragraph(draft.content)

    file_path = DATA_DIR / novel_id / f"{chapter_id}.docx"
    document.save(file_path)

    return str(file_path)

