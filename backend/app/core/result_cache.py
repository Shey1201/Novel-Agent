"""
结果缓存 - 对重复内容秒级响应

功能：
- 缓存生成结果，对重复内容直接返回缓存
- 支持 hash 键，快速查找
- 可配置过期时间
"""
import hashlib
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from threading import Lock


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float
    ttl: float  # 过期时间（秒）
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl <= 0:
            return False  # 永不过期
        return time.time() - self.created_at > self.ttl


class ResultCache:
    """
    结果缓存管理器
    
    使用方式：
    cache = ResultCache(ttl=3600)  # 1小时过期
    cache.set("key", "value")
    value = cache.get("key")
    """
    
    def __init__(self, max_size: int = 1000, ttl: float = 3600):
        """
        初始化缓存
        
        Args:
            max_size: 最大缓存条目数
            ttl: 默认过期时间（秒），0 表示永不过期
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = ttl
        self._lock = Lock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                return None
            
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return None
            
            self._hits += 1
            return entry.value
    
    def set(self, key: str, value: Any, ttl: float = None):
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None 使用默认值
        """
        with self._lock:
            # 如果缓存已满，删除最旧的条目
            if len(self._cache) >= self._max_size:
                self._evict_oldest()
            
            self._cache[key] = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                ttl=ttl if ttl is not None else self._default_ttl,
            )
    
    def delete(self, key: str):
        """删除缓存"""
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def _evict_oldest(self):
        """删除最旧的缓存条目"""
        if not self._cache:
            return
        
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at
        )
        del self._cache[oldest_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": f"{hit_rate * 100:.1f}%",
            }
    
    def __len__(self):
        return len(self._cache)


def generate_cache_key(
    content: str,
    agent_type: str,
    story_id: str = None,
    chapter_id: str = None,
) -> str:
    """
    生成缓存键
    
    使用内容的 hash 作为键，确保相同内容生成相同的键
    """
    # 组合信息
    parts = [
        agent_type,
        story_id or "",
        chapter_id or "",
        content[:500],  # 只取前500字符
    ]
    
    key_str = "|".join(parts)
    return hashlib.md5(key_str.encode('utf-8')).hexdigest()


# 全局缓存实例
_result_cache = None


def get_result_cache() -> ResultCache:
    """获取全局结果缓存"""
    global _result_cache
    if _result_cache is None:
        _result_cache = ResultCache(max_size=500, ttl=3600)
    return _result_cache


# 便捷函数
def cached_generation(
    key: str,
    generator_func,
    *args,
    **kwargs,
):
    """
    缓存生成装饰器/函数
    
    使用方式：
    result = cached_generation(
        key=cache_key,
        generator_func=agent.run,
        outline="...",
    )
    """
    cache = get_result_cache()
    
    # 尝试从缓存获取
    cached = cache.get(key)
    if cached is not None:
        print(f"[Cache] 命中缓存: {key[:16]}...")
        return cached
    
    # 执行生成
    result = generator_func(*args, **kwargs)
    
    # 保存到缓存
    cache.set(key, result)
    print(f"[Cache] 已缓存: {key[:16]}...")
    
    return result
