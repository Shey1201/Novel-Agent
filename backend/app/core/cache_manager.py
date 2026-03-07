"""
Cache Manager - 缓存管理器
提供多级缓存策略，包括内存缓存、磁盘缓存和智能预热
"""

import os
import json
import pickle
import hashlib
import time
import asyncio
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from functools import wraps
import threading


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float
    expires_at: float
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)


@dataclass
class CacheStats:
    """缓存统计"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_size: int = 0
    entry_count: int = 0


class MemoryCache:
    """
    内存缓存 (L1)
    
    基于 LRU 策略的高速内存缓存
    """
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.stats = CacheStats()
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            entry = self.cache.get(key)
            
            if entry is None:
                self.stats.misses += 1
                return None
            
            # 检查是否过期
            if time.time() > entry.expires_at:
                del self.cache[key]
                self.stats.misses += 1
                self.stats.evictions += 1
                return None
            
            # 更新访问统计
            entry.access_count += 1
            entry.last_accessed = time.time()
            self.stats.hits += 1
            
            return entry.value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """设置缓存值"""
        with self.lock:
            # 清理过期项
            self._cleanup_expired()
            
            # 如果缓存已满，淘汰最少使用的
            if len(self.cache) >= self.max_size:
                self._evict_lru()
            
            expires_at = time.time() + (ttl or self.ttl)
            
            self.cache[key] = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                expires_at=expires_at
            )
            
            self.stats.entry_count = len(self.cache)
    
    def delete(self, key: str):
        """删除缓存项"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                self.stats.entry_count = len(self.cache)
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.stats = CacheStats()
    
    def _cleanup_expired(self):
        """清理过期项"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time > entry.expires_at
        ]
        for key in expired_keys:
            del self.cache[key]
            self.stats.evictions += 1
    
    def _evict_lru(self):
        """淘汰最少使用的项"""
        if not self.cache:
            return
        
        # 找到最少访问的项
        lru_key = min(
            self.cache.keys(),
            key=lambda k: (
                self.cache[k].access_count,
                self.cache[k].last_accessed
            )
        )
        
        del self.cache[lru_key]
        self.stats.evictions += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            total_requests = self.stats.hits + self.stats.misses
            hit_rate = self.stats.hits / total_requests if total_requests > 0 else 0
            
            return {
                "hits": self.stats.hits,
                "misses": self.stats.misses,
                "hit_rate": hit_rate,
                "evictions": self.stats.evictions,
                "entry_count": len(self.cache),
                "max_size": self.max_size,
                "ttl": self.ttl
            }


class DiskCache:
    """
    磁盘缓存 (L2)
    
    持久化存储，用于大对象和长期缓存
    """
    
    def __init__(self, cache_dir: str = ".cache", max_size_mb: int = 100):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.stats = CacheStats()
        self.lock = threading.RLock()
        
        # 索引文件
        self.index_file = self.cache_dir / "index.json"
        self.index: Dict[str, Dict[str, Any]] = self._load_index()
    
    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        """加载索引"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_index(self):
        """保存索引"""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f)
    
    def _get_cache_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        # 使用哈希作为文件名
        filename = hashlib.md5(key.encode()).hexdigest() + ".cache"
        return self.cache_dir / filename
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            if key not in self.index:
                self.stats.misses += 1
                return None
            
            entry_info = self.index[key]
            
            # 检查是否过期
            if time.time() > entry_info.get("expires_at", 0):
                self.delete(key)
                self.stats.misses += 1
                return None
            
            # 读取文件
            cache_path = self._get_cache_path(key)
            if not cache_path.exists():
                del self.index[key]
                self._save_index()
                self.stats.misses += 1
                return None
            
            try:
                with open(cache_path, 'rb') as f:
                    value = pickle.load(f)
                
                # 更新访问统计
                entry_info["access_count"] = entry_info.get("access_count", 0) + 1
                entry_info["last_accessed"] = time.time()
                self._save_index()
                
                self.stats.hits += 1
                return value
            except Exception:
                self.stats.misses += 1
                return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """设置缓存值"""
        with self.lock:
            # 检查磁盘空间
            self._cleanup_if_needed()
            
            cache_path = self._get_cache_path(key)
            
            try:
                # 保存到文件
                with open(cache_path, 'wb') as f:
                    pickle.dump(value, f)
                
                # 更新索引
                expires_at = time.time() + (ttl or 3600)  # 默认1小时
                self.index[key] = {
                    "created_at": time.time(),
                    "expires_at": expires_at,
                    "access_count": 0,
                    "last_accessed": time.time(),
                    "size": cache_path.stat().st_size
                }
                
                self._save_index()
            except Exception as e:
                print(f"Disk cache write error: {e}")
    
    def delete(self, key: str):
        """删除缓存项"""
        with self.lock:
            if key in self.index:
                cache_path = self._get_cache_path(key)
                if cache_path.exists():
                    cache_path.unlink()
                del self.index[key]
                self._save_index()
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            # 删除所有缓存文件
            for key in list(self.index.keys()):
                cache_path = self._get_cache_path(key)
                if cache_path.exists():
                    cache_path.unlink()
            
            self.index.clear()
            self._save_index()
            self.stats = CacheStats()
    
    def _cleanup_if_needed(self):
        """如果需要，清理缓存"""
        total_size = sum(
            info.get("size", 0) for info in self.index.values()
        )
        
        if total_size < self.max_size_bytes:
            return
        
        # 按最后访问时间排序
        sorted_items = sorted(
            self.index.items(),
            key=lambda x: x[1].get("last_accessed", 0)
        )
        
        # 删除最旧的直到空间足够
        target_size = self.max_size_bytes * 0.8  # 保留80%
        for key, info in sorted_items:
            if total_size <= target_size:
                break
            
            self.delete(key)
            total_size -= info.get("size", 0)
            self.stats.evictions += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            total_requests = self.stats.hits + self.stats.misses
            hit_rate = self.stats.hits / total_requests if total_requests > 0 else 0
            
            total_size = sum(
                info.get("size", 0) for info in self.index.values()
            )
            
            return {
                "hits": self.stats.hits,
                "misses": self.stats.misses,
                "hit_rate": hit_rate,
                "evictions": self.stats.evictions,
                "entry_count": len(self.index),
                "total_size_mb": total_size / (1024 * 1024),
                "max_size_mb": self.max_size_bytes / (1024 * 1024)
            }


class CacheManager:
    """
    缓存管理器
    
    统一管理多级缓存
    """
    
    def __init__(
        self,
        memory_cache_size: int = 1000,
        memory_ttl: int = 300,
        disk_cache_dir: str = ".cache",
        disk_cache_size_mb: int = 100
    ):
        self.l1_cache = MemoryCache(
            max_size=memory_cache_size,
            ttl=memory_ttl
        )
        self.l2_cache = DiskCache(
            cache_dir=disk_cache_dir,
            max_size_mb=disk_cache_size_mb
        )
        
        # 预热数据
        self.warmup_keys: set = set()
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        先查 L1，再查 L2
        """
        # 尝试 L1
        value = self.l1_cache.get(key)
        if value is not None:
            return value
        
        # 尝试 L2
        value = self.l2_cache.get(key)
        if value is not None:
            # 回填 L1
            self.l1_cache.set(key, value)
            return value
        
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        level: str = "both"  # "l1", "l2", "both"
    ):
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            level: 缓存级别
        """
        if level in ("l1", "both"):
            self.l1_cache.set(key, value, ttl)
        
        if level in ("l2", "both"):
            self.l2_cache.set(key, value, ttl)
    
    def delete(self, key: str):
        """删除缓存项"""
        self.l1_cache.delete(key)
        self.l2_cache.delete(key)
    
    def clear(self, level: str = "both"):
        """清空缓存"""
        if level in ("l1", "both"):
            self.l1_cache.clear()
        
        if level in ("l2", "both"):
            self.l2_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "l1_memory": self.l1_cache.get_stats(),
            "l2_disk": self.l2_cache.get_stats()
        }
    
    async def warmup(self, keys_and_values: Dict[str, Any], ttl: int = 3600):
        """
        预热缓存
        
        Args:
            keys_and_values: 键值对
            ttl: 过期时间
        """
        for key, value in keys_and_values.items():
            self.set(key, value, ttl, level="both")
            self.warmup_keys.add(key)
    
    def is_warmup_key(self, key: str) -> bool:
        """检查是否是预热键"""
        return key in self.warmup_keys


def cached(
    ttl: int = 300,
    key_prefix: str = "",
    cache_manager: Optional[CacheManager] = None
):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存时间（秒）
        key_prefix: 键前缀
        cache_manager: 缓存管理器实例
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 生成缓存键
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = hashlib.md5(
                ":".join(key_parts).encode()
            ).hexdigest()
            
            # 获取缓存管理器
            cm = cache_manager or _default_cache_manager
            
            # 尝试获取缓存
            cached_value = cm.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            cm.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 生成缓存键
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = hashlib.md5(
                ":".join(key_parts).encode()
            ).hexdigest()
            
            # 获取缓存管理器
            cm = cache_manager or _default_cache_manager
            
            # 尝试获取缓存
            cached_value = cm.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            cm.set(cache_key, result, ttl)
            
            return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# 默认缓存管理器实例
_default_cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """获取默认缓存管理器"""
    return _default_cache_manager


def set_default_cache_manager(cm: CacheManager):
    """设置默认缓存管理器"""
    global _default_cache_manager
    _default_cache_manager = cm
