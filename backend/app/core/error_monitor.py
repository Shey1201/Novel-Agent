"""
错误监控模块
提供错误收集、报告和分析功能
"""
import traceback
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict
import threading
import logging

logger = logging.getLogger(__name__)


class ErrorRecord:
    """错误记录"""
    
    def __init__(
        self,
        error_type: str,
        message: str,
        stack_trace: str,
        context: Optional[Dict[str, Any]] = None
    ):
        self.id = hashlib.md5(f"{error_type}:{message}".encode()).hexdigest()[:12]
        self.error_type = error_type
        self.message = message
        self.stack_trace = stack_trace
        self.context = context or {}
        self.timestamp = datetime.now()
        self.count = 1
        self.resolved = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "error_type": self.error_type,
            "message": self.message,
            "stack_trace": self.stack_trace,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "count": self.count,
            "resolved": self.resolved,
        }


class ErrorMonitor:
    """错误监控器"""
    
    def __init__(self, max_errors: int = 1000, retention_days: int = 7):
        self.max_errors = max_errors
        self.retention_days = retention_days
        self.errors: Dict[str, ErrorRecord] = {}
        self.error_counts: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()
        self._callbacks: List[Callable[[ErrorRecord], None]] = []
    
    def capture_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorRecord:
        """捕获异常"""
        error_type = type(exception).__name__
        message = str(exception)
        stack_trace = traceback.format_exc()
        
        # 生成错误ID
        error_key = hashlib.md5(
            f"{error_type}:{message}:{stack_trace[:200]}".encode()
        ).hexdigest()
        
        with self._lock:
            if error_key in self.errors:
                # 已存在的错误，增加计数
                self.errors[error_key].count += 1
                self.errors[error_key].timestamp = datetime.now()
                record = self.errors[error_key]
            else:
                # 新错误
                record = ErrorRecord(
                    error_type=error_type,
                    message=message,
                    stack_trace=stack_trace,
                    context=context
                )
                self.errors[error_key] = record
                
                # 清理旧错误
                self._cleanup_old_errors()
            
            self.error_counts[error_type] += 1
        
        # 记录到日志
        logger.error(
            f"[{record.id}] {error_type}: {message}",
            extra={
                "error_id": record.id,
                "error_type": error_type,
                "context": context,
            }
        )
        
        # 触发回调
        for callback in self._callbacks:
            try:
                callback(record)
            except Exception as e:
                logger.error(f"Error callback failed: {e}")
        
        return record
    
    def capture_message(
        self,
        message: str,
        level: str = "error",
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorRecord:
        """捕获消息"""
        record = ErrorRecord(
            error_type="Message",
            message=message,
            stack_trace="",
            context={**context, "level": level} if context else {"level": level}
        )
        
        with self._lock:
            self.errors[record.id] = record
            self._cleanup_old_errors()
        
        log_func = getattr(logger, level, logger.error)
        log_func(f"[{record.id}] {message}")
        
        return record
    
    def _cleanup_old_errors(self):
        """清理旧错误"""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        
        # 按时间排序并删除旧错误
        sorted_errors = sorted(
            self.errors.items(),
            key=lambda x: x[1].timestamp
        )
        
        # 删除超过保留期的错误
        for key, record in sorted_errors:
            if record.timestamp < cutoff:
                del self.errors[key]
        
        # 如果仍然超过最大数量，删除最旧的
        while len(self.errors) > self.max_errors:
            oldest_key = sorted_errors[0][0]
            if oldest_key in self.errors:
                del self.errors[oldest_key]
            sorted_errors.pop(0)
    
    def get_error(self, error_id: str) -> Optional[ErrorRecord]:
        """获取单个错误"""
        return self.errors.get(error_id)
    
    def get_all_errors(
        self,
        error_type: Optional[str] = None,
        resolved: Optional[bool] = None
    ) -> List[ErrorRecord]:
        """获取所有错误"""
        errors = list(self.errors.values())
        
        if error_type:
            errors = [e for e in errors if e.error_type == error_type]
        
        if resolved is not None:
            errors = [e for e in errors if e.resolved == resolved]
        
        return sorted(errors, key=lambda x: x.timestamp, reverse=True)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计"""
        with self._lock:
            total_errors = sum(e.count for e in self.errors.values())
            unique_errors = len(self.errors)
            
            # 按类型统计
            by_type = defaultdict(lambda: {"count": 0, "unique": 0})
            for error in self.errors.values():
                by_type[error.error_type]["count"] += error.count
                by_type[error.error_type]["unique"] += 1
            
            # 最近24小时的错误
            last_24h = datetime.now() - timedelta(hours=24)
            recent_errors = [
                e for e in self.errors.values()
                if e.timestamp > last_24h
            ]
            
            return {
                "total_errors": total_errors,
                "unique_errors": unique_errors,
                "recent_errors": len(recent_errors),
                "by_type": dict(by_type),
            }
    
    def resolve_error(self, error_id: str) -> bool:
        """标记错误为已解决"""
        with self._lock:
            if error_id in self.errors:
                self.errors[error_id].resolved = True
                return True
            return False
    
    def clear_errors(self):
        """清除所有错误"""
        with self._lock:
            self.errors.clear()
            self.error_counts.clear()
    
    def add_callback(self, callback: Callable[[ErrorRecord], None]):
        """添加错误回调"""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[ErrorRecord], None]):
        """移除错误回调"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)


# 全局错误监控器实例
error_monitor = ErrorMonitor()


def get_error_monitor() -> ErrorMonitor:
    """获取错误监控器实例"""
    return error_monitor


# 装饰器：自动捕获函数异常
def capture_errors(context: Optional[Dict[str, Any]] = None):
    """
    自动捕获函数异常装饰器
    
    Example:
        @capture_errors({"component": "my_module"})
        def my_function():
            raise Exception("error")
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                ctx = context or {}
                ctx.update({
                    "function": func.__name__,
                    "args": str(args),
                    "kwargs": str(kwargs),
                })
                error_monitor.capture_exception(e, ctx)
                raise
        return wrapper
    return decorator


# 异步版本
def capture_errors_async(context: Optional[Dict[str, Any]] = None):
    """异步函数错误捕获装饰器"""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                ctx = context or {}
                ctx.update({
                    "function": func.__name__,
                    "args": str(args),
                    "kwargs": str(kwargs),
                })
                error_monitor.capture_exception(e, ctx)
                raise
        return wrapper
    return decorator
