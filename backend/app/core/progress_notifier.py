"""
流式进度通知系统 - 实时显示生成进度

功能：
- 实时推送生成进度
- 支持 WebSocket 和 Server-Sent Events
- 可自定义进度消息
"""
import json
import time
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class ProgressStage(Enum):
    """进度阶段"""
    START = "start"
    PLANNING = "planning"
    WRITING = "writing"
    EDITING = "editing"
    DEBATING = "debating"
    REFINING = "refining"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ProgressMessage:
    """进度消息"""
    stage: str
    message: str
    progress: float  # 0-100
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "stage": self.stage,
            "message": self.message,
            "progress": self.progress,
            "timestamp": self.timestamp,
            "data": self.data,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class ProgressNotifier:
    """
    进度通知器
    
    使用方式：
    notifier = ProgressNotifier()
    notifier.notify(ProgressStage.PLANNING, "正在生成大纲...", 20)
    """
    
    def __init__(self):
        self._callbacks: List[Callable[[ProgressMessage], None]] = []
        self._current_stage = ProgressStage.START
        self._progress = 0
        self._start_time = None
        self._stage_times: Dict[str, float] = {}
    
    def add_callback(self, callback: Callable[[ProgressMessage], None]):
        """添加进度回调"""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[ProgressMessage], None]):
        """移除进度回调"""
        self._callbacks.remove(callback)
    
    def notify(
        self,
        stage: ProgressStage,
        message: str,
        progress: float = None,
        data: Dict[str, Any] = None,
    ):
        """
        发送进度通知
        
        Args:
            stage: 当前阶段
            message: 消息内容
            progress: 进度 (0-100)，如果为 None 则根据阶段自动计算
            data: 额外数据
        """
        # 记录阶段开始时间
        stage_key = stage.value
        if stage_key not in self._stage_times:
            self._stage_times[stage_key] = time.time()
        
        # 自动计算进度
        if progress is None:
            progress = self._calculate_progress(stage)
        
        # 创建消息
        msg = ProgressMessage(
            stage=stage.value,
            message=message,
            progress=progress,
            data=data or {},
        )
        
        # 记录当前状态
        self._current_stage = stage
        self._progress = progress
        
        # 调用所有回调
        for callback in self._callbacks:
            try:
                callback(msg)
            except Exception as e:
                print(f"[Progress] 回调错误: {e}")
    
    def _calculate_progress(self, stage: ProgressStage) -> float:
        """根据阶段计算进度"""
        progress_map = {
            ProgressStage.START: 0,
            ProgressStage.PLANNING: 10,
            ProgressStage.WRITING: 40,
            ProgressStage.EDITING: 70,
            ProgressStage.DEBATING: 80,
            ProgressStage.REFINING: 90,
            ProgressStage.COMPLETED: 100,
            ProgressStage.ERROR: 0,
        }
        return progress_map.get(stage, 0)
    
    def start(self):
        """开始计时"""
        self._start_time = time.time()
        self.notify(ProgressStage.START, "开始生成...", 0)
    
    def complete(self, final_data: Dict[str, Any] = None):
        """完成"""
        elapsed = time.time() - self._start_time if self._start_time else 0
        data = {"elapsed": elapsed}
        if final_data:
            data.update(final_data)
        self.notify(ProgressStage.COMPLETED, f"生成完成！耗时 {elapsed:.1f}s", 100, data)
    
    def error(self, error_msg: str):
        """错误"""
        self.notify(ProgressStage.ERROR, f"错误: {error_msg}", 0, {"error": error_msg})
    
    def get_elapsed(self) -> float:
        """获取已用时间"""
        if not self._start_time:
            return 0
        return time.time() - self._start_time
    
    def get_stage_time(self, stage: str) -> float:
        """获取某个阶段的用时"""
        start = self._stage_times.get(stage)
        if not start:
            return 0
        return time.time() - start


# 全局实例
_progress_notifier = None


def get_progress_notifier() -> ProgressNotifier:
    """获取全局进度通知器"""
    global _progress_notifier
    if _progress_notifier is None:
        _progress_notifier = ProgressNotifier()
    return _progress_notifier


# 便捷函数
def notify_progress(stage: ProgressStage, message: str, progress: float = None, data: Dict = None):
    """便捷函数：发送进度通知"""
    notifier = get_progress_notifier()
    notifier.notify(stage, message, progress, data)


# ========== 与 Pipeline 集成的便捷类 ==========

class PipelineProgress:
    """
    Pipeline 进度跟踪器
    
    使用方式：
    progress = PipelineProgress()
    progress.planning()
    progress.writing()
    progress.editing()
    progress.complete()
    """
    
    def __init__(self, notifier: ProgressNotifier = None):
        self.notifier = notifier or get_progress_notifier()
        self.notifier.start()
    
    def planning(self, plan_text: str = ""):
        """规划阶段"""
        word_count = len(plan_text) if plan_text else 0
        self.notifier.notify(
            ProgressStage.PLANNING,
            "正在生成大纲...",
            10,
            {"word_count": word_count}
        )
    
    def writing(self, draft_text: str = ""):
        """写作阶段"""
        word_count = len(draft_text) if draft_text else 0
        self.notifier.notify(
            ProgressStage.WRITING,
            "正在撰写章节...",
            40,
            {"word_count": word_count}
        )
    
    def debating(self, round_num: int = 1, total_rounds: int = 2):
        """评审阶段"""
        progress = 80 - (total_rounds - round_num) * 5
        self.notifier.notify(
            ProgressStage.DEBATING,
            f"正在评审 (第 {round_num}/{total_rounds} 轮)...",
            progress,
            {"round": round_num, "total": total_rounds}
        )
    
    def editing(self, edited_text: str = ""):
        """编辑阶段"""
        word_count = len(edited_text) if edited_text else 0
        self.notifier.notify(
            ProgressStage.EDITING,
            "正在编辑优化...",
            70,
            {"word_count": word_count}
        )
    
    def refining(self):
        """精修阶段"""
        self.notifier.notify(
            ProgressStage.REFINING,
            "正在进行最终优化...",
            90
        )
    
    def complete(self, final_text: str = "", word_counts: Dict = None):
        """完成"""
        data = {
            "word_count": len(final_text) if final_text else 0,
            "word_counts": word_counts or {}
        }
        self.notifier.complete(data)
    
    def error(self, error_msg: str):
        """错误"""
        self.notifier.error(error_msg)
