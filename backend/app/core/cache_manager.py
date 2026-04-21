"""
缓存管理模块
提供数据库查询缓存功能
"""
import time
from functools import wraps
from typing import Any, Callable, Optional, Dict, Tuple
from threading import Lock

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, default_ttl: int = 300):
        """
        初始化缓存管理器
        
        Args:
            default_ttl: 默认缓存过期时间（秒）
        """
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.default_ttl = default_ttl
        self.lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            if key in self.cache:
                value, expiry = self.cache[key]
                if time.time() < expiry:
                    return value
                else:
                    del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        with self.lock:
            expiry = time.time() + (ttl if ttl is not None else self.default_ttl)
            self.cache[key] = (value, expiry)
    
    def delete(self, key: str) -> None:
        """删除缓存值"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
    
    def clear(self) -> None:
        """清空所有缓存"""
        with self.lock:
            self.cache.clear()
    
    def cleanup_expired(self) -> None:
        """清理过期缓存"""
        with self.lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, expiry) in self.cache.items()
                if current_time >= expiry
            ]
            for key in expired_keys:
                del self.cache[key]

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self.lock:
            total_items = len(self.cache)
            expired_items = sum(1 for _, expiry in self.cache.values() if time.time() >= expiry)
            return {
                "l1_memory": {
                    "total_items": total_items,
                    "expired_items": expired_items,
                    "active_items": total_items - expired_items
                },
                "l2_disk": {
                    "enabled": False,
                    "items": 0
                }
            }

    def warmup(self, data: Dict[str, Any], ttl: int = 3600) -> Dict[str, Any]:
        """预热缓存，批量设置多个缓存项"""
        results = {}
        for key, value in data.items():
            try:
                self.set(key, value, ttl)
                results[key] = True
            except Exception as e:
                results[key] = False
                print(f"Warning: Failed to warmup cache for key {key}: {e}")
        return {"success": True, "items_warmed": len(results), "details": results}


# 全局缓存管理器实例
cache_manager = CacheManager(default_ttl=300)


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存过期时间（秒）
        key_prefix: 缓存键前缀
    
    Example:
        @cached(ttl=60, key_prefix="novels")
        def get_all_novels(self):
            # ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试从缓存获取
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


def cache_invalidate(pattern: str = "") -> None:
    """
    使缓存失效
    
    Args:
        pattern: 缓存键模式（如果为空，则清空所有缓存）
    """
    if pattern:
        with cache_manager.lock:
            keys_to_delete = [
                key for key in cache_manager.cache.keys()
                if key.startswith(pattern)
            ]
            for key in keys_to_delete:
                del cache_manager.cache[key]
    else:
        cache_manager.clear()


def get_cache_manager() -> CacheManager:
    """获取缓存管理器实例"""
    return cache_manager