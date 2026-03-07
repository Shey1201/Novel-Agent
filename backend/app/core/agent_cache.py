"""
Agent Cache - Agent 结果缓存系统
缓存 Agent 的输出结果，避免重复调用 LLM
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import json


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    result: Any
    timestamp: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    
    def touch(self):
        """更新访问信息"""
        self.access_count += 1
        self.last_accessed = datetime.now()


@dataclass
class CacheConfig:
    """缓存配置"""
    max_size: int = 1000              # 最大缓存条目数
    ttl_hours: int = 24               # 默认过期时间
    enable_planner_cache: bool = True
    enable_conflict_cache: bool = True
    enable_consistency_cache: bool = True


class AgentCache:
    """
    Agent 结果缓存
    
    缓存以下 Agent 的结果：
    - Planner: 章节规划
    - Conflict: 冲突分析
    - Consistency: 一致性检查
    
    当作者未修改剧情时，直接复用缓存
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.cache: Dict[str, CacheEntry] = {}
        self._access_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
    
    def _generate_key(
        self,
        agent_type: str,
        novel_id: str,
        chapter_id: str,
        input_hash: str
    ) -> str:
        """生成缓存 key"""
        key_data = f"{agent_type}:{novel_id}:{chapter_id}:{input_hash}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _generate_input_hash(
        self,
        context: Dict[str, Any],
        prompt: str = ""
    ) -> str:
        """生成输入内容的 hash"""
        # 提取关键信息用于 hash
        key_data = {
            "plot_outline": context.get("plot_outline", ""),
            "characters": context.get("characters", []),
            "key_events": context.get("key_events", []),
            "prompt": prompt[:200]  # 只取 prompt 前200字符
        }
        data_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()[:16]
    
    def get(
        self,
        agent_type: str,
        novel_id: str,
        chapter_id: str,
        context: Dict[str, Any],
        prompt: str = ""
    ) -> Optional[Any]:
        """
        获取缓存结果
        
        Returns:
            缓存的结果，如果不存在返回 None
        """
        # 检查是否启用该 Agent 的缓存
        if not self._is_cache_enabled(agent_type):
            return None
        
        input_hash = self._generate_input_hash(context, prompt)
        key = self._generate_key(agent_type, novel_id, chapter_id, input_hash)
        
        entry = self.cache.get(key)
        if entry is None:
            self._access_stats["misses"] += 1
            return None
        
        # 检查是否过期
        if self._is_expired(entry):
            del self.cache[key]
            self._access_stats["misses"] += 1
            return None
        
        # 更新访问信息
        entry.touch()
        self._access_stats["hits"] += 1
        
        return entry.result
    
    def set(
        self,
        agent_type: str,
        novel_id: str,
        chapter_id: str,
        context: Dict[str, Any],
        result: Any,
        prompt: str = ""
    ):
        """设置缓存"""
        # 检查是否启用该 Agent 的缓存
        if not self._is_cache_enabled(agent_type):
            return
        
        # 清理过期条目
        self._cleanup_expired()
        
        # 如果缓存满了，清理最久未使用的
        if len(self.cache) >= self.config.max_size:
            self._evict_lru()
        
        input_hash = self._generate_input_hash(context, prompt)
        key = self._generate_key(agent_type, novel_id, chapter_id, input_hash)
        
        entry = CacheEntry(
            key=key,
            result=result
        )
        self.cache[key] = entry
    
    def _is_cache_enabled(self, agent_type: str) -> bool:
        """检查是否启用该 Agent 的缓存"""
        enabled_map = {
            "planner": self.config.enable_planner_cache,
            "conflict": self.config.enable_conflict_cache,
            "consistency": self.config.enable_consistency_cache,
        }
        return enabled_map.get(agent_type, False)
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """检查条目是否过期"""
        ttl = timedelta(hours=self.config.ttl_hours)
        return datetime.now() - entry.timestamp > ttl
    
    def _cleanup_expired(self):
        """清理过期条目"""
        expired_keys = [
            key for key, entry in self.cache.items()
            if self._is_expired(entry)
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def _evict_lru(self):
        """清理最久未使用的条目"""
        if not self.cache:
            return
        
        # 找到最久未访问的
        lru_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k].last_accessed
        )
        del self.cache[lru_key]
        self._access_stats["evictions"] += 1
    
    def invalidate(
        self,
        novel_id: Optional[str] = None,
        chapter_id: Optional[str] = None,
        agent_type: Optional[str] = None
    ):
        """
        使缓存失效
        
        当剧情修改时调用
        """
        keys_to_remove = []
        
        for key, entry in self.cache.items():
            # 解析 key (虽然无法完全还原，但可以通过重新生成来判断)
            should_remove = False
            
            # 这里简化处理：如果指定了条件，清除所有匹配前缀的
            # 实际应该存储更多信息用于精确匹配
            if novel_id and key.startswith(self._get_prefix(agent_type, novel_id, chapter_id)):
                should_remove = True
            
            if should_remove:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
    
    def _get_prefix(
        self,
        agent_type: Optional[str],
        novel_id: Optional[str],
        chapter_id: Optional[str]
    ) -> str:
        """获取缓存 key 前缀（用于批量失效）"""
        # 简化处理，实际应该存储原始信息
        return f"{agent_type or ''}:{novel_id or ''}:{chapter_id or ''}"
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_requests = self._access_stats["hits"] + self._access_stats["misses"]
        hit_rate = (
            self._access_stats["hits"] / total_requests
            if total_requests > 0 else 0
        )
        
        return {
            "size": len(self.cache),
            "max_size": self.config.max_size,
            "hits": self._access_stats["hits"],
            "misses": self._access_stats["misses"],
            "hit_rate": f"{hit_rate:.2%}",
            "evictions": self._access_stats["evictions"]
        }
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self._access_stats = {"hits": 0, "misses": 0, "evictions": 0}


class CachedAgentWrapper:
    """
    带缓存的 Agent 包装器
    
    自动处理缓存逻辑
    """
    
    def __init__(self, agent_type: str, cache: AgentCache):
        self.agent_type = agent_type
        self.cache = cache
    
    async def call(
        self,
        novel_id: str,
        chapter_id: str,
        context: Dict[str, Any],
        prompt: str,
        agent_func: Callable,
        force_refresh: bool = False
    ) -> Any:
        """
        调用 Agent（带缓存）
        
        Args:
            novel_id: 小说 ID
            chapter_id: 章节 ID
            context: 上下文
            prompt: 提示词
            agent_func: 实际的 Agent 调用函数
            force_refresh: 强制刷新缓存
            
        Returns:
            Agent 结果
        """
        # 尝试从缓存获取
        if not force_refresh:
            cached_result = self.cache.get(
                self.agent_type,
                novel_id,
                chapter_id,
                context,
                prompt
            )
            if cached_result is not None:
                return {
                    "result": cached_result,
                    "from_cache": True
                }
        
        # 调用实际 Agent
        result = await agent_func()
        
        # 存入缓存
        self.cache.set(
            self.agent_type,
            novel_id,
            chapter_id,
            context,
            result,
            prompt
        )
        
        return {
            "result": result,
            "from_cache": False
        }


# 全局实例
agent_cache = AgentCache()


def get_agent_cache() -> AgentCache:
    """获取 Agent 缓存实例"""
    return agent_cache
