"""
Agent Reasoning Engine - Agent思考能力引擎
每个Agent执行前增加Reasoning阶段
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class ReasoningType(Enum):
    """推理类型"""
    CHAPTER_GOAL = "chapter_goal"           # 章节目标分析
    PLOT_VALIDATION = "plot_validation"     # 剧情合理性验证
    CHOICE_ANALYSIS = "choice_analysis"     # 多种剧情选择分析
    AUTHOR_CONSULTATION = "author_consultation"  # 需要作者决策
    DIRECT_ACTION = "direct_action"         # 直接执行


class DecisionType(Enum):
    """决策类型"""
    GENERATE = "generate"           # 生成内容
    MODIFY = "modify"               # 修改内容
    QUESTION = "question"           # 向作者提问
    DISCUSS = "discuss"             # 发起讨论
    SKIP = "skip"                   # 跳过


class ConfidenceLevel(Enum):
    """置信度等级"""
    HIGH = "high"       # > 0.8
    MEDIUM = "medium"   # 0.5 - 0.8
    LOW = "low"         # < 0.5


@dataclass
class ReasoningContext:
    """推理上下文"""
    novel_id: str
    chapter_id: str
    agent_type: str
    current_scene: str
    story_summary: str
    character_states: Dict[str, Any]
    plot_progress: float  # 0-1
    foreshadowing_status: List[Dict[str, Any]]
    previous_chapters_summary: str
    target_word_count: int


@dataclass
class ReasoningResult:
    """推理结果"""
    reasoning_id: str
    agent_type: str
    reasoning_type: ReasoningType
    decision: DecisionType
    confidence: float
    
    # 分析内容
    chapter_goal_analysis: Optional[str] = None
    plot_validity_assessment: Optional[str] = None
    available_choices: List[Dict[str, Any]] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    
    # 决策依据
    reasoning_process: str = ""
    
    # 建议
    recommendations: List[str] = field(default_factory=list)
    
    # 是否需要作者决策
    requires_author_decision: bool = False
    author_question: Optional[Dict[str, Any]] = None
    
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "reasoning_id": self.reasoning_id,
            "agent_type": self.agent_type,
            "reasoning_type": self.reasoning_type.value,
            "decision": self.decision.value,
            "confidence": round(self.confidence, 2),
            "confidence_level": self._get_confidence_level(),
            "chapter_goal_analysis": self.chapter_goal_analysis,
            "plot_validity_assessment": self.plot_validity_assessment,
            "available_choices": self.available_choices,
            "concerns": self.concerns,
            "reasoning_process": self.reasoning_process,
            "recommendations": self.recommendations,
            "requires_author_decision": self.requires_author_decision,
            "author_question": self.author_question,
            "timestamp": self.timestamp
        }
    
    def _get_confidence_level(self) -> str:
        if self.confidence >= 0.8:
            return ConfidenceLevel.HIGH.value
        elif self.confidence >= 0.5:
            return ConfidenceLevel.MEDIUM.value
        else:
            return ConfidenceLevel.LOW.value


@dataclass
class ChapterGoal:
    """章节目标"""
    goal_type: str  # setup/conflict/development/climax/resolution
    description: str
    priority: int
    success_criteria: List[str]


@dataclass
class PlotChoice:
    """剧情选择"""
    choice_id: str
    description: str
    pros: List[str]
    cons: List[str]
    impact_on_story: str
    confidence: float


class AgentReasoningEngine:
    """
    Agent思考能力引擎
    
    每个Agent执行前进行Reasoning：
    1. 分析当前章节目标
    2. 验证剧情合理性
    3. 识别多种剧情选择
    4. 判断是否需要作者决策
    """
    
    def __init__(self):
        self.reasoning_history: List[ReasoningResult] = []
        self.chapter_goals: Dict[str, List[ChapterGoal]] = {}
        self.plot_choices_cache: Dict[str, List[PlotChoice]] = {}
    
    async def reason_before_action(
        self,
        context: ReasoningContext
    ) -> ReasoningResult:
        """
        执行前进行推理
        
        Returns:
            推理结果，包含决策和建议
        """
        reasoning_id = f"reason_{datetime.now().timestamp()}"
        
        # 1. 分析章节目标
        chapter_goal = self._analyze_chapter_goal(context)
        
        # 2. 验证剧情合理性
        validity = self._validate_plot_validity(context)
        
        # 3. 分析可选剧情
        choices = self._analyze_plot_choices(context)
        
        # 4. 识别担忧和问题
        concerns = self._identify_concerns(context, validity)
        
        # 5. 确定推理类型和决策
        reasoning_type, decision, confidence = self._determine_reasoning_type(
            context, validity, choices, concerns
        )
        
        # 6. 生成推理过程
        reasoning_process = self._generate_reasoning_process(
            context, chapter_goal, validity, choices, concerns, decision
        )
        
        # 7. 生成建议
        recommendations = self._generate_recommendations(
            context, chapter_goal, choices, concerns
        )
        
        # 8. 判断是否需要作者决策
        requires_author, author_question = self._check_author_decision_needed(
            context, choices, concerns, confidence
        )
        
        result = ReasoningResult(
            reasoning_id=reasoning_id,
            agent_type=context.agent_type,
            reasoning_type=reasoning_type,
            decision=decision,
            confidence=confidence,
            chapter_goal_analysis=chapter_goal.description if chapter_goal else None,
            plot_validity_assessment=validity.get("assessment"),
            available_choices=[c.__dict__ for c in choices],
            concerns=concerns,
            reasoning_process=reasoning_process,
            recommendations=recommendations,
            requires_author_decision=requires_author,
            author_question=author_question
        )
        
        self.reasoning_history.append(result)
        
        return result
    
    def _analyze_chapter_goal(self, context: ReasoningContext) -> Optional[ChapterGoal]:
        """分析章节目标"""
        # 根据章节进度确定目标类型
        progress = context.plot_progress
        
        if progress < 0.1:
            goal_type = "setup"
            description = "建立场景，引入角色和背景"
        elif progress < 0.3:
            goal_type = "conflict_introduction"
            description = "引入冲突，推动剧情发展"
        elif progress < 0.6:
            goal_type = "development"
            description = "展开剧情，深化角色关系"
        elif progress < 0.8:
            goal_type = "climax_building"
            description = "构建高潮，增加紧张感"
        elif progress < 0.95:
            goal_type = "climax"
            description = "达到高潮，解决主要冲突"
        else:
            goal_type = "resolution"
            description = "收尾，解决剩余问题"
        
        # 根据Agent类型调整目标
        agent_specific_goals = {
            "planner": f"规划{description}",
            "conflict": f"设计冲突：{description}",
            "writer": f"写作：{description}",
            "editor": f"评估结构：{description}",
            "reader": f"模拟读者反应：{description}"
        }
        
        adjusted_description = agent_specific_goals.get(
            context.agent_type,
            description
        )
        
        return ChapterGoal(
            goal_type=goal_type,
            description=adjusted_description,
            priority=8 if goal_type in ["climax", "resolution"] else 5,
            success_criteria=[
                "完成目标描述的内容",
                "保持角色一致性",
                "推进整体剧情"
            ]
        )
    
    def _validate_plot_validity(self, context: ReasoningContext) -> Dict[str, Any]:
        """验证剧情合理性"""
        assessment = {
            "is_valid": True,
            "assessment": "",
            "issues": [],
            "warnings": []
        }
        
        # 检查角色状态一致性
        for char_id, state in context.character_states.items():
            if state.get("location") != state.get("previous_location"):
                # 检查位置变化是否合理
                if not state.get("travel_explained"):
                    assessment["warnings"].append(
                        f"角色{char_id}位置变化未解释"
                    )
        
        # 检查伏笔状态
        unresolved_critical = [
            f for f in context.foreshadowing_status
            if f.get("status") == "unresolved" and f.get("priority") == "high"
        ]
        
        if len(unresolved_critical) > 3:
            assessment["warnings"].append(
                f"有{len(unresolved_critical)}个重要伏笔未解决"
            )
        
        # 检查剧情进度
        if context.plot_progress > 0.8 and not any(
            f.get("type") == "climax_foreshadowing"
            for f in context.foreshadowing_status
        ):
            assessment["warnings"].append(
                "接近高潮但缺乏高潮铺垫"
            )
        
        # 生成评估文本
        if assessment["issues"]:
            assessment["assessment"] = "存在严重剧情问题，需要修正"
            assessment["is_valid"] = False
        elif assessment["warnings"]:
            assessment["assessment"] = "剧情基本合理，但有一些需要注意的问题"
        else:
            assessment["assessment"] = "剧情合理，可以继续"
        
        return assessment
    
    def _analyze_plot_choices(self, context: ReasoningContext) -> List[PlotChoice]:
        """分析可选剧情"""
        choices = []
        
        # 根据Agent类型和上下文生成选择
        if context.agent_type == "planner":
            choices = [
                PlotChoice(
                    choice_id="choice_1",
                    description="按原计划推进剧情",
                    pros=["保持故事连贯性", "风险较低"],
                    cons=["可能缺乏惊喜"],
                    impact_on_story="稳步推进主线",
                    confidence=0.8
                ),
                PlotChoice(
                    choice_id="choice_2",
                    description="引入意外转折",
                    pros=["增加戏剧性", "吸引读者"],
                    cons=["风险较高", "需要额外铺垫"],
                    impact_on_story="可能改变故事走向",
                    confidence=0.6
                ),
                PlotChoice(
                    choice_id="choice_3",
                    description="深化角色关系",
                    pros=["丰富人物", "增加情感深度"],
                    cons=["可能拖慢节奏"],
                    impact_on_story="增强角色塑造",
                    confidence=0.7
                )
            ]
        elif context.agent_type == "conflict":
            choices = [
                PlotChoice(
                    choice_id="conflict_1",
                    description="外部冲突（与环境/敌人）",
                    pros=["动作性强", "易于描写"],
                    cons=["可能流于表面"],
                    impact_on_story="推动外部剧情",
                    confidence=0.75
                ),
                PlotChoice(
                    choice_id="conflict_2",
                    description="内部冲突（心理/道德）",
                    pros=["深度强", "角色成长"],
                    cons=["描写难度大"],
                    impact_on_story="深化角色内涵",
                    confidence=0.7
                ),
                PlotChoice(
                    choice_id="conflict_3",
                    description="人际冲突（角色间）",
                    pros=["关系复杂", "戏剧性强"],
                    cons=["需要 careful 处理"],
                    impact_on_story="改变角色关系",
                    confidence=0.65
                )
            ]
        elif context.agent_type == "writer":
            choices = [
                PlotChoice(
                    choice_id="write_1",
                    description="详细描写场景",
                    pros=["沉浸感强", "画面感好"],
                    cons=["字数可能超标"],
                    impact_on_story="增强阅读体验",
                    confidence=0.75
                ),
                PlotChoice(
                    choice_id="write_2",
                    description="快节奏推进",
                    pros=["节奏紧凑", "保持张力"],
                    cons=["可能缺乏细节"],
                    impact_on_story="加快剧情节奏",
                    confidence=0.7
                )
            ]
        
        return choices
    
    def _identify_concerns(
        self,
        context: ReasoningContext,
        validity: Dict[str, Any]
    ) -> List[str]:
        """识别担忧和问题"""
        concerns = []
        
        # 基于验证结果
        concerns.extend(validity.get("issues", []))
        concerns.extend(validity.get("warnings", []))
        
        # 基于Agent类型的特定担忧
        agent_concerns = {
            "planner": [
                "章节目标是否明确",
                "与整体大纲是否一致"
            ],
            "conflict": [
                "冲突强度是否合适",
                "是否有足够的戏剧张力"
            ],
            "writer": [
                "字数控制是否在范围内",
                "描写是否生动"
            ],
            "editor": [
                "结构是否完整",
                "逻辑是否通顺"
            ],
            "reader": [
                "读者是否会感兴趣",
                "是否有足够的吸引力"
            ]
        }
        
        concerns.extend(agent_concerns.get(context.agent_type, []))
        
        return concerns
    
    def _determine_reasoning_type(
        self,
        context: ReasoningContext,
        validity: Dict[str, Any],
        choices: List[PlotChoice],
        concerns: List[str]
    ) -> Tuple[ReasoningType, DecisionType, float]:
        """确定推理类型和决策"""
        
        # 如果有严重问题，需要作者决策
        if validity.get("issues"):
            return ReasoningType.AUTHOR_CONSULTATION, DecisionType.QUESTION, 0.3
        
        # 如果有多个高置信度选择，需要讨论
        high_confidence_choices = [c for c in choices if c.confidence > 0.7]
        if len(high_confidence_choices) >= 2:
            return ReasoningType.CHOICE_ANALYSIS, DecisionType.DISCUSS, 0.6
        
        # 如果有担忧但不太严重
        if concerns and len(concerns) <= 2:
            return ReasoningType.PLOT_VALIDATION, DecisionType.GENERATE, 0.7
        
        # 如果有很多担忧
        if len(concerns) > 2:
            return ReasoningType.AUTHOR_CONSULTATION, DecisionType.QUESTION, 0.5
        
        # 默认情况
        return ReasoningType.DIRECT_ACTION, DecisionType.GENERATE, 0.85
    
    def _generate_reasoning_process(
        self,
        context: ReasoningContext,
        chapter_goal: Optional[ChapterGoal],
        validity: Dict[str, Any],
        choices: List[PlotChoice],
        concerns: List[str],
        decision: DecisionType
    ) -> str:
        """生成推理过程描述"""
        process_parts = []
        
        # 分析章节目标
        if chapter_goal:
            process_parts.append(
                f"1. 分析章节目标：{chapter_goal.description}"
            )
        
        # 验证剧情
        process_parts.append(
            f"2. 验证剧情合理性：{validity.get('assessment', '未评估')}"
        )
        
        # 分析选择
        if choices:
            process_parts.append(
                f"3. 识别{len(choices)}个可能的选择"
            )
            best_choice = max(choices, key=lambda c: c.confidence)
            process_parts.append(
                f"   最佳选择：{best_choice.description}（置信度{best_choice.confidence}）"
            )
        
        # 识别担忧
        if concerns:
            process_parts.append(
                f"4. 识别{len(concerns)}个潜在问题"
            )
        
        # 做出决策
        process_parts.append(
            f"5. 做出决策：{decision.value}"
        )
        
        return "\n".join(process_parts)
    
    def _generate_recommendations(
        self,
        context: ReasoningContext,
        chapter_goal: Optional[ChapterGoal],
        choices: List[PlotChoice],
        concerns: List[str]
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 基于章节目标
        if chapter_goal:
            recommendations.append(
                f"重点关注：{chapter_goal.description}"
            )
        
        # 基于最佳选择
        if choices:
            best_choice = max(choices, key=lambda c: c.confidence)
            recommendations.append(
                f"建议采用：{best_choice.description}"
            )
        
        # 基于担忧
        if concerns:
            recommendations.append(
                f"需要注意：{concerns[0]}"
            )
        
        # 字数控制建议
        recommendations.append(
            f"字数控制：目标{context.target_word_count}字，注意控制节奏"
        )
        
        return recommendations
    
    def _check_author_decision_needed(
        self,
        context: ReasoningContext,
        choices: List[PlotChoice],
        concerns: List[str],
        confidence: float
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """检查是否需要作者决策"""
        
        # 置信度低时需要作者决策
        if confidence < 0.5:
            question = {
                "agent": context.agent_type,
                "question": f"{context.agent_type}对当前剧情方向不确定，需要您的指导",
                "context": {
                    "chapter": context.chapter_id,
                    "concerns": concerns[:3],
                    "choices": [
                        {"id": c.choice_id, "description": c.description}
                        for c in choices[:3]
                    ]
                },
                "importance": "high",
                "blocking": True
            }
            return True, question
        
        # 如果有多个同样好的选择
        high_confidence_choices = [c for c in choices if c.confidence > 0.7]
        if len(high_confidence_choices) >= 2:
            question = {
                "agent": context.agent_type,
                "question": "有多个可行的剧情方向，请选择您偏好的方向",
                "options": [
                    c.description for c in high_confidence_choices[:3]
                ],
                "importance": "medium",
                "blocking": False
            }
            return True, question
        
        return False, None
    
    def get_reasoning_history(
        self,
        novel_id: Optional[str] = None,
        agent_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取推理历史"""
        filtered = self.reasoning_history
        
        if novel_id:
            # 这里简化处理，实际应该根据context中的novel_id过滤
            pass
        
        if agent_type:
            filtered = [r for r in filtered if r.agent_type == agent_type]
        
        return [r.to_dict() for r in filtered[-20:]]  # 最近20条


# 全局实例
_reasoning_engine: Optional[AgentReasoningEngine] = None


def get_agent_reasoning_engine() -> AgentReasoningEngine:
    """获取Agent推理引擎实例"""
    global _reasoning_engine
    if _reasoning_engine is None:
        _reasoning_engine = AgentReasoningEngine()
    return _reasoning_engine
