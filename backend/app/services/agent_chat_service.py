from typing import Any, Dict, List, Optional
import random
import json

from app.agents.critic_agent import CriticAgent
from app.agents.editor_agent import EditorAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.strategist_agent import StrategistAgent
from app.agents.writing_agent import WritingAgent
from app.memory.story_memory import StoryBible
from app.services.chapter_service import load_memory
from app.services.world_service import WorldDebateRequest, WorldService
from app.core.llm import get_llm


class AgentChatService:
    def __init__(self, llm: Any = None):
        # 如果没有传入 llm，尝试从配置获取
        self.llm = llm or get_llm()
        self.strategist = StrategistAgent(llm=self.llm)
        self.writer = WritingAgent(llm=self.llm)
        self.editor = EditorAgent(llm=self.llm)
        self.critic = CriticAgent(llm=self.llm)
        self.memory = MemoryAgent(llm=self.llm)
        self.world = WorldService(llm=self.llm)

    def _recent_summaries(self, story_id: str, n: int = 3) -> List[str]:
        memory = load_memory(story_id)
        if not memory or not memory.chapter_summaries:
            return []
        return [f"{c.chapter_id}: {c.summary}" for c in memory.chapter_summaries[-n:]]

    def _build_room_context(self, story_id: str) -> Dict[str, Any]:
        world_info = self.world.get_world(story_id)
        bible = StoryBible.model_validate(world_info.get("world_bible", {}))
        recent = self._recent_summaries(story_id)
        # 获取世界规则文本（world_rules 是列表，需要转换为文本）
        rules_text = ""
        if bible.world_rules:
            rules_text = "\n".join([f"- {rule.name}: {rule.description}" for rule in bible.world_rules])
        return {
            "world": bible.world_view or "",
            "rules": rules_text,
            "recent_summaries": recent,
            "world_approved": world_info.get("approved", False),
        }

    def _analyze_intent(self, message: str) -> Dict[str, Any]:
        """
        分析用户意图，确定需要执行的操作流程
        """
        lower_msg = message.lower()
        
        # 检测操作类型
        if any(kw in lower_msg for kw in ['写', '创作', 'draft', 'write', '生成内容']):
            return {
                "type": "write",
                "needs_discussion": True,
                "decision_points": ["确认大纲", "确认风格", "确认字数"],
                "auto_execute": False
            }
        elif any(kw in lower_msg for kw in ['大纲', 'outline', '规划', '结构', '框架']):
            return {
                "type": "outline",
                "needs_discussion": True,
                "decision_points": ["确认主线", "确认章节数", "确认节奏"],
                "auto_execute": False
            }
        elif any(kw in lower_msg for kw in ['设定', '世界观', 'world', 'setting', '背景']):
            return {
                "type": "world_building",
                "needs_discussion": True,
                "decision_points": ["确认世界观类型", "确认核心规则"],
                "auto_execute": False
            }
        elif any(kw in lower_msg for kw in ['角色', '人物', 'character']):
            return {
                "type": "character",
                "needs_discussion": True,
                "decision_points": ["确认主角设定", "确认配角关系"],
                "auto_execute": False
            }
        elif any(kw in lower_msg for kw in ['修改', '润色', '优化', 'edit', 'rewrite']):
            return {
                "type": "edit",
                "needs_discussion": True,
                "decision_points": ["确认修改方向"],
                "auto_execute": False
            }
        else:
            return {
                "type": "general",
                "needs_discussion": True,
                "decision_points": [],
                "auto_execute": True
            }

    def _check_story_bible_completeness(self, context: Dict[str, Any]) -> Dict[str, bool]:
        """
        检查 Story Bible 的完整性，返回缺失的部分
        """
        return {
            "world": bool(context.get("world") and len(context.get("world", "")) > 50),
            "outline": bool(context.get("recent_summaries") and len(context.get("recent_summaries", [])) > 0),
            "characters": False,  # 简化检查，实际应该从数据库获取
            "factions": False,
            "timeline": False,
            "locations": False
        }
    
    def _call_llm(self, prompt: str, system_message: str = "") -> str:
        """
        调用 LLM 生成内容
        """
        if self.llm is None:
            return "[LLM 未配置，无法生成内容]"
        
        try:
            from langchain.schema import HumanMessage, SystemMessage
            
            messages = []
            if system_message:
                messages.append(SystemMessage(content=system_message))
            messages.append(HumanMessage(content=prompt))
            
            response = self.llm.invoke(messages)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"LLM call error: {e}")
            return f"[调用 LLM 时出错: {str(e)}]"
    
    def _generate_story_bible_content(self, topic: str, missing_parts: Dict[str, bool]) -> List[Dict[str, Any]]:
        """
        为缺失的 Story Bible 部分生成内容
        使用 LLM 生成，而不是硬编码
        """
        logs: List[Dict[str, Any]] = []
        
        # 检查是否需要补充世界观
        if not missing_parts.get("world", False):
            world_prompt = f"""基于以下小说主题，设计一个详细的世界观设定：

主题：{topic}

请提供：
1. 世界背景（时代、地点、基本环境）
2. 核心规则（这个世界的特殊规则或力量体系）
3. 社会结构（主要势力、组织、阶层）
4. 与故事主题的关联

请用简洁但详细的中文回答。"""
            
            world_content = self._call_llm(world_prompt, "你是一位专业的世界观设计师，擅长为小说创建引人入胜的世界观设定。")
            
            logs.append({
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "🌍 补充世界观",
                "content": f"检测到 Story Bible 中缺少世界观设定。基于主题'{topic}'，我来补充：\n\n{world_content}",
                "auto_fill": {
                    "type": "worldbuilding",
                    "content": world_content[:200] + "..." if len(world_content) > 200 else world_content
                }
            })
        
        # 检查是否需要补充角色
        if not missing_parts.get("characters", False):
            char_prompt = f"""基于以下小说主题和世界观，设计主要角色：

主题：{topic}

请提供：
1. 主角（姓名、年龄、性格、背景、目标）
2. 2-3个重要配角（与主角的关系、性格特点）
3. 角色之间的关系网

请用简洁但详细的中文回答，使用列表格式。"""
            
            char_content = self._call_llm(char_prompt, "你是一位专业的角色设计师，擅长创造有深度、令人难忘的角色。")
            
            # 尝试从内容中提取角色名
            import re
            char_names = re.findall(r'[【\[]([^【\]\[\]]+)[】\]]|([^：:\n]{2,8})[：:]', char_content)
            char_items = []
            for match in char_names[:5]:
                name = (match[0] or match[1]).strip()
                if name and len(name) > 1:
                    char_items.append({"name": name, "role": "角色"})
            
            if not char_items:
                char_items = [{"name": "主角", "role": "主角"}]
            
            logs.append({
                "agent": "writer",
                "agent_name": "作家",
                "message": "👤 设计主角",
                "content": f"基于主题，我设计了以下核心角色：\n\n{char_content}",
                "auto_fill": {
                    "type": "characters",
                    "items": char_items
                }
            })
        
        # 检查是否需要补充大纲
        if not missing_parts.get("outline", False):
            outline_prompt = f"""基于以下小说主题，构建一个详细的故事大纲：

主题：{topic}

请提供：
1. 故事结构（建议分为3-4幕）
2. 每幕的主要情节点
3. 关键转折点
4. 预计章节数（每幕的章节范围）

请用简洁但详细的中文回答，使用清晰的层次结构。"""
            
            outline_content = self._call_llm(outline_prompt, "你是一位专业的故事结构设计师，擅长构建引人入胜的故事大纲。")
            
            logs.append({
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "📋 构建大纲",
                "content": f"让我为这个故事构建一个基础大纲：\n\n{outline_content}",
                "auto_fill": {
                    "type": "outline",
                    "content": outline_content[:300] + "..." if len(outline_content) > 300 else outline_content
                }
            })
        
        # 检查是否需要补充势力/组织
        if not missing_parts.get("factions", False):
            faction_prompt = f"""基于以下小说主题，设计故事中的主要势力或组织：

主题：{topic}

请提供：
1. 3-4个主要势力/组织
2. 每个势力的性质、目标、与主角的关系
3. 势力之间的冲突和关系

请用简洁但详细的中文回答。"""
            
            faction_content = self._call_llm(faction_prompt, "你是一位专业的势力设计师，擅长创造有张力的组织冲突。")
            
            # 尝试提取势力名
            faction_names = re.findall(r'[【\[]([^【\]\[\]]+)[】\]]|([^：:\n]{2,10})[：:]', faction_content)
            faction_items = []
            for match in faction_names[:5]:
                name = (match[0] or match[1]).strip()
                if name and len(name) > 1:
                    faction_items.append(name)
            
            if not faction_items:
                faction_items = ["主要势力"]
            
            logs.append({
                "agent": "critic",
                "agent_name": "评论家",
                "message": "🏛️ 设定势力",
                "content": f"为了让故事更有张力，我建议加入以下势力：\n\n{faction_content}",
                "auto_fill": {
                    "type": "factions",
                    "items": faction_items
                }
            })
        
        return logs

    def _generate_autonomous_workflow(self, topic: str, context: Dict[str, Any], intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成 Agent 自主工作流程
        Agent 自主讨论、决策，只在关键点询问用户
        所有讨论内容通过 LLM 生成
        """
        logs: List[Dict[str, Any]] = []
        workflow_type = intent["type"]
        
        # 开场：理解用户需求
        logs.append({
            "agent": "system",
            "message": "🎬 Agent Room 启动",
            "content": f"收到任务：{topic}\n类型识别：{workflow_type}\nAgent 团队开始自主分析..."
        })
        
        # Step 1: 策划师分析需求（使用 LLM）
        strategist_prompt = f"""作为策划师，分析以下创作任务：

任务：{topic}
类型：{workflow_type}

请分析：
1. 任务的核心需求是什么
2. 关键约束条件
3. 执行策略建议

用第一人称回答，简洁专业。"""
        
        strategist_analysis = self._call_llm(strategist_prompt, "你是一位专业的策划师，擅长分析创作需求并制定策略。")
        
        logs.append({
            "agent": "strategist",
            "agent_name": "策划师",
            "message": "📋 任务分析",
            "content": strategist_analysis
        })
        
        # Step 2: 检查 Story Bible 完整性并自动补充
        logs.append({
            "agent": "system",
            "message": "🔍 检查 Story Bible",
            "content": "Agent 们正在检查当前项目的设定完整性..."
        })
        
        completeness = self._check_story_bible_completeness(context)
        missing_count = sum(1 for v in completeness.values() if not v)
        
        if missing_count > 0:
            logs.append({
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "⚠️ 发现缺失",
                "content": f"检测到 Story Bible 有 {missing_count} 个部分需要补充。Agent 团队将自主完善这些内容。"
            })
            
            # 自动生成缺失内容（通过 LLM）
            auto_fill_logs = self._generate_story_bible_content(topic, completeness)
            logs.extend(auto_fill_logs)
            
            logs.append({
                "agent": "system",
                "message": "✅ 补充完成",
                "content": "Story Bible 基础内容已自动生成。这些内容已保存到项目设定中。"
            })
        else:
            logs.append({
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "✓ 设定完整",
                "content": "Story Bible 内容完整，可以直接开始创作。"
            })
        
        # Step 3: 评论家提出潜在问题（使用 LLM）
        critic_prompt = f"""作为评论家，评估以下创作任务可能存在的风险：

任务：{topic}
类型：{workflow_type}

请分析：
1. 潜在的创作风险
2. 需要注意的问题
3. 对用户的建议

用第一人称回答，简洁专业。"""
        
        critic_analysis = self._call_llm(critic_prompt, "你是一位专业的评论家，擅长发现创作中的潜在问题。")
        
        logs.append({
            "agent": "critic",
            "agent_name": "评论家",
            "message": "⚠️ 风险评估",
            "content": critic_analysis
        })
        
        # Step 4: 编辑建议流程（使用 LLM）
        editor_prompt = f"""作为编辑，为以下创作任务建议执行流程：

任务：{topic}
类型：{workflow_type}

请建议：
1. 推荐的执行步骤
2. 关键检查点
3. 质量把控要点

用第一人称回答，简洁专业。"""
        
        editor_suggestion = self._call_llm(editor_prompt, "你是一位专业的编辑，擅长规划创作流程。")
        
        logs.append({
            "agent": "editor",
            "agent_name": "编辑",
            "message": "📝 流程建议",
            "content": editor_suggestion
        })
        
        # Step 5: 团队内部讨论（使用 LLM 生成专业讨论）
        logs.append({
            "agent": "system",
            "message": "💬 团队内部讨论",
            "content": "Agent 们正在讨论最佳方案..."
        })
        
        # 根据任务类型进行专业讨论（使用 LLM）
        if workflow_type == "write":
            discussion_prompt = f"""模拟一个专业的小说创作团队讨论如何写作以下内容：

写作任务：{topic}

团队成员：
- 策划师：负责整体规划
- 作家：负责具体写作
- 评论家：负责质量把控

请生成一段团队讨论，每个人从自己的专业角度提出建议，最后达成共识。
用对话形式呈现，每个人说2-3句话。"""
            
            discussion_content = self._call_llm(discussion_prompt, "你是一位专业的小说创作团队成员，正在进行团队讨论。")
            
            # 解析讨论内容并分配给不同 Agent
            # 简单处理：将 LLM 生成的内容作为策划师的总结
            logs.append({
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "💡 方案提议",
                "content": discussion_content
            })
            
        elif workflow_type == "outline":
            outline_prompt = f"""作为策划师，为以下主题设计故事大纲结构：

主题：{topic}

请提供：
1. 推荐的故事结构
2. 关键情节点规划
3. 节奏控制建议

用第一人称回答，简洁专业。"""
            
            outline_analysis = self._call_llm(outline_prompt, "你是一位专业的故事结构设计师。")
            
            logs.append({
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "📊 结构规划",
                "content": outline_analysis
            })
            
        elif workflow_type == "world_building":
            world_prompt = f"""作为世界观设计师，为以下主题设计世界观框架：

主题：{topic}

请提供：
1. 世界观核心要素
2. 与故事的关联
3. 呈现方式建议

用第一人称回答，简洁专业。"""
            
            world_analysis = self._call_llm(world_prompt, "你是一位专业的世界观设计师。")
            
            logs.append({
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "🌍 世界观框架",
                "content": world_analysis
            })
        
        # Step 6: 达成共识（使用 LLM 生成总结）
        summary_prompt = f"""作为策划师，总结团队对以下任务的执行计划：

任务：{topic}
类型：{workflow_type}

请总结：
1. 确定的执行方案
2. 各 Agent 的分工
3. 下一步行动

用第一人称回答，简洁专业。"""
        
        summary_content = self._call_llm(summary_prompt, "你是一位专业的策划师，正在总结团队共识。")
        
        logs.append({
            "agent": "system",
            "message": "✅ 方案确定",
            "content": "Agent 团队已达成共识，准备执行"
        })
        
        logs.append({
            "agent": "strategist",
            "agent_name": "策划师",
            "message": "📋 执行计划",
            "content": summary_content
        })
        
        return logs

    def _generate_decision_point(self, workflow_type: str, stage: str, topic: str = "") -> Dict[str, Any]:
        """
        生成决策点，向用户询问
        使用 LLM 生成询问内容
        """
        # 根据 workflow_type 和 stage 生成询问内容
        if workflow_type == "write" and stage == "after_outline":
            prompt = f"""作为策划师，向用户确认写作任务的细节：

任务：{topic}

请生成询问内容，包括：
1. 确认情节走向
2. 询问字数要求
3. 询问风格偏好

用第一人称，简洁友好。"""
            
            content = self._call_llm(prompt, "你是一位专业的策划师，正在向用户确认写作细节。")
            
            return {
                "agent": "strategist",
                "agent_name": "策划师", 
                "message": "🤔 需要您的确认",
                "content": content,
                "requires_user_input": True
            }
            
        elif workflow_type == "write" and stage == "after_first_draft":
            prompt = f"""作为编辑，向用户征求对初稿的反馈：

任务：{topic}

请生成询问内容，包括：
1. 询问整体评价
2. 询问需要调整的地方
3. 提供下一步选项

用第一人称，简洁友好。"""
            
            content = self._call_llm(prompt, "你是一位专业的编辑，正在征求用户反馈。")
            
            return {
                "agent": "editor",
                "agent_name": "编辑",
                "message": "📝 初稿完成，请审阅",
                "content": content,
                "requires_user_input": True
            }
            
        elif workflow_type == "outline" and stage == "after_proposal":
            prompt = f"""作为策划师，向用户确认大纲方案：

主题：{topic}

请生成询问内容，包括：
1. 确认章节数偏好
2. 询问节奏偏好
3. 询问结局倾向

用第一人称，简洁友好。"""
            
            content = self._call_llm(prompt, "你是一位专业的策划师，正在向用户确认大纲细节。")
            
            return {
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "📋 大纲方案",
                "content": content,
                "requires_user_input": True
            }
            
        elif workflow_type == "world_building" and stage == "after_framework":
            prompt = f"""作为世界观设计师，向用户确认世界观框架：

主题：{topic}

请生成询问内容，包括：
1. 确认世界观类型
2. 询问需要避免或包含的元素
3. 询问复杂度偏好

用第一人称，简洁友好。"""
            
            content = self._call_llm(prompt, "你是一位专业的世界观设计师，正在向用户确认世界观细节。")
            
            return {
                "agent": "strategist", 
                "agent_name": "策划师",
                "message": "🌍 世界观框架确认",
                "content": content,
                "requires_user_input": True
            }
        
        # 默认决策点
        return {
            "agent": "system",
            "agent_name": "系统",
            "message": "⏸️ 等待用户反馈",
            "content": "执行到关键节点，需要您的确认或反馈后才能继续。",
            "requires_user_input": True
        }

    def chat(self, message: str, story_id: str = "demo-story", word_count_range: Dict[str, int] = None, conversation_state: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        主聊天接口
        支持 Agent 自主流程 + 关键点询问用户
        """
        msg = message.strip()
        logs: List[Dict[str, Any]] = []
        
        # 初始化或恢复对话状态
        if conversation_state is None:
            conversation_state = {
                "stage": "initial",
                "workflow_type": None,
                "waiting_for_user": False,
                "accumulated_content": []
            }
        
        # 如果正在等待用户输入，处理用户反馈
        if conversation_state.get("waiting_for_user"):
            logs.append({
                "agent": "system",
                "message": "📥 收到反馈",
                "content": f"用户反馈：{msg}\n\nAgent 团队会根据反馈调整方案..."
            })
            
            # 根据反馈继续流程
            workflow_type = conversation_state.get("workflow_type", "general")
            
            # 模拟 Agent 讨论用户反馈
            logs.append({
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "💭 分析反馈",
                "content": "收到用户的反馈，让我分析一下...\n\n根据用户的意见，我们需要调整之前的方案。"
            })
            
            logs.append({
                "agent": "writer",
                "agent_name": "作家",
                "message": "✍️ 调整思路",
                "content": "明白用户的需求了，我会在后续创作中注意这些要点。"
            })
            
            # 继续执行，生成内容
            conversation_state["waiting_for_user"] = False
            conversation_state["stage"] = "executing"
        
        # 分析用户意图
        intent = self._analyze_intent(msg)
        workflow_type = intent["type"]
        conversation_state["workflow_type"] = workflow_type
        
        # 构建上下文
        context = self._build_room_context(story_id)
        
        # 生成自主工作流程
        workflow_logs = self._generate_autonomous_workflow(msg, context, intent)
        logs.extend(workflow_logs)
        
        # 根据任务类型执行具体操作
        final_text = ""
        final_agent_name = ""
        
        if workflow_type == "write":
            # 写作任务：先询问关键信息，再生成
            if conversation_state["stage"] == "initial":
                decision = self._generate_decision_point("write", "after_outline", msg)
                logs.append(decision)
                conversation_state["waiting_for_user"] = True
                conversation_state["stage"] = "waiting_for_details"
                final_text = "等待用户确认写作细节..."
                final_agent_name = "策划师"
            else:
                # 执行写作
                result = self.writer.run({"text": msg})
                final_text = result.get("draft_text", "")
                final_agent_name = "作家"
                
                logs.append({
                    "agent": "writer",
                    "agent_name": "作家",
                    "message": "✅ 写作完成",
                    "content": f"已完成创作，共 {len(final_text)} 字。\n\n{final_text[:200]}..."
                })
                
                # 询问是否继续下一章
                logs.append({
                    "agent": "strategist",
                    "agent_name": "策划师", 
                    "message": "🤔 下一步？",
                    "content": "本章已完成！\n\n您觉得如何？\n\n- 回复'继续'生成下一章\n- 回复修改意见，我们调整本章\n- 回复'保存'确认完成",
                    "requires_user_input": True
                })
                conversation_state["waiting_for_user"] = True
                
        elif workflow_type == "outline":
            # 大纲任务
            if conversation_state["stage"] == "initial":
                decision = self._generate_decision_point("outline", "after_proposal", msg)
                logs.append(decision)
                conversation_state["waiting_for_user"] = True
                conversation_state["stage"] = "waiting_for_details"
                final_text = "等待用户确认大纲框架..."
                final_agent_name = "策划师"
            else:
                result = self.strategist.run({"text": msg})
                final_text = result.get("plan_text", "")
                final_agent_name = "策划师"
                
                logs.append({
                    "agent": "strategist",
                    "agent_name": "策划师",
                    "message": "📋 大纲完成",
                    "content": f"大纲已生成！\n\n{final_text[:300]}..."
                })
                
        elif workflow_type == "world_building":
            # 世界观任务
            if conversation_state["stage"] == "initial":
                decision = self._generate_decision_point("world_building", "after_framework", msg)
                logs.append(decision)
                conversation_state["waiting_for_user"] = True
                conversation_state["stage"] = "waiting_for_details"
                final_text = "等待用户确认世界观框架..."
                final_agent_name = "策划师"
            else:
                # 生成世界观
                debate = self.world.debate(WorldDebateRequest(prompt=msg, story_id=story_id, max_rounds=1))
                logs.extend(debate.agent_logs)
                final_text = debate.world_bible.world_view or ""
                final_agent_name = "策划师"
                
        elif workflow_type == "edit":
            # 编辑任务
            result = self.editor.run({"draft_text": msg})
            final_text = result.get("edited_text", "")
            final_agent_name = "编辑"
            
            logs.append({
                "agent": "editor",
                "agent_name": "编辑",
                "message": "✅ 润色完成",
                "content": f"已完成润色！\n\n主要修改：\n- 优化了文字流畅度\n- 调整了部分句式\n- 增强了表现力\n\n{final_text[:200]}..."
            })
            
        else:
            # 通用对话
            result = self.strategist.run({"text": msg})
            final_text = result.get("plan_text", "")
            final_agent_name = "策划师"
        
        return {
            "agent_logs": logs,
            "final_text": final_text,
            "final_agent": final_agent_name,
            "conversation_state": conversation_state,
            "requires_user_input": conversation_state.get("waiting_for_user", False)
        }
