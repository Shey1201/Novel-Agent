"""
Author Decision System - 作者决策系统
当Agent无法达成共识时，向作者提问并等待决策
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
from collections import defaultdict


class QuestionType(Enum):
    """问题类型"""
    PLOT_DIRECTION = "plot_direction"       # 剧情方向
    CHARACTER_ACTION = "character_action"   # 角色行为
    SETTING_DETAIL = "setting_detail"       # 设定细节
    STYLE_PREFERENCE = "style_preference"   # 风格偏好
    CONFLICT_RESOLUTION = "conflict_resolution"  # 冲突解决
    EMOTIONAL_TONE = "emotional_tone"       # 情感基调


class QuestionPriority(Enum):
    """问题优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DecisionStatus(Enum):
    """决策状态"""
    PENDING = "pending"           # 等待决策
    ANSWERED = "answered"         # 已回答
    TIMEOUT = "timeout"           # 超时
    OVERRIDDEN = "overridden"     # 被覆盖


@dataclass
class AuthorQuestion:
    """作者问题"""
    question_id: str
    question_type: QuestionType
    priority: QuestionPriority
    
    # 问题内容
    title: str
    description: str
    context: Dict[str, Any]
    
    # 选项
    options: List[Dict[str, Any]]  # [{"id": "opt1", "label": "选项1", "description": "..."}]
    
    # 来源
    source_agent: str
    
    # 可选字段（带默认值）
    allow_custom: bool = False     # 是否允许自定义回答
    source_discussion_id: Optional[str] = None
    
    # 阻塞设置
    blocking: bool = False         # 是否阻塞后续流程
    timeout_seconds: int = 300     # 超时时间
    
    # 状态
    status: DecisionStatus = DecisionStatus.PENDING
    selected_option: Optional[str] = None
    custom_answer: Optional[str] = None
    answered_at: Optional[str] = None
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "question_type": self.question_type.value,
            "priority": self.priority.value,
            "priority_label": self._get_priority_label(),
            "title": self.title,
            "description": self.description,
            "context": self.context,
            "options": self.options,
            "allow_custom": self.allow_custom,
            "source_agent": self.source_agent,
            "blocking": self.blocking,
            "status": self.status.value,
            "selected_option": self.selected_option,
            "custom_answer": self.custom_answer,
            "created_at": self.created_at,
            "answered_at": self.answered_at
        }
    
    def _get_priority_label(self) -> str:
        labels = {
            QuestionPriority.LOW: "低",
            QuestionPriority.MEDIUM: "中",
            QuestionPriority.HIGH: "高",
            QuestionPriority.CRITICAL: "紧急"
        }
        return labels.get(self.priority, "未知")


@dataclass
class DecisionRecord:
    """决策记录"""
    decision_id: str
    question_id: str
    novel_id: str
    chapter_id: Optional[str]
    
    selected_option: str
    custom_answer: Optional[str]
    impact_summary: str
    
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class AuthorDecisionSystem:
    """
    作者决策系统
    
    管理Agent向作者提出的问题：
    1. 收集需要作者决策的问题
    2. 按优先级排序展示
    3. 等待作者回答
    4. 将决策结果反馈给Agent
    """
    
    def __init__(self):
        self.pending_questions: Dict[str, AuthorQuestion] = {}
        self.answered_questions: Dict[str, AuthorQuestion] = {}
        self.decision_records: List[DecisionRecord] = []
        
        # 按小说组织问题
        self.novel_questions: Dict[str, List[str]] = defaultdict(list)
        
        # 决策回调
        self.decision_callbacks: Dict[str, List[callable]] = defaultdict(list)
    
    def create_question(
        self,
        novel_id: str,
        question_type: QuestionType,
        priority: QuestionPriority,
        title: str,
        description: str,
        options: List[Dict[str, Any]],
        source_agent: str,
        context: Dict[str, Any] = None,
        chapter_id: Optional[str] = None,
        blocking: bool = False,
        allow_custom: bool = False,
        timeout_seconds: int = 300
    ) -> str:
        """
        创建作者问题
        
        Returns:
            问题ID
        """
        question_id = f"q_{novel_id}_{datetime.now().timestamp()}"
        
        question = AuthorQuestion(
            question_id=question_id,
            question_type=question_type,
            priority=priority,
            title=title,
            description=description,
            context=context or {},
            options=options,
            allow_custom=allow_custom,
            source_agent=source_agent,
            blocking=blocking,
            timeout_seconds=timeout_seconds
        )
        
        self.pending_questions[question_id] = question
        self.novel_questions[novel_id].append(question_id)
        
        return question_id
    
    def submit_answer(
        self,
        question_id: str,
        selected_option: str,
        custom_answer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        提交作者回答
        
        Returns:
            决策结果和影响
        """
        question = self.pending_questions.get(question_id)
        
        if not question:
            return {"error": "问题不存在或已回答"}
        
        # 更新问题状态
        question.status = DecisionStatus.ANSWERED
        question.selected_option = selected_option
        question.custom_answer = custom_answer
        question.answered_at = datetime.now().isoformat()
        
        # 移动到已回答
        self.answered_questions[question_id] = question
        del self.pending_questions[question_id]
        
        # 创建决策记录
        decision = DecisionRecord(
            decision_id=f"dec_{question_id}",
            question_id=question_id,
            novel_id=self._get_novel_id_from_question(question_id),
            chapter_id=question.context.get("chapter_id"),
            selected_option=selected_option,
            custom_answer=custom_answer,
            impact_summary=self._generate_impact_summary(question, selected_option)
        )
        
        self.decision_records.append(decision)
        
        # 触发回调
        self._trigger_callbacks(question_id, decision)
        
        return {
            "success": True,
            "decision_id": decision.decision_id,
            "impact": decision.impact_summary,
            "next_steps": self._generate_next_steps(question, selected_option)
        }
    
    def _get_novel_id_from_question(self, question_id: str) -> str:
        """从问题ID获取小说ID"""
        # 简单解析
        parts = question_id.split("_")
        return parts[1] if len(parts) > 1 else "unknown"
    
    def _generate_impact_summary(
        self,
        question: AuthorQuestion,
        selected_option: str
    ) -> str:
        """生成决策影响摘要"""
        option_labels = {opt["id"]: opt["label"] for opt in question.options}
        selected_label = option_labels.get(selected_option, selected_option)
        
        impact_templates = {
            QuestionType.PLOT_DIRECTION: f"剧情将按'{selected_label}'方向发展",
            QuestionType.CHARACTER_ACTION: f"角色将执行'{selected_label}'",
            QuestionType.SETTING_DETAIL: f"设定采用'{selected_label}'",
            QuestionType.STYLE_PREFERENCE: f"写作风格偏向'{selected_label}'",
            QuestionType.CONFLICT_RESOLUTION: f"冲突将以'{selected_label}'方式解决",
            QuestionType.EMOTIONAL_TONE: f"情感基调定为'{selected_label}'"
        }
        
        return impact_templates.get(
            question.question_type,
            f"决策：{selected_label}"
        )
    
    def _generate_next_steps(
        self,
        question: AuthorQuestion,
        selected_option: str
    ) -> List[str]:
        """生成下一步建议"""
        steps = []
        
        if question.blocking:
            steps.append("继续之前暂停的写作流程")
        
        steps.append(f"Agent将根据您的选择'{selected_option}'继续工作")
        
        if question.question_type == QuestionType.PLOT_DIRECTION:
            steps.append("Planner将更新章节大纲")
            steps.append("Writer将按照新方向写作")
        
        return steps
    
    def get_pending_questions(
        self,
        novel_id: Optional[str] = None,
        priority: Optional[QuestionPriority] = None
    ) -> List[Dict[str, Any]]:
        """获取待回答的问题"""
        questions = []
        
        for qid, question in self.pending_questions.items():
            if novel_id and qid not in self.novel_questions.get(novel_id, []):
                continue
            
            if priority and question.priority != priority:
                continue
            
            questions.append(question.to_dict())
        
        # 按优先级排序
        priority_order = {
            QuestionPriority.CRITICAL: 0,
            QuestionPriority.HIGH: 1,
            QuestionPriority.MEDIUM: 2,
            QuestionPriority.LOW: 3
        }
        
        questions.sort(key=lambda q: priority_order.get(
            QuestionPriority(q["priority"]), 4
        ))
        
        return questions
    
    def get_question(self, question_id: str) -> Optional[Dict[str, Any]]:
        """获取问题详情"""
        question = self.pending_questions.get(question_id)
        if not question:
            question = self.answered_questions.get(question_id)
        
        return question.to_dict() if question else None
    
    def register_callback(self, question_id: str, callback: callable):
        """注册决策回调"""
        self.decision_callbacks[question_id].append(callback)
    
    def _trigger_callbacks(self, question_id: str, decision: DecisionRecord):
        """触发回调"""
        callbacks = self.decision_callbacks.get(question_id, [])
        for callback in callbacks:
            try:
                callback(decision)
            except Exception as e:
                print(f"回调执行失败: {e}")
        
        # 清理回调
        if question_id in self.decision_callbacks:
            del self.decision_callbacks[question_id]
    
    def get_decision_statistics(self, novel_id: Optional[str] = None) -> Dict[str, Any]:
        """获取决策统计"""
        records = self.decision_records
        
        if novel_id:
            records = [r for r in records if r.novel_id == novel_id]
        
        if not records:
            return {"message": "暂无决策记录"}
        
        # 按类型统计
        type_counts = defaultdict(int)
        for record in records:
            question = self.answered_questions.get(record.question_id)
            if question:
                type_counts[question.question_type.value] += 1
        
        return {
            "total_decisions": len(records),
            "by_type": dict(type_counts),
            "recent_decisions": [
                {
                    "decision_id": r.decision_id,
                    "selected": r.selected_option,
                    "impact": r.impact_summary,
                    "timestamp": r.timestamp
                }
                for r in records[-5:]
            ]
        }
    
    async def wait_for_decision(
        self,
        question_id: str,
        timeout: int = 300
    ) -> Optional[DecisionRecord]:
        """
        等待决策结果（异步）
        
        用于阻塞式流程
        """
        start_time = datetime.now()
        
        while True:
            # 检查是否已回答
            if question_id in self.answered_questions:
                question = self.answered_questions[question_id]
                return DecisionRecord(
                    decision_id=f"dec_{question_id}",
                    question_id=question_id,
                    novel_id=self._get_novel_id_from_question(question_id),
                    chapter_id=question.context.get("chapter_id"),
                    selected_option=question.selected_option,
                    custom_answer=question.custom_answer,
                    impact_summary=self._generate_impact_summary(
                        question, question.selected_option
                    )
                )
            
            # 检查超时
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > timeout:
                # 标记为超时
                if question_id in self.pending_questions:
                    self.pending_questions[question_id].status = DecisionStatus.TIMEOUT
                return None
            
            await asyncio.sleep(1)


# 全局实例
_decision_system: Optional[AuthorDecisionSystem] = None


def get_author_decision_system() -> AuthorDecisionSystem:
    """获取作者决策系统实例"""
    global _decision_system
    if _decision_system is None:
        _decision_system = AuthorDecisionSystem()
    return _decision_system
