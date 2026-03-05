from typing import Any, Dict, Optional

from app.agents.writing_agent import WritingAgent
from app.agents.editor_agent import EditorAgent
from app.agents.conflict_agent import ConflictAgent
from app.memory.story_memory import StoryMemory, StoryBible


def generate_chapter(
    outline: str,
    story_memory: Optional[StoryMemory] = None,
    llm: Any = None,
) -> Dict[str, Any]:
    """
    Controller：基于「大纲 + Story Memory」生成章节。

    当前占位流程：
    大纲 -> ConflictAgent(基于大纲提出冲突建议)
         -> WritingAgent(根据大纲+冲突建议生成草稿)
         -> EditorAgent(对草稿做基础润色)
         -> 返回结果（含冲突建议）

    说明：
    - llm 由上层传入（前端提供配置后，再在调用处实例化传入），此处不做具体绑定。
    - story_memory 目前未深入使用，后续会用于保持人设/时间线一致。
    """

    if story_memory is None:
        story_memory = StoryMemory(story_id="demo-story", bible=StoryBible())

    # 初始化三个 Agent（当前未接具体 LLM）
    conflict_agent = ConflictAgent(llm=llm)
    writing_agent = WritingAgent(llm=llm)
    editor_agent = EditorAgent(llm=llm)

    # 1. 大纲先经过 Conflict Agent，得到冲突建议
    conflict_input = {"draft_text": outline}
    conflict_result = conflict_agent.run(conflict_input)
    conflict_suggestions = conflict_result.get("conflict_suggestions", [])

    # 将冲突建议简单拼接回大纲，用于指导写作
    conflict_notes = "\n".join(f"- {s}" for s in conflict_suggestions)
    outline_with_conflict = outline
    if conflict_notes:
        outline_with_conflict = f"{outline}\n\n[Conflict Notes]\n{conflict_notes}"

    # 2. Writing Agent 根据「大纲 + 冲突」生成草稿
    writing_state = {"text": outline_with_conflict}
    writing_result = writing_agent.run(writing_state)
    draft_text = writing_result.get("draft_text", "")

    # 3. Editor Agent 对草稿进行基础润色
    editor_state = {"draft_text": draft_text}
    editor_result = editor_agent.run(editor_state)
    edited_text = editor_result.get("edited_text", "")

    return {
        "outline": outline,
        "outline_with_conflict": outline_with_conflict,
        "draft_text": draft_text,
        "edited_text": edited_text,
        "conflict_suggestions": conflict_suggestions,
        "story_id": story_memory.story_id,
    }

