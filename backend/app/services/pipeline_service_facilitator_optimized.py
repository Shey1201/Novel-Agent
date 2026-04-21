"""
基于 Facilitator 动态协调的章节生成流水线 - 优化版

优化点：
1. 简化 LLM 决策 prompt - 减少 token
2. 添加 Agent 配置缓存 - 减少数据库查询
3. 添加结果缓存 - 重复内容秒级响应
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
class AgentConfigCache:
    """Agent 配置缓存 - 避免重复查询数据库"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._timestamp: Dict[str, float] = {}
        self._ttl = 300  # 5分钟缓存
    
    def get(self, agent_id: str) -> Optional[Any]:
        """获取缓存的配置"""
        if agent_id in self._cache:
            if time.time() - self._timestamp.get(agent_id, 0) < self._ttl:
                return self._cache[agent_id]
        return None
    
    def set(self, agent_id: str, config: Any):
        """设置缓存"""
        self._cache[agent_id] = config
        self._timestamp[agent_id] = time.time()
    
    def invalidate(self):
        """清空缓存"""
        self._cache.clear()
        self._timestamp.clear()


class ResultCache:
    """结果缓存 - 重复内容秒级响应"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._timestamp: Dict[str, float] = {}
        self._ttl = 3600  # 1小时缓存
    
    def _make_key(self, agent_id: str, input_hash: str) -> str:
        """生成缓存 key"""
        return f"{agent_id}:{input_hash}"
    
    def get(self, agent_id: str, input_text: str) -> Optional[Any]:
        """获取缓存的结果"""
        input_hash = hashlib.md5(input_text.encode()).hexdigest()[:16]
        key = self._make_key(agent_id, input_hash)
        
        if key in self._cache:
            if time.time() - self._timestamp.get(key, 0) < self._ttl:
                return self._cache[key]
        return None
    
    def set(self, agent_id: str, input_text: str, result: Any):
        """设置缓存"""
        input_hash = hashlib.md5(input_text.encode()).hexdigest()[:16]
        key = self._make_key(agent_id, input_hash)
        self._cache[key] = result
        self._timestamp[key] = time.time()


# 全局缓存实例
_config_cache = AgentConfigCache()
_result_cache = ResultCache()


def _get_cached_config(agent_id: str) -> Optional[Any]:
    """获取缓存的 Agent 配置"""
    return _config_cache.get(agent_id)


def _set_cached_config(agent_id: str, config: Any):
    """设置缓存的 Agent 配置"""
    _config_cache.set(agent_id, config)


def _get_cached_result(agent_id: str, input_text: str) -> Optional[Any]:
    """获取缓存的结果"""
    return _result_cache.get(agent_id, input_text)


def _set_cached_result(agent_id: str, input_text: str, result: Any):
    """设置缓存的结果"""
    _result_cache.set(agent_id, input_text, result)


def _build_constraints_prefix(story_id: str, agent_id: str) -> str:
    """与 AgentChatService 一致：Agent 配置 prompt + 挂载 skills 约束"""
    # 先从缓存获取
    cfg = _get_cached_config(agent_id)
    if cfg is None:
        cfg = agent_memory.get_config(agent_id)
        if cfg:
            _set_cached_config(agent_id, cfg)
    
    parts: List[str] = []
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


# ... (其余函数保持不变，引用上面的缓存函数)


def _facilitator_decide_next_step_v2(
    current_agent: str,
    state_summary: str,
    completed_agents: List[str],
    pending_agents: List[str],
    base_llm: Any,
    enabled_agents: List[str] = None,
) -> Dict[str, Any]:
    """
    简化版 LLM 决策 - 减少 token 数量
    """
    from langchain_core.messages import HumanMessage
    
    if enabled_agents is None:
        enabled_agents = ["reader", "critic", "editor", "consistency"]
    
    # 从评估矩阵获取推荐
    try:
        from app.services.agent_evaluation_matrix import get_evaluators_for_agent, get_evaluation_config
        matrix_config = get_evaluation_config(current_agent)
        recommended_evaluators = get_evaluators_for_agent(current_agent, enabled_agents)
        recommended_rounds = matrix_config.get("default_rounds", 1) if matrix_config else 1
    except ImportError:
        recommended_evaluators = []
        recommended_rounds = 1
    
    # 简化版 prompt
    content_len = len(state_summary)
    is_short = content_len < 50
    
    prompt = f"""当前: {current_agent}, 内容长度: {content_len}字符

推荐评审: {recommended_evaluators}, 轮数: {recommended_rounds}

判断是否需要评审？

JSON输出:
{{
  "needs_evaluation": true/false,
  "evaluators": ["reader"],
  "debate_rounds": 1,
  "reason": "原因"
}}"""
    
    try:
        response = base_llm.invoke([HumanMessage(content=prompt)])
        response_text = response.content if hasattr(response, "content") else str(response)
        
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            result = json.loads(json_match.group())
            
            # 特殊情况：内容太短，跳过评审
            if is_short:
                result["needs_evaluation"] = False
                result["reason"] = "内容太短，跳过评审"
            
            return {
                "needs_evaluation": result.get("needs_evaluation", False),
                "evaluators": result.get("evaluators", recommended_evaluators),
                "debate_rounds": result.get("debate_rounds", recommended_rounds),
                "reason": result.get("reason", ""),
            }
    except Exception as e:
        print(f"[Facilitator] 决策失败: {e}")
    
    # 降级：短内容跳过，长内容默认评审
    return {
        "needs_evaluation": not is_short,
        "evaluators": recommended_evaluators if not is_short else [],
        "debate_rounds": recommended_rounds,
        "reason": "默认决策",
    }


# 导出优化后的函数
def enable_caching():
    """启用缓存"""
    global _config_cache, _result_cache
    _config_cache = AgentConfigCache()
    _result_cache = ResultCache()


def clear_cache():
    """清空缓存"""
    _config_cache.invalidate()
    _result_cache = ResultCache()