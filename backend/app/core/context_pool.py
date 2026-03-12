"""
Context Pool - 上下文缓存池
减少重复的文件 I/O 和向量检索，降低 Token 消耗
"""

import time
import hashlib
import threading
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from collections import OrderedDict
import json


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float
    access_count: int = 0
    last_accessed: float = 0
    
    def is_expired(self, ttl_seconds: float) -> bool:
        return (time.time() - self.created_at) > ttl_seconds


class LRUCache:
    """LRU 缓存实现"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: float = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            
            # 检查过期
            if entry.is_expired(self.ttl_seconds):
                del self._cache[key]
                return None
            
            # 更新访问信息
            entry.access_count += 1
            entry.last_accessed = time.time()
            # 移到末尾（最近使用）
            self._cache.move_to_end(key)
            
            return entry.value
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存"""
        with self._lock:
            # 如果存在，更新
            if key in self._cache:
                self._cache[key].value = value
                self._cache[key].created_at = time.time()
                self._cache[key].last_accessed = time.time()
                self._cache.move_to_end(key)
                return
            
            # 如果超过最大容量，删除最旧的
            if len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
            
            # 添加新条目
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                last_accessed=time.time()
            )
            self._cache[key] = entry
    
    def invalidate(self, key: str) -> None:
        """删除指定缓存"""
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            total_accesses = sum(e.access_count for e in self._cache.values())
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "total_accesses": total_accesses,
                "hit_rate": total_accesses / max(1, len(self._cache))
            }


class ContextPool:
    """
    上下文缓存池
    
    功能：
    1. 缓存 StoryMemory - 减少文件 I/O
    2. 缓存世界设定 - 减少重复加载
    3. 缓存角色数据 - 减少数据库查询
    4. 预取机制 - 提前加载常用数据
    """
    
    _instance: Optional['ContextPool'] = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, memory_ttl: float = 300, world_ttl: float = 600, character_ttl: float = 600):
        # 如果已初始化，跳过
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        # 记忆缓存 (5分钟 TTL)
        self.memory_cache = LRUCache(max_size=50, ttl_seconds=memory_ttl)
        
        # 世界设定缓存 (10分钟 TTL)
        self.world_cache = LRUCache(max_size=30, ttl_seconds=world_ttl)
        
        # 角色缓存 (10分钟 TTL)
        self.character_cache = LRUCache(max_size=100, ttl_seconds=character_ttl)
        
        # 语义检索缓存 (3分钟 TTL)
        self.semantic_cache = LRUCache(max_size=200, ttl_seconds=180)
        
        self._initialized = True
    
    @staticmethod
    def get_instance() -> 'ContextPool':
        """获取单例实例"""
        return ContextPool()
    
    # ========== 记忆缓存 ==========
    
    def get_memory(self, story_id: str) -> Optional[Any]:
        """获取缓存的记忆"""
        key = f"memory:{story_id}"
        return self.memory_cache.get(key)
    
    def set_memory(self, story_id: str, memory: Any) -> None:
        """缓存记忆"""
        key = f"memory:{story_id}"
        self.memory_cache.set(key, memory)
    
    def invalidate_memory(self, story_id: str) -> None:
        """使记忆缓存失效"""
        key = f"memory:{story_id}"
        self.memory_cache.invalidate(key)
    
    # ========== 世界设定缓存 ==========
    
    def get_world(self, story_id: str) -> Optional[Dict]:
        """获取缓存的世界设定"""
        key = f"world:{story_id}"
        return self.world_cache.get(key)
    
    def set_world(self, story_id: str, world_data: Dict) -> None:
        """缓存世界设定"""
        key = f"world:{story_id}"
        self.world_cache.set(key, world_data)
    
    # ========== 角色缓存 ==========
    
    def get_character(self, story_id: str, character_id: str) -> Optional[Dict]:
        """获取缓存的角色"""
        key = f"char:{story_id}:{character_id}"
        return self.character_cache.get(key)
    
    def get_all_characters(self, story_id: str) -> Optional[List[Dict]]:
        """获取缓存的所有角色"""
        key = f"chars:{story_id}"
        return self.character_cache.get(key)
    
    def set_character(self, story_id: str, character_id: str, character_data: Dict) -> None:
        """缓存角色"""
        key = f"char:{story_id}:{character_id}"
        self.character_cache.set(key, character_data)
    
    def set_all_characters(self, story_id: str, characters: List[Dict]) -> None:
        """缓存所有角色"""
        key = f"chars:{story_id}"
        self.character_cache.set(key, characters)
    
    # ========== 语义检索缓存 ==========
    
    def get_semantic(self, story_id: str, query: str, top_k: int = 5) -> Optional[List[Dict]]:
        """获取缓存的语义检索结果"""
        # 对查询进行哈希
        query_hash = hashlib.md5(query.encode()).hexdigest()[:16]
        key = f"semantic:{story_id}:{query_hash}:{top_k}"
        return self.semantic_cache.get(key)
    
    def set_semantic(self, story_id: str, query: str, top_k: int, results: List[Dict]) -> None:
        """缓存语义检索结果"""
        query_hash = hashlib.md5(query.encode()).hexdigest()[:16]
        key = f"semantic:{story_id}:{query_hash}:{top_k}"
        self.semantic_cache.set(key, results)
    
    # ========== 预取 ==========
    
    def prefetch_memory(self, story_id: str, loader_fn) -> None:
        """预取记忆数据"""
        # 如果缓存中没有，则加载
        if self.get_memory(story_id) is None:
            try:
                memory = loader_fn(story_id)
                if memory:
                    self.set_memory(story_id, memory)
            except Exception as e:
                print(f"[ContextPool] Prefetch memory failed: {e}")
    
    def prefetch_world(self, story_id: str, loader_fn) -> None:
        """预取世界设定"""
        if self.get_world(story_id) is None:
            try:
                world = loader_fn(story_id)
                if world:
                    self.set_world(story_id, world)
            except Exception as e:
                print(f"[ContextPool] Prefetch world failed: {e}")
    
    def prefetch_characters(self, story_id: str, loader_fn) -> None:
        """预取角色列表"""
        if self.get_all_characters(story_id) is None:
            try:
                characters = loader_fn(story_id)
                if characters:
                    self.set_all_characters(story_id, characters)
            except Exception as e:
                print(f"[ContextPool] Prefetch characters failed: {e}")
    
    # ========== 统计和清理 ==========
    
    def get_stats(self) -> Dict[str, Any]:
        """获取所有缓存的统计信息"""
        return {
            "memory": self.memory_cache.get_stats(),
            "world": self.world_cache.get_stats(),
            "characters": self.character_cache.get_stats(),
            "semantic": self.semantic_cache.get_stats()
        }
    
    def clear_all(self) -> None:
        """清空所有缓存"""
        self.memory_cache.clear()
        self.world_cache.clear()
        self.character_cache.clear()
        self.semantic_cache.clear()
    
    def clear_story(self, story_id: str) -> None:
        """清空某个故事的缓存"""
        # 这里简化处理，实际可能需要更精细的清理
        self.invalidate_memory(story_id)


# 全局单例
_context_pool: Optional[ContextPool] = None


def get_context_pool() -> ContextPool:
    """获取全局上下文池实例"""
    global _context_pool
    if _context_pool is None:
        _context_pool = ContextPool()
    return _context_pool


def clear_context_pool() -> None:
    """清空全局上下文池"""
    global _context_pool
    if _context_pool:
        _context_pool.clear_all()
        _context_pool = None
