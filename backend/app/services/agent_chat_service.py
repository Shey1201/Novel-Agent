from typing import Any, Callable, Dict, List, Optional
import random
import json
import time
from datetime import datetime

from app.agents.critic_agent import CriticAgent
from app.agents.editor_agent import EditorAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.strategist_agent import StrategistAgent
from app.agents.writing_agent import WritingAgent
from app.agents.reader_agent import ReaderAgent
from app.agents.consistency_agent import ConsistencyAgent
from app.memory.story_memory import StoryBible, StoryMemory, ChapterSummary
from app.memory.novel_memory import novel_memory
from app.memory.skill_memory import skill_memory
from app.services.chapter_service import load_memory, save_memory
from app.services.world_service import WorldDebateRequest, WorldService
from app.core.ai_config import get_llm_with_fallback
from app.core.token_budget_manager import TokenBudgetManager, AgentType
from app.core.agent_cache import AgentCache, CacheConfig
from app.core.agent_discussion_engine import get_agent_discussion_engine, DiscussionContext
from app.core.author_decision_system import get_author_decision_system, QuestionType, QuestionPriority
from app.core.narrative_intelligence_engine import get_narrative_intelligence_engine

# 尝试导入 langchain，如果失败则在运行时处理
try:
    from langchain.schema import HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    HumanMessage = None
    SystemMessage = None


class AgentChatService:
    def __init__(self, llm: Any = None):
        # 如果没有传入 llm，仅从数据库 AI 配置获取
        self.llm = llm or get_llm_with_fallback()
        self.strategist = StrategistAgent(llm=self.llm)
        self.writer = WritingAgent(llm=self.llm)
        self.editor = EditorAgent(llm=self.llm)
        self.critic = CriticAgent(llm=self.llm)
        self.reader = ReaderAgent(llm=self.llm)
        self.consistency = ConsistencyAgent(llm=self.llm)
        self.memory = MemoryAgent(llm=self.llm)
        self.world = WorldService(llm=self.llm)

        # 初始化讨论引擎、作者决策系统、叙事智能引擎
        self.discussion_engine = get_agent_discussion_engine()
        self.author_decision = get_author_decision_system()
        self.narrative_engine = get_narrative_intelligence_engine()

        # 初始化 Token 预算管理器
        self.token_budget_manager = TokenBudgetManager()
        
        # 初始化缓存
        cache_config = CacheConfig(
            max_size=1000,
            ttl_hours=24,
            enable_planner_cache=True,
            enable_conflict_cache=True,
            enable_consistency_cache=True
        )
        self.agent_cache = AgentCache(config=cache_config)
        
        # 性能监控数据
        self.performance_stats = {
            "agent_calls": {},
            "total_tokens": 0,
            "start_time": None
        }

    def _record_agent_call(self, agent_name: str, start_time: float, tokens_used: int = 0):
        """记录 Agent 调用性能数据"""
        duration = time.time() - start_time
        if agent_name not in self.performance_stats["agent_calls"]:
            self.performance_stats["agent_calls"][agent_name] = {
                "count": 0,
                "total_duration": 0,
                "total_tokens": 0
            }
        self.performance_stats["agent_calls"][agent_name]["count"] += 1
        self.performance_stats["agent_calls"][agent_name]["total_duration"] += duration
        self.performance_stats["agent_calls"][agent_name]["total_tokens"] += tokens_used
        self.performance_stats["total_tokens"] += tokens_used

    def _get_cache_key(self, agent_type: str, context: Dict[str, Any], prompt: str = "") -> str:
        """生成缓存 key"""
        import hashlib
        key_data = f"{agent_type}:{json.dumps(context, sort_keys=True)}:{prompt[:200]}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _check_token_budget(self, chapter_id: str, agent_type: AgentType, estimated_tokens: int = 1000) -> bool:
        """检查 Token 预算是否充足"""
        if not chapter_id:
            return True
        
        budget = self.token_budget_manager.chapter_budgets.get(chapter_id)
        if not budget or not budget.is_enabled:
            return True
        
        # 检查是否超预算
        if budget.is_over_budget(agent_type):
            return False
        
        # 检查剩余预算
        remaining = budget.get_remaining_budget()
        return remaining >= estimated_tokens

    def _record_token_usage(self, chapter_id: str, agent_type: AgentType, tokens_used: int):
        """记录 Token 使用情况"""
        if chapter_id:
            self.token_budget_manager.record_usage(chapter_id, agent_type, tokens_used)

    def _safe_agent_call(self, agent_name: str, agent, input_data: Dict[str, Any], 
                         chapter_id: str = None, agent_type: AgentType = None,
                         use_cache: bool = False, cache_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        安全地调用 Agent，包含错误处理、性能监控和缓存
        
        Args:
            agent_name: Agent 名称
            agent: Agent 实例
            input_data: 输入数据
            chapter_id: 章节ID（用于 Token 预算）
            agent_type: Agent 类型（用于 Token 预算）
            use_cache: 是否使用缓存
            cache_context: 缓存上下文
            
        Returns:
            Agent 执行结果
        """
        start_time = time.time()
        
        # 检查 Token 预算
        if chapter_id and agent_type:
            if not self._check_token_budget(chapter_id, agent_type, estimated_tokens=1000):
                return {
                    "error": f"Token 预算不足，无法执行 {agent_name}",
                    "feedback": f"⚠️ Token 预算不足，请检查设置或重置预算"
                }
        
        # 检查缓存
        if use_cache and cache_context:
            cache_key = self._get_cache_key(agent_name, cache_context, str(input_data)[:200])
            cached_result = self.agent_cache.get(agent_name, cache_context.get("story_id", ""), 
                                                 cache_context.get("chapter_id", ""), cache_context)
            if cached_result:
                self._record_agent_call(agent_name, start_time, 0)
                return cached_result
        
        try:
            # 执行 Agent
            result = agent.run(input_data)
            
            # 记录性能数据
            duration = time.time() - start_time
            self._record_agent_call(agent_name, start_time, 0)
            
            # 记录 Token 使用（估算）
            if chapter_id and agent_type:
                estimated_tokens = len(str(input_data)) + len(str(result)) // 4
                self._record_token_usage(chapter_id, agent_type, estimated_tokens)
            
            # 保存到缓存
            if use_cache and cache_context:
                self.agent_cache.set(agent_name, cache_context.get("story_id", ""),
                                    cache_context.get("chapter_id", ""), cache_context, result)
            
            return result
            
        except Exception as e:
            print(f"Agent {agent_name} 执行出错: {e}")
            return {
                "error": str(e),
                "feedback": f"⚠️ {agent_name} 执行失败: {str(e)}"
            }

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
            return "当前未检测到可用的 AI 配置。请在设置中填写并启用 API Key、模型与 Base URL。"
        
        if not LANGCHAIN_AVAILABLE:
            return "[langchain 未安装，无法生成内容]"
        
        try:
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
        
        # 检查 LLM 是否已配置
        if self.llm is None:
            return [{
                "agent": "system",
                "agent_name": "系统",
                "message": "⚠️ AI 配置不可用",
                "content": "当前无法调用大模型。请前往“系统设置 / AI 配置”确认已填写 API Key、模型，并开启启用开关后重试。"
            }]
        
        # 检查是否需要补充世界观
        if not missing_parts.get("world", False):
            world_prompt = f"""作为策划师，基于以下小说主题设计世界观并说明你的思考过程：

主题：{topic}

请用第一人称回答：
1. 你检测到什么设定缺失
2. 基于主题设计什么样的世界观
3. 具体的世界背景、核心规则、社会结构

请用简洁但详细的中文回答，以"检测到 Story Bible 中缺少世界观设定..."开头。"""
            
            world_content = self._call_llm(world_prompt, "你是一位专业的世界观设计师，擅长为小说创建引人入胜的世界观设定。")
            
            logs.append({
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "🌍 补充世界观",
                "content": world_content,
                "auto_fill": {
                    "type": "worldbuilding",
                    "content": world_content[:200] + "..." if len(world_content) > 200 else world_content
                }
            })
        
        # 检查是否需要补充角色
        if not missing_parts.get("characters", False):
            char_prompt = f"""作为作家，基于以下小说主题设计主要角色并说明你的设计思路：

主题：{topic}

请用第一人称回答：
1. 你基于什么考虑设计这些角色
2. 主角和配角的详细设定（姓名、年龄、性格、背景、目标）
3. 角色之间的关系网

请用简洁但详细的中文回答，以"基于主题..."开头。"""
            
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
                "content": char_content,
                "auto_fill": {
                    "type": "characters",
                    "items": char_items
                }
            })
        
        # 检查是否需要补充大纲
        if not missing_parts.get("outline", False):
            outline_prompt = f"""作为策划师，基于以下小说主题构建故事大纲并说明你的设计思路：

主题：{topic}

请用第一人称回答：
1. 你为这个故事选择什么样的结构
2. 每幕的主要情节点和关键转折点
3. 预计章节数规划

请用简洁但详细的中文回答，以"让我为这个故事构建..."开头。"""
            
            outline_content = self._call_llm(outline_prompt, "你是一位专业的故事结构设计师，擅长构建引人入胜的故事大纲。")
            
            logs.append({
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "📋 构建大纲",
                "content": outline_content,
                "auto_fill": {
                    "type": "outline",
                    "content": outline_content[:300] + "..." if len(outline_content) > 300 else outline_content
                }
            })
        
        # 检查是否需要补充势力/组织
        if not missing_parts.get("factions", False):
            faction_prompt = f"""作为评论家，基于以下小说主题设计主要势力或组织并说明你的设计思路：

主题：{topic}

请用第一人称回答：
1. 你为什么要为这些势力/组织
2. 每个势力的性质、目标、与主角的关系
3. 势力之间的冲突和关系

请用简洁但详细的中文回答，以"为了让故事更有张力..."开头。"""
            
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
                "content": faction_content,
                "auto_fill": {
                    "type": "factions",
                    "items": faction_items
                }
            })
        
        return logs

    def _save_story_bible_to_database(self, story_id: str, generated_content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        将生成的 Story Bible 内容保存到数据库
        包括：世界观、角色、大纲、势力等
        """
        saved_items = {
            "worldbuilding": [],
            "characters": [],
            "outline": None,
            "factions": []
        }
        
        try:
            # 获取小说信息
            novel = novel_memory.get_novel(story_id)
            if not novel:
                print(f"[AgentChatService] Novel not found: {story_id}")
                return saved_items
            
            # 提取生成的内容
            for log in generated_content:
                auto_fill = log.get("auto_fill", {})
                content_type = auto_fill.get("type", "")
                
                if content_type == "worldbuilding":
                    # 保存世界观到 assets 表
                    content = auto_fill.get("content", "")
                    if content:
                        try:
                            asset_id = skill_memory.create_asset({
                                "name": f"{novel.title} - 世界观",
                                "type": "worldbuilding",
                                "description": content[:500] if len(content) > 500 else content,
                                "content": {"detail": content},
                                "novel_id": story_id,
                                "is_global": False
                            })
                            if asset_id:
                                saved_items["worldbuilding"].append(asset_id)
                                print(f"[AgentChatService] Saved worldbuilding asset: {asset_id}")
                        except Exception as e:
                            print(f"[AgentChatService] Error saving worldbuilding: {e}")
                
                elif content_type == "characters":
                    # 保存角色到 assets 表
                    items = auto_fill.get("items", [])
                    for char in items:
                        try:
                            char_name = char.get("name", "未命名角色")
                            asset_id = skill_memory.create_asset({
                                "name": char_name,
                                "type": "characters",
                                "description": f"角色设定：{char_name}",
                                "content": char,
                                "novel_id": story_id,
                                "is_global": False
                            })
                            if asset_id:
                                saved_items["characters"].append(asset_id)
                                print(f"[AgentChatService] Saved character asset: {asset_id}")
                        except Exception as e:
                            print(f"[AgentChatService] Error saving character: {e}")
                
                elif content_type == "outline":
                    # 保存大纲到小说表
                    content = auto_fill.get("content", "")
                    if content:
                        try:
                            # 更新小说的大纲字段
                            novel_memory.update_novel(story_id, outline=content)
                            saved_items["outline"] = story_id
                            print(f"[AgentChatService] Saved outline to novel: {story_id}")
                        except Exception as e:
                            print(f"[AgentChatService] Error saving outline: {e}")
                
                elif content_type == "factions":
                    # 保存势力到 assets 表
                    items = auto_fill.get("items", [])
                    for faction_name in items:
                        try:
                            asset_id = skill_memory.create_asset({
                                "name": faction_name,
                                "type": "factions",
                                "description": f"势力设定：{faction_name}",
                                "content": {"name": faction_name},
                                "novel_id": story_id,
                                "is_global": False
                            })
                            if asset_id:
                                saved_items["factions"].append(asset_id)
                                print(f"[AgentChatService] Saved faction asset: {asset_id}")
                        except Exception as e:
                            print(f"[AgentChatService] Error saving faction: {e}")
            
            return saved_items
            
        except Exception as e:
            print(f"[AgentChatService] Error in _save_story_bible_to_database: {e}")
            return saved_items

    def _generate_autonomous_workflow(
        self,
        topic: str,
        context: Dict[str, Any],
        intent: Dict[str, Any],
        story_id: str = "demo-story",
        conversation_state: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        生成 Agent 自主工作流程
        Agent 自主讨论、决策，只在关键点询问用户
        所有讨论内容通过 LLM 生成
        """
        if conversation_state is None:
            conversation_state = {}
        logs: List[Dict[str, Any]] = []
        workflow_type = intent["type"]
        
        # 检查 LLM 是否已配置
        if self.llm is None:
            return [{
                "agent": "system",
                "agent_name": "系统",
                "message": "⚠️ AI 配置不可用",
                "content": "当前无法调用大模型。请前往“系统设置 / AI 配置”确认已填写 API Key、模型，并开启启用开关后重试。"
            }]
        
        # 开场：使用 LLM 生成启动消息
        startup_prompt = f"""作为系统，宣布 Agent Room 启动并说明当前任务：

任务：{topic}
类型：{workflow_type}

请用第一人称宣布启动，简洁专业。"""
        
        startup_content = self._call_llm(startup_prompt, "你是 Agent Room 的系统管理员。")
        
        logs.append({
            "agent": "system",
            "message": "🎬 Agent Room 启动",
            "content": startup_content
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
        check_prompt = f"""作为系统，宣布正在检查 Story Bible 完整性：

任务：{topic}

请用第一人称说明正在进行的检查工作，简洁专业。"""
        
        check_content = self._call_llm(check_prompt, "你是 Agent Room 的系统管理员。")
        
        logs.append({
            "agent": "system",
            "message": "🔍 检查 Story Bible",
            "content": check_content
        })
        
        completeness = self._check_story_bible_completeness(context)
        missing_count = sum(1 for v in completeness.values() if not v)
        
        if missing_count > 0:
            missing_prompt = f"""作为策划师，宣布发现 Story Bible 有 {missing_count} 个部分需要补充：

任务：{topic}
缺失部分数：{missing_count}

请用第一人称说明发现的问题和接下来的行动计划，简洁专业。"""
            
            missing_content = self._call_llm(missing_prompt, "你是一位专业的策划师。")
            
            logs.append({
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "⚠️ 发现缺失",
                "content": missing_content
            })
            
            # 自动生成缺失内容（通过 LLM）
            auto_fill_logs = self._generate_story_bible_content(topic, completeness)
            logs.extend(auto_fill_logs)
            
            # 询问用户是否保存生成的内容
            save_summary = []
            for log in auto_fill_logs:
                auto_fill = log.get("auto_fill", {})
                content_type = auto_fill.get("type", "")
                if content_type == "worldbuilding":
                    save_summary.append("世界观")
                elif content_type == "characters":
                    items = auto_fill.get("items", [])
                    save_summary.append(f"角色({len(items)}个)")
                elif content_type == "outline":
                    save_summary.append("大纲")
                elif content_type == "factions":
                    items = auto_fill.get("items", [])
                    save_summary.append(f"势力({len(items)}个)")
            
            if save_summary:
                # 将生成的内容暂存到 conversation_state，等待用户确认
                conversation_state["pending_save"] = {
                    "story_id": story_id,
                    "logs": auto_fill_logs,
                    "summary": save_summary
                }
                conversation_state["waiting_for_user"] = True
                conversation_state["stage"] = "waiting_save_confirmation"
                
                logs.append({
                    "agent": "system",
                    "agent_name": "系统",
                    "message": "💾 保存确认",
                    "content": f"已生成以下内容：{', '.join(save_summary)}\n\n是否保存到数据库？\n- 回复「确认」保存所有内容\n- 回复「取消」不保存\n- 回复「修改」并提供意见进行调整",
                    "requires_user_input": True
                })
            
            complete_prompt = f"""作为系统，宣布 Story Bible 补充完成：

任务：{topic}

请用第一人称说明补充工作已完成，简洁专业。"""
            
            complete_content = self._call_llm(complete_prompt, "你是 Agent Room 的系统管理员。")
            
            logs.append({
                "agent": "system",
                "message": "✅ 补充完成",
                "content": complete_content
            })
        else:
            complete_prompt = f"""作为策划师，宣布 Story Bible 内容完整：

任务：{topic}

请用第一人称说明设定完整，可以直接开始创作，简洁专业。"""
            
            complete_content = self._call_llm(complete_prompt, "你是一位专业的策划师。")
            
            logs.append({
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "✓ 设定完整",
                "content": complete_content
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
        discuss_prompt = f"""作为系统，宣布 Agent 们正在进行团队内部讨论：

任务：{topic}
类型：{workflow_type}

请用第一人称说明讨论正在进行，简洁专业。"""
        
        discuss_content = self._call_llm(discuss_prompt, "你是 Agent Room 的系统管理员。")
        
        logs.append({
            "agent": "system",
            "message": "💬 团队内部讨论",
            "content": discuss_content
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
        
        consensus_prompt = f"""作为系统，宣布 Agent 团队已达成共识：

任务：{topic}
类型：{workflow_type}

请用第一人称宣布共识已达成，准备执行，简洁专业。"""
        
        consensus_content = self._call_llm(consensus_prompt, "你是 Agent Room 的系统管理员。")
        
        logs.append({
            "agent": "system",
            "message": "✅ 方案确定",
            "content": consensus_content
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
        default_prompt = f"""作为系统，向用户说明需要等待反馈：

任务：{topic}
阶段：{stage}
类型：{workflow_type}

请用第一人称说明执行到关键节点，需要用户确认或反馈，简洁友好。"""
        
        default_content = self._call_llm(default_prompt, "你是 Agent Room 的系统管理员。")
        
        return {
            "agent": "system",
            "agent_name": "系统",
            "message": "⏸️ 等待用户反馈",
            "content": default_content,
            "requires_user_input": True
        }

    def chat(self, message: str, story_id: str = "demo-story", chapter_id: str = None, chapter_name: str = None, word_count_range: Dict[str, int] = None, conversation_state: Dict[str, Any] = None, story_name: str = None) -> Dict[str, Any]:
        """
        主聊天接口
        支持 Agent 自主流程 + 关键点询问用户
        
        Args:
            message: 用户消息
            story_id: 故事ID
            chapter_id: 章节ID（可选，用于关联章节总结）
            chapter_name: 章节名称（可选，供显示用）
            word_count_range: 字数范围
            conversation_state: 对话状态
            story_name: 小说名称（可选，供显示用）
        """
        msg = message.strip()
        logs: List[Dict[str, Any]] = []
        trace_data: List[Dict[str, Any]] = []
        
        # 初始化或恢复对话状态
        if conversation_state is None:
            conversation_state = {
                "stage": "initial",
                "workflow_type": None,
                "waiting_for_user": False,
                "accumulated_content": [],
                "story_id": story_id,
                "story_name": story_name,
                "chapter_id": chapter_id
            }

        # 如果传入了新的 story_name，更新到 conversation_state
        if story_name:
            conversation_state["story_name"] = story_name
        
        # 如果传入了新的 chapter_name，更新到 conversation_state
        if chapter_name:
            conversation_state["chapter_name"] = chapter_name

        # 检查并确认 story_id 和 chapter_id
        if conversation_state["stage"] == "initial" and not conversation_state.get("context_confirmed"):
            # 使用 story_name 显示给用户，如果没传则显示 story_id
            display_name = story_name or story_id
            # 使用 chapter_name 显示给用户，如果没传则显示 chapter_id
            display_chapter = chapter_name or chapter_id or '未指定'
            confirm_prompt = f"""作为系统，向用户确认当前工作上下文：

检测到的工作上下文：
- 小说名称: {display_name}
- 章节名称: {display_chapter}

请用第一人称询问用户是否在这个上下文下继续工作，简洁友好。"""
            
            confirm_content = self._call_llm(confirm_prompt, "你是 Agent Room 的系统管理员。")
            
            logs.append({
                "agent": "system",
                "agent_name": "系统",
                "message": "📍 确认上下文",
                "content": confirm_content,
                "requires_user_input": True
            })
            
            conversation_state["waiting_for_user"] = True
            conversation_state["context_confirmed"] = True
            
            return {
                "agent_logs": logs,
                "final_text": "",
                "final_agent": "system",
                "conversation_state": conversation_state,
                "requires_user_input": True
            }
        
        # 如果正在等待用户输入，处理用户反馈
        if conversation_state.get("waiting_for_user") and conversation_state.get("stage") != "initial":
            # 检查是否是保存确认阶段
            if conversation_state.get("stage") == "waiting_save_confirmation":
                pending_save = conversation_state.get("pending_save", {})
                
                if "确认" in msg or "保存" in msg:
                    # 用户确认保存
                    try:
                        saved_items = self._save_story_bible_to_database(
                            pending_save.get("story_id", story_id),
                            pending_save.get("logs", [])
                        )
                        
                        save_summary = []
                        if saved_items["worldbuilding"]:
                            save_summary.append(f"世界观({len(saved_items['worldbuilding'])}个)")
                        if saved_items["characters"]:
                            save_summary.append(f"角色({len(saved_items['characters'])}个)")
                        if saved_items["outline"]:
                            save_summary.append("大纲")
                        if saved_items["factions"]:
                            save_summary.append(f"势力({len(saved_items['factions'])}个)")
                        
                        logs.append({
                            "agent": "system",
                            "agent_name": "系统",
                            "message": "✅ 保存成功",
                            "content": f"已成功保存到数据库：{', '.join(save_summary)}"
                        })
                    except Exception as e:
                        logs.append({
                            "agent": "system",
                            "agent_name": "系统",
                            "message": "❌ 保存失败",
                            "content": f"保存时发生错误：{str(e)}"
                        })
                    
                    # 清除待保存状态
                    conversation_state.pop("pending_save", None)
                    conversation_state["waiting_for_user"] = False
                    conversation_state["stage"] = "save_completed"
                    
                elif "取消" in msg:
                    # 用户取消保存
                    logs.append({
                        "agent": "system",
                        "agent_name": "系统",
                        "message": "🗑️ 已取消",
                        "content": "已取消保存，生成的内容不会被存入数据库。"
                    })
                    
                    conversation_state.pop("pending_save", None)
                    conversation_state["waiting_for_user"] = False
                    conversation_state["stage"] = "save_cancelled"
                    
                elif "修改" in msg:
                    # 用户要求修改
                    logs.append({
                        "agent": "system",
                        "agent_name": "系统",
                        "message": "📝 需要修改",
                        "content": f"收到修改意见：{msg}\n\n请详细说明需要调整的地方，Agent 会根据您的意见重新生成。"
                    })
                    
                    # 保持等待状态，让用户继续输入
                    conversation_state["stage"] = "waiting_modification"
                    
                    return {
                        "agent_logs": logs,
                        "final_text": "",
                        "final_agent": "system",
                        "conversation_state": conversation_state,
                        "requires_user_input": True
                    }
                else:
                    # 未识别的回复，继续询问
                    logs.append({
                        "agent": "system",
                        "agent_name": "系统",
                        "message": "❓ 请确认",
                        "content": "请回复「确认」保存、「取消」不保存、或「修改」+您的意见。"
                    })
                    
                    return {
                        "agent_logs": logs,
                        "final_text": "",
                        "final_agent": "system",
                        "conversation_state": conversation_state,
                        "requires_user_input": True
                    }
                
                # 保存处理完成后，继续后续流程
                return {
                    "agent_logs": logs,
                    "final_text": "",
                    "final_agent": "system",
                    "conversation_state": conversation_state,
                    "requires_user_input": False
                }
            
            feedback_prompt = f"""作为系统，确认收到用户反馈：

用户反馈：{msg}

请用第一人称说明已收到反馈，Agent 团队会根据反馈调整方案，简洁专业。"""
            
            feedback_content = self._call_llm(feedback_prompt, "你是 Agent Room 的系统管理员。")
            
            logs.append({
                "agent": "system",
                "message": "📥 收到反馈",
                "content": feedback_content
            })
            
            # 根据反馈继续流程
            workflow_type = conversation_state.get("workflow_type", "general")
            
            # Agent 讨论用户反馈 - 使用 LLM 生成
            strategist_feedback_prompt = f"""作为策划师，分析用户反馈：

用户反馈：{msg}
当前任务类型：{workflow_type}

请用第一人称说明你如何分析用户反馈，以及需要如何调整方案，简洁专业。"""
            
            strategist_feedback_content = self._call_llm(strategist_feedback_prompt, "你是一位专业的策划师。")
            
            logs.append({
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "💭 分析反馈",
                "content": strategist_feedback_content
            })
            
            writer_feedback_prompt = f"""作为作家，回应用户反馈：

用户反馈：{msg}

请用第一人称说明你理解了用户需求，会在后续创作中注意这些要点，简洁专业。"""
            
            writer_feedback_content = self._call_llm(writer_feedback_prompt, "你是一位专业的作家。")
            
            logs.append({
                "agent": "writer",
                "agent_name": "作家",
                "message": "✍️ 调整思路",
                "content": writer_feedback_content
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
        
        # 生成自主工作流程（传入 conversation_state 供内部写入 pending_save 等）
        workflow_logs = self._generate_autonomous_workflow(msg, context, intent, story_id, conversation_state)
        logs.extend(workflow_logs)
        
        # 根据任务类型执行具体操作
        final_text = ""
        final_agent_name = ""
        
        if workflow_type == "write":
            # 写作任务：先询问关键信息，再生成
            if conversation_state["stage"] == "initial" or conversation_state["stage"] == "waiting_for_details":
                decision = self._generate_decision_point("write", "after_outline", msg)
                logs.append(decision)
                conversation_state["waiting_for_user"] = True
                conversation_state["stage"] = "waiting_for_details"
                final_text = "等待用户确认写作细节..."
                final_agent_name = "策划师"
            else:
                # 执行写作流程 - 使用安全的 Agent 调用
                cache_context = {"story_id": story_id, "chapter_id": chapter_id, "workflow": "write"}
                
                # Step 1: 使用 StrategistAgent 制定计划
                plan_result = self._safe_agent_call(
                    "StrategistAgent", self.strategist, {"text": msg},
                    chapter_id, AgentType.PLANNER,
                    use_cache=True, cache_context=cache_context
                )
                
                if "error" in plan_result:
                    logs.append({
                        "agent": "strategist",
                        "agent_name": "策划师",
                        "message": "❌ 计划生成失败",
                        "content": plan_result.get("feedback", "未知错误")
                    })
                    final_text = ""
                    final_agent_name = "system"
                else:
                    plan_text = plan_result.get("plan_text", "")
                    
                    logs.append({
                        "agent": "strategist",
                        "agent_name": "策划师",
                        "message": "📋 写作计划",
                        "content": plan_text
                    })
                    
                    # Step 2: 使用 CriticAgent 分析冲突
                    critic_result = self._safe_agent_call(
                        "CriticAgent", self.critic, {"text": plan_text, "plan": plan_text},
                        chapter_id, AgentType.CONFLICT,
                        use_cache=False, cache_context=cache_context
                    )
                    critic_feedback = critic_result.get("feedback", "") if "error" not in critic_result else "冲突分析跳过"
                    
                    logs.append({
                        "agent": "critic",
                        "agent_name": "评论家",
                        "message": "⚠️ 冲突分析",
                        "content": critic_feedback
                    })
                    
                    # Step 3: 执行写作
                    write_input = {
                        "text": msg,
                        "plan": plan_text,
                        "conflict_suggestions": critic_feedback
                    }
                    if word_count_range:
                        write_input["word_count_range"] = word_count_range
                    
                    result = self._safe_agent_call(
                        "WritingAgent", self.writer, write_input,
                        chapter_id, AgentType.WRITING,
                        use_cache=False, cache_context=cache_context
                    )
                    
                    if "error" in result:
                        logs.append({
                            "agent": "writer",
                            "agent_name": "作家",
                            "message": "❌ 写作失败",
                            "content": result.get("feedback", "未知错误")
                        })
                        final_text = ""
                        final_agent_name = "system"
                    else:
                        final_text = result.get("draft_text", "")
                        final_agent_name = "作家"
                        
                        # 添加溯源数据
                        trace_data.append({
                            "text": final_text[:500],
                            "source_agent": "WritingAgent",
                            "revisions": ["Initial draft generated"]
                        })
                        
                        # Step 4: 使用 ConsistencyAgent 检查一致性
                        consistency_result = self._safe_agent_call(
                            "ConsistencyAgent", self.consistency,
                            {
                                "text": final_text,
                                "story_bible": context,
                                "check_type": "all"
                            },
                            chapter_id, AgentType.CONSISTENCY,
                            use_cache=False, cache_context=cache_context
                        )
                        
                        if "error" not in consistency_result and consistency_result.get("has_issues"):
                            logs.append({
                                "agent": "consistency",
                                "agent_name": "一致性检查",
                                "message": f"⚠️ 发现 {consistency_result.get('issues_count', 0)} 个问题",
                                "content": consistency_result.get("formatted_issues", "")
                            })
                        
                        # Step 5: 使用 EditorAgent 润色
                        editor_result = self._safe_agent_call(
                            "EditorAgent", self.editor, {"draft_text": final_text},
                            chapter_id, AgentType.EDITOR,
                            use_cache=False, cache_context=cache_context
                        )
                        
                        if "error" not in editor_result:
                            edited_text = editor_result.get("edited_text", final_text)
                            
                            if edited_text != final_text:
                                final_text = edited_text
                                trace_data[-1]["revisions"].append("Edited by EditorAgent")
                                
                                logs.append({
                                    "agent": "editor",
                                    "agent_name": "编辑",
                                    "message": "✅ 润色完成",
                                    "content": "已完成文本润色，改进表达流畅度"
                                })
                        
                        # Step 6: 使用 ReaderAgent 提供反馈
                        reader_result = self._safe_agent_call(
                            "ReaderAgent", self.reader, {"text": final_text},
                            chapter_id, AgentType.READER,
                            use_cache=False, cache_context=cache_context
                        )
                        
                        if "error" not in reader_result:
                            reader_feedback = reader_result.get("feedback", "")
                            
                            logs.append({
                                "agent": "reader",
                                "agent_name": "读者",
                                "message": "👁️ 读者反馈",
                                "content": reader_feedback
                            })
                        
                        # Step 7: 生成写作完成消息
                        complete_prompt = f"""作为作家，宣布写作完成：

创作字数：{len(final_text)}
内容预览：{final_text[:200]}...

请用第一人称宣布写作完成，并简要总结创作内容，简洁专业。"""
                        
                        complete_content = self._call_llm(complete_prompt, "你是一位专业的作家。")
                        
                        logs.append({
                            "agent": "writer",
                            "agent_name": "作家",
                            "message": "✅ 写作完成",
                            "content": complete_content
                        })
                        
                        # Step 8: 生成章节总结并保存 Story Memory
                        if chapter_id:
                            try:
                                # 生成总结
                                summary_prompt = f"""请为以下章节内容生成简洁的总结：

章节内容：
{final_text[:1000]}...

请生成：
1. 章节摘要（100字以内）
2. 关键事件
3. 出场的角色
4. 时间线进展

格式：
摘要：xxx
关键事件：xxx
角色：xxx
时间线：xxx"""
                                
                                summary_result = self._call_llm(summary_prompt, "你是一位专业的编辑，擅长总结章节内容。")
                                
                                # 保存到 Story Memory
                                memory = load_memory(story_id)
                                if memory is None:
                                    memory = StoryMemory(story_id=story_id, bible=StoryBible())
                                
                                # 添加章节总结
                                memory.chapter_summaries.append(
                                    ChapterSummary(
                                        chapter_id=chapter_id,
                                        title=f"章节 {chapter_id}",
                                        summary=summary_result[:200]
                                    )
                                )
                                
                                # 保存 memory
                                save_memory(memory)
                                
                                logs.append({
                                    "agent": "memory",
                                    "agent_name": "记忆",
                                    "message": "💾 保存总结",
                                    "content": f"已保存章节 {chapter_id} 的总结到 Story Memory"
                                })
                            except Exception as e:
                                error_msg = f"保存 Story Memory 失败: {str(e)}"
                                print(error_msg)
                                logs.append({
                                    "agent": "memory",
                                    "agent_name": "记忆",
                                    "message": "⚠️ 保存失败",
                                    "content": error_msg
                                })
                        
                        # Step 9: Agent 讨论章节管理操作
                        # 使用 chapter_name 显示，如果没传则用 chapter_id
                        display_chapter = chapter_name or chapter_id or '未指定'
                        chapter_mgmt_prompt = f"""作为策划师，讨论章节管理：

当前章节：{display_chapter}
写作状态：已完成
字数：{len(final_text)}

请用第一人称：
1. 说明当前章节状态
2. 建议下一步操作（保存草稿、标记完成、继续下一章等）
3. 询问用户意见

简洁专业。"""
                        
                        chapter_mgmt_content = self._call_llm(chapter_mgmt_prompt, "你是一位专业的策划师。")
                        
                        logs.append({
                            "agent": "strategist",
                            "agent_name": "策划师",
                            "message": "📁 章节管理",
                            "content": chapter_mgmt_content,
                            "requires_user_input": True
                        })
                        conversation_state["waiting_for_user"] = True
                        conversation_state["stage"] = "completed"
                
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
                # 使用 StrategistAgent 生成大纲
                result = self.strategist.run({"text": msg})
                final_text = result.get("plan_text", "")
                final_agent_name = "策划师"
                
                # 使用 CriticAgent 评估大纲
                critic_result = self.critic.run({"text": final_text})
                critic_feedback = critic_result.get("feedback", "")
                
                logs.append({
                    "agent": "critic",
                    "agent_name": "评论家",
                    "message": "⚠️ 大纲评估",
                    "content": critic_feedback
                })
                
                # 使用 LLM 生成大纲完成消息
                outline_complete_prompt = f"""作为策划师，宣布大纲完成：

大纲预览：{final_text[:300]}...

请用第一人称宣布大纲已生成，并简要说明大纲要点，简洁专业。"""
                
                outline_complete_content = self._call_llm(outline_complete_prompt, "你是一位专业的策划师。")
                
                logs.append({
                    "agent": "strategist",
                    "agent_name": "策划师",
                    "message": "📋 大纲完成",
                    "content": outline_complete_content
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
            
            # 使用 ReaderAgent 提供反馈
            reader_result = self.reader.run({"text": final_text})
            reader_feedback = reader_result.get("feedback", "")
            
            logs.append({
                "agent": "reader",
                "agent_name": "读者",
                "message": "👁️ 润色后反馈",
                "content": reader_feedback
            })
            
            # 使用 LLM 生成润色完成消息
            edit_complete_prompt = f"""作为编辑，宣布润色完成：

润色后预览：{final_text[:200]}...

请用第一人称宣布润色已完成，并简要说明主要修改点（如文字流畅度、句式调整、表现力增强等），简洁专业。"""
            
            edit_complete_content = self._call_llm(edit_complete_prompt, "你是一位专业的编辑。")
            
            logs.append({
                "agent": "editor",
                "agent_name": "编辑",
                "message": "✅ 润色完成",
                "content": edit_complete_content
            })
            
        else:
            # 通用对话 - 使用 StrategistAgent
            result = self.strategist.run({"text": msg})
            final_text = result.get("plan_text", "")
            final_agent_name = "策划师"
        
        return {
            "agent_logs": logs,
            "final_text": final_text,
            "final_agent": final_agent_name,
            "conversation_state": conversation_state,
            "requires_user_input": conversation_state.get("waiting_for_user", False),
            "trace_data": trace_data if trace_data else None
        }

    async def chat_with_callback(
        self,
        message: str,
        story_id: str = "demo-story",
        chapter_id: str = None,
        chapter_name: str = None,
        word_count_range: Dict[str, int] = None,
        conversation_state: Dict[str, Any] = None,
        story_name: str = None,
        stream_callback: Callable = None
    ) -> Dict[str, Any]:
        """
        带流式回调的聊天接口
        每次生成 agent_log 时立即通过回调推送消息

        Args:
            stream_callback: 回调函数，签名: async def callback(message_type: str, data: Dict)
        """
        # 如果没有回调，等同于普通 chat
        if stream_callback is None:
            return self.chat(
                message,
                story_id,
                chapter_id=chapter_id,
                chapter_name=chapter_name,
                word_count_range=word_count_range,
                conversation_state=conversation_state,
                story_name=story_name
            )

        # 辅助函数：带回调的日志添加
        async def add_log_with_callback(log: Dict[str, Any], message_type: str = "agent_message"):
            logs.append(log)
            await stream_callback(message_type, {"log": log, "logs_count": len(logs)})

        msg = message.strip()
        logs: List[Dict[str, Any]] = []
        trace_data: List[Dict[str, Any]] = []

        # 发送开始通知
        await stream_callback("agent_start", {"message": "开始处理请求", "story_id": story_id})

        # 初始化或恢复对话状态
        if conversation_state is None:
            conversation_state = {
                "stage": "initial",
                "workflow_type": None,
                "waiting_for_user": False,
                "accumulated_content": [],
                "story_id": story_id,
                "story_name": story_name,
                "chapter_id": chapter_id
            }

        if story_name:
            conversation_state["story_name"] = story_name
        
        # 如果传入了新的 chapter_name，更新到 conversation_state
        if chapter_name:
            conversation_state["chapter_name"] = chapter_name

        # 检查并确认 story_id 和 chapter_id
        if conversation_state["stage"] == "initial" and not conversation_state.get("context_confirmed"):
            display_name = story_name or story_id
            # 使用 chapter_name 显示给用户，如果没传则显示 chapter_id
            display_chapter = chapter_name or chapter_id or '未指定'
            confirm_prompt = f"""作为系统，向用户确认当前工作上下文：

检测到的工作上下文：
- 小说名称: {display_name}
- 章节名称: {display_chapter}

请用第一人称询问用户是否在这个上下文下继续工作，简洁友好。"""

            confirm_content = self._call_llm(confirm_prompt, "你是 Agent Room 的系统管理员。")

            log = {
                "agent": "system",
                "agent_name": "系统",
                "message": "📍 确认上下文",
                "content": confirm_content,
                "requires_user_input": True
            }
            await add_log_with_callback(log, "user_input_required")

            conversation_state["waiting_for_user"] = True
            conversation_state["context_confirmed"] = True

            return {
                "agent_logs": logs,
                "final_text": "",
                "final_agent": "system",
                "conversation_state": conversation_state,
                "requires_user_input": True
            }

        # 如果正在等待用户输入，处理用户反馈
        if conversation_state.get("waiting_for_user") and conversation_state.get("stage") != "initial":
            if conversation_state.get("stage") == "waiting_save_confirmation":
                pending_save = conversation_state.get("pending_save", {})

                if "确认" in msg or "保存" in msg:
                    try:
                        saved_items = self._save_story_bible_to_database(
                            pending_save.get("story_id", story_id),
                            pending_save.get("logs", [])
                        )

                        save_summary = []
                        if saved_items["worldbuilding"]:
                            save_summary.append(f"世界观({len(saved_items['worldbuilding'])}个)")
                        if saved_items["characters"]:
                            save_summary.append(f"角色({len(saved_items['characters'])}个)")
                        if saved_items["outline"]:
                            save_summary.append("大纲")
                        if saved_items["factions"]:
                            save_summary.append(f"势力({len(saved_items['factions'])}个)")

                        log = {
                            "agent": "system",
                            "agent_name": "系统",
                            "message": "✅ 保存成功",
                            "content": f"已成功保存到数据库：{', '.join(save_summary)}"
                        }
                        await add_log_with_callback(log)
                    except Exception as e:
                        log = {
                            "agent": "system",
                            "agent_name": "系统",
                            "message": "❌ 保存失败",
                            "content": f"保存时发生错误：{str(e)}"
                        }
                        await add_log_with_callback(log)

                    conversation_state.pop("pending_save", None)
                    conversation_state["waiting_for_user"] = False
                    conversation_state["stage"] = "save_completed"

                elif "取消" in msg:
                    log = {
                        "agent": "system",
                        "agent_name": "系统",
                        "message": "🗑️ 已取消",
                        "content": "已取消保存，生成的内容不会被存入数据库。"
                    }
                    await add_log_with_callback(log)

                    conversation_state.pop("pending_save", None)
                    conversation_state["waiting_for_user"] = False
                    conversation_state["stage"] = "save_cancelled"

                elif "修改" in msg:
                    log = {
                        "agent": "system",
                        "agent_name": "系统",
                        "message": "📝 需要修改",
                        "content": f"收到修改意见：{msg}\n\n请详细说明需要调整的地方，Agent 会根据您的意见重新生成。"
                    }
                    await add_log_with_callback(log, "user_input_required")

                    conversation_state["stage"] = "waiting_modification"

                    return {
                        "agent_logs": logs,
                        "final_text": "",
                        "final_agent": "system",
                        "conversation_state": conversation_state,
                        "requires_user_input": True
                    }
                else:
                    log = {
                        "agent": "system",
                        "agent_name": "系统",
                        "message": "❓ 请确认",
                        "content": "请回复「确认」保存、「取消」不保存、或「修改」+您的意见。"
                    }
                    await add_log_with_callback(log, "user_input_required")

                    return {
                        "agent_logs": logs,
                        "final_text": "",
                        "final_agent": "system",
                        "conversation_state": conversation_state,
                        "requires_user_input": True
                    }

                return {
                    "agent_logs": logs,
                    "final_text": "",
                    "final_agent": "system",
                    "conversation_state": conversation_state,
                    "requires_user_input": False
                }

            feedback_prompt = f"""作为系统，确认收到用户反馈：

用户反馈：{msg}

请用第一人称说明已收到反馈，Agent 团队会根据反馈调整方案，简洁专业。"""

            feedback_content = self._call_llm(feedback_prompt, "你是 Agent Room 的系统管理员。")

            log = {
                "agent": "system",
                "message": "📥 收到反馈",
                "content": feedback_content
            }
            await add_log_with_callback(log)

            workflow_type = conversation_state.get("workflow_type", "general")

            # Agent 讨论用户反馈
            strategist_feedback_prompt = f"""作为策划师，分析用户反馈：

用户反馈：{msg}
当前任务类型：{workflow_type}

请用第一人称说明你如何分析用户反馈，以及需要如何调整方案，简洁专业。"""

            strategist_feedback_content = self._call_llm(strategist_feedback_prompt, "你是一位专业的策划师。")

            log = {
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "💭 分析反馈",
                "content": strategist_feedback_content
            }
            await add_log_with_callback(log)

            writer_feedback_prompt = f"""作为作家，回应用户反馈：

用户反馈：{msg}

请用第一人称说明你理解了用户需求，会在后续创作中注意这些要点，简洁专业。"""

            writer_feedback_content = self._call_llm(writer_feedback_prompt, "你是一位专业的作家。")

            log = {
                "agent": "writer",
                "agent_name": "作家",
                "message": "✍️ 调整思路",
                "content": writer_feedback_content
            }
            await add_log_with_callback(log)

            conversation_state["waiting_for_user"] = False
            conversation_state["stage"] = "executing"

        # 分析用户意图
        intent = self._analyze_intent(msg)
        workflow_type = intent["type"]
        conversation_state["workflow_type"] = workflow_type

        # 构建上下文
        context = self._build_room_context(story_id)

        # 生成自主工作流程（传入 conversation_state 供内部写入 pending_save 等）
        workflow_logs = self._generate_autonomous_workflow(msg, context, intent, story_id, conversation_state)

        # 每个工作流日志都通过回调推送
        for workflow_log in workflow_logs:
            await add_log_with_callback(workflow_log)
            # 如果需要用户输入，推送通知
            if workflow_log.get("requires_user_input"):
                await stream_callback("user_input_required", {
                    "log": workflow_log,
                    "conversation_state": conversation_state
                })

        # 根据任务类型执行具体操作
        final_text = ""
        final_agent_name = ""

        if workflow_type == "write":
            if conversation_state["stage"] == "initial" or conversation_state["stage"] == "waiting_for_details":
                decision = self._generate_decision_point("write", "after_outline", msg)
                await add_log_with_callback(decision, "user_input_required")
                conversation_state["waiting_for_user"] = True
                conversation_state["stage"] = "waiting_for_details"
                final_text = "等待用户确认写作细节..."
                final_agent_name = "策划师"
            else:
                cache_context = {"story_id": story_id, "chapter_id": chapter_id, "workflow": "write"}

                # Step 1: 策划师制定计划
                await stream_callback("progress_update", {"step": "planning", "message": "策划师正在制定计划..."})
                plan_result = self._safe_agent_call(
                    "StrategistAgent", self.strategist, {"text": msg},
                    chapter_id, AgentType.PLANNER,
                    use_cache=True, cache_context=cache_context
                )

                if "error" in plan_result:
                    log = {
                        "agent": "strategist",
                        "agent_name": "策划师",
                        "message": "❌ 计划生成失败",
                        "content": plan_result.get("feedback", "未知错误")
                    }
                    await add_log_with_callback(log)
                    final_text = ""
                    final_agent_name = "system"
                else:
                    plan_text = plan_result.get("plan_text", "")

                    log = {
                        "agent": "strategist",
                        "agent_name": "策划师",
                        "message": "📋 写作计划",
                        "content": plan_text
                    }
                    await add_log_with_callback(log)

                    # Step 2: 评论家分析冲突
                    await stream_callback("progress_update", {"step": "conflict_analysis", "message": "评论家正在分析冲突..."})
                    critic_result = self._safe_agent_call(
                        "CriticAgent", self.critic, {"text": plan_text, "plan": plan_text},
                        chapter_id, AgentType.CONFLICT,
                        use_cache=False, cache_context=cache_context
                    )
                    critic_feedback = critic_result.get("feedback", "") if "error" not in critic_result else "冲突分析跳过"

                    log = {
                        "agent": "critic",
                        "agent_name": "评论家",
                        "message": "⚠️ 冲突分析",
                        "content": critic_feedback
                    }
                    await add_log_with_callback(log)

                    # Step 3: 执行写作
                    await stream_callback("progress_update", {"step": "writing", "message": "作家正在创作内容..."})
                    write_input = {
                        "text": msg,
                        "plan": plan_text,
                        "conflict_suggestions": critic_feedback
                    }
                    if word_count_range:
                        write_input["word_count_range"] = word_count_range

                    result = self._safe_agent_call(
                        "WritingAgent", self.writer, write_input,
                        chapter_id, AgentType.WRITING,
                        use_cache=False, cache_context=cache_context
                    )

                    if "error" in result:
                        log = {
                            "agent": "writer",
                            "agent_name": "作家",
                            "message": "❌ 写作失败",
                            "content": result.get("feedback", "未知错误")
                        }
                        await add_log_with_callback(log)
                        final_text = ""
                        final_agent_name = "system"
                    else:
                        final_text = result.get("draft_text", "")
                        final_agent_name = "作家"

                        trace_data.append({
                            "text": final_text[:500],
                            "source_agent": "WritingAgent",
                            "revisions": ["Initial draft generated"]
                        })

                        # Step 4: 一致性检查
                        await stream_callback("progress_update", {"step": "consistency_check", "message": "正在进行一致性检查..."})
                        consistency_result = self._safe_agent_call(
                            "ConsistencyAgent", self.consistency,
                            {
                                "text": final_text,
                                "story_bible": context,
                                "check_type": "all"
                            },
                            chapter_id, AgentType.CONSISTENCY,
                            use_cache=False, cache_context=cache_context
                        )

                        if "error" not in consistency_result and consistency_result.get("has_issues"):
                            log = {
                                "agent": "consistency",
                                "agent_name": "一致性检查",
                                "message": f"⚠️ 发现 {consistency_result.get('issues_count', 0)} 个问题",
                                "content": consistency_result.get("formatted_issues", "")
                            }
                            await add_log_with_callback(log)

                        # Step 5: 润色
                        await stream_callback("progress_update", {"step": "editing", "message": "编辑正在润色内容..."})
                        editor_result = self._safe_agent_call(
                            "EditorAgent", self.editor, {"draft_text": final_text},
                            chapter_id, AgentType.EDITOR,
                            use_cache=False, cache_context=cache_context
                        )

                        if "error" not in editor_result:
                            edited_text = editor_result.get("edited_text", final_text)

                            if edited_text != final_text:
                                final_text = edited_text
                                trace_data[-1]["revisions"].append("Edited by EditorAgent")

                                log = {
                                    "agent": "editor",
                                    "agent_name": "编辑",
                                    "message": "✅ 润色完成",
                                    "content": "已完成文本润色，改进表达流畅度"
                                }
                                await add_log_with_callback(log)

                        # Step 6: 读者反馈
                        await stream_callback("progress_update", {"step": "reader_feedback", "message": "读者正在提供反馈..."})
                        reader_result = self._safe_agent_call(
                            "ReaderAgent", self.reader, {"text": final_text},
                            chapter_id, AgentType.READER,
                            use_cache=False, cache_context=cache_context
                        )

                        if "error" not in reader_result:
                            reader_feedback = reader_result.get("feedback", "")

                            log = {
                                "agent": "reader",
                                "agent_name": "读者",
                                "message": "👁️ 读者反馈",
                                "content": reader_feedback
                            }
                            await add_log_with_callback(log)

                        # Step 7: 写作完成
                        complete_prompt = f"""作为作家，宣布写作完成：

创作字数：{len(final_text)}
内容预览：{final_text[:200]}...

请用第一人称宣布写作完成，并简要总结创作内容，简洁专业。"""

                        complete_content = self._call_llm(complete_prompt, "你是一位专业的作家。")

                        log = {
                            "agent": "writer",
                            "agent_name": "作家",
                            "message": "✅ 写作完成",
                            "content": complete_content
                        }
                        await add_log_with_callback(log)

                        # Step 8: 保存章节总结
                        if chapter_id:
                            try:
                                summary_prompt = f"""请为以下章节内容生成简洁的总结：

章节内容：
{final_text[:1000]}...

请生成：
1. 章节摘要（100字以内）
2. 关键事件
3. 出场的角色
4. 时间线进展

格式：
摘要：xxx
关键事件：xxx
角色：xxx
时间线：xxx"""

                                summary_result = self._call_llm(summary_prompt, "你是一位专业的编辑，擅长总结章节内容。")

                                memory = load_memory(story_id)
                                if memory is None:
                                    memory = StoryMemory(story_id=story_id, bible=StoryBible())

                                memory.chapter_summaries.append(
                                    ChapterSummary(
                                        chapter_id=chapter_id,
                                        title=f"章节 {chapter_id}",
                                        summary=summary_result[:200]
                                    )
                                )

                                save_memory(memory)

                                log = {
                                    "agent": "memory",
                                    "agent_name": "记忆",
                                    "message": "💾 保存总结",
                                    "content": f"已保存章节 {chapter_id} 的总结到 Story Memory"
                                }
                                await add_log_with_callback(log)
                            except Exception as e:
                                error_msg = f"保存 Story Memory 失败: {str(e)}"
                                print(error_msg)
                                log = {
                                    "agent": "memory",
                                    "agent_name": "记忆",
                                    "message": "⚠️ 保存失败",
                                    "content": error_msg
                                }
                                await add_log_with_callback(log)

                        # Step 9: 章节管理
                        # 使用 chapter_name 显示，如果没传则用 chapter_id
                        display_chapter = chapter_name or chapter_id or '未指定'
                        chapter_mgmt_prompt = f"""作为策划师，讨论章节管理：

当前章节：{display_chapter}
写作状态：已完成
字数：{len(final_text)}

请用第一人称：
1. 说明当前章节状态
2. 建议下一步操作（保存草稿、标记完成、继续下一章等）
3. 询问用户意见

简洁专业。"""

                        chapter_mgmt_content = self._call_llm(chapter_mgmt_prompt, "你是一位专业的策划师。")

                        log = {
                            "agent": "strategist",
                            "agent_name": "策划师",
                            "message": "📁 章节管理",
                            "content": chapter_mgmt_content,
                            "requires_user_input": True
                        }
                        await add_log_with_callback(log, "user_input_required")
                        conversation_state["waiting_for_user"] = True
                        conversation_state["stage"] = "completed"

        elif workflow_type == "outline":
            if conversation_state["stage"] == "initial":
                decision = self._generate_decision_point("outline", "after_proposal", msg)
                await add_log_with_callback(decision, "user_input_required")
                conversation_state["waiting_for_user"] = True
                conversation_state["stage"] = "waiting_for_details"
                final_text = "等待用户确认大纲框架..."
                final_agent_name = "策划师"
            else:
                result = self.strategist.run({"text": msg})
                final_text = result.get("plan_text", "")
                final_agent_name = "策划师"

                critic_result = self.critic.run({"text": final_text})
                critic_feedback = critic_result.get("feedback", "")

                log = {
                    "agent": "critic",
                    "agent_name": "评论家",
                    "message": "⚠️ 大纲评估",
                    "content": critic_feedback
                }
                await add_log_with_callback(log)

                outline_complete_prompt = f"""作为策划师，宣布大纲完成：

大纲预览：{final_text[:300]}...

请用第一人称宣布大纲已生成，并简要说明大纲要点，简洁专业。"""

                outline_complete_content = self._call_llm(outline_complete_prompt, "你是一位专业的策划师。")

                log = {
                    "agent": "strategist",
                    "agent_name": "策划师",
                    "message": "📋 大纲完成",
                    "content": outline_complete_content
                }
                await add_log_with_callback(log)

        elif workflow_type == "world_building":
            if conversation_state["stage"] == "initial":
                decision = self._generate_decision_point("world_building", "after_framework", msg)
                await add_log_with_callback(decision, "user_input_required")
                conversation_state["waiting_for_user"] = True
                conversation_state["stage"] = "waiting_for_details"
                final_text = "等待用户确认世界观框架..."
                final_agent_name = "策划师"
            else:
                await stream_callback("progress_update", {"step": "world_building", "message": "正在生成世界观..."})
                debate = self.world.debate(WorldDebateRequest(prompt=msg, story_id=story_id, max_rounds=1))
                for debate_log in debate.agent_logs:
                    await add_log_with_callback(debate_log)
                final_text = debate.world_bible.world_view or ""
                final_agent_name = "策划师"

        elif workflow_type == "edit":
            await stream_callback("progress_update", {"step": "editing", "message": "正在润色内容..."})
            result = self.editor.run({"draft_text": msg})
            final_text = result.get("edited_text", "")
            final_agent_name = "编辑"

            reader_result = self.reader.run({"text": final_text})
            reader_feedback = reader_result.get("feedback", "")

            log = {
                "agent": "reader",
                "agent_name": "读者",
                "message": "👁️ 润色后反馈",
                "content": reader_feedback
            }
            await add_log_with_callback(log)

            edit_complete_prompt = f"""作为编辑，宣布润色完成：

润色后预览：{final_text[:200]}...

请用第一人称宣布润色已完成，并简要说明主要修改点，简洁专业。"""

            edit_complete_content = self._call_llm(edit_complete_prompt, "你是一位专业的编辑。")

            log = {
                "agent": "editor",
                "agent_name": "编辑",
                "message": "✅ 润色完成",
                "content": edit_complete_content
            }
            await add_log_with_callback(log)

        else:
            await stream_callback("progress_update", {"step": "general", "message": "正在处理请求..."})
            result = self.strategist.run({"text": msg})
            final_text = result.get("plan_text", "")
            final_agent_name = "策划师"

        # 发送完成通知
        await stream_callback("agent_complete", {
            "final_text": final_text,
            "final_agent": final_agent_name,
            "conversation_state": conversation_state
        })

        return {
            "agent_logs": logs,
            "final_text": final_text,
            "final_agent": final_agent_name,
            "conversation_state": conversation_state,
            "requires_user_input": conversation_state.get("waiting_for_user", False),
            "trace_data": trace_data if trace_data else None
        }
