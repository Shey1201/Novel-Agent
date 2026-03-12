from typing import Any, Callable, Dict, List, Optional
import random
import json
import time
import os
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
from app.memory.agent_memory import agent_memory, AgentConfig
from app.core.token_budget_manager import AgentType, get_token_budget_manager
from app.core.agent_cache import CacheConfig, get_agent_cache
from app.core.agent_discussion_engine import get_agent_discussion_engine, DiscussionContext
from app.core.discussion_controller import get_discussion_controller
from app.core.author_decision_system import get_author_decision_system, QuestionType, QuestionPriority
from app.core.narrative_intelligence_engine import get_narrative_intelligence_engine
from app.memory.system_settings import get_system_settings_manager
from app.core.streaming_writer import StreamingConfig, get_streaming_writer, get_reader_scheduler
from app.core.context_pool import get_context_pool

# 尝试导入 langchain，如果失败则在运行时处理
try:
    from langchain_core.messages import HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
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

        # 读取数据库中的 Agent 配置（temperature/prompt/enabled）
        self._agent_configs: Dict[str, AgentConfig] = {}
        try:
            for cfg in (agent_memory.get_all_configs() or []):
                self._agent_configs[cfg.agent_id] = cfg
        except Exception as e:
            print(f"[AgentChatService] Failed to load agent configs: {e}")

        # 为每个 agent_id 构造独立 LLM（用于 temperature 生效）
        self._llm_by_agent_id: Dict[str, Any] = {}

        self.strategist = StrategistAgent(llm=self._llm_for_agent("planner"))
        self.writer = WritingAgent(llm=self._llm_for_agent("writer"))
        self.editor = EditorAgent(llm=self._llm_for_agent("editor"))
        self.critic = CriticAgent(llm=self._llm_for_agent("critic"))
        self.reader = ReaderAgent(llm=self._llm_for_agent("reader"))
        self.consistency = ConsistencyAgent(llm=self._llm_for_agent("consistency"))
        self.memory = MemoryAgent(llm=self._llm_for_agent("summary"))
        self.world = WorldService(llm=self._llm_for_agent("planner"))

        # 初始化讨论引擎、作者决策系统、叙事智能引擎
        self.discussion_engine = get_agent_discussion_engine()
        self.author_decision = get_author_decision_system()
        self.narrative_engine = get_narrative_intelligence_engine()

        # 读取系统设置（从数据库）
        system_settings = None
        try:
            system_settings = get_system_settings_manager().get_settings()
        except Exception as e:
            print(f"[AgentChatService] Failed to load system settings: {e}")

        # 将 settings 应用到全局单例（确保前端修改后立刻生效）
        # TokenBudgetManager
        self.token_budget_manager = get_token_budget_manager()
        if system_settings and system_settings.token.enabled:
            self.token_budget_manager.set_daily_limit(system_settings.token.daily_limit)
        else:
            self.token_budget_manager.set_daily_limit(None)

        # AgentCache
        self.agent_cache = get_agent_cache()
        if system_settings:
            self.agent_cache.config = CacheConfig(
                max_size=self.agent_cache.config.max_size,
                ttl_hours=system_settings.cache.ttl_hours,
                enable_planner_cache=system_settings.cache.enable_planner_cache,
                enable_conflict_cache=system_settings.cache.enable_conflict_cache,
                enable_consistency_cache=system_settings.cache.enable_consistency_cache,
            )

        # DiscussionController
        try:
            dc = get_discussion_controller()
            if system_settings:
                dc.default_config.max_rounds = system_settings.discussion.max_rounds
                dc.default_config.max_tokens_per_response = system_settings.discussion.max_tokens_per_response
                dc.default_config.enable_short_mode = system_settings.discussion.enable_short_mode
        except Exception as e:
            print(f"[AgentChatService] Failed to apply discussion settings: {e}")

        # StreamingWriter / ReaderScheduler
        try:
            sw = get_streaming_writer()
            rs = get_reader_scheduler()
            if system_settings:
                sw.config = StreamingConfig(
                    paragraph_length=system_settings.generation.paragraph_length,
                    max_paragraphs=sw.config.max_paragraphs,
                    overlap_sentences=sw.config.overlap_sentences,
                    enable_streaming=system_settings.generation.enable_streaming,
                )
                rs.interval = system_settings.generation.reader_interval
        except Exception as e:
            print(f"[AgentChatService] Failed to apply generation settings: {e}")
        
        # 性能监控数据
        self.performance_stats = {
            "agent_calls": {},
            "total_tokens": 0,
            "start_time": None
        }

        # 上下文缓存池 - 减少重复 I/O 和 Token 消耗
        self.context_pool = get_context_pool()

        # 快速模式：仍由环境变量控制（避免和 UI 设置语义混淆）
        self.fast_mode = os.getenv("AGENT_ROOM_FAST_MODE", "1") != "0"

    def _agent_id_for(self, agent_name: str) -> str:
        """
        将内部 agent 名称映射到配置/skills 使用的 agent_id。
        这些 agent_id 与前端保存到 supabase 的 agents.agent_id 保持一致。
        """
        mapping = {
            "StrategistAgent": "planner",
            "WritingAgent": "writer",
            "EditorAgent": "editor",
            "CriticAgent": "critic",
            "ReaderAgent": "reader",
            "ConsistencyAgent": "consistency",
            "MemoryAgent": "summary",
            "WorldService": "planner",
        }
        return mapping.get(agent_name, agent_name)

    def _get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        return self._agent_configs.get(agent_id)

    def _llm_for_agent(self, agent_id: str):
        """
        基于基础 llm 克隆一个带 temperature 的实例。
        如果无法克隆或没有配置，则回退到 self.llm。
        """
        if self.llm is None:
            return None

        if agent_id in self._llm_by_agent_id:
            return self._llm_by_agent_id[agent_id]

        cfg = self._get_agent_config(agent_id)
        target_temp = cfg.temperature if cfg and cfg.temperature is not None else None

        # 如果没有特殊 temperature，直接复用 base llm
        if target_temp is None:
            self._llm_by_agent_id[agent_id] = self.llm
            return self.llm

        try:
            from langchain_openai import ChatOpenAI

            # 尝试从现有 llm 提取连接信息
            model = getattr(self.llm, "model_name", None) or getattr(self.llm, "model", None)
            api_key = getattr(self.llm, "openai_api_key", None)
            base_url = getattr(self.llm, "openai_api_base", None)

            # openai_api_key 可能是 SecretStr
            if hasattr(api_key, "get_secret_value"):
                api_key = api_key.get_secret_value()

            llm_kwargs = {
                "model": model,
                "temperature": float(target_temp),
                # 避免模型端或网络异常导致阻塞
                "max_retries": 2,
                "timeout": 30,
                "request_timeout": 30,
            }
            if api_key:
                llm_kwargs["api_key"] = api_key
            if base_url:
                llm_kwargs["base_url"] = base_url

            try:
                cloned = ChatOpenAI(**llm_kwargs)
            except TypeError:
                fallback_kwargs = dict(llm_kwargs)
                fallback_kwargs.pop("request_timeout", None)
                fallback_kwargs.pop("timeout", None)
                fallback_kwargs.pop("max_retries", None)
                cloned = ChatOpenAI(**fallback_kwargs)
            self._llm_by_agent_id[agent_id] = cloned
            return cloned
        except Exception as e:
            print(f"[AgentChatService] Failed to clone LLM for {agent_id}: {e}")
            self._llm_by_agent_id[agent_id] = self.llm
            return self.llm

    def _build_constraints_prefix(self, story_id: str, agent_id: str) -> str:
        """
        汇总“Agent 配置 prompt” + “挂载 skills 约束”并作为前缀注入 prompt。
        """
        parts: List[str] = []
        cfg = self._get_agent_config(agent_id)
        if cfg:
            if not cfg.enabled:
                # 由调用方处理禁用逻辑，这里仅提供信息
                pass
            if cfg.prompt:
                parts.append(cfg.prompt.strip())

        try:
            skill_prompt = skill_memory.build_agent_prompt(story_id, agent_id)
            if skill_prompt:
                parts.append(skill_prompt.strip())
        except Exception as e:
            print(f"[AgentChatService] build_agent_prompt failed: {e}")

        if not parts:
            return ""
        return "\n\n".join(parts).strip() + "\n\n"

    def _inject_constraints(self, story_id: str, agent_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        prefix = self._build_constraints_prefix(story_id, agent_id)
        if not prefix:
            return input_data

        patched = dict(input_data)
        for key in ("text", "draft_text", "plan"):
            val = patched.get(key)
            if isinstance(val, str) and val.strip():
                patched[key] = prefix + val
        return patched

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

        story_id = (cache_context or {}).get("story_id") or ""
        agent_id = self._agent_id_for(agent_name)
        cfg = self._get_agent_config(agent_id)
        if cfg and cfg.enabled is False:
            return {
                "error": f"{agent_id} disabled",
                "feedback": f"⚠️ {agent_id} 已在设置中禁用，已跳过。"
            }

        if story_id:
            input_data = self._inject_constraints(story_id, agent_id, input_data)
        
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

    def _recent_summaries(
        self, story_id: str, n: int = 3, memory: Optional[StoryMemory] = None
    ) -> List[str]:
        """近期章节摘要。传入 memory 可避免重复 load，减少 I/O 与 token 构建次数。"""
        if memory is None:
            # 尝试从缓存获取
            cached = self.context_pool.get_memory(story_id)
            if cached:
                memory = cached
            else:
                memory = load_memory(story_id)
                if memory:
                    self.context_pool.set_memory(story_id, memory)
        if not memory or not memory.chapter_summaries:
            return []
        return [f"{c.chapter_id}: {c.summary}" for c in memory.chapter_summaries[-n:]]

    def _build_room_context(
        self, story_id: str, memory: Optional[StoryMemory] = None
    ) -> Dict[str, Any]:
        """构建房间上下文。传入 memory 时直接使用，避免重复 load_memory / get_world。"""
        if memory is not None:
            bible = memory.bible
            recent = self._recent_summaries(story_id, n=3, memory=memory)
            rules_text = ""
            if bible.world_rules:
                rules_text = "\n".join([f"- {r.name}: {r.description}" for r in bible.world_rules])
            return {
                "world": bible.world_view or "",
                "rules": rules_text,
                "recent_summaries": recent,
                "world_approved": memory.world_locked,
            }
        world_info = self.world.get_world(story_id)
        bible = StoryBible.model_validate(world_info.get("world_bible", {}))
        recent = self._recent_summaries(story_id)
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

        # 为了性能：不再为“流程日志”额外调用 LLM（这些调用会显著拖慢响应）
        logs.append({
            "agent": "system",
            "agent_name": "系统",
            "message": "🎬 Agent Room 启动",
            "content": f"收到任务：{topic}\n类型：{workflow_type}\n将按当前 Agent 配置与挂载 Skills 执行。"
        })

        # 简单的 Story Bible 完整性提示（不自动补全，避免额外 LLM 调用）
        completeness = self._check_story_bible_completeness(context)
        missing = [k for k, ok in completeness.items() if not ok]
        if missing:
            logs.append({
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "🔍 设定检查",
                "content": f"检测到设定可能不完整：{', '.join(missing)}。将继续按现有信息执行（如需补全请用户明确提出）。"
            })
        else:
            logs.append({
                "agent": "strategist",
                "agent_name": "策划师",
                "message": "🔍 设定检查",
                "content": "设定信息看起来足够，可以直接进入执行。"
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
        print(f"[CHAT] Received message: {message[:50]}...")
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

        # 不再预设「确认上下文」步骤，直接根据用户消息处理（agents 只响应用户发送的内容）
        if conversation_state["stage"] == "initial" and not conversation_state.get("context_confirmed"):
            conversation_state["context_confirmed"] = True

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
        # 调试日志：确认意图识别结果
        print(f"[DEBUG] Intent detection: msg='{msg}' -> type='{workflow_type}'")
        
        # 请求内记忆池：一次加载，多处复用，减少 I/O 与重复构建
        # 优先从缓存获取
        request_memory = self.context_pool.get_memory(story_id)
        if not request_memory:
            request_memory = load_memory(story_id)
            if request_memory:
                self.context_pool.set_memory(story_id, request_memory)
        # 构建上下文
        context = self._build_room_context(story_id, memory=request_memory)
        
        # 生成自主工作流程（传入 conversation_state 供内部写入 pending_save 等）
        workflow_logs = self._generate_autonomous_workflow(msg, context, intent, story_id, conversation_state)
        logs.extend(workflow_logs)
        
        # 根据任务类型执行具体操作
        final_text = ""
        final_agent_name = ""
        
        if workflow_type == "write":
            # 写作任务：不再进入“先确认再执行”的预设流程，收到用户消息即直接执行
            conversation_state["waiting_for_user"] = False
            conversation_state["stage"] = "executing"

            # 执行写作流程 - 使用安全的 Agent 调用
            cache_context = {"story_id": story_id, "chapter_id": chapter_id, "workflow": "write"}
            # 说明：此处使用包裹块，避免大段代码因缩进调整产生语法问题
            if True:
                
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

                    # Step 2: 冲突分析（快速模式默认跳过以提升速度）
                    critic_feedback = ""
                    if not self.fast_mode:
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
                        
                        # Step 4+: 一致性/润色/读者反馈/总结等（快速模式默认跳过）
                        if not self.fast_mode:
                            consistency_result = self._safe_agent_call(
                                "ConsistencyAgent", self.consistency,
                                {"text": final_text, "story_bible": context, "check_type": "all"},
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
                        
                        # 不再追加“章节管理询问”这类预设交互，保持一次请求一次响应
                        conversation_state["waiting_for_user"] = False
                        conversation_state["stage"] = "completed"
                
        elif workflow_type == "outline":
            # 大纲任务：直接生成（不进入预设确认流程）
            conversation_state["waiting_for_user"] = False
            conversation_state["stage"] = "executing"

            result = self._safe_agent_call(
                "StrategistAgent", self.strategist, {"text": msg},
                chapter_id, AgentType.PLANNER,
                use_cache=True, cache_context={"story_id": story_id, "chapter_id": chapter_id, "workflow": "outline"}
            )
            final_text = result.get("plan_text", "")
            final_agent_name = "策划师"
            # 兼容既有缩进结构
            if True:
                
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
            # 世界观任务：直接生成（不进入预设确认流程）
            conversation_state["waiting_for_user"] = False
            conversation_state["stage"] = "executing"

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

        # 记忆落盘：非流式 chat() 也需要保存章节总结，否则记忆只在 chat_with_callback/工作流中更新
        if workflow_type == "write" and chapter_id and final_text:
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

                # 复用请求内记忆池，避免再次 load_memory
                memory = request_memory if request_memory is not None else StoryMemory(story_id=story_id, bible=StoryBible())
                if request_memory is None:
                    request_memory = memory
                memory.chapter_summaries.append(
                    ChapterSummary(
                        chapter_id=chapter_id,
                        title=f"章节 {chapter_id}",
                        summary=summary_result[:200],
                    )
                )
                save_memory(memory)
                # 保存后使缓存失效，下次请求会重新加载
                self.context_pool.invalidate_memory(story_id)
            except Exception as e:
                print(f"[AgentChatService] Failed to save chapter summary: {e}")
        
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

        # 不再预设「确认上下文」步骤，直接根据用户消息处理
        if conversation_state["stage"] == "initial" and not conversation_state.get("context_confirmed"):
            conversation_state["context_confirmed"] = True

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
        # 调试日志：确认意图识别结果
        print(f"[DEBUG] Intent detection: msg='{msg}' -> type='{workflow_type}'")

        # 请求内记忆池：一次加载，多处复用
        # 优先从缓存获取
        request_memory = self.context_pool.get_memory(story_id)
        if not request_memory:
            request_memory = load_memory(story_id)
            if request_memory:
                self.context_pool.set_memory(story_id, request_memory)
        # 构建上下文
        context = self._build_room_context(story_id, memory=request_memory)

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
            # 写作任务：不进入预设确认流程，直接执行
            conversation_state["waiting_for_user"] = False
            conversation_state["stage"] = "executing"

            cache_context = {"story_id": story_id, "chapter_id": chapter_id, "workflow": "write"}
            if True:

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

                    # Step 2: 评论家分析冲突（快速模式默认跳过）
                    critic_feedback = ""
                    if not self.fast_mode:
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

                        # Step 4+: 一致性/润色/读者反馈/总结（快速模式默认跳过）
                        if not self.fast_mode:
                            await stream_callback("progress_update", {"step": "consistency_check", "message": "正在进行一致性检查..."})
                            consistency_result = self._safe_agent_call(
                                "ConsistencyAgent", self.consistency,
                                {"text": final_text, "story_bible": context, "check_type": "all"},
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

                                # 复用请求内记忆池
                                memory = request_memory if request_memory is not None else StoryMemory(story_id=story_id, bible=StoryBible())
                                if request_memory is None:
                                    request_memory = memory
                                memory.chapter_summaries.append(
                                    ChapterSummary(
                                        chapter_id=chapter_id,
                                        title=f"章节 {chapter_id}",
                                        summary=summary_result[:200]
                                    )
                                )
                                save_memory(memory)
                                # 保存后使缓存失效，下次请求会重新加载
                                self.context_pool.invalidate_memory(story_id)

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
            # 大纲任务：直接生成
            conversation_state["waiting_for_user"] = False
            conversation_state["stage"] = "executing"

            result = self._safe_agent_call(
                "StrategistAgent", self.strategist, {"text": msg},
                chapter_id, AgentType.PLANNER,
                use_cache=True, cache_context={"story_id": story_id, "chapter_id": chapter_id, "workflow": "outline"}
            )
            final_text = result.get("plan_text", "")
            final_agent_name = "策划师"
            if True:

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
            # 世界观任务：直接生成
            conversation_state["waiting_for_user"] = False
            conversation_state["stage"] = "executing"

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
