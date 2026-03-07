"""
Enhanced Token Compressor - 增强版 Token 压缩器
智能上下文优先级：保留关键角色/伏笔信息，丢弃次要文本
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re


class ContentPriority(Enum):
    """内容优先级"""
    CRITICAL = 10    # 关键：主角信息、核心伏笔
    HIGH = 7         # 高：重要角色、主要伏笔
    MEDIUM = 5       # 中：次要角色、一般设定
    LOW = 3          # 低：背景信息、细节描述
    DISCARDABLE = 1  # 可丢弃：冗余信息


@dataclass
class ContentSegment:
    """内容片段"""
    content: str
    priority: ContentPriority
    segment_type: str  # character/foreshadowing/world/plot/dialogue/description
    relevance_score: float  # 0-1 相关性分数
    token_count: int
    entity_mentions: List[str]  # 提及的实体


class SmartContextPrioritizer:
    """
    智能上下文优先级管理器
    
    根据内容重要性动态分配优先级
    """
    
    def __init__(self):
        self.critical_entities: set = set()  # 关键实体（主角、核心伏笔）
        self.high_priority_entities: set = set()  # 高优先级实体
        self.entity_importance: Dict[str, float] = {}  # 实体重要性分数
    
    def set_critical_entities(self, entities: List[str]):
        """设置关键实体"""
        self.critical_entities = set(entities)
    
    def update_entity_importance(self, entity: str, importance: float):
        """更新实体重要性"""
        self.entity_importance[entity] = importance
        if importance >= 0.8:
            self.critical_entities.add(entity)
        elif importance >= 0.6:
            self.high_priority_entities.add(entity)
    
    def calculate_segment_priority(
        self,
        segment: ContentSegment,
        current_context: Dict[str, Any]
    ) -> ContentPriority:
        """
        计算片段优先级
        
        基于：
        1. 是否包含关键实体
        2. 片段类型
        3. 相关性分数
        4. 在故事中的位置
        """
        score = 0
        
        # 检查关键实体
        critical_mentions = self.critical_entities & set(segment.entity_mentions)
        high_mentions = self.high_priority_entities & set(segment.entity_mentions)
        
        if critical_mentions:
            score += 4
        if high_mentions:
            score += 2
        
        # 根据类型加分
        type_scores = {
            "foreshadowing": 3,
            "character": 2,
            "plot": 2,
            "dialogue": 1,
            "world": 1,
            "description": 0
        }
        score += type_scores.get(segment.segment_type, 0)
        
        # 相关性分数
        score += segment.relevance_score * 2
        
        # 映射到优先级
        if score >= 6:
            return ContentPriority.CRITICAL
        elif score >= 4:
            return ContentPriority.HIGH
        elif score >= 2:
            return ContentPriority.MEDIUM
        elif score >= 1:
            return ContentPriority.LOW
        else:
            return ContentPriority.DISCARDABLE


class EnhancedTokenCompressor:
    """
    增强版 Token 压缩器
    
    智能保留关键信息，压缩次要内容
    """
    
    def __init__(self):
        self.prioritizer = SmartContextPrioritizer()
        self.min_priority_threshold = ContentPriority.LOW
    
    def analyze_content(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> List[ContentSegment]:
        """
        分析内容，识别不同类型的片段
        
        识别：
        - 角色描述
        - 伏笔信息
        - 对话
        - 世界观设定
        - 情节发展
        - 环境描述
        """
        segments = []
        
        # 按段落分割
        paragraphs = text.split('\n\n')
        
        for para in paragraphs:
            if not para.strip():
                continue
            
            # 识别片段类型
            segment_type = self._identify_segment_type(para)
            
            # 提取提及的实体
            entities = self._extract_entities(para)
            
            # 计算相关性
            relevance = self._calculate_relevance(para, context)
            
            # 估算 token 数（简单估算：中文字符数 / 2）
            token_count = len(para) // 2
            
            segment = ContentSegment(
                content=para,
                priority=ContentPriority.MEDIUM,  # 临时，后面会重新计算
                segment_type=segment_type,
                relevance_score=relevance,
                token_count=token_count,
                entity_mentions=entities
            )
            
            # 计算最终优先级
            segment.priority = self.prioritizer.calculate_segment_priority(
                segment, context
            )
            
            segments.append(segment)
        
        return segments
    
    def _identify_segment_type(self, text: str) -> str:
        """识别片段类型"""
        # 伏笔关键词
        foreshadowing_keywords = ['伏笔', '暗示', '预示', '征兆', '线索', '谜团', '未解']
        # 对话特征
        dialogue_patterns = ['"', '"', '"', '"', '：', '说', '问', '答']
        # 角色描述
        character_keywords = ['角色', '人物', '性格', '外貌', '能力', '背景']
        # 世界观
        world_keywords = ['世界', '设定', '规则', '魔法', '历史', '地理', '势力']
        
        text_lower = text.lower()
        
        # 检查各类特征
        if any(k in text for k in foreshadowing_keywords):
            return "foreshadowing"
        elif sum(text.count(p) for p in dialogue_patterns) >= 3:
            return "dialogue"
        elif any(k in text_lower for k in character_keywords):
            return "character"
        elif any(k in text_lower for k in world_keywords):
            return "world"
        elif re.search(r'第[一二三四五六七八九十\d]+章', text):
            return "plot"
        else:
            return "description"
    
    def _extract_entities(self, text: str) -> List[str]:
        """提取文本中提及的实体（简单实现）"""
        # 这里可以使用 NER，简单版本提取引号内和特定模式
        entities = []
        
        # 提取引号内的名称
        quoted = re.findall(r'[""]([^""]+)[""]', text)
        entities.extend(quoted)
        
        # 提取【】内的名称
        bracketed = re.findall(r'【([^】]+)】', text)
        entities.extend(bracketed)
        
        return list(set(entities))
    
    def _calculate_relevance(self, text: str, context: Dict[str, Any]) -> float:
        """计算与当前上下文的相关性"""
        relevance = 0.5  # 基础分数
        
        # 检查是否包含上下文中的关键词
        current_chapter = context.get("current_chapter", "")
        active_characters = context.get("active_characters", [])
        
        if current_chapter and current_chapter in text:
            relevance += 0.2
        
        for char in active_characters:
            if char in text:
                relevance += 0.1
        
        return min(1.0, relevance)
    
    def compress_with_priority(
        self,
        text: str,
        max_tokens: int,
        context: Dict[str, Any],
        preserve_foreshadowing: bool = True
    ) -> str:
        """
        基于优先级压缩文本
        
        Args:
            text: 原始文本
            max_tokens: 最大 token 数
            context: 上下文信息
            preserve_foreshadowing: 是否优先保留伏笔
            
        Returns:
            压缩后的文本
        """
        # 分析内容
        segments = self.analyze_content(text, context)
        
        # 按优先级排序
        priority_order = [
            ContentPriority.CRITICAL,
            ContentPriority.HIGH,
            ContentPriority.MEDIUM,
            ContentPriority.LOW,
            ContentPriority.DISCARDABLE
        ]
        
        if preserve_foreshadowing:
            # 伏笔片段提升优先级
            for seg in segments:
                if seg.segment_type == "foreshadowing":
                    # 提升一级优先级
                    current_idx = priority_order.index(seg.priority)
                    if current_idx > 0:
                        seg.priority = priority_order[current_idx - 1]
        
        # 按优先级排序
        sorted_segments = sorted(
            segments,
            key=lambda s: (priority_order.index(s.priority), -s.relevance_score)
        )
        
        # 选择片段直到达到 token 限制
        selected = []
        total_tokens = 0
        
        for seg in sorted_segments:
            if total_tokens + seg.token_count <= max_tokens:
                selected.append(seg)
                total_tokens += seg.token_count
            elif seg.priority == ContentPriority.CRITICAL:
                # 关键内容必须保留，压缩其内容
                compressed = self._compress_segment(seg, max_tokens - total_tokens)
                if compressed:
                    selected.append(compressed)
                    total_tokens += compressed.token_count
        
        # 按原始顺序重组文本
        selected_ids = {id(s) for s in selected}
        final_segments = [s for s in segments if id(s) in selected_ids]
        
        # 生成压缩报告
        compression_report = {
            "original_tokens": sum(s.token_count for s in segments),
            "compressed_tokens": total_tokens,
            "compression_ratio": total_tokens / sum(s.token_count for s in segments) if segments else 0,
            "critical_preserved": sum(1 for s in selected if s.priority == ContentPriority.CRITICAL),
            "foreshadowing_preserved": sum(1 for s in selected if s.segment_type == "foreshadowing")       }
        
        result = "\n\n".join(s.content for s in final_segments)
        
        # 添加压缩标记（调试用）
        if context.get("debug"):
            result += f"\n\n[压缩报告: {compression_report}]"
        
        return result
    
    def _compress_segment(
        self,
        segment: ContentSegment,
        max_tokens: int
    ) -> Optional[ContentSegment]:
        """压缩单个片段"""
        # 简单压缩：截断并添加省略号
        max_chars = max_tokens * 2
        
        if len(segment.content) <= max_chars:
            return segment
        
        compressed_content = segment.content[:max_chars] + "..."
        
        return ContentSegment(
            content=compressed_content,
            priority=segment.priority,
            segment_type=segment.segment_type,
            relevance_score=segment.relevance_score,
            token_count=max_tokens,
            entity_mentions=segment.entity_mentions
        )
    
    def create_priority_summary(
        self,
        segments: List[ContentSegment]
    ) -> Dict[str, Any]:
        """创建优先级摘要"""
        summary = {
            "total_segments": len(segments),
            "by_priority": {},
            "by_type": {},
            "critical_entities_covered": set(),
            "foreshadowing_count": 0
        }
        
        for seg in segments:
            # 按优先级统计
            priority_name = seg.priority.name
            summary["by_priority"][priority_name] = summary["by_priority"].get(priority_name, 0) + 1
            
            # 按类型统计
            summary["by_type"][seg.segment_type] = summary["by_type"].get(seg.segment_type, 0) + 1
            
            # 统计关键实体覆盖
            if seg.priority in [ContentPriority.CRITICAL, ContentPriority.HIGH]:
                summary["critical_entities_covered"].update(seg.entity_mentions)
            
            # 统计伏笔
            if seg.segment_type == "foreshadowing":
                summary["foreshadowing_count"] += 1
        
        summary["critical_entities_covered"] = list(summary["critical_entities_covered"])
        
        return summary


# 全局实例
_enhanced_compressor: Optional[EnhancedTokenCompressor] = None


def get_enhanced_token_compressor() -> EnhancedTokenCompressor:
    """获取增强版 Token 压缩器实例"""
    global _enhanced_compressor
    if _enhanced_compressor is None:
        _enhanced_compressor = EnhancedTokenCompressor()
    return _enhanced_compressor
