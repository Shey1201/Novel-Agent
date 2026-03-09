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
    
    def _generate_story_bible_content(self, topic: str, missing_parts: Dict[str, bool]) -> List[Dict[str, Any]]:
        """
        为缺失的 Story Bible 部分生成内容
        """
        logs: List[Dict[str, Any]] = []
        
        # 检查是否需要补充世界观
        if not missing_parts.get("world", False):
            logs.append({
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "🌍 补充世界观",
                "content": f"检测到 Story Bible 中缺少世界观设定。基于主题'{topic}'，我来补充：\n\n【世界观框架】\n- 故事发生在一个现代都市背景\n- 社会结构：普通人类社会，存在隐秘的超自然元素\n- 核心规则：主角拥有特殊能力，但需要在日常生活中隐藏\n- 时代背景：当代，科技发达但神秘力量依然存在\n\n这个设定可以支撑青春校园+奇幻的故事类型。",
                "auto_fill": {
                    "type": "worldbuilding",
                    "content": "现代都市背景，存在隐秘超自然元素。主角拥有特殊能力但需隐藏。"
                }
            })
        
        # 检查是否需要补充角色
        if not missing_parts.get("characters", False):
            logs.append({
                "agent": "writer",
                "agent_name": "作家",
                "message": "👤 设计主角",
                "content": "基于主题，我设计了以下核心角色：\n\n【主角】\n- 姓名：林墨（暂定）\n- 年龄：17岁\n- 性格：内向敏感，但内心坚韧\n- 背景：普通高中生，偶然发现自己有特殊能力\n- 目标：在保护秘密的同时，寻找自己能力的来源\n\n【重要配角】\n- 苏晴：主角的同学，阳光开朗，可能是第一个发现主角秘密的人\n- 陈教授：神秘的历史老师，似乎知道一些关于超自然力量的秘密",
                "auto_fill": {
                    "type": "characters",
                    "items": [
                        {"name": "林墨", "role": "主角"},
                        {"name": "苏晴", "role": "同学/朋友"},
                        {"name": "陈教授", "role": "导师"}
                    ]
                }
            })
        
        # 检查是否需要补充大纲
        if not missing_parts.get("outline", False):
            logs.append({
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "📋 构建大纲",
                "content": "让我为这个故事构建一个基础大纲：\n\n【第一幕：觉醒】（第1-5章）\n- 主角发现自己的能力\n- 试图隐藏但遇到困难\n- 遇到第一个关键人物\n\n【第二幕：探索】（第6-15章）\n- 逐渐了解能力来源\n- 建立人际关系\n- 发现潜在威胁\n\n【第三幕：冲突】（第16-25章）\n- 秘密面临暴露危机\n- 与反派势力对抗\n- 关键抉择时刻\n\n【第四幕：结局】（第26-30章）\n- 最终对决\n- 能力完全觉醒\n- 新的开始",
                "auto_fill": {
                    "type": "outline",
                    "content": "第一幕：觉醒（1-5章）→ 第二幕：探索（6-15章）→ 第三幕：冲突（16-25章）→ 第四幕：结局（26-30章）"
                }
            })
        
        # 检查是否需要补充势力/组织
        if not missing_parts.get("factions", False):
            logs.append({
                "agent": "critic",
                "agent_name": "评论家",
                "message": "🏛️ 设定势力",
                "content": "为了让故事更有张力，我建议加入以下势力：\n\n【守秘人协会】\n- 性质：隐秘组织\n- 目标：保护超自然秘密，维持平衡\n- 对主角态度：观察中，可能招募\n\n【觉醒者联盟】\n- 性质：松散的能力者组织\n- 目标：帮助新觉醒者适应能力\n- 对主角态度：友好，提供帮助\n\n【影子议会】\n- 性质：神秘势力\n- 目标：利用能力者达到某种目的\n- 对主角态度：敌视，可能制造麻烦",
                "auto_fill": {
                    "type": "factions",
                    "items": ["守秘人协会", "觉醒者联盟", "影子议会"]
                }
            })
        
        return logs

    def _generate_autonomous_workflow(self, topic: str, context: Dict[str, Any], intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成 Agent 自主工作流程
        Agent 自主讨论、决策，只在关键点询问用户
        """
        logs: List[Dict[str, Any]] = []
        workflow_type = intent["type"]
        
        # 开场：理解用户需求
        logs.append({
            "agent": "system",
            "message": "🎬 Agent Room 启动",
            "content": f"收到任务：{topic}\n类型识别：{workflow_type}\nAgent 团队开始自主分析..."
        })
        
        # Step 1: 策划师分析需求
        logs.append({
            "agent": "strategist",
            "agent_name": "策划师",
            "message": "📋 任务分析",
            "content": f"我理解用户的需求是：{topic}\n\n让我分析一下关键点：\n1. 这是一个{workflow_type}类型的任务\n2. 需要先明确目标和约束条件\n3. 制定执行策略"
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
            
            # 自动生成缺失内容
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
        
        # Step 3: 评论家提出潜在问题
        logs.append({
            "agent": "critic",
            "agent_name": "评论家",
            "message": "⚠️ 风险评估",
            "content": "在开始前，我需要考虑几个潜在问题：\n- 用户是否有明确的风格偏好？\n- 是否有特定的字数或篇幅要求？\n- 目标读者群体是谁？\n\n如果这些信息不明确，可能会偏离用户预期。"
        })
        
        # Step 4: 编辑建议流程
        logs.append({
            "agent": "editor",
            "agent_name": "编辑",
            "message": "📝 流程建议",
            "content": "建议按以下流程执行：\n1. 先进行内部讨论，明确方案\n2. 在关键决策点向用户确认\n3. 根据反馈调整\n4. 最终输出成果"
        })
        
        # Step 5: 团队内部讨论（模拟自主决策）
        logs.append({
            "agent": "system",
            "message": "💬 团队内部讨论",
            "content": "Agent 们正在讨论最佳方案..."
        })
        
        # 根据任务类型进行专业讨论
        if workflow_type == "write":
            logs.append({
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "💡 方案提议",
                "content": "我建议这样安排：先确定本章的核心冲突和情感走向，然后由作家负责具体写作，编辑润色，最后评论家审核。"
            })
            
            logs.append({
                "agent": "writer",
                "agent_name": "作家",
                "message": "✍️ 执行思路",
                "content": "我同意策划师的方案。在具体写作时，我会注意场景切换的自然性，对话要符合人物性格，同时保持节奏紧凑。"
            })
            
            logs.append({
                "agent": "critic",
                "agent_name": "评论家",
                "message": "👁️ 质量把控",
                "content": "我会重点关注：情节逻辑是否通顺、人物动机是否合理、是否存在让读者出戏的描写。"
            })
            
        elif workflow_type == "outline":
            logs.append({
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "📊 结构规划",
                "content": "我建议采用三幕式结构：铺垫-冲突-高潮-结局。先确定关键情节点，再细化每章内容。"
            })
            
            logs.append({
                "agent": "critic",
                "agent_name": "评论家",
                "message": "📈 节奏建议",
                "content": "要注意节奏把控，避免前期铺垫过长导致读者流失。建议在每章结尾设置小悬念。"
            })
            
        elif workflow_type == "world_building":
            logs.append({
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "🌍 世界观框架",
                "content": "我们需要确定：世界的基本规则、力量体系（如果有）、社会结构、历史背景。这些要服务于故事主题。"
            })
            
            logs.append({
                "agent": "writer",
                "agent_name": "作家",
                "message": "🎨 呈现方式",
                "content": "世界观要通过故事自然展现，避免大段说明。建议设计几个典型场景来体现世界特点。"
            })
        
        # Step 5: 达成共识
        logs.append({
            "agent": "system",
            "message": "✅ 方案确定",
            "content": "Agent 团队已达成共识，准备执行"
        })
        
        logs.append({
            "agent": "strategist",
            "agent_name": "策划师",
            "message": "📋 执行计划",
            "content": f"我们确定的方案是：\n1. 针对'{topic}'进行创作\n2. 按照专业流程执行\n3. 在关键节点向用户汇报进展\n\n现在开始执行第一阶段..."
        })
        
        return logs

    def _generate_decision_point(self, workflow_type: str, stage: str) -> Dict[str, Any]:
        """
        生成决策点，向用户询问
        """
        decision_points = {
            "write": {
                "after_outline": {
                    "agent": "strategist",
                    "agent_name": "策划师", 
                    "message": "🤔 需要您的确认",
                    "content": "大纲已经规划完成。在开始正式写作前，想确认一下：\n\n1. 这个情节走向是否符合您的预期？\n2. 您希望这一章的字数大概在什么范围？\n3. 有没有特别想要强调的情感或主题？\n\n请告诉我，我们会据此调整。",
                    "requires_user_input": True
                },
                "after_first_draft": {
                    "agent": "editor",
                    "agent_name": "编辑",
                    "message": "📝 初稿完成，请审阅",
                    "content": "初稿已经完成。在继续润色前，想听听您的意见：\n\n- 整体风格是否符合您的要求？\n- 有没有需要调整的情节或描写？\n- 人物表现是否自然？\n\n您可以直接回复修改意见，或者回复'继续'让编辑进行润色。",
                    "requires_user_input": True
                }
            },
            "outline": {
                "after_proposal": {
                    "agent": "strategist",
                    "agent_name": "策划师",
                    "message": "📋 大纲方案",
                    "content": "我们讨论出了一个大纲框架。在细化前，想确认几个关键点：\n\n1. 总章节数您有预期吗？（建议15-30章）\n2. 希望故事节奏偏快还是偏慢？\n3. 结局倾向于圆满、开放式还是悲剧？\n\n请给出您的偏好，我们会据此优化大纲。",
                    "requires_user_input": True
                }
            },
            "world_building": {
                "after_framework": {
                    "agent": "strategist", 
                    "agent_name": "策划师",
                    "message": "🌍 世界观框架确认",
                    "content": "世界观的基本框架已经确定。在详细展开前，想确认：\n\n1. 这个世界观类型是否符合您的设想？\n2. 有没有特别想要避免或一定要包含的元素？\n3. 力量体系（如果有）的复杂度您希望如何？\n\n请告诉我们，避免偏离您的预期。",
                    "requires_user_input": True
                }
            }
        }
        
        return decision_points.get(workflow_type, {}).get(stage, {
            "agent": "system",
            "agent_name": "系统",
            "message": "⏸️ 等待用户反馈",
            "content": "执行到关键节点，需要您的确认或反馈后才能继续。",
            "requires_user_input": True
        })

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
                decision = self._generate_decision_point("write", "after_outline")
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
                decision = self._generate_decision_point("outline", "after_proposal")
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
                decision = self._generate_decision_point("world_building", "after_framework")
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
