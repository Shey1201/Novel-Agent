"""
基于 Facilitator 动态协调的章节生成流水线

优化点：
- 简化 LLM 决策 prompt（减少 token）
- 添加 Agent 配置缓存（减少数据库查询）
- 短内容自动跳过（避免不必要的 API 调用）

- facilitator 在每步执行完后决定下一步调用哪个 Agent
- facilitator 输出结构化决策（JSON），决定继续/跳过/结束
- 只调用在 DB 中启用的 Agent
- 每个 Agent 调用时注入：agent 配置中的 prompt + skill_memory 的 skills 约束
"""
from typing import Any, Dict, List, Optional, Set
import time
import json
import re
import hashlib

from app.memory.story_memory import StoryBible, StoryMemory
from app.memory.agent_memory import agent_memory
from app.memory.skill_memory import skill_memory
from app.core.llm import get_llm
from app.core.ai_config import get_llm_with_fallback

# ========== 缓存系统 ==========
_agent_config_cache: Dict[str, Any] = {}
_agent_config_timestamp: Dict[str, float] = {}
_CACHE_TTL = 300  # 5分钟缓存


def _get_cached_config(agent_id: str) -> Optional[Any]:
    """获取缓存的 Agent 配置"""
    if agent_id in _agent_config_cache:
        if time.time() - _agent_config_timestamp.get(agent_id, 0) < _CACHE_TTL:
            return _agent_config_cache[agent_id]
    return None


def _set_cached_config(agent_id: str, config: Any):
    """设置缓存的 Agent 配置"""
    _agent_config_cache[agent_id] = config
    _agent_config_timestamp[agent_id] = time.time()


def clear_agent_cache():
    """清空 Agent 配置缓存"""
    global _agent_config_cache, _agent_config_timestamp
    _agent_config_cache = {}
    _agent_config_timestamp = {}

# Agent 类映射
from app.agents.planner_agent import PlannerAgent
from app.agents.conflict_agent import ConflictAgent
from app.agents.writing_agent import WritingAgent
from app.agents.editor_agent import EditorAgent
from app.agents.reader_agent import ReaderAgent
from app.agents.critic_agent import CriticAgent
from app.agents.consistency_agent import ConsistencyAgent
from app.agents.summary_agent import SummaryAgent

FACILITATOR_ID = "facilitator"

# 所有可执行的 Agent（不含 facilitator）
ALL_EXECUTION_AGENTS = [
    "planner",
    "conflict",
    "writer",
    "editor",
    "reader",
    "critic",
    "consistency",
    "summary",
]

AGENT_CLASSES = {
    "planner": PlannerAgent,
    "conflict": ConflictAgent,
    "writer": WritingAgent,
    "editor": EditorAgent,
    "reader": ReaderAgent,
    "critic": CriticAgent,
    "consistency": ConsistencyAgent,
    "summary": SummaryAgent,
}


def _analyze_user_requirement(user_requirement: str) -> List[str]:
    """
    分析用户需求，返回需要跳过的 Agent 列表
    
    Args:
        user_requirement: 用户需求描述
    
    Returns:
        需要跳过的 Agent ID 列表
    """
    if not user_requirement:
        return []
    
    req = user_requirement.lower()
    skip_agents = []
    
    # 分析用户需求
    needs_plan = any(kw in req for kw in ["大纲", "计划", "规划", "结构", "outline", "plan"])
    needs_content = any(kw in req for kw in ["写", "生成", "创作", "内容", "write", "generate", "create", "章节"])
    needs_edit = any(kw in req for kw in ["编辑", "修改", "优化", "润色", "edit", "revise", "improve"])
    needs_feedback = any(kw in req for kw in ["反馈", "批评", "评估", "意见", "review", "critic", "feedback"])
    needs_consistency = any(kw in req for kw in ["检查", "一致性", "逻辑", "consistency", "logic", "check"])
    needs_summary = any(kw in req for kw in ["摘要", "总结", "summary"])
    needs_conflict = any(kw in req for kw in ["冲突", "戏剧", "conflict", "drama", "tension"])
    needs_full = any(kw in req for kw in ["完整", "全部", "full", "complete"])
    
    # 如果用户需要完整流程，不跳过任何 Agent
    if needs_full:
        return []
    
    # 默认跳过评估类 Agent（除非明确需要）
    default_skip = ["reader", "critic", "consistency", "summary"]
    
    # 根据需求决定跳过哪些
    skip_agents = []
    
    # 只要大纲/计划
    if needs_plan and not needs_content:
        skip_agents = ["writer", "editor", "reader", "critic", "consistency", "summary", "conflict"]
    
    # 只要写作（不需要评估）
    elif needs_content and not needs_edit and not needs_feedback:
        skip_agents = ["reader", "critic", "consistency", "summary"]
    
    # 只要写作+编辑
    elif needs_content and needs_edit and not needs_feedback:
        skip_agents = ["reader", "critic", "consistency", "summary"]
    
    # 需要写作+反馈
    elif needs_content and needs_feedback:
        skip_agents = []  # 不跳过任何
    
    # 只做一致性检查
    elif needs_consistency and not needs_content:
        skip_agents = ["planner", "conflict", "writer", "editor", "reader", "critic", "summary"]
    
    # 其他情况使用默认跳过
    else:
        skip_agents = default_skip
    
    return skip_agents


def _analyze_requirement_completeness(
    user_requirement: str,
    outline: str,
    llm: Any = None,
    fast_mode: bool = True,
) -> Dict[str, Any]:
    """
    使用 AI 分析用户需求和大纲的完整性，判断是否需要向用户提问
    
    Args:
        user_requirement: 用户需求描述
        outline: 用户提供的章节大纲/开头
        llm: 可选的 LLM 实例，如果传入则使用 AI 分析
        fast_mode: 快速模式，跳过 LLM 调用使用规则判断

    Returns:
        {
            "is_complete": bool,  # 需求是否完整
            "missing_info": List[str],  # 缺失的信息列表
            "questions": List[str],  # 需要向用户提问的问题
            "can_proceed": bool,  # 是否可以继续执行
            "analysis": str,  # AI 的分析说明
        }
    """
    # 快速模式：使用简单的规则判断，跳过 LLM 调用
    if fast_mode or not llm:
        combined = (user_requirement or "") + "\n" + (outline or "")
        combined_lower = combined.lower()
        
        # 简单规则
        missing_info = []
        questions = []
        
        story_types = ["科幻", "奇幻", "都市", "悬疑", "言情", "武侠", "玄幻", "历史", "军事", "游戏"]
        if not any(t in combined_lower for t in story_types):
            missing_info.append("故事类型/题材")
            questions.append("您想创作什么类型的小说？")
        
        if len(combined) < 50:
            missing_info.append("内容太少")
            questions.append("能详细描述一下您的故事想法吗？")
        
        is_complete = len(combined) > 80
        return {
            "is_complete": is_complete,
            "missing_info": missing_info,
            "questions": questions[:3],
            "can_proceed": is_complete,
            "analysis": "基于规则判断（快速模式）",
        }
    
    # AI 分析模式（默认关闭，保留完整功能）
    prompt = f"""你是 AI 小说创作的协调者，负责判断用户需求是否足够开始创作。

## 用户需求
"{user_requirement}"

## 用户提供的大纲
"{outline[:500] if outline else '(无)'}"

## 判断标准
- 如果用户提供了基本的故事想法（类型、角色、背景之一），就可以开始
- 只有当信息极度缺乏（如只说"帮我写小说"）时才需要提问

## 输出格式（JSON）
{{
    "can_proceed": true/false,
    "questions": ["如果需要提问，最多2个问题"],
    "analysis": "一句话判断理由"
}}

示例：
- "帮我写小说", "" → can_proceed=false, questions=["您想写什么类型的故事？"]
- "写科幻小说", "主角是宇航员" → can_proceed=true, questions=[]
- "写一个完整的章节", "林晓是清华学生，获得外星科技..." → can_proceed=true, questions=[]

请直接输出 JSON。"""

    from langchain_core.messages import HumanMessage
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        response_text = response.content if hasattr(response, "content") else str(response)
        
        # 解析 JSON
        import json
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            result = json.loads(json_match.group())
            return {
                "is_complete": result.get("is_complete", True),
                "missing_info": result.get("missing_info", []),
                "questions": result.get("questions", [])[:2],
                "can_proceed": result.get("can_proceed", True),
                "analysis": result.get("analysis", ""),
            }
    except Exception as e:
        print(f"[AI分析] 失败: {e}")
    
    # 降级到简单规则
    return {
        "is_complete": len((user_requirement or "") + (outline or "")) > 80,
        "missing_info": [],
        "questions": [],
        "can_proceed": True,
        "analysis": "降级到规则判断",
    }


def _build_constraints_prefix(story_id: str, agent_id: str) -> str:
    """与 AgentChatService 一致：Agent 配置 prompt + 挂载 skills 约束（使用缓存）"""
    parts: List[str] = []
    
    # 使用缓存获取配置
    cfg = _get_cached_config(agent_id)
    if cfg is None:
        cfg = agent_memory.get_config(agent_id)
        if cfg:
            _set_cached_config(agent_id, cfg)
    
    if cfg and cfg.prompt:
        parts.append(cfg.prompt.strip())
    try:
        sp = skill_memory.build_agent_prompt(story_id, agent_id)
        if sp:
            parts.append(sp.strip())
    except Exception:
        pass
    if not parts:
        return ""
    return "\n\n".join(parts).strip() + "\n\n"


def _get_llm_for_agent(agent_id: str, base_llm: Any) -> Any:
    """按 Agent 配置的 temperature 返回 LLM（使用缓存）"""
    # 使用缓存获取配置
    cfg = _get_cached_config(agent_id)
    if cfg is None:
        cfg = agent_memory.get_config(agent_id)
        if cfg:
            _set_cached_config(agent_id, cfg)
    
    if not cfg or cfg.temperature is None:
        return base_llm
    
    # 使用配置的 temperature 重新创建 LLM
    try:
        from langchain_openai import ChatOpenAI
        model = getattr(base_llm, "model_name", None) or getattr(base_llm, "model", None)
        api_key = getattr(base_llm, "openai_api_key", None)
        base_url = getattr(base_llm, "openai_api_base", None)
        if hasattr(api_key, "get_secret_value"):
            api_key = api_key.get_secret_value()
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=float(cfg.temperature),
        )
    except Exception:
        return base_llm


def _build_facilitator_prompt(
    current_step: int,
    completed_agents: List[str],
    pending_agents: List[str],
    state: Dict[str, Any],
    user_requirement: str = "",
    fast_mode: bool = False,
) -> str:
    """构建 facilitator 的决策 prompt - 支持快速模式"""
    
    # 快速模式：使用简化 prompt
    if fast_mode:
        return _build_fast_facilitator_prompt(
            current_step, completed_agents, pending_agents, state, user_requirement
        )
    
    # 用户需求分析
    user_req_lower = user_requirement.lower() if user_requirement else ""
    
    # 分析用户意图
    user_intents = []
    if any(kw in user_req_lower for kw in ["大纲", "计划", "规划", "结构", "outline", "plan"]):
        user_intents.append("只需要大纲规划")
    if any(kw in user_req_lower for kw in ["写", "生成", "创作", "内容", "write", "generate", "create"]):
        user_intents.append("需要生成内容")
    if any(kw in user_req_lower for kw in ["批评", "评估", "反馈", "意见", "critic", "review", "feedback"]):
        user_intents.append("需要批评建议")
    if any(kw in user_req_lower for kw in ["编辑", "修改", "优化", "润色", "edit", "revise", "improve"]):
        user_intents.append("需要编辑修改")
    if any(kw in user_req_lower for kw in ["检查", "一致性", "逻辑", "consistency", "logic", "check"]):
        user_intents.append("需要逻辑检查")
    if any(kw in user_req_lower for kw in ["摘要", "总结", "summary"]):
        user_intents.append("需要生成摘要")
    if any(kw in user_req_lower for kw in ["完整", "全部", "full", "complete"]):
        user_intents.append("需要完整流程")
    
    if not user_intents:
        user_intents = ["默认完整流程"]
    
    intents_str = " | ".join(user_intents)
    
    # 当前状态摘要（精简）
    status_parts = [
        f"已完成: {', '.join(completed_agents) or '无'}",
        f"待执行: {', '.join(pending_agents) or '无'}",
        f"需求: {intents_str}",
    ]
    
    # 只在有内容时才添加详细信息
    if state.get("draft_text"):
        status_parts.append(f"草稿: {len(state['draft_text'])}字符")
    if state.get("edited_text"):
        status_parts.append(f"编辑: {len(state['edited_text'])}字符")
    
    status = "\n".join(status_parts)
    
    prompt = f"""你是 AI 小说创作团队的协调者（Facilitator）。

## 当前状态
{status}

## 可用 Agent
- planner: 规划大纲（必需）
- conflict: 增强冲突（可选）
- writer: 生成内容（必需）
- editor: 编辑优化（可选）
- reader: 读者反馈（可选）
- critic: 批评建议（可选）
- consistency: 逻辑检查（可选）
- summary: 生成摘要（可选）

## 规则
1. planner 是必需的（除非已有计划）
2. writer 是生成内容必需的
3. 用户不需要的 Agent 跳过

## 输出 JSON
{{"next_agent": "agent_id 或 'finish'", "reason": "原因", "skip": []}}"""
    return prompt


def _build_fast_facilitator_prompt(
    current_step: int,
    completed_agents: List[str],
    pending_agents: List[str],
    state: Dict[str, Any],
    user_requirement: str = "",
) -> str:
    """快速模式：极简 prompt"""
    
    # 简化需求分析
    user_req_lower = user_requirement.lower() if user_requirement else ""
    need_plan = any(kw in user_req_lower for kw in ["大纲", "计划", "规划", "outline", "plan"])
    need_write = any(kw in user_req_lower for kw in ["写", "生成", "创作", "write", "generate"])
    need_edit = any(kw in user_req_lower for kw in ["编辑", "修改", "优化", "edit", "revise"])
    
    # 快速决策逻辑
    if not completed_agents:
        # 第一步：规划
        if need_plan:
            return '{"next_agent": "planner", "reason": "需要大纲", "skip": ["writer", "editor", "reader", "critic"]}'
        elif need_write:
            return '{"next_agent": "planner", "reason": "先生成大纲", "skip": []}'
        else:
            return '{"next_agent": "planner", "reason": "默认规划", "skip": []}'
    
    elif "planner" in completed_agents and "writer" not in completed_agents:
        # 第二步：写作
        if need_write or need_edit:
            return '{"next_agent": "writer", "reason": "生成内容", "skip": ["reader", "critic"]}'
        else:
            return '{"next_agent": "writer", "reason": "生成内容", "skip": []}'
    
    elif "writer" in completed_agents:
        # 第三步：编辑
        if need_edit:
            return '{"next_agent": "editor", "reason": "需要编辑", "skip": []}'
        else:
            return '{"next_agent": "finish", "reason": "完成", "skip": []}'
    
    return '{"next_agent": "finish", "reason": "默认结束", "skip": []}'


def _parse_facilitator_response(response: str) -> Dict[str, Any]:
    """解析 facilitator 的决策响应"""
    try:
        # 尝试提取 JSON
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"[Facilitator] 解析失败: {e}")
    
    # 解析失败时的默认决策
    return {"next_agent": "finish", "reason": "解析失败，默认结束"}


def _execute_agent(
    agent_id: str,
    state: Dict[str, Any],
    story_id: str,
    base_llm: Any,
) -> Dict[str, Any]:
    """执行单个 Agent 并返回耗时"""
    if agent_id not in AGENT_CLASSES:
        return {"elapsed": 0, "error": f"Unknown agent: {agent_id}"}
    
    prefix = _build_constraints_prefix(story_id, agent_id)
    llm = _get_llm_for_agent(agent_id, base_llm)
    agent = AGENT_CLASSES[agent_id](llm=llm)
    
    t0 = time.time()
    
    try:
        if agent_id == "planner":
            input_text = prefix + state["input_text"]
            out = agent.run({"text": input_text})
            state["plan_text"] = out.get("plan_text", "")
        elif agent_id == "conflict":
            input_text = prefix + (state.get("plan_text") or state["input_text"])
            out = agent.run({"draft_text": input_text})
            state["conflict_suggestions"] = out.get("conflict_suggestions", [])
        elif agent_id == "writer":
            base = (state.get("plan_text") or "") + "\n\n" + "\n".join(state.get("conflict_suggestions", []))
            input_text = prefix + base
            out = agent.run({"text": input_text})
            state["draft_text"] = out.get("draft_text", "")
        elif agent_id == "editor":
            input_text = prefix + state.get("draft_text", "")
            out = agent.run({"draft_text": input_text, "trace_data": state.get("trace_data", [])})
            state["edited_text"] = out.get("edited_text", state.get("draft_text", ""))
        elif agent_id == "reader":
            input_text = prefix + state.get("edited_text", state.get("draft_text", ""))
            out = agent.run({"draft_text": input_text})
            state["reader_feedback"] = out.get("reader_feedback", [])
        elif agent_id == "critic":
            input_text = prefix + state.get("edited_text", state.get("draft_text", ""))
            agent.run({"text": input_text})
        elif agent_id == "consistency":
            input_text = prefix + state.get("edited_text", state.get("draft_text", ""))
            agent.run({"text": input_text})
        elif agent_id == "summary":
            chapter_text = state.get("edited_text") or state.get("draft_text", "")
            state["summary_text"] = agent.run(chapter_text)
            state["final_text"] = state.get("edited_text") or state.get("draft_text", "")
    except Exception as e:
        elapsed = time.time() - t0
        return {"elapsed": elapsed, "error": str(e)}
    
    elapsed = time.time() - t0
    return {"elapsed": elapsed}


def run_with_facilitator_coordinator(
    outline: str,
    story_id: Optional[str] = None,
    chapter_id: Optional[str] = None,
    llm_config: Optional[Dict[str, Any]] = None,
    max_steps: int = 20,
    user_requirement: str = "",
) -> Dict[str, Any]:
    """
    使用 facilitator 动态协调的章节生成流水线。
    
    - facilitator 根据用户需求动态决定使用哪些 Agent
    - 只调用必要的 Agent，不固定顺序和数量
    - 记录每步耗时和 facilitator 的决策
    
    Args:
        outline: 章节大纲/输入
        story_id: 故事ID
        chapter_id: 章节ID
        llm_config: LLM配置
        max_steps: 最大步数
        user_requirement: 用户需求描述（如"只需要大纲"、"生成完整章节"等）
    """
    story_id = story_id or "demo-story"

    # 初始化 LLM
    if llm_config:
        from langchain_openai import ChatOpenAI
        base_llm = ChatOpenAI(
            api_key=llm_config.get("api_key"),
            model=llm_config.get("model", "gpt-4o-mini"),
            base_url=llm_config.get("base_url"),
            temperature=llm_config.get("temperature", 0.7),
        )
    else:
        base_llm = get_llm() or get_llm_with_fallback()

    # 获取 facilitator 的 LLM（可使用不同的 temperature）
    facilitator_cfg = agent_memory.get_config(FACILITATOR_ID)
    if facilitator_cfg and facilitator_cfg.temperature is not None:
        facilitator_llm = _get_llm_for_agent(FACILITATOR_ID, base_llm)
    else:
        facilitator_llm = base_llm

    # 从 DB 获取启用的 Agent
    all_configs = agent_memory.get_all_configs()
    enabled_agents = {
        c.agent_id for c in all_configs 
        if c.agent_id != FACILITATOR_ID and c.enabled
    }
    
    # 初始状态
    state: Dict[str, Any] = {
        "input_text": outline,
        "plan_text": "",
        "conflict_suggestions": [],
        "draft_text": "",
        "edited_text": "",
        "reader_feedback": [],
        "summary_text": "",
        "final_text": "",
        "agent_logs": [],
        "facilitator_decisions": [],
        "story_id": story_id,
        "chapter_id": chapter_id,
    }

    completed_agents: List[str] = []
    pending_agents = [a for a in ALL_EXECUTION_AGENTS if a in enabled_agents]
    current_step = 0

    # ========== 核心修改：先分析用户需求，再决定 Agent ==========
    skipped_agents = _analyze_user_requirement(user_requirement)
    pending_agents = [a for a in pending_agents if a not in skipped_agents]
    
    print(f"\n[用户需求] {user_requirement or '默认完整流程'}")
    print(f"[跳过 Agent] {skipped_agents if skipped_agents else '无'}")
    print(f"[有效 Agent] {pending_agents}")

    # ========== 检查需求完整性，如果信息不足则提问（使用 AI 分析）==========
    completeness = _analyze_requirement_completeness(user_requirement, outline, llm=base_llm, fast_mode=True)
    
    if not completeness["can_proceed"]:
        # 需求不完整，需要向用户提问
        print(f"\n[Facilitator] 需求信息不足，需要向用户提问")
        print(f"[AI分析] {completeness.get('analysis', '')}")
        print(f"[缺失信息] {completeness['missing_info']}")
        
        # 返回问题给用户，而不是继续执行
        state["needs_user_input"] = True
        state["questions"] = completeness["questions"]
        state["missing_info"] = completeness["missing_info"]
        state["can_proceed"] = False
        state["analysis"] = completeness.get("analysis", "")
        return state
    
    print(f"[需求检查] 完整，可以继续执行")

    # 如果没有有效的 Agent，直接返回
    if not pending_agents:
        print(f"\n[Facilitator] 没有需要执行的 Agent")
        state["final_text"] = state.get("input_text", "")
        return state
    
    # 如果只需要大纲（只有 planner）
    if pending_agents == ["planner"]:
        print(f"\n[Facilitator] 用户只需要大纲规划，执行 planner...")
        result = _execute_agent("planner", state, story_id, base_llm)
        elapsed = result.get("elapsed", 0)
        state["agent_logs"].append({
            "agent": "planner",
            "message": "生成大纲",
            "elapsed_seconds": round(elapsed, 2),
        })
        print(f"[完成] 大纲长度: {len(state.get('plan_text', ''))} 字符")
        state["final_text"] = state.get("plan_text", "")
        return state
    
    # 如果需要 planner，先执行
    if "planner" in pending_agents and "planner" not in completed_agents:
        print(f"\n[Step {current_step + 1}] 执行 planner（初始规划）")
        result = _execute_agent("planner", state, story_id, base_llm)
        elapsed = result.get("elapsed", 0)
        state["agent_logs"].append({
            "agent": "planner",
            "message": "初始规划",
            "elapsed_seconds": round(elapsed, 2),
        })
        completed_agents.append("planner")
        pending_agents.remove("planner")
        current_step += 1
    
    # 如果执行完 planner 后没有其他 Agent 了，结束
    if not pending_agents:
        print(f"\n[Facilitator] 规划完成")
        state["final_text"] = state.get("plan_text", "")
        return state

    # ========== 加载 Debate 设置 ==========
    try:
        from app.memory.system_settings import get_system_settings_manager
        system_settings = get_system_settings_manager()
        debate_enabled = system_settings.settings.debate.enabled
        debate_agents = system_settings.settings.debate.agents_to_debate
        debate_max_rounds = system_settings.settings.debate.max_rounds
        print(f"[Debate] 启用: {debate_enabled}, Agents: {debate_agents}, 轮数: {debate_max_rounds}")
    except Exception as e:
        print(f"[Debate] 加载设置失败: {e}, 使用默认设置")
        debate_enabled = True
        debate_agents = ["reader", "critic", "editor", "summary"]  # 新增 summary
        debate_max_rounds = 2

    # ========== 按顺序执行剩余 Agent，每个执行完后让 Facilitator 自主判断下一步 ==========
    print(f"\n[执行] 按顺序执行: {pending_agents}")
    
    for agent_id in pending_agents:
        if agent_id == "planner":
            continue  # 已执行
        if agent_id not in enabled_agents:
            continue
            
        print(f"\n[Step {current_step + 1}] 执行 {agent_id}...")
        result = _execute_agent(agent_id, state, story_id, base_llm)
        elapsed = result.get("elapsed", 0)
        
        state["agent_logs"].append({
            "agent": agent_id,
            "message": f"执行 {agent_id}",
            "elapsed_seconds": round(elapsed, 2),
        })
        
        completed_agents.append(agent_id)
        current_step += 1
        
        # ========== 每个 Agent 执行完后，都让 Facilitator 自主判断下一步 ==========
        if debate_enabled:
            # 构建当前状态摘要
            state_summary = _build_state_summary(agent_id, state)
            
            # 让 LLM 自主决定是否需要 debate/评审（传入启用的 Agent 列表）
            decision = _facilitator_decide_next_step(
                current_agent=agent_id,
                state_summary=state_summary,
                completed_agents=completed_agents,
                pending_agents=pending_agents,
                base_llm=base_llm,
                enabled_agents=enabled_agents,
                fast_mode=True,  # 快速模式，使用评估矩阵
            )
            
            if decision.get("should_debate") and decision.get("debate_agents"):
                selected_agents = decision["debate_agents"]
                print(f"\n[Facilitator] 判断需要评审: {selected_agents}")
                print(f"[原因] {decision.get('reason', '')}")
                
                debate_result = _run_debate(
                    draft_text=state.get("draft_text") or state.get("plan_text", ""),
                    outline=outline,
                    debate_agents=selected_agents,
                    max_rounds=decision.get("debate_rounds", debate_max_rounds),
                    state=state,
                    story_id=story_id,
                    base_llm=base_llm,
                )
                
                if debate_result.get("improved_text"):
                    state["draft_text"] = debate_result["improved_text"]
                
                state["agent_logs"].append({
                    "agent": "debate",
                    "message": f"评审 {selected_agents}",
                    "elapsed_seconds": round(debate_result.get("elapsed", 0), 2),
                })
        
        # 如果是 writer 且用户不需要后续评估，可以提前结束
        if agent_id == "writer" and not user_requirement:
            # 检查用户是否需要编辑/评估
            req = user_requirement.lower() if user_requirement else ""
            if "编辑" not in req and "修改" not in req and "评估" not in req and "反馈" not in req:
                print(f"[优化] 用户不需要编辑/评估，提前结束")
                break

    # 最后生成摘要（如果有内容）
    if state.get("draft_text") or state.get("edited_text"):
        final_text = state.get("edited_text") or state.get("draft_text", "")
        state["final_text"] = final_text

    return state

    # 计算总耗时
    total_agent_time = sum(log["elapsed_seconds"] for log in state["agent_logs"])
    total_facilitator_time = sum(dec["elapsed_seconds"] for dec in state["facilitator_decisions"])
    
    state["total_agent_time"] = round(total_agent_time, 2)
    state["total_facilitator_time"] = round(total_facilitator_time, 2)
    state["total_time"] = round(total_agent_time + total_facilitator_time, 2)
    state["steps_executed"] = current_step

    return state


def _select_debate_agents(
    outline: str,
    draft_text: str,
    available_agents: List[str],
    base_llm: Any,
) -> Dict[str, Any]:
    """
    由 LLM 自主决定需要哪些 Agent 参与辩论
    
    Args:
        outline: 章节大纲
        draft_text: 当前草稿
        available_agents: 可选的 Agent 列表
        base_llm: LLM 实例
    
    Returns:
        {
            "selected_agents": List[str],  # 选中的 Agent
            "reason": str,  # 选择理由
        }
    """
    from langchain_core.messages import HumanMessage
    
    agent_descriptions = {
        "reader": "Reader - 读者视角，评估阅读体验和情感共鸣",
        "critic": "Critic - 批评家视角，发现逻辑漏洞和情节问题",
        "editor": "Editor - 编辑视角，优化结构和语言表达",
        "consistency": "Consistency - 一致性检查，关注角色设定和世界观逻辑",
        "summary": "Summary - 总结师视角，提取核心观点和关键信息",
    }
    
    available_desc = "\n".join([f"- {agent_descriptions.get(a, a)}" for a in available_agents])
    
    prompt = f"""你是 Facilitator（协调者），需要决定哪些 Agent 参与对草稿的评审。

## 大纲
{outline[:500]}

## 当前草稿（开头）
{draft_text[:500]}

## 可选 Agent
{available_desc}

## 决策规则
1. 如果只是大纲/计划阶段，只需要 Editor（结构优化）
2. 如果是初稿写作后，需要 Reader + Critic（评估反馈）
3. 如果是修改稿，可以只选 1-2 个针对性评估
4. 如果草稿已经很完善，可以不选择任何 Agent

## 输出格式（JSON）
{{
    "selected_agents": ["agent1", "agent2"],  // 选择参与评审的 Agent，空数组表示不需要
    "reason": "选择理由"
}}

请直接输出 JSON："""
    
    try:
        response = base_llm.invoke([HumanMessage(content=prompt)])
        response_text = response.content if hasattr(response, "content") else str(response)
        
        import json
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            result = json.loads(json_match.group())
            return {
                "selected_agents": result.get("selected_agents", available_agents),
                "reason": result.get("reason", ""),
            }
    except Exception as e:
        print(f"[Debate 选择] LLM 判断失败: {e}")
    
    # 降级：返回所有可用 Agent
    return {
        "selected_agents": available_agents,
        "reason": "默认使用所有 Agent",
    }


def _build_state_summary(agent_id: str, state: Dict[str, Any]) -> str:
    """构建当前状态摘要，供 Facilitator 判断"""
    outputs = []
    
    if agent_id == "planner" and state.get("plan_text"):
        outputs.append(f"【Planner 输出】\n{state['plan_text'][:500]}")
    elif agent_id == "conflict" and state.get("conflict_text"):
        outputs.append(f"【Conflict 输出】\n{state['conflict_text'][:300]}")
    elif agent_id == "writer" and state.get("draft_text"):
        outputs.append(f"【Writer 草稿】\n{state['draft_text'][:500]}")
    elif agent_id == "editor" and state.get("edited_text"):
        outputs.append(f"【Editor 修订】\n{state['edited_text'][:500]}")
    
    if state.get("input_text"):
        outputs.append(f"【用户输入】\n{state['input_text'][:200]}")
    
    return "\n\n".join(outputs)


def _facilitator_decide_next_step(
    current_agent: str,
    state_summary: str,
    completed_agents: List[str],
    pending_agents: List[str],
    base_llm: Any,
    enabled_agents: List[str] = None,
    fast_mode: bool = True,
) -> Dict[str, Any]:
    """
    由 Facilitator 自主决定下一步：
    1. 是否需要评审/debate？
    2. 需要哪些 Agent 参与？
    3. 需要几轮评审？
    
    结合了评估矩阵和 LLM 自主判断
    
    Args:
        fast_mode: 快速模式，使用评估矩阵结果而不调用 LLM
    """
    from langchain_core.messages import HumanMessage
    
    # 默认启用所有评估 Agent（包含新增的 summary）
    if enabled_agents is None:
        enabled_agents = ["reader", "critic", "editor", "consistency", "summary"]
    
    # ========== 评估矩阵信息 ==========
    all_review_agents = {
        "reader": "读者 - 阅读体验/情感",
        "critic": "批评家 - 逻辑/情节",
        "editor": "编辑 - 结构/语言",
        "consistency": "一致性 - 设定/逻辑",
        "summary": "总结师 - 核心观点/关键信息",
    }
    
    # 从评估矩阵获取推荐
    recommended_evaluators = []
    recommended_rounds = 1
    try:
        from app.services.agent_evaluation_matrix import get_evaluators_for_agent, get_evaluation_config
        matrix_config = get_evaluation_config(current_agent)
        recommended_evaluators = get_evaluators_for_agent(current_agent, enabled_agents)
        recommended_rounds = matrix_config.get("default_rounds", 1) if matrix_config else 1
    except ImportError:
        pass
    
    # 简化版 prompt - 减少 token
    content_len = len(state_summary)
    is_short = content_len < 50
    
    # 短内容直接跳过，避免调用 LLM
    if is_short:
        return {
            "should_debate": False,
            "debate_agents": [],
            "debate_rounds": 1,
            "reason": "内容太短，跳过评审",
        }
    
    # ========== 快速模式：直接使用评估矩阵结果 ==========
    if fast_mode:
        # 根据评估矩阵决定是否需要评审
        if not recommended_evaluators:
            return {
                "should_debate": False,
                "debate_agents": [],
                "debate_rounds": 1,
                "reason": "评估矩阵无推荐，使用快速模式",
            }
        
        # 短内容减少评审轮数
        if content_len < 500:
            recommended_rounds = 1
        
        return {
            "should_debate": True,
            "debate_agents": recommended_evaluators,
            "debate_rounds": recommended_rounds,
            "reason": f"快速模式：使用评估矩阵推荐 {recommended_evaluators}",
        }
    
    # ========== 完整模式：使用 LLM 决策 ==========
    prompt = f"""当前: {current_agent}, 内容: {content_len}字符

推荐: {recommended_evaluators}, {recommended_rounds}轮

需要评审? 输出JSON:
{{"should_debate": true/false, "debate_agents": [], "debate_rounds": 1, "reason": ""}}"""
    
    try:
        response = base_llm.invoke([HumanMessage(content=prompt)])
        response_text = response.content if hasattr(response, "content") else str(response)
        
        import json
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            result = json.loads(json_match.group())
            return {
                "should_debate": result.get("should_debate", False),
                "debate_agents": result.get("debate_agents", []),
                "debate_rounds": result.get("debate_rounds", 1),
                "reason": result.get("reason", ""),
            }
    except Exception as e:
        print(f"[Facilitator] 决策失败: {e}")
    
    # 降级：默认不评审
    return {
        "should_debate": False,
        "debate_agents": [],
        "debate_rounds": 1,
        "reason": "默认不评审",
    }


def _run_debate(
    draft_text: str,
    outline: str,
    debate_agents: List[str],
    max_rounds: int,
    state: Dict[str, Any],
    story_id: str,
    base_llm: Any,
) -> Dict[str, Any]:
    """
    运行 Debate 模式：多个 Agent 对草稿进行辩论并改进
    
    优化点：
    1. 使用 ThreadPoolExecutor 并行执行各 Agent 的反馈
    2. 动态决定需要哪些 Agent 参与
    3. 根据反馈质量动态决定是否需要下一轮
    """
    from langchain_core.messages import HumanMessage
    import time
    import concurrent.futures
    
    t0 = time.time()
    rounds = []
    current_text = draft_text
    
    # Agent 角色定义
    agent_roles = {
        "reader": "读者视角：关注阅读体验、情感共鸣、节奏感",
        "critic": "批评家视角：关注逻辑漏洞、情节合理性、人物一致性",
        "editor": "编辑视角：关注结构优化、语言表达、整体质量",
        "consistency": "一致性检查：关注角色设定一致、世界观逻辑",
        "summary": "总结师视角：提取核心观点、关键信息、总结归纳",  # 新增
    }
    
    print(f"\n[Debate] 开始并行辩论，参与者: {debate_agents}")
    
    for round_num in range(1, max_rounds + 1):
        print(f"\n--- Debate Round {round_num}/{max_rounds} ---")
        round_start = time.time()
        
        # 定义同步的反馈获取函数
        def get_feedback_sync(agent_id: str) -> dict:
            role_desc = agent_roles.get(agent_id, "提供反馈")
            
            # 注入 skill 约束和 agent prompt（关键修复！）
            constraints = _build_constraints_prefix(story_id, agent_id)
            
            prompt = f"""{constraints}你是{role_desc}。

请简洁地阅读以下章节草稿，给出1-2条最重要的改进建议。

## 大纲
{outline[:300]}

## 草稿
{current_text[:1500]}

直接给出建议，不要超过50字。"""
            
            try:
                agent_llm = _get_llm_for_agent(agent_id, base_llm)
                response = agent_llm.invoke([HumanMessage(content=prompt)])
                feedback = response.content if hasattr(response, "content") else str(response)
                return {"agent": agent_id, "feedback": feedback[:300]}
            except Exception as e:
                return {"agent": agent_id, "feedback": f"错误: {e}"}
        
        # 并行执行所有 Agent（使用 ThreadPoolExecutor）
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(debate_agents)) as executor:
            futures = [executor.submit(get_feedback_sync, agent_id) for agent_id in debate_agents]
            round_feedback = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # 按原始顺序排列
        feedback_dict = {f["agent"]: f["feedback"] for f in round_feedback}
        round_feedback = [{"agent": a, "feedback": feedback_dict.get(a, "")} for a in debate_agents]
        
        for fb in round_feedback:
            print(f"[{fb['agent']}] {fb['feedback'][:100]}...")
        
        rounds.append({
            "round": round_num,
            "feedbacks": round_feedback,
        })
        
        # 快速判断是否需要改进 - 如果反馈都是正面的，跳出
        negative_count = sum(1 for f in round_feedback if any(kw in f["feedback"] for kw in ["问题", "不足", "需要", "建议", "可以", "优化"]))
        
        # 最后一轮或反馈较少时不改进
        if round_num >= max_rounds or negative_count < len(debate_agents) * 0.5:
            print(f"[Debate] 反馈良好，跳过后续改进")
            break
        
        # 综合反馈，让 Writer 快速改进（注入 skill 约束！）
        feedback_summary = "\n".join([f"- {f['agent']}: {f['feedback']}" for f in round_feedback])
        
        # 注入 writer 的 skill 约束
        constraints = _build_constraints_prefix(story_id, "writer")
        improve_prompt = f"""{constraints}根据以下反馈改进草稿：

{feedback_summary}

## 原文
{current_text}

只输出改进后的内容，保持原样，只修改必要部分："""
        
        try:
            writer_llm = _get_llm_for_agent("writer", base_llm)
            response = writer_llm.invoke([HumanMessage(content=improve_prompt)])
            improved = response.content if hasattr(response, "content") else str(response)
            
            # 清理 markdown 格式
            if "```" in improved:
                import re
                match = re.search(r'```[\w]*\n?([\s\S]*?)```', improved)
                if match:
                    improved = match.group(1).strip()
            
            if improved and len(improved) > len(current_text) * 0.5:
                current_text = improved
                print(f"[Debate] 改进完成，耗时: {time.time() - round_start:.1f}s")
            else:
                print(f"[Debate] 改进效果不佳，保持原样")
        except Exception as e:
            print(f"[Debate] 改进失败: {e}")
            break
    
    elapsed = time.time() - t0
    print(f"\n[Debate] 完成，耗时: {elapsed:.1f}s")
    
    return {
        "rounds": rounds,
        "improved_text": current_text,
        "elapsed": elapsed,
    }
