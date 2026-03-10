"""
性能监控模块
提供API响应时间监控功能
"""
import time
from fastapi import Request
from typing import Callable, Dict, Optional
from collections import defaultdict
import threading
from fastapi import Response

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        """初始化性能监控器"""
        self.request_times: Dict[str, list] = defaultdict(list)
        self.lock = threading.Lock()
    
    def record_request(self, path: str, duration: float) -> None:
        """记录请求时间"""
        with self.lock:
            self.request_times[path].append(duration)
            # 只保留最近1000条记录
            if len(self.request_times[path]) > 1000:
                self.request_times[path] = self.request_times[path][-1000:]
    
    def get_stats(self, path: str) -> Dict[str, float]:
        """获取指定路径的统计信息"""
        with self.lock:
            times = self.request_times.get(path, [])
            if not times:
                return {
                    "count": 0,
                    "avg": 0,
                    "min": 0,
                    "max": 0,
                    "p50": 0,
                    "p95": 0,
                    "p99": 0
                }
            
            sorted_times = sorted(times)
            return {
                "count": len(times),
                "avg": sum(times) / len(times),
                "min": min(times),
                "max": max(times),
                "p50": sorted_times[len(sorted_times) // 2],
                "p95": sorted_times[int(len(sorted_times) * 0.95)],
                "p99": sorted_times[int(len(sorted_times) * 0.99)]
            }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """获取所有路径的统计信息"""
        with self.lock:
            return {path: self.get_stats(path) for path in self.request_times.keys()}
    
    def clear_stats(self, path: Optional[str] = None) -> None:
        """清除统计信息"""
        with self.lock:
            if path:
                self.request_times[path] = []
            else:
                self.request_times.clear()


# 全局性能监控器实例
performance_monitor = PerformanceMonitor()


async def performance_middleware(request: Request, call_next: Callable) -> Response:
    """
    性能监控中间件
    
    记录每个API请求的响应时间
    """
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # 记录请求时间
        path = request.url.path
        performance_monitor.record_request(path, duration)
        
        # 添加响应头
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        
        return response
    except Exception as e:
        duration = time.time() - start_time
        path = request.url.path
        performance_monitor.record_request(path, duration)
        raise


def get_performance_monitor() -> PerformanceMonitor:
    """获取性能监控器实例"""
    return performance_monitor