"""
Conflict Analyzer - 冲突热力图分析器
提供章节冲突强度分析、张力曲线生成和冲突建议
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import re

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


class ConflictType(Enum):
    """冲突类型"""
    INTERNAL = "internal"           # 内心冲突
    EXTERNAL = "external"           # 外部冲突
    INTERPERSONAL = "interpersonal"  # 人际冲突
    SOCIETAL = "societal"           # 社会冲突
    NATURE = "nature"               # 人与自然
    SUPERNATURAL = "supernatural"   # 超自然冲突


class TensionLevel(Enum):
    """张力等级"""
    CALM = 0.0          # 平静
    LOW = 0.25          # 低张力
    MEDIUM = 0.5        # 中等张力
    HIGH = 0.75         # 高张力
    CLIMAX = 1.0        # 高潮


@dataclass
class ConflictPoint:
    """冲突点"""
    position: float                     # 在章节中的位置 (0-1)
    tension_score: float               # 张力分数 (0-1)
    conflict_type: ConflictType
    description: str
    characters_involved: List[str] = field(default_factory=list)
    intensity: str = "medium"          # low/medium/high


@dataclass
class TensionCurve:
    """张力曲线"""
    points: List[Tuple[float, float]]  # [(位置, 张力值), ...]
    average_tension: float
    peak_tension: float
    peak_position: float
    curve_type: str                     # rising/falling/wave/static


@dataclass
class ConflictAnalysis:
    """冲突分析结果"""
    tension_score: float               # 总体张力分数 (0-1)
    conflict_types: List[ConflictType]
    tension_curve: TensionCurve
    conflict_points: List[ConflictPoint]
    suggestions: List[Dict[str, Any]]
    pacing_analysis: Dict[str, Any]
    emotional_arc: List[str]


class TensionAnalyzer:
    """
    张力分析器
    
    分析文本的张力分布
    """
    
    # 张力关键词
    TENSION_KEYWORDS = {
        "high": [
            "紧张", "危险", "危机", "战斗", "冲突", "对抗", "追逐",
            "死亡", "杀", "逃", "陷阱", "阴谋", "背叛", "决斗",
            "激烈", "爆发", "高潮", "绝境", "生死", "拼命"
        ],
        "medium": [
            "担忧", "焦虑", "不安", "怀疑", "争执", "分歧", "压力",
            "困难", "挑战", "阻碍", "麻烦", "纠纷", "误会", "竞争",
            "紧张", "警惕", "小心", "防备", "准备", "计划"
        ],
        "low": [
            "平静", "放松", "休息", "聊天", "日常", "平静", "安逸",
            "舒适", "愉快", "轻松", "和谐", "友好", "温馨", "宁静",
            "悠闲", "惬意", "满足", "幸福", "快乐", "欢喜"
        ]
    }
    
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.2)
    
    def analyze_tension_curve(self, text: str, num_points: int = 10) -> TensionCurve:
        """
        分析张力曲线
        
        Args:
            text: 章节文本
            num_points: 采样点数
            
        Returns:
            张力曲线
        """
        # 将文本分成段落
        paragraphs = self._split_into_paragraphs(text)
        if not paragraphs:
            return TensionCurve(
                points=[(0, 0.5)],
                average_tension=0.5,
                peak_tension=0.5,
                peak_position=0.5,
                curve_type="static"
            )
        
        # 计算每个段落的张力
        points = []
        step = 1.0 / len(paragraphs)
        
        for i, paragraph in enumerate(paragraphs):
            position = i * step
            tension = self._calculate_paragraph_tension(paragraph)
            points.append((position, tension))
        
        # 分析曲线特征
        tensions = [p[1] for p in points]
        avg_tension = sum(tensions) / len(tensions)
        peak_tension = max(tensions)
        peak_idx = tensions.index(peak_tension)
        peak_position = points[peak_idx][0]
        
        # 判断曲线类型
        curve_type = self._determine_curve_type(points)
        
        return TensionCurve(
            points=points,
            average_tension=avg_tension,
            peak_tension=peak_tension,
            peak_position=peak_position,
            curve_type=curve_type
        )
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """分割成段落"""
        # 按空行分割
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        
        # 如果段落太少，按句子分割
        if len(paragraphs) < 5:
            sentences = re.split(r'[。！？\.\!\?]+', text)
            paragraphs = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        return paragraphs
    
    def _calculate_paragraph_tension(self, paragraph: str) -> float:
        """计算段落的张力值"""
        tension_score = 0.5  # 基础值
        
        # 检查高张力关键词
        high_count = sum(1 for kw in self.TENSION_KEYWORDS["high"] if kw in paragraph)
        tension_score += high_count * 0.15
        
        # 检查中等张力关键词
        medium_count = sum(1 for kw in self.TENSION_KEYWORDS["medium"] if kw in paragraph)
        tension_score += medium_count * 0.05
        
        # 检查低张力关键词（降低张力）
        low_count = sum(1 for kw in self.TENSION_KEYWORDS["low"] if kw in paragraph)
        tension_score -= low_count * 0.1
        
        # 对话密度（对话多通常张力较低）
        dialogue_count = paragraph.count('"') + paragraph.count('"') + paragraph.count('"')
        if dialogue_count > 4:
            tension_score -= 0.1
        
        # 限制在 0-1 范围
        return max(0.0, min(1.0, tension_score))
    
    def _determine_curve_type(self, points: List[Tuple[float, float]]) -> str:
        """判断曲线类型"""
        if len(points) < 3:
            return "static"
        
        tensions = [p[1] for p in points]
        
        # 计算趋势
        first_half = tensions[:len(tensions)//2]
        second_half = tensions[len(tensions)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        diff = second_avg - first_avg
        
        if diff > 0.2:
            return "rising"
        elif diff < -0.2:
            return "falling"
        elif max(tensions) - min(tensions) > 0.3:
            return "wave"
        else:
            return "static"


class ConflictDetector:
    """
    冲突检测器
    
    检测文本中的冲突点
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.3)
    
    async def detect_conflicts(self, text: str) -> List[ConflictPoint]:
        """
        检测冲突点
        
        Args:
            text: 章节文本
            
        Returns:
            冲突点列表
        """
        # 使用 LLM 检测冲突
        llm_conflicts = await self._llm_detect_conflicts(text)
        
        # 规则检测
        rule_conflicts = self._rule_detect_conflicts(text)
        
        # 合并结果
        all_conflicts = llm_conflicts + rule_conflicts
        
        # 去重和排序
        unique_conflicts = self._deduplicate_conflicts(all_conflicts)
        
        return sorted(unique_conflicts, key=lambda x: x.position)
    
    async def _llm_detect_conflicts(self, text: str) -> List[ConflictPoint]:
        """使用 LLM 检测冲突"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位专业的小说分析师，擅长识别故事中的冲突。

请分析提供的章节内容，识别所有冲突点，包括：
1. **内心冲突** - 角色的内心挣扎、矛盾
2. **外部冲突** - 角色与外部环境、事件的冲突
3. **人际冲突** - 角色之间的矛盾、对抗
4. **社会冲突** - 与社会规则、势力的冲突
5. **自然冲突** - 与自然环境、灾难的冲突

对每个冲突点，请提供：
- 在章节中的大致位置 (0-1)
- 张力强度 (0-1)
- 冲突类型
- 简要描述
- 涉及的角色

以 JSON 格式返回结果。"""),
            ("human", """【章节内容】
{text}

请分析冲突点并以 JSON 格式返回：
{{
    "conflicts": [
        {{
            "position": 位置数字,
            "tension_score": 张力分数,
            "conflict_type": "internal/external/interpersonal/societal/nature",
            "description": "冲突描述",
            "characters": ["角色1", "角色2"],
            "intensity": "low/medium/high"
        }}
    ]
}}""")
        ])
        
        chain = prompt | self.llm
        
        try:
            response = await chain.ainvoke({
                "text": text[:4000]
            })
            
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content.strip())
            
            conflicts = []
            for c in result.get("conflicts", []):
                try:
                    conflict = ConflictPoint(
                        position=c.get("position", 0.5),
                        tension_score=c.get("tension_score", 0.5),
                        conflict_type=ConflictType(c.get("conflict_type", "external")),
                        description=c.get("description", ""),
                        characters_involved=c.get("characters", []),
                        intensity=c.get("intensity", "medium")
                    )
                    conflicts.append(conflict)
                except (ValueError, KeyError):
                    continue
            
            return conflicts
        except Exception as e:
            print(f"LLM conflict detection error: {e}")
            return []
    
    def _rule_detect_conflicts(self, text: str) -> List[ConflictPoint]:
        """基于规则检测冲突"""
        conflicts = []
        
        # 战斗场景检测
        battle_keywords = ["战斗", "打斗", "攻击", "防御", "武器", "受伤", "流血"]
        for i, keyword in enumerate(battle_keywords):
            if keyword in text:
                # 找到位置
                pos = text.find(keyword) / len(text) if text else 0.5
                conflicts.append(ConflictPoint(
                    position=pos,
                    tension_score=0.8 + (0.1 * (i % 3)),
                    conflict_type=ConflictType.EXTERNAL,
                    description=f"检测到战斗场景: {keyword}",
                    intensity="high"
                ))
                break
        
        # 对话冲突检测
        dialogue_conflicts = ["争吵", "争论", "反驳", "质疑", "指责", "威胁"]
        for keyword in dialogue_conflicts:
            if keyword in text:
                pos = text.find(keyword) / len(text) if text else 0.5
                conflicts.append(ConflictPoint(
                    position=pos,
                    tension_score=0.6,
                    conflict_type=ConflictType.INTERPERSONAL,
                    description=f"检测到对话冲突: {keyword}",
                    intensity="medium"
                ))
                break
        
        # 内心挣扎检测
        internal_keywords = ["犹豫", "挣扎", "矛盾", "纠结", "痛苦", "迷茫"]
        for keyword in internal_keywords:
            if keyword in text:
                pos = text.find(keyword) / len(text) if text else 0.5
                conflicts.append(ConflictPoint(
                    position=pos,
                    tension_score=0.5,
                    conflict_type=ConflictType.INTERNAL,
                    description=f"检测到内心挣扎: {keyword}",
                    intensity="medium"
                ))
                break
        
        return conflicts
    
    def _deduplicate_conflicts(self, conflicts: List[ConflictPoint]) -> List[ConflictPoint]:
        """去重"""
        seen_positions = set()
        unique = []
        
        for c in conflicts:
            # 按位置分组（每0.1范围视为一个位置）
            pos_key = round(c.position * 10) / 10
            if pos_key not in seen_positions:
                seen_positions.add(pos_key)
                unique.append(c)
        
        return unique


class ConflictSuggestionEngine:
    """
    冲突建议引擎
    
    基于分析结果生成改进建议
    """
    
    def generate_suggestions(
        self,
        tension_score: float,
        tension_curve: TensionCurve,
        conflict_points: List[ConflictPoint]
    ) -> List[Dict[str, Any]]:
        """
        生成改进建议
        
        Args:
            tension_score: 总体张力分数
            tension_curve: 张力曲线
            conflict_points: 冲突点列表
            
        Returns:
            建议列表
        """
        suggestions = []
        
        # 1. 张力分数建议
        if tension_score < 0.3:
            suggestions.append({
                "priority": "high",
                "type": "increase_tension",
                "title": "冲突张力不足",
                "description": "当前章节冲突张力较低，建议增加戏剧冲突",
                "suggestions": [
                    "引入外部威胁或障碍",
                    "增加角色间的矛盾",
                    "设置时间限制或 deadline",
                    "提高失败的代价"
                ]
            })
        elif tension_score > 0.9:
            suggestions.append({
                "priority": "medium",
                "type": "add_breathing_room",
                "title": "张力过高",
                "description": "章节全程高张力，读者可能感到疲劳",
                "suggestions": [
                    "插入缓冲段落，让角色和读者休息",
                    "添加一些轻松的场景",
                    "在高潮前适当降低张力"
                ]
            })
        
        # 2. 曲线类型建议
        if tension_curve.curve_type == "static":
            suggestions.append({
                "priority": "medium",
                "type": "improve_pacing",
                "title": "节奏平淡",
                "description": "张力曲线过于平稳，缺乏起伏",
                "suggestions": [
                    "设置小高潮和低谷交替",
                    "在章节中段增加转折",
                    "让冲突逐步升级"
                ]
            })
        elif tension_curve.curve_type == "falling":
            suggestions.append({
                "priority": "medium",
                "type": "adjust_structure",
                "title": "高开低走",
                "description": "章节开始时张力高，但逐渐下降",
                "suggestions": [
                    "在结尾设置悬念或新冲突",
                    "让主要冲突在结尾达到高潮",
                    "添加意外的转折"
                ]
            })
        
        # 3. 冲突类型建议
        conflict_types = set(c.conflict_type for c in conflict_points)
        if len(conflict_types) == 1:
            conflict_type_name = list(conflict_types)[0].value
            suggestions.append({
                "priority": "low",
                "type": "diversify_conflicts",
                "title": "冲突类型单一",
                "description": f"当前只有 {conflict_type_name} 冲突",
                "suggestions": [
                    "增加不同类型的冲突",
                    "结合内心冲突和外部冲突",
                    "引入人际矛盾"
                ]
            })
        
        # 4. 冲突密度建议
        if len(conflict_points) < 2 and tension_score > 0.3:
            suggestions.append({
                "priority": "low",
                "type": "add_conflict_points",
                "title": "冲突点较少",
                "description": "章节中冲突点较少，可能影响节奏",
                "suggestions": [
                    "增加小冲突或障碍",
                    "设置次要矛盾",
                    "添加意外事件"
                ]
            })
        
        return suggestions


class ConflictHeatmapGenerator:
    """
    冲突热力图生成器
    
    生成可视化的冲突热力图数据
    """
    
    def generate_heatmap_data(
        self,
        text: str,
        tension_curve: TensionCurve,
        conflict_points: List[ConflictPoint]
    ) -> Dict[str, Any]:
        """
        生成热力图数据
        
        Returns:
            {
                "segments": [
                    {
                        "position": float,
                        "tension": float,
                        "color": str,
                        "conflicts": [...]
                    }
                ],
                "overall_stats": {...}
            }
        """
        # 将章节分成若干段
        num_segments = 20
        segment_size = 1.0 / num_segments
        
        segments = []
        for i in range(num_segments):
            start_pos = i * segment_size
            end_pos = (i + 1) * segment_size
            center_pos = (start_pos + end_pos) / 2
            
            # 找到该段的张力值
            tension = self._get_tension_at_position(center_pos, tension_curve)
            
            # 找到该段的冲突
            segment_conflicts = [
                c for c in conflict_points
                if start_pos <= c.position < end_pos
            ]
            
            # 确定颜色
            color = self._tension_to_color(tension)
            
            segments.append({
                "position": center_pos,
                "tension": tension,
                "color": color,
                "conflicts": [
                    {
                        "type": c.conflict_type.value,
                        "description": c.description,
                        "intensity": c.intensity
                    }
                    for c in segment_conflicts
                ]
            })
        
        return {
            "segments": segments,
            "overall_stats": {
                "average_tension": tension_curve.average_tension,
                "peak_tension": tension_curve.peak_tension,
                "peak_position": tension_curve.peak_position,
                "curve_type": tension_curve.curve_type,
                "total_conflicts": len(conflict_points)
            }
        }
    
    def _get_tension_at_position(
        self,
        position: float,
        curve: TensionCurve
    ) -> float:
        """获取指定位置的张力值"""
        # 找到最近的点
        closest_point = min(curve.points, key=lambda p: abs(p[0] - position))
        return closest_point[1]
    
    def _tension_to_color(self, tension: float) -> str:
        """将张力值转换为颜色"""
        if tension < 0.2:
            return "#4ade80"  # 绿色 - 平静
        elif tension < 0.4:
            return "#facc15"  # 黄色 - 低张力
        elif tension < 0.6:
            return "#fb923c"  # 橙色 - 中等
        elif tension < 0.8:
            return "#f87171"  # 红色 - 高张力
        else:
            return "#dc2626"  # 深红 - 高潮


class ConflictAnalyzer:
    """
    冲突分析器主类
    
    提供统一的冲突分析接口
    """
    
    def __init__(self):
        self.tension_analyzer = TensionAnalyzer()
        self.conflict_detector = ConflictDetector()
        self.suggestion_engine = ConflictSuggestionEngine()
        self.heatmap_generator = ConflictHeatmapGenerator()
    
    async def analyze(self, chapter_text: str) -> ConflictAnalysis:
        """
        分析章节冲突
        
        Args:
            chapter_text: 章节文本
            
        Returns:
            冲突分析结果
        """
        # 1. 分析张力曲线
        tension_curve = self.tension_analyzer.analyze_tension_curve(chapter_text)
        
        # 2. 检测冲突点
        conflict_points = await self.conflict_detector.detect_conflicts(chapter_text)
        
        # 3. 计算总体张力分数
        tension_score = tension_curve.average_tension
        if conflict_points:
            conflict_tension = sum(c.tension_score for c in conflict_points) / len(conflict_points)
            tension_score = (tension_score + conflict_tension) / 2
        
        # 4. 识别冲突类型
        conflict_types = list(set(c.conflict_type for c in conflict_points))
        
        # 5. 生成建议
        suggestions = self.suggestion_engine.generate_suggestions(
            tension_score, tension_curve, conflict_points
        )
        
        # 6. 分析节奏
        pacing_analysis = self._analyze_pacing(tension_curve)
        
        # 7. 情感弧线
        emotional_arc = self._analyze_emotional_arc(tension_curve)
        
        return ConflictAnalysis(
            tension_score=tension_score,
            conflict_types=conflict_types,
            tension_curve=tension_curve,
            conflict_points=conflict_points,
            suggestions=suggestions,
            pacing_analysis=pacing_analysis,
            emotional_arc=emotional_arc
        )
    
    def _analyze_pacing(self, curve: TensionCurve) -> Dict[str, Any]:
        """分析节奏"""
        return {
            "curve_type": curve.curve_type,
            "variation": max(p[1] for p in curve.points) - min(p[1] for p in curve.points),
            "is_balanced": 0.3 < curve.average_tension < 0.7,
            "has_climax": curve.peak_tension > 0.8
        }
    
    def _analyze_emotional_arc(self, curve: TensionCurve) -> List[str]:
        """分析情感弧线"""
        arc = []
        
        for pos, tension in curve.points:
            if tension < 0.3:
                arc.append("calm")
            elif tension < 0.5:
                arc.append("building")
            elif tension < 0.7:
                arc.append("tense")
            else:
                arc.append("climax")
        
        return arc
    
    async def generate_heatmap(self, chapter_text: str) -> Dict[str, Any]:
        """生成冲突热力图"""
        analysis = await self.analyze(chapter_text)
        
        return self.heatmap_generator.generate_heatmap_data(
            chapter_text,
            analysis.tension_curve,
            analysis.conflict_points
        )


# 便捷函数
_conflict_analyzer: Optional[ConflictAnalyzer] = None


def get_conflict_analyzer() -> ConflictAnalyzer:
    """获取冲突分析器实例"""
    global _conflict_analyzer
    if _conflict_analyzer is None:
        _conflict_analyzer = ConflictAnalyzer()
    return _conflict_analyzer


async def analyze_chapter_conflict(chapter_text: str) -> Dict[str, Any]:
    """分析章节冲突"""
    analyzer = get_conflict_analyzer()
    analysis = await analyzer.analyze(chapter_text)
    
    return {
        "tension_score": analysis.tension_score,
        "conflict_types": [t.value for t in analysis.conflict_types],
        "tension_curve": {
            "points": analysis.tension_curve.points,
            "average": analysis.tension_curve.average_tension,
            "peak": analysis.tension_curve.peak_tension,
            "curve_type": analysis.tension_curve.curve_type
        },
        "conflict_points": [
            {
                "position": c.position,
                "tension": c.tension_score,
                "type": c.conflict_type.value,
                "description": c.description,
                "intensity": c.intensity
            }
            for c in analysis.conflict_points
        ],
        "suggestions": analysis.suggestions,
        "pacing": analysis.pacing_analysis,
        "emotional_arc": analysis.emotional_arc
    }


async def generate_conflict_heatmap(chapter_text: str) -> Dict[str, Any]:
    """生成冲突热力图"""
    analyzer = get_conflict_analyzer()
    return await analyzer.generate_heatmap(chapter_text)
