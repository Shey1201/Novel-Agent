from typing import Any, Dict, List

from app.agents.critic_agent import CriticAgent
from app.agents.editor_agent import EditorAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.strategist_agent import StrategistAgent
from app.agents.writing_agent import WritingAgent
from app.memory.story_memory import StoryBible
from app.services.chapter_service import load_memory
from app.services.world_service import WorldDebateRequest, WorldService


class AgentChatService:
    def __init__(self, llm: Any = None):
        self.strategist = StrategistAgent(llm=llm)
        self.writer = WritingAgent(llm=llm)
        self.editor = EditorAgent(llm=llm)
        self.critic = CriticAgent(llm=llm)
        self.memory = MemoryAgent(llm=llm)
        self.world = WorldService(llm=llm)

    def _recent_summaries(self, story_id: str, n: int = 3) -> List[str]:
        memory = load_memory(story_id)
        if not memory or not memory.chapter_summaries:
            return []
        return [f"{c.chapter_id}: {c.summary}" for c in memory.chapter_summaries[-n:]]

    def _build_room_context(self, story_id: str) -> Dict[str, Any]:
        world_info = self.world.get_world(story_id)
        bible = StoryBible.model_validate(world_info.get("world_bible", {}))
        recent = self._recent_summaries(story_id)
        return {
            "world": bible.world_view or "",
            "rules": bible.rules or "",
            "recent_summaries": recent,
            "world_approved": world_info.get("approved", False),
        }

    def chat(self, message: str, story_id: str = "demo-story") -> Dict[str, Any]:
        msg = message.strip()
        logs: List[Dict[str, Any]] = []

        if msg.startswith("/start chapter"):
            context = self._build_room_context(story_id)
            logs.append({"agent": "system", "message": "Context loaded"})
            logs.append(
                {
                    "agent": "memory-agent",
                    "message": "Recent Chapters",
                    "content": "\n".join(context["recent_summaries"]) or "暂无最近章节总结",
                }
            )
            return {"agent_logs": logs, "context": context, "final_text": ""}

        if msg.startswith("/world"):
            if msg.startswith("/world approve"):
                world_info = self.world.get_world(story_id)
                bible = StoryBible.model_validate(world_info.get("world_bible", {}))
                result = self.world.approve(story_id, bible)
                logs.append({"agent": "memory-agent", "message": result["message"]})
                return {"agent_logs": logs, "final_text": bible.world_view or "", "world": result, "approved": True}

            prompt = msg.replace("/world", "").strip() or "请设计一个新世界观"
            debate = self.world.debate(WorldDebateRequest(prompt=prompt, story_id=story_id, max_rounds=2))
            logs.extend(debate.agent_logs)
            logs.append({"agent": "memory-agent", "message": "世界观草案已进入待审批状态"})
            return {
                "agent_logs": logs,
                "final_text": debate.world_bible.world_view or "",
                "world_bible": debate.world_bible.model_dump(),
                "approved": False,
            }

        if msg.startswith("/generate"):
            # Room 推荐流程：Planner -> Conflict -> Writer -> Editor -> Critic
            plan = self.strategist.run({"text": msg})
            logs.append(plan)
            conflict_notes = ["建议强化对手压迫感", "建议引入资源竞争与时间压力"]
            logs.append({"agent": "conflict-agent", "message": "已提出冲突建议", "content": "\n".join(conflict_notes)})
            write_input = f"{plan.get('plan_text','')}\n\n[Conflict]\n" + "\n".join(conflict_notes)
            draft = self.writer.run({"text": write_input})
            logs.append(draft)
            polished = self.editor.run({"draft_text": draft.get("draft_text", "")})
            logs.append(polished)
            review = self.critic.run({"draft_text": polished.get("edited_text", "")})
            logs.append(review)
            return {"agent_logs": logs, "final_text": polished.get("edited_text", "")}

        if msg.startswith("/plan") or msg.startswith("/outline"):
            r = self.strategist.run({"text": msg})
            logs.append(r)
            return {"agent_logs": logs, "final_text": r.get("plan_text", "")}

        if msg.startswith("/write") or msg.startswith("/continue"):
            w = self.writer.run({"text": msg})
            logs.append(w)
            return {"agent_logs": logs, "final_text": w.get("draft_text", "")}

        if msg.startswith("/rewrite") or msg.startswith("/style"):
            e = self.editor.run({"draft_text": msg})
            logs.append(e)
            return {"agent_logs": logs, "final_text": e.get("edited_text", "")}

        if msg.startswith("/review"):
            c = self.critic.run({"draft_text": msg})
            logs.append(c)
            return {"agent_logs": logs, "final_text": "\n".join(c.get("reader_feedback", []))}

        r = self.strategist.run({"text": msg})
        logs.append(r)
        return {"agent_logs": logs, "final_text": r.get("plan_text", "")}
