"""
Originality Tracker - 创作原真性追踪系统
AI贡献度分析 + 原创性验证
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import json
import re


class ContentSourceType(Enum):
    """内容来源类型"""
    USER_INPUT = "user_input"       # 用户直接输入
    AI_GENERATED = "ai_generated"   # AI生成
    AI_EDITED = "ai_edited"         # AI修改用户内容
    USER_EDITED_AI = "user_edited_ai"  # 用户修改AI内容
    IMPORTED = "imported"           # 导入内容


class OriginalityLevel(Enum):
    """原创性等级"""
    HIGHLY_ORIGINAL = "highly_original"    # 高度原创 (>80%)
    MOSTLY_ORIGINAL = "mostly_original"    # 较原创 (60-80%)
    MIXED = "mixed"                        # 混合 (40-60%)
    AI_ASSISTED = "ai_assisted"           # AI辅助 (20-40%)
    AI_DOMINATED = "ai_dominated"         # AI主导 (<20%)


@dataclass
class ContentSegment:
    """内容片段"""
    segment_id: str
    content: str
    source_type: ContentSourceType
    author_id: Optional[str] = None  # 用户ID或Agent类型
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    word_count: int = 0
    parent_segment_id: Optional[str] = None  # 如果是修改，指向原片段
    edit_distance: int = 0  # 编辑距离（如果是修改）


@dataclass
class OriginalityReport:
    """原创性报告"""
    novel_id: str
    chapter_id: Optional[str]
    total_word_count: int
    user_word_count: int
    ai_word_count: int
    user_percentage: float
    ai_percentage: float
    originality_level: OriginalityLevel
    edit_history: List[Dict[str, Any]]
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "novel_id": self.novel_id,
            "chapter_id": self.chapter_id,
            "total_word_count": self.total_word_count,
            "user_word_count": self.user_word_count,
            "ai_word_count": self.ai_word_count,
            "user_percentage": round(self.user_percentage, 2),
            "ai_percentage": round(self.ai_percentage, 2),
            "originality_level": self.originality_level.value,
            "originality_label": self._get_originality_label(),
            "edit_history_count": len(self.edit_history),
            "generated_at": self.generated_at
        }
    
    def _get_originality_label(self) -> str:
        """获取原创性标签"""
        labels = {
            OriginalityLevel.HIGHLY_ORIGINAL: "高度原创",
            OriginalityLevel.MOSTLY_ORIGINAL: "较原创",
            OriginalityLevel.MIXED: "人机协作",
            OriginalityLevel.AI_ASSISTED: "AI辅助",
            OriginalityLevel.AI_DOMINATED: "AI主导"
        }
        return labels.get(self.originality_level, "未知")


class AIContributionAnalyzer:
    """
    AI 贡献度分析器
    
    分析整部小说中用户输入与 AI 生成的比例
    """
    
    def __init__(self):
        self.segments: Dict[str, ContentSegment] = {}
        self.novel_segments: Dict[str, List[str]] = defaultdict(list)  # novel_id -> segment_ids
        self.chapter_segments: Dict[str, List[str]] = defaultdict(list)  # chapter_id -> segment_ids
    
    def add_segment(
        self,
        novel_id: str,
        content: str,
        source_type: ContentSourceType,
        chapter_id: Optional[str] = None,
        author_id: Optional[str] = None,
        parent_segment_id: Optional[str] = None
    ) -> str:
        """
        添加内容片段
        
        Args:
            novel_id: 小说ID
            content: 内容
            source_type: 来源类型
            chapter_id: 章节ID（可选）
            author_id: 作者ID（可选）
            parent_segment_id: 父片段ID（如果是修改）
            
        Returns:
            片段ID
        """
        segment_id = f"seg_{datetime.now().timestamp()}_{hash(content) % 10000}"
        
        # 计算编辑距离（如果是修改）
        edit_distance = 0
        if parent_segment_id and parent_segment_id in self.segments:
            parent_content = self.segments[parent_segment_id].content
            edit_distance = self._calculate_edit_distance(parent_content, content)
        
        segment = ContentSegment(
            segment_id=segment_id,
            content=content,
            source_type=source_type,
            author_id=author_id,
            word_count=len(content),
            parent_segment_id=parent_segment_id,
            edit_distance=edit_distance
        )
        
        self.segments[segment_id] = segment
        self.novel_segments[novel_id].append(segment_id)
        
        if chapter_id:
            self.chapter_segments[chapter_id].append(segment_id)
        
        return segment_id
    
    def _calculate_edit_distance(self, s1: str, s2: str) -> int:
        """计算编辑距离（Levenshtein距离）"""
        if len(s1) < len(s2):
            return self._calculate_edit_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def analyze_originality(
        self,
        novel_id: str,
        chapter_id: Optional[str] = None
    ) -> OriginalityReport:
        """
        分析原创性
        
        Args:
            novel_id: 小说ID
            chapter_id: 章节ID（可选，不指定则分析整部小说）
            
        Returns:
            原创性报告
        """
        # 获取相关片段
        if chapter_id:
            segment_ids = self.chapter_segments.get(chapter_id, [])
        else:
            segment_ids = self.novel_segments.get(novel_id, [])
        
        segments = [self.segments[sid] for sid in segment_ids if sid in self.segments]
        
        # 统计字数
        total_words = sum(s.word_count for s in segments)
        user_words = sum(s.word_count for s in segments if s.source_type == ContentSourceType.USER_INPUT)
        ai_words = sum(s.word_count for s in segments if s.source_type == ContentSourceType.AI_GENERATED)
        
        # 计算混合内容的贡献
        for s in segments:
            if s.source_type == ContentSourceType.AI_EDITED:
                # AI修改用户内容，算50% AI贡献
                ai_words += s.word_count * 0.5
                user_words += s.word_count * 0.5
            elif s.source_type == ContentSourceType.USER_EDITED_AI:
                # 用户修改AI内容，根据编辑距离计算
                if s.parent_segment_id and s.parent_segment_id in self.segments:
                    parent = self.segments[s.parent_segment_id]
                    edit_ratio = s.edit_distance / max(len(parent.content), 1)
                    user_contribution = min(edit_ratio * 2, 1.0)  # 编辑越多，用户贡献越大
                    user_words += s.word_count * user_contribution
                    ai_words += s.word_count * (1 - user_contribution)
        
        # 计算百分比
        user_percentage = (user_words / total_words * 100) if total_words > 0 else 0
        ai_percentage = (ai_words / total_words * 100) if total_words > 0 else 0
        
        # 确定原创性等级
        originality_level = self._determine_originality_level(user_percentage)
        
        # 生成编辑历史
        edit_history = self._generate_edit_history(segments)
        
        return OriginalityReport(
            novel_id=novel_id,
            chapter_id=chapter_id,
            total_word_count=total_words,
            user_word_count=int(user_words),
            ai_word_count=int(ai_words),
            user_percentage=user_percentage,
            ai_percentage=ai_percentage,
            originality_level=originality_level,
            edit_history=edit_history
        )
    
    def _determine_originality_level(self, user_percentage: float) -> OriginalityLevel:
        """确定原创性等级"""
        if user_percentage >= 80:
            return OriginalityLevel.HIGHLY_ORIGINAL
        elif user_percentage >= 60:
            return OriginalityLevel.MOSTLY_ORIGINAL
        elif user_percentage >= 40:
            return OriginalityLevel.MIXED
        elif user_percentage >= 20:
            return OriginalityLevel.AI_ASSISTED
        else:
            return OriginalityLevel.AI_DOMINATED
    
    def _generate_edit_history(self, segments: List[ContentSegment]) -> List[Dict[str, Any]]:
        """生成编辑历史"""
        history = []
        
        for segment in segments:
            if segment.parent_segment_id:
                parent = self.segments.get(segment.parent_segment_id)
                if parent:
                    history.append({
                        "timestamp": segment.timestamp,
                        "from_source": parent.source_type.value,
                        "to_source": segment.source_type.value,
                        "edit_distance": segment.edit_distance,
                        "change_ratio": segment.edit_distance / max(len(parent.content), 1)
                    })
        
        return sorted(history, key=lambda x: x["timestamp"])
    
    def get_novel_statistics(self, novel_id: str) -> Dict[str, Any]:
        """获取小说统计信息"""
        segment_ids = self.novel_segments.get(novel_id, [])
        segments = [self.segments[sid] for sid in segment_ids if sid in self.segments]
        
        # 按章节统计
        chapter_stats = {}
        for chapter_id, chapter_segment_ids in self.chapter_segments.items():
            if any(sid in segment_ids for sid in chapter_segment_ids):
                report = self.analyze_originality(novel_id, chapter_id)
                chapter_stats[chapter_id] = report.to_dict()
        
        # 整体统计
        overall_report = self.analyze_originality(novel_id)
        
        # 创作趋势
        trend = self._analyze_creation_trend(segments)
        
        return {
            "novel_id": novel_id,
            "overall": overall_report.to_dict(),
            "chapter_breakdown": chapter_stats,
            "creation_trend": trend,
            "total_segments": len(segments),
            "ai_interventions": sum(
                1 for s in segments
                if s.source_type in [ContentSourceType.AI_GENERATED, ContentSourceType.AI_EDITED]
            )
        }
    
    def _analyze_creation_trend(self, segments: List[ContentSegment]) -> Dict[str, Any]:
        """分析创作趋势"""
        if not segments:
            return {}
        
        # 按时间排序
        sorted_segments = sorted(segments, key=lambda s: s.timestamp)
        
        # 计算滑动窗口的原创性
        window_size = max(len(sorted_segments) // 5, 1)
        trends = []
        
        for i in range(0, len(sorted_segments), window_size):
            window = sorted_segments[i:i+window_size]
            user_words = sum(s.word_count for s in window if s.source_type == ContentSourceType.USER_INPUT)
            total_words = sum(s.word_count for s in window)
            
            if total_words > 0:
                originality = user_words / total_words * 100
                trends.append(round(originality, 2))
        
        return {
            "originality_trend": trends,
            "trend_direction": "increasing" if trends and trends[-1] > trends[0] else "decreasing",
            "average_originality": round(sum(trends) / len(trends), 2) if trends else 0
        }


class OriginalityCertificate:
    """
    原创性证书
    
    生成可验证的原创性证明
    """
    
    def __init__(self):
        self.certificates: Dict[str, Dict[str, Any]] = {}
    
    def generate_certificate(
        self,
        novel_id: str,
        analyzer: AIContributionAnalyzer
    ) -> Dict[str, Any]:
        """生成原创性证书"""
        stats = analyzer.get_novel_statistics(novel_id)
        overall = stats["overall"]
        
        # 生成证书内容
        certificate = {
            "certificate_id": f"cert_{novel_id}_{datetime.now().timestamp()}",
            "novel_id": novel_id,
            "issued_at": datetime.now().isoformat(),
            "originality_score": overall["user_percentage"],
            "originality_level": overall["originality_level"],
            "originality_label": overall["originality_label"],
            "total_words": overall["total_word_count"],
            "user_contribution": overall["user_word_count"],
            "ai_contribution": overall["ai_word_count"],
            "verification_hash": self._generate_verification_hash(stats),
            "claims": self._generate_claims(overall)
        }
        
        self.certificates[novel_id] = certificate
        
        return certificate
    
    def _generate_verification_hash(self, stats: Dict[str, Any]) -> str:
        """生成验证哈希"""
        content = json.dumps(stats, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _generate_claims(self, overall: Dict[str, Any]) -> List[str]:
        """生成声明列表"""
        claims = []
        
        user_pct = overall["user_percentage"]
        
        if user_pct >= 80:
            claims.append("本作品主要由作者独立创作完成")
            claims.append("AI仅作为辅助工具使用")
        elif user_pct >= 50:
            claims.append("本作品为作者与AI协作创作")
            claims.append("作者对内容有实质性贡献和把控")
        else:
            claims.append("本作品包含大量AI生成内容")
            claims.append("作者对AI输出进行了编辑和筛选")
        
        claims.append(f"用户原创内容占比：{user_pct:.1f}%")
        claims.append(f"AI辅助内容占比：{overall['ai_percentage']:.1f}%")
        
        return claims
    
    def verify_certificate(self, novel_id: str, provided_hash: str) -> bool:
        """验证证书"""
        certificate = self.certificates.get(novel_id)
        if not certificate:
            return False
        
        return certificate["verification_hash"] == provided_hash


# 全局实例
_originality_analyzer: Optional[AIContributionAnalyzer] = None
_certificate_generator: Optional[OriginalityCertificate] = None


def get_originality_analyzer() -> AIContributionAnalyzer:
    """获取原创性分析器实例"""
    global _originality_analyzer
    if _originality_analyzer is None:
        _originality_analyzer = AIContributionAnalyzer()
    return _originality_analyzer


def get_certificate_generator() -> OriginalityCertificate:
    """获取证书生成器实例"""
    global _certificate_generator
    if _certificate_generator is None:
        _certificate_generator = OriginalityCertificate()
    return _certificate_generator
