"""
Text Traceability System - 文本溯源系统
提供文本来源追踪、生成历史记录和溯源气泡功能
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import json


class TextSourceType(Enum):
    """文本来源类型"""
    AI_GENERATION = "ai_generation"      # AI 生成
    HUMAN_WRITE = "human_write"          # 人工撰写
    AI_EDIT = "ai_edit"                  # AI 编辑
    DISCUSSION = "discussion"            # 讨论生成
    REWRITE = "rewrite"                  # 重写
    MERGE = "merge"                      # 合并
    IMPORT = "import"                    # 导入


class AgentType(Enum):
    """Agent 类型"""
    PLANNER = "planner"
    CONFLICT = "conflict"
    WRITING = "writing"
    EDITOR = "editor"
    READER = "reader"
    CRITIC = "critic"
    CONSISTENCY = "consistency"
    SUMMARY = "summary"
    FACILITATOR = "facilitator"


@dataclass
class TextSegment:
    """文本片段"""
    id: str
    content: str
    start_pos: int
    end_pos: int
    source: 'TextSource'
    parent_ids: List[str] = field(default_factory=list)
    version: int = 1


@dataclass
class TextSource:
    """文本来源信息"""
    id: str
    type: TextSourceType
    agent_type: Optional[AgentType] = None
    agent_name: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    session_id: str = ""
    discussion_id: Optional[str] = None
    round_number: Optional[int] = None
    prompt: str = ""                   # 使用的提示词
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "agent_type": self.agent_type.value if self.agent_type else None,
            "agent_name": self.agent_name,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "discussion_id": self.discussion_id,
            "round_number": self.round_number,
            "prompt": self.prompt[:200] + "..." if len(self.prompt) > 200 else self.prompt,
            "context": self.context,
            "metadata": self.metadata
        }


@dataclass
class EditOperation:
    """编辑操作记录"""
    id: str
    segment_id: str
    operation_type: str              # insert/delete/replace
    old_content: Optional[str]
    new_content: Optional[str]
    position: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    editor: str = ""                 # 编辑者（人或 AI）
    reason: str = ""                 # 编辑原因


class TextTraceabilityManager:
    """
    文本溯源管理器
    
    管理文本的完整生成历史
    """
    
    def __init__(self):
        self.sources: Dict[str, TextSource] = {}
        self.segments: Dict[str, TextSegment] = {}
        self.edit_history: List[EditOperation] = []
        self.content_index: Dict[str, List[str]] = {}  # 内容哈希 -> 片段ID列表
    
    def create_source(
        self,
        source_type: TextSourceType,
        agent_type: Optional[AgentType] = None,
        agent_name: str = "",
        session_id: str = "",
        discussion_id: Optional[str] = None,
        round_number: Optional[int] = None,
        prompt: str = "",
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TextSource:
        """创建文本来源"""
        source_id = f"source_{datetime.now().timestamp()}"
        
        source = TextSource(
            id=source_id,
            type=source_type,
            agent_type=agent_type,
            agent_name=agent_name,
            session_id=session_id,
            discussion_id=discussion_id,
            round_number=round_number,
            prompt=prompt,
            context=context or {},
            metadata=metadata or {}
        )
        
        self.sources[source_id] = source
        return source
    
    def add_segment(
        self,
        content: str,
        source: TextSource,
        start_pos: int = 0,
        parent_ids: Optional[List[str]] = None
    ) -> TextSegment:
        """添加文本片段"""
        segment_id = f"seg_{datetime.now().timestamp()}"
        
        segment = TextSegment(
            id=segment_id,
            content=content,
            start_pos=start_pos,
            end_pos=start_pos + len(content),
            source=source,
            parent_ids=parent_ids or []
        )
        
        self.segments[segment_id] = segment
        
        # 更新内容索引
        content_hash = self._hash_content(content)
        if content_hash not in self.content_index:
            self.content_index[content_hash] = []
        self.content_index[content_hash].append(segment_id)
        
        return segment
    
    def record_edit(
        self,
        segment_id: str,
        operation_type: str,
        old_content: Optional[str],
        new_content: Optional[str],
        position: int,
        editor: str = "",
        reason: str = ""
    ) -> EditOperation:
        """记录编辑操作"""
        edit_id = f"edit_{datetime.now().timestamp()}"
        
        operation = EditOperation(
            id=edit_id,
            segment_id=segment_id,
            operation_type=operation_type,
            old_content=old_content,
            new_content=new_content,
            position=position,
            editor=editor,
            reason=reason
        )
        
        self.edit_history.append(operation)
        return operation
    
    def get_segment_source(self, segment_id: str) -> Optional[TextSource]:
        """获取片段的来源"""
        segment = self.segments.get(segment_id)
        if segment:
            return self.sources.get(segment.source.id)
        return None
    
    def get_segment_history(self, segment_id: str) -> List[Dict[str, Any]]:
        """获取片段的完整历史"""
        history = []
        visited = set()
        
        def trace_back(seg_id: str):
            if seg_id in visited:
                return
            visited.add(seg_id)
            
            segment = self.segments.get(seg_id)
            if not segment:
                return
            
            source = self.sources.get(segment.source.id)
            if source:
                history.append({
                    "segment_id": seg_id,
                    "content_preview": segment.content[:100] + "..." if len(segment.content) > 100 else segment.content,
                    "source": source.to_dict()
                })
            
            # 追溯父片段
            for parent_id in segment.parent_ids:
                trace_back(parent_id)
        
        trace_back(segment_id)
        return history
    
    def find_similar_content(self, content: str, threshold: float = 0.8) -> List[TextSegment]:
        """查找相似内容"""
        content_hash = self._hash_content(content)
        
        # 直接匹配
        if content_hash in self.content_index:
            segment_ids = self.content_index[content_hash]
            return [self.segments[sid] for sid in segment_ids if sid in self.segments]
        
        return []
    
    def _hash_content(self, content: str) -> str:
        """计算内容哈希"""
        # 简化处理，取前50个字符的哈希
        normalized = content[:50].strip().lower()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_sources": len(self.sources),
            "total_segments": len(self.segments),
            "total_edits": len(self.edit_history),
            "source_type_distribution": self._count_source_types(),
            "agent_distribution": self._count_agents()
        }
    
    def _count_source_types(self) -> Dict[str, int]:
        """统计来源类型分布"""
        counts = {}
        for source in self.sources.values():
            type_name = source.type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts
    
    def _count_agents(self) -> Dict[str, int]:
        """统计 Agent 分布"""
        counts = {}
        for source in self.sources.values():
            if source.agent_type:
                agent_name = source.agent_type.value
                counts[agent_name] = counts.get(agent_name, 0) + 1
        return counts


class TraceabilityBubble:
    """
    溯源气泡
    
    为选中的文本显示来源信息
    """
    
    def __init__(self, manager: TextTraceabilityManager):
        self.manager = manager
    
    def get_bubble_info(
        self,
        selected_text: str,
        document_id: str = ""
    ) -> Dict[str, Any]:
        """
        获取溯源气泡信息
        
        Args:
            selected_text: 选中的文本
            document_id: 文档ID
            
        Returns:
            气泡信息
        """
        # 查找相似内容
        similar_segments = self.manager.find_similar_content(selected_text)
        
        if not similar_segments:
            return {
                "found": False,
                "message": "未找到该文本的生成记录"
            }
        
        # 获取最匹配的片段
        best_match = similar_segments[0]
        source = self.manager.get_segment_source(best_match.id)
        
        if not source:
            return {
                "found": False,
                "message": "来源信息丢失"
            }
        
        # 构建气泡信息
        bubble_info = {
            "found": True,
            "segment_id": best_match.id,
            "source": {
                "type": source.type.value,
                "type_label": self._get_source_type_label(source.type),
                "agent_name": source.agent_name or (source.agent_type.value if source.agent_type else "未知"),
                "timestamp": source.timestamp,
                "time_ago": self._format_time_ago(source.timestamp)
            },
            "generation_context": {
                "prompt_preview": source.prompt[:150] + "..." if len(source.prompt) > 150 else source.prompt,
                "discussion_id": source.discussion_id,
                "round_number": source.round_number,
                "session_id": source.session_id
            },
            "metadata": source.metadata,
            "history": self.manager.get_segment_history(best_match.id)[:3]  # 最近3条历史
        }
        
        # 添加 Agent 图标和颜色
        if source.agent_type:
            bubble_info["source"]["icon"] = self._get_agent_icon(source.agent_type)
            bubble_info["source"]["color"] = self._get_agent_color(source.agent_type)
        
        return bubble_info
    
    def _get_source_type_label(self, source_type: TextSourceType) -> str:
        """获取来源类型标签"""
        labels = {
            TextSourceType.AI_GENERATION: "AI 生成",
            TextSourceType.HUMAN_WRITE: "人工撰写",
            TextSourceType.AI_EDIT: "AI 编辑",
            TextSourceType.DISCUSSION: "讨论生成",
            TextSourceType.REWRITE: "重写",
            TextSourceType.MERGE: "合并",
            TextSourceType.IMPORT: "导入"
        }
        return labels.get(source_type, "未知")
    
    def _format_time_ago(self, timestamp: str) -> str:
        """格式化时间差"""
        try:
            past = datetime.fromisoformat(timestamp)
            now = datetime.now()
            diff = now - past
            
            seconds = diff.total_seconds()
            
            if seconds < 60:
                return "刚刚"
            elif seconds < 3600:
                return f"{int(seconds / 60)} 分钟前"
            elif seconds < 86400:
                return f"{int(seconds / 3600)} 小时前"
            else:
                return f"{int(seconds / 86400)} 天前"
        except:
            return "未知时间"
    
    def _get_agent_icon(self, agent_type: AgentType) -> str:
        """获取 Agent 图标"""
        icons = {
            AgentType.PLANNER: "📝",
            AgentType.CONFLICT: "⚔️",
            AgentType.WRITING: "✍️",
            AgentType.EDITOR: "✏️",
            AgentType.READER: "👁️",
            AgentType.CRITIC: "🔍",
            AgentType.CONSISTENCY: "⚠️",
            AgentType.SUMMARY: "📋",
            AgentType.FACILITATOR: "🎤"
        }
        return icons.get(agent_type, "🤖")
    
    def _get_agent_color(self, agent_type: AgentType) -> str:
        """获取 Agent 颜色"""
        colors = {
            AgentType.PLANNER: "#3b82f6",      # 蓝色
            AgentType.CONFLICT: "#ef4444",     # 红色
            AgentType.WRITING: "#10b981",      # 绿色
            AgentType.EDITOR: "#f59e0b",       # 橙色
            AgentType.READER: "#8b5cf6",       # 紫色
            AgentType.CRITIC: "#ec4899",       # 粉色
            AgentType.CONSISTENCY: "#f97316",  # 橙红
            AgentType.SUMMARY: "#06b6d4",      # 青色
            AgentType.FACILITATOR: "#84cc16"   # 黄绿
        }
        return colors.get(agent_type, "#6b7280")


class TextGenerationTracker:
    """
    文本生成追踪器
    
    追踪 AI 写作过程中的文本生成
    """
    
    def __init__(self):
        self.manager = TextTraceabilityManager()
        self.current_session: Optional[str] = None
        self.current_source: Optional[TextSource] = None
    
    def start_session(
        self,
        session_id: str,
        agent_type: AgentType,
        agent_name: str,
        prompt: str = "",
        context: Optional[Dict[str, Any]] = None
    ):
        """开始追踪会话"""
        self.current_session = session_id
        self.current_source = self.manager.create_source(
            source_type=TextSourceType.AI_GENERATION,
            agent_type=agent_type,
            agent_name=agent_name,
            session_id=session_id,
            prompt=prompt,
            context=context or {}
        )
    
    def track_generation(
        self,
        content: str,
        position: int = 0,
        parent_ids: Optional[List[str]] = None
    ) -> TextSegment:
        """追踪生成的文本"""
        if not self.current_source:
            raise ValueError("No active session. Call start_session first.")
        
        return self.manager.add_segment(
            content=content,
            source=self.current_source,
            start_pos=position,
            parent_ids=parent_ids
        )
    
    def track_edit(
        self,
        segment_id: str,
        operation: str,
        old_content: str,
        new_content: str,
        editor: str = "",
        reason: str = ""
    ):
        """追踪编辑操作"""
        self.manager.record_edit(
            segment_id=segment_id,
            operation_type=operation,
            old_content=old_content,
            new_content=new_content,
            position=0,
            editor=editor,
            reason=reason
        )
    
    def end_session(self):
        """结束追踪会话"""
        self.current_session = None
        self.current_source = None
    
    def get_traceability_info(self, text: str) -> Dict[str, Any]:
        """获取文本的溯源信息"""
        bubble = TraceabilityBubble(self.manager)
        return bubble.get_bubble_info(text)


# 便捷函数
_traceability_manager: Optional[TextTraceabilityManager] = None
_tracker: Optional[TextGenerationTracker] = None


def get_traceability_manager() -> TextTraceabilityManager:
    """获取溯源管理器实例"""
    global _traceability_manager
    if _traceability_manager is None:
        _traceability_manager = TextTraceabilityManager()
    return _traceability_manager


def get_tracker() -> TextGenerationTracker:
    """获取追踪器实例"""
    global _tracker
    if _tracker is None:
        _tracker = TextGenerationTracker()
    return _tracker


def get_text_source_info(selected_text: str) -> Dict[str, Any]:
    """获取文本来源信息（供前端调用）"""
    manager = get_traceability_manager()
    bubble = TraceabilityBubble(manager)
    return bubble.get_bubble_info(selected_text)


def start_generation_tracking(
    session_id: str,
    agent_type: str,
    agent_name: str,
    prompt: str = ""
):
    """开始生成追踪"""
    tracker = get_tracker()
    agent_enum = AgentType(agent_type) if agent_type else None
    tracker.start_session(session_id, agent_enum, agent_name, prompt)


def track_generated_text(content: str, position: int = 0) -> str:
    """追踪生成的文本"""
    tracker = get_tracker()
    segment = tracker.track_generation(content, position)
    return segment.id


def end_generation_tracking():
    """结束生成追踪"""
    tracker = get_tracker()
    tracker.end_session()
