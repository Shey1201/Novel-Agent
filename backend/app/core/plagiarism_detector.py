"""
Plagiarism Detector - 洗稿/敏感词实时监测系统
全网热书相似度比对 + 敏感内容检测
"""

from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import re
import json

from langchain_openai import OpenAIEmbeddings
import numpy as np


class SimilarityLevel(Enum):
    """相似度等级"""
    NONE = "none"              # 无相似 (< 10%)
    LOW = "low"                # 低相似 (10-30%)
    MEDIUM = "medium"          # 中等相似 (30-60%)
    HIGH = "high"              # 高相似 (60-80%)
    CRITICAL = "critical"      # 严重相似 (> 80%)


class SensitivityType(Enum):
    """敏感类型"""
    POLITICAL = "political"    # 政治敏感
    VIOLENCE = "violence"      # 暴力
    ADULT = "adult"           # 成人内容
    DISCRIMINATION = "discrimination"  # 歧视
    ILLEGAL = "illegal"       # 违法
    COPYRIGHT = "copyright"   # 版权


@dataclass
class SimilarityMatch:
    """相似度匹配结果"""
    source_text: str
    matched_text: str
    similarity_score: float  # 0-1
    source_reference: str    # 来源作品
    source_author: Optional[str] = None
    match_type: str = "exact"  # exact/paraphrase/structure


@dataclass
class SensitivityFinding:
    """敏感内容发现"""
    text: str
    sensitivity_type: SensitivityType
    severity: float  # 0-1
    suggestion: str
    position: Tuple[int, int]  # (start, end)


@dataclass
class PlagiarismReport:
    """洗稿检测报告"""
    text_id: str
    overall_similarity: float
    similarity_level: SimilarityLevel
    matches: List[SimilarityMatch]
    sensitivity_findings: List[SensitivityFinding]
    is_original: bool
    risk_score: float  # 0-1 综合风险分数
    suggestions: List[str]
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text_id": self.text_id,
            "overall_similarity": round(self.overall_similarity, 3),
            "similarity_level": self.similarity_level.value,
            "similarity_label": self._get_similarity_label(),
            "match_count": len(self.matches),
            "sensitivity_count": len(self.sensitivity_findings),
            "is_original": self.is_original,
            "risk_score": round(self.risk_score, 3),
            "risk_level": self._get_risk_level(),
            "suggestions": self.suggestions
        }
    
    def _get_similarity_label(self) -> str:
        """获取相似度标签"""
        labels = {
            SimilarityLevel.NONE: "高度原创",
            SimilarityLevel.LOW: "轻微相似",
            SimilarityLevel.MEDIUM: "中等相似",
            SimilarityLevel.HIGH: "高度相似",
            SimilarityLevel.CRITICAL: "严重相似"
        }
        return labels.get(self.similarity_level, "未知")
    
    def _get_risk_level(self) -> str:
        """获取风险等级"""
        if self.risk_score < 0.2:
            return "安全"
        elif self.risk_score < 0.4:
            return "低风险"
        elif self.risk_score < 0.6:
            return "中风险"
        elif self.risk_score < 0.8:
            return "高风险"
        else:
            return "极高风险"


class ReferenceDatabase:
    """
    参考数据库
    
    存储热门作品的特征向量，用于相似度比对
    """
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.reference_works: Dict[str, Dict[str, Any]] = {}  # work_id -> metadata
        self.reference_chunks: Dict[str, List[Dict[str, Any]]] = {}  # work_id -> chunks
        self.sensitive_patterns: Dict[SensitivityType, List[str]] = self._load_sensitive_patterns()
    
    def _load_sensitive_patterns(self) -> Dict[SensitivityType, List[str]]:
        """加载敏感词模式"""
        # 这里应该从配置文件或数据库加载
        # 简化版本使用硬编码示例
        return {
            SensitivityType.POLITICAL: [
                r"反动", r"颠覆", r"暴乱", r"分裂", r"独立"
            ],
            SensitivityType.VIOLENCE: [
                r"血腥", r"虐杀", r"肢解", r"酷刑", r"折磨"
            ],
            SensitivityType.ADULT: [
                r"色情", r"淫秽", r"性爱", r"裸体"
            ],
            SensitivityType.DISCRIMINATION: [
                r"种族歧视", r"性别歧视", r"地域歧视"
            ],
            SensitivityType.ILLEGAL: [
                r"毒品", r"赌博", r"走私", r"贩毒"
            ]
        }
    
    async def add_reference_work(
        self,
        work_id: str,
        title: str,
        author: str,
        content_chunks: List[str]
    ):
        """添加参考作品"""
        self.reference_works[work_id] = {
            "title": title,
            "author": author,
            "added_at": datetime.now().isoformat(),
            "chunk_count": len(content_chunks)
        }
        
        # 生成 embedding
        self.reference_chunks[work_id] = []
        for i, chunk in enumerate(content_chunks):
            embedding = await self.embeddings.aembed_query(chunk)
            
            self.reference_chunks[work_id].append({
                "chunk_id": f"{work_id}_chunk_{i}",
                "content": chunk,
                "embedding": embedding,
                "hash": hashlib.md5(chunk.encode()).hexdigest()[:16]
            })
    
    async def find_similar_chunks(
        self,
        query_text: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[SimilarityMatch]:
        """
        查找相似的文本块
        
        Args:
            query_text: 查询文本
            top_k: 返回最相似的k个
            similarity_threshold: 相似度阈值
            
        Returns:
            相似匹配列表
        """
        # 生成查询 embedding
        query_embedding = await self.embeddings.aembed_query(query_text)
        
        matches = []
        
        # 遍历所有参考作品
        for work_id, chunks in self.reference_chunks.items():
            work_info = self.reference_works.get(work_id, {})
            
            for chunk in chunks:
                # 计算相似度
                similarity = self._cosine_similarity(
                    query_embedding,
                    chunk["embedding"]
                )
                
                if similarity >= similarity_threshold:
                    match = SimilarityMatch(
                        source_text=query_text,
                        matched_text=chunk["content"],
                        similarity_score=similarity,
                        source_reference=work_info.get("title", "Unknown"),
                        source_author=work_info.get("author"),
                        match_type="semantic"
                    )
                    matches.append(match)
        
        # 排序并返回 top_k
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        return matches[:top_k]
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """计算余弦相似度"""
        a_array = np.array(a)
        b_array = np.array(b)
        
        dot_product = np.dot(a_array, b_array)
        norm_a = np.linalg.norm(a_array)
        norm_b = np.linalg.norm(b_array)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
    
    def check_sensitive_content(self, text: str) -> List[SensitivityFinding]:
        """检查敏感内容"""
        findings = []
        
        for sensitivity_type, patterns in self.sensitive_patterns.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    finding = SensitivityFinding(
                        text=match.group(),
                        sensitivity_type=sensitivity_type,
                        severity=0.8,  # 简化为固定值
                        suggestion=f"建议修改或删除涉及{sensitivity_type.value}的内容",
                        position=(match.start(), match.end())
                    )
                    findings.append(finding)
        
        return findings


class PlagiarismDetector:
    """
    洗稿检测器
    
    实时检测文本相似度和敏感内容
    """
    
    def __init__(self):
        self.reference_db = ReferenceDatabase()
        self.detection_history: List[PlagiarismReport] = []
        self.similarity_thresholds = {
            SimilarityLevel.NONE: 0.1,
            SimilarityLevel.LOW: 0.3,
            SimilarityLevel.MEDIUM: 0.6,
            SimilarityLevel.HIGH: 0.8,
            SimilarityLevel.CRITICAL: 1.0
        }
    
    async def detect(
        self,
        text: str,
        text_id: str,
        check_sensitive: bool = True,
        check_similarity: bool = True
    ) -> PlagiarismReport:
        """
        执行洗稿检测
        
        Args:
            text: 待检测文本
            text_id: 文本ID
            check_sensitive: 是否检查敏感内容
            check_similarity: 是否检查相似度
            
        Returns:
            检测报告
        """
        matches = []
        sensitivity_findings = []
        
        # 1. 相似度检测
        if check_similarity:
            # 分段检测
            segments = self._segment_text(text)
            
            for segment in segments:
                segment_matches = await self.reference_db.find_similar_chunks(
                    segment,
                    top_k=3,
                    similarity_threshold=0.6
                )
                matches.extend(segment_matches)
        
        # 2. 敏感内容检测
        if check_sensitive:
            sensitivity_findings = self.reference_db.check_sensitive_content(text)
        
        # 3. 计算综合指标
        overall_similarity = self._calculate_overall_similarity(matches, text)
        similarity_level = self._determine_similarity_level(overall_similarity)
        
        # 4. 计算风险分数
        risk_score = self._calculate_risk_score(
            overall_similarity,
            len(sensitivity_findings),
            matches
        )
        
        # 5. 生成建议
        suggestions = self._generate_suggestions(
            similarity_level,
            sensitivity_findings,
            matches
        )
        
        # 6. 判断是否原创
        is_original = (
            similarity_level in [SimilarityLevel.NONE, SimilarityLevel.LOW]
            and len(sensitivity_findings) == 0
        )
        
        report = PlagiarismReport(
            text_id=text_id,
            overall_similarity=overall_similarity,
            similarity_level=similarity_level,
            matches=matches,
            sensitivity_findings=sensitivity_findings,
            is_original=is_original,
            risk_score=risk_score,
            suggestions=suggestions
        )
        
        self.detection_history.append(report)
        
        return report
    
    def _segment_text(self, text: str, segment_size: int = 200) -> List[str]:
        """将文本分割成检测段"""
        segments = []
        
        # 按句子分割
        sentences = re.split(r'[。！？\.\n]+', text)
        
        current_segment = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_segment) + len(sentence) < segment_size:
                current_segment += sentence
            else:
                if current_segment:
                    segments.append(current_segment)
                current_segment = sentence
        
        if current_segment:
            segments.append(current_segment)
        
        return segments
    
    def _calculate_overall_similarity(
        self,
        matches: List[SimilarityMatch],
        text: str
    ) -> float:
        """计算整体相似度"""
        if not matches:
            return 0.0
        
        # 计算匹配文本占总文本的比例
        total_matched_length = sum(len(m.matched_text) for m in matches)
        text_length = len(text)
        
        if text_length == 0:
            return 0.0
        
        coverage_ratio = total_matched_length / text_length
        
        # 结合相似度分数和覆盖率
        avg_similarity = sum(m.similarity_score for m in matches) / len(matches)
        
        overall = avg_similarity * 0.6 + coverage_ratio * 0.4
        
        return min(overall, 1.0)
    
    def _determine_similarity_level(self, similarity: float) -> SimilarityLevel:
        """确定相似度等级"""
        if similarity < 0.1:
            return SimilarityLevel.NONE
        elif similarity < 0.3:
            return SimilarityLevel.LOW
        elif similarity < 0.6:
            return SimilarityLevel.MEDIUM
        elif similarity < 0.8:
            return SimilarityLevel.HIGH
        else:
            return SimilarityLevel.CRITICAL
    
    def _calculate_risk_score(
        self,
        similarity: float,
        sensitivity_count: int,
        matches: List[SimilarityMatch]
    ) -> float:
        """计算风险分数"""
        # 相似度风险
        similarity_risk = similarity * 0.5
        
        # 敏感内容风险
        sensitivity_risk = min(sensitivity_count * 0.1, 0.3)
        
        # 高风险匹配风险
        high_risk_matches = sum(1 for m in matches if m.similarity_score > 0.8)
        match_risk = min(high_risk_matches * 0.1, 0.2)
        
        total_risk = similarity_risk + sensitivity_risk + match_risk
        
        return min(total_risk, 1.0)
    
    def _generate_suggestions(
        self,
        similarity_level: SimilarityLevel,
        sensitivity_findings: List[SensitivityFinding],
        matches: List[SimilarityMatch]
    ) -> List[str]:
        """生成修改建议"""
        suggestions = []
        
        # 相似度建议
        if similarity_level == SimilarityLevel.CRITICAL:
            suggestions.append("⚠️ 检测到严重相似内容，建议大幅修改或重写")
        elif similarity_level == SimilarityLevel.HIGH:
            suggestions.append("⚠️ 检测到高度相似内容，建议修改相似段落")
        elif similarity_level == SimilarityLevel.MEDIUM:
            suggestions.append("💡 检测到中等相似内容，建议调整表达方式")
        
        # 敏感内容建议
        if sensitivity_findings:
            sensitivity_types = set(f.sensitivity_type.value for f in sensitivity_findings)
            suggestions.append(
                f"⚠️ 检测到敏感内容（{', '.join(sensitivity_types)}），建议修改"
            )
        
        # 具体匹配建议
        for match in matches[:3]:  # 最多显示3个
            if match.similarity_score > 0.7:
                suggestions.append(
                    f"• 与《{match.source_reference}》相似度 {match.similarity_score:.1%}，"
                    f"建议修改：'{match.source_text[:50]}...'"
                )
        
        if not suggestions:
            suggestions.append("✅ 内容通过原创性检测")
        
        return suggestions
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """获取检测统计"""
        if not self.detection_history:
            return {"message": "暂无检测记录"}
        
        total_checks = len(self.detection_history)
        original_count = sum(1 for r in self.detection_history if r.is_original)
        
        level_distribution = {}
        for report in self.detection_history:
            level = report.similarity_level.value
            level_distribution[level] = level_distribution.get(level, 0) + 1
        
        avg_risk = sum(r.risk_score for r in self.detection_history) / total_checks
        
        return {
            "total_checks": total_checks,
            "original_count": original_count,
            "original_rate": round(original_count / total_checks, 3),
            "level_distribution": level_distribution,
            "average_risk_score": round(avg_risk, 3),
            "high_risk_count": sum(1 for r in self.detection_history if r.risk_score > 0.6)
        }


# 全局实例
_plagiarism_detector: Optional[PlagiarismDetector] = None


def get_plagiarism_detector() -> PlagiarismDetector:
    """获取洗稿检测器实例"""
    global _plagiarism_detector
    if _plagiarism_detector is None:
        _plagiarism_detector = PlagiarismDetector()
    return _plagiarism_detector
