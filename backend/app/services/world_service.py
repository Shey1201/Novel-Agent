from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.agents.conflict_agent import ConflictAgent
from app.agents.editor_agent import EditorAgent
from app.agents.logic_agent import LogicAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.reader_agent import ReaderAgent
from app.memory.story_memory import StoryBible
from app.services.chapter_service import load_memory, save_memory


class WorldDebateRequest(BaseModel):
    prompt: str
    story_id: str = "demo-story"
    max_rounds: int = 2


class WorldDebateResult(BaseModel):
    story_id: str
    rounds: int
    world_bible: StoryBible
    agent_logs: List[Dict[str, Any]] = Field(default_factory=list)
    approved: bool = False


class WorldService:
    def __init__(self, llm: Any = None):
        self.planner = PlannerAgent(llm=llm)
        self.conflict = ConflictAgent(llm=llm)
        self.reader = ReaderAgent(llm=llm)
        self.editor = EditorAgent(llm=llm)
        self.logic = LogicAgent(llm=llm)

    def debate(self, payload: WorldDebateRequest) -> WorldDebateResult:
        max_rounds = max(1, min(payload.max_rounds, 2))
        agent_logs: List[Dict[str, Any]] = []

        planner_draft = self.planner.run({"text": payload.prompt}).get("plan_text", "")
        agent_logs.append({"agent": "planner-agent", "message": "提出世界观草案", "content": planner_draft})

        for i in range(max_rounds):
            conflict_result = self.conflict.run({"draft_text": planner_draft})
            conflict_suggestions = conflict_result.get("conflict_suggestions", [])
            agent_logs.append(
                {
                    "agent": "conflict-agent",
                    "message": f"第 {i + 1} 轮挑刺完成",
                    "conflicts": conflict_suggestions,
                }
            )

            logic_result = self.logic.run({"world_draft": planner_draft})
            logic_issues = logic_result.get("logic_issues", [])
            agent_logs.append(
                {
                    "agent": "logic-agent",
                    "message": f"第 {i + 1} 轮逻辑审查",
                    "logic_issues": logic_issues,
                }
            )

            reader_result = self.reader.run({"draft_text": planner_draft})
            feedback = reader_result.get("reader_feedback", [])
            score = {
                "novelty": 6 + (i % 2),
                "power_fantasy": 7,
                "hook": 6,
                "comment": "建议强化核心钩子和成长驱动力",
            }
            agent_logs.append(
                {
                    "agent": "reader-agent",
                    "message": f"第 {i + 1} 轮读者评估",
                    "reader_feedback": feedback,
                    "reader_score": score,
                }
            )

            revise_text = "\n".join([planner_draft] + [f"- {s}" for s in conflict_suggestions + logic_issues + feedback])
            planner_draft = self.planner.run({"text": revise_text}).get("plan_text", planner_draft)
            agent_logs.append(
                {
                    "agent": "planner-agent",
                    "message": f"第 {i + 1} 轮修订完成",
                    "content": planner_draft,
                }
            )

        edited = self.editor.run({"draft_text": planner_draft}).get("edited_text", planner_draft)
        agent_logs.append({"agent": "editor-agent", "message": "完成世界观定稿整理", "content": edited})

        world_bible = StoryBible(
            world_view=edited,
            rules="以用户输入题材为准，不预设玄幻模板；若为科幻/现实向则采用对应规则。",
            themes=["成长", "冲突", "选择"],
        )
        return WorldDebateResult(
            story_id=payload.story_id,
            rounds=max_rounds,
            world_bible=world_bible,
            agent_logs=agent_logs,
            approved=False,
        )

    def approve(self, story_id: str, world_bible: StoryBible) -> Dict[str, Any]:
        memory = load_memory(story_id)
        if memory is None:
            from app.memory.story_memory import StoryMemory

            memory = StoryMemory(story_id=story_id)

        memory.bible = world_bible
        memory.world_locked = True
        save_memory(memory)
        return {
            "story_id": story_id,
            "approved": True,
            "message": "世界观已写入 Story Bible 并锁定",
        }

    def get_world(self, story_id: str) -> Dict[str, Any]:
        memory = load_memory(story_id)
        if memory is None:
            return {
                "story_id": story_id,
                "approved": False,
                "world_bible": StoryBible().model_dump(),
            }
        return {
            "story_id": story_id,
            "approved": memory.world_locked,
            "world_bible": memory.bible.model_dump(),
        }
