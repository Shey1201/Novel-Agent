from typing import Any, Dict, List
import random

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

    def _generate_discussion(self, topic: str, context: Dict[str, Any], max_rounds: int = 3) -> List[Dict[str, Any]]:
        """
        生成多 Agent 讨论流程
        模拟多个 Agent 围绕话题进行讨论、提问、完善想法
        """
        logs: List[Dict[str, Any]] = []
        
        # 定义参与讨论的 Agents 及其角色定位
        agents = [
            {
                "name": "strategist",
                "display_name": "策划师",
                "personality": "善于规划故事结构，关注整体框架",
                "concerns": ["故事主线是否清晰", "情节发展是否合理", "读者期待如何满足"]
            },
            {
                "name": "writer",
                "display_name": "作家",
                "personality": "专注于具体写作，关注细节描写",
                "concerns": ["场景描写是否生动", "对话是否自然", "节奏是否合适"]
            },
            {
                "name": "editor",
                "display_name": "编辑",
                "personality": "注重文字质量，追求精炼表达",
                "concerns": ["文字是否流畅", "逻辑是否通顺", "风格是否统一"]
            },
            {
                "name": "critic",
                "display_name": "评论家",
                "personality": "善于发现问题，提出改进建议",
                "concerns": ["是否存在逻辑漏洞", "人物行为是否一致", "情节是否可信"]
            }
        ]
        
        # 第一轮：各 Agent 提出初步想法
        logs.append({
            "agent": "system",
            "message": f"🎯 讨论主题：{topic}",
            "content": "各 Agent 开始围绕主题展开讨论..."
        })
        
        for agent in agents:
            concern = random.choice(agent["concerns"])
            logs.append({
                "agent": agent["name"],
                "agent_name": agent["display_name"],
                "message": f"💭 {agent['display_name']}思考中...",
                "content": f"从{agent['personality']}的角度来看，我想关注：{concern}。\n\n关于'{topic}'，我认为..."
            })
        
        # 第二轮：互相提问和回应
        if max_rounds >= 2:
            logs.append({
                "agent": "system",
                "message": "🔄 进入互动讨论阶段",
                "content": "Agent 们开始互相提问、质疑、完善想法"
            })
            
            # 评论家提问
            logs.append({
                "agent": "critic",
                "agent_name": "评论家",
                "message": "❓ 我有一个疑问",
                "content": f"策划师，关于'{topic}'，如果读者对这个设定不感兴趣怎么办？我们是否需要增加一些悬念元素？"
            })
            
            # 策划师回应
            logs.append({
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "💡 回应评论家的疑问",
                "content": "很好的问题！我建议在开篇加入一个冲突场景，让读者立刻被吸引。同时，我们可以设置一个长期悬念..."
            })
            
            # 作家提出执行层面的问题
            logs.append({
                "agent": "writer",
                "agent_name": "作家",
                "message": "✍️ 从写作角度考虑",
                "content": "这个思路很好，但我担心具体的场景描写。策划师能否给出一个具体的场景示例？这样我能更好地把握氛围。"
            })
            
            # 编辑提出优化建议
            logs.append({
                "agent": "editor",
                "agent_name": "编辑",
                "message": "🔍 文字优化建议",
                "content": "在写作时，注意控制节奏。建议先铺垫再爆发，让读者有情感积累的过程。另外，对话要简洁有力，避免冗长。"
            })
        
        # 第三轮：总结和达成共识
        if max_rounds >= 3:
            logs.append({
                "agent": "system",
                "message": "✅ 讨论总结",
                "content": "各 Agent 达成共识，形成最终方案"
            })
            
            logs.append({
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "📋 整体方案",
                "content": f"经过讨论，我们确定'{topic}'的核心方向：\n1. 开篇设置悬念吸引读者\n2. 情节发展注重逻辑性\n3. 人物行为符合设定\n4. 结尾留有回味空间"
            })
            
            logs.append({
                "agent": "writer",
                "agent_name": "作家",
                "message": "📝 写作要点",
                "content": "我会重点关注：场景描写的层次感、对话的自然度、情感的真挚性。确保文字能够打动读者。"
            })
            
            logs.append({
                "agent": "critic",
                "agent_name": "评论家",
                "message": "👍 最终确认",
                "content": "这个方案考虑得比较全面。建议在执行过程中注意人物动机的一致性，避免出现为了情节牺牲人物的情况。"
            })
        
        return logs

    def chat(self, message: str, story_id: str = "demo-story", word_count_range: Dict[str, int] = None) -> Dict[str, Any]:
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
            # 使用多 Agent 讨论模式
            topic = msg.replace("/plan", "").replace("/outline", "").strip() or "故事大纲规划"
            context = self._build_room_context(story_id)
            logs.extend(self._generate_discussion(topic, context, max_rounds=3))
            
            # 最后由策划师输出正式的计划
            r = self.strategist.run({"text": msg})
            logs.append(r)
            return {"agent_logs": logs, "final_text": r.get("plan_text", "")}

        if msg.startswith("/write") or msg.startswith("/continue"):
            # 使用多 Agent 讨论模式
            topic = msg.replace("/write", "").replace("/continue", "").strip() or "章节写作"
            context = self._build_room_context(story_id)
            logs.extend(self._generate_discussion(topic, context, max_rounds=3))
            
            # 最后由作家输出正式的内容
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

        if msg.startswith("/discuss"):
            # 专门的多 Agent 讨论命令
            topic = msg.replace("/discuss", "").strip() or "故事创作"
            context = self._build_room_context(story_id)
            logs.extend(self._generate_discussion(topic, context, max_rounds=3))
            return {"agent_logs": logs, "final_text": f"讨论完成。各 Agent 已就'{topic}'达成共识。"}

        # 默认：普通对话也使用多 Agent 讨论模式
        context = self._build_room_context(story_id)
        logs.extend(self._generate_discussion(msg, context, max_rounds=2))
        
        r = self.strategist.run({"text": msg})
        logs.append(r)
        return {"agent_logs": logs, "final_text": r.get("plan_text", "")}
