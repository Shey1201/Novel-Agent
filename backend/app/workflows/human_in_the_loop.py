"""
Human-in-the-loop System - 人工干预系统
提供增强的中断节点和人工审核功能
"""

from typing import Dict, Any, Optional, List, Callable, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import json


class InterruptType(Enum):
    """中断类型"""
    PLAN_REVIEW = "plan_review"           # 大纲审核
    CONTENT_REVIEW = "content_review"     # 内容审核
    QUALITY_GATE = "quality_gate"         # 质量关卡
    CONSISTENCY_CHECK = "consistency_check"  # 一致性检查
    PLOT_DECISION = "plot_decision"       # 剧情决策点
    EMERGENCY_STOP = "emergency_stop"     # 紧急停止


class HumanDecision(Enum):
    """人类决策"""
    APPROVE = "approve"           # 批准继续
    REJECT = "reject"             # 拒绝，重新生成
    MODIFY = "modify"             # 修改后继续
    SKIP = "skip"                 # 跳过此步骤
    STOP = "stop"                 # 停止工作流
    ASK_AGAIN = "ask_again"       # 要求重新解释


@dataclass
class InterruptPoint:
    """中断点定义"""
    id: str
    type: InterruptType
    title: str
    description: str
    content: Any                        # 需要审核的内容
    context: Dict[str, Any] = field(default_factory=dict)
    options: List[str] = field(default_factory=list)
    timeout: Optional[int] = None       # 超时时间（秒）
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "context": self.context,
            "options": self.options,
            "timeout": self.timeout,
            "created_at": self.created_at
        }


@dataclass
class HumanResponse:
    """人类响应"""
    interrupt_id: str
    decision: HumanDecision
    feedback: str = ""                  # 详细反馈
    modified_content: Optional[str] = None  # 修改后的内容
    responded_at: str = field(default_factory=lambda: datetime.now().isoformat())


class InterruptManager:
    """
    中断管理器
    
    管理工作流中的中断点
    """
    
    def __init__(self):
        self.pending_interrupts: Dict[str, InterruptPoint] = {}
        self.responses: Dict[str, HumanResponse] = {}
        self.waiting_events: Dict[str, asyncio.Event] = {}
        self.history: List[Dict[str, Any]] = []
    
    async def create_interrupt(
        self,
        interrupt_type: InterruptType,
        title: str,
        description: str,
        content: Any,
        context: Optional[Dict[str, Any]] = None,
        options: Optional[List[str]] = None,
        timeout: Optional[int] = None
    ) -> InterruptPoint:
        """
        创建中断点
        
        Args:
            interrupt_type: 中断类型
            title: 标题
            description: 描述
            content: 需要审核的内容
            context: 上下文信息
            options: 可选操作
            timeout: 超时时间
            
        Returns:
            中断点对象
        """
        interrupt_id = f"interrupt_{datetime.now().timestamp()}"
        
        interrupt = InterruptPoint(
            id=interrupt_id,
            type=interrupt_type,
            title=title,
            description=description,
            content=content,
            context=context or {},
            options=options or ["approve", "reject", "modify"],
            timeout=timeout
        )
        
        self.pending_interrupts[interrupt_id] = interrupt
        self.waiting_events[interrupt_id] = asyncio.Event()
        
        return interrupt
    
    async def wait_for_response(
        self,
        interrupt_id: str,
        timeout: Optional[int] = None
    ) -> Optional[HumanResponse]:
        """
        等待人类响应
        
        Args:
            interrupt_id: 中断点ID
            timeout: 超时时间
            
        Returns:
            人类响应，超时返回None
        """
        event = self.waiting_events.get(interrupt_id)
        if not event:
            return None
        
        try:
            await asyncio.wait_for(
                event.wait(),
                timeout=timeout or 300  # 默认5分钟超时
            )
            return self.responses.get(interrupt_id)
        except asyncio.TimeoutError:
            return None
    
    def submit_response(self, response: HumanResponse) -> bool:
        """
        提交人类响应
        
        Args:
            response: 响应对象
            
        Returns:
            是否成功
        """
        interrupt_id = response.interrupt_id
        
        if interrupt_id not in self.pending_interrupts:
            return False
        
        self.responses[interrupt_id] = response
        
        # 记录历史
        self.history.append({
            "interrupt": self.pending_interrupts[interrupt_id].to_dict(),
            "response": {
                "decision": response.decision.value,
                "feedback": response.feedback,
                "responded_at": response.responded_at
            }
        })
        
        # 触发事件
        event = self.waiting_events.get(interrupt_id)
        if event:
            event.set()
        
        return True
    
    def get_pending_interrupts(self) -> List[InterruptPoint]:
        """获取所有待处理的中断"""
        return list(self.pending_interrupts.values())
    
    def get_interrupt(self, interrupt_id: str) -> Optional[InterruptPoint]:
        """获取特定中断"""
        return self.pending_interrupts.get(interrupt_id)
    
    def clear_interrupt(self, interrupt_id: str):
        """清除中断"""
        self.pending_interrupts.pop(interrupt_id, None)
        self.responses.pop(interrupt_id, None)
        self.waiting_events.pop(interrupt_id, None)
    
    def get_history(
        self,
        interrupt_type: Optional[InterruptType] = None
    ) -> List[Dict[str, Any]]:
        """获取历史记录"""
        if interrupt_type:
            return [
                h for h in self.history
                if h["interrupt"]["type"] == interrupt_type.value
            ]
        return self.history


class HumanInTheLoop:
    """
    Human-in-the-loop 主类
    
    提供便捷的人工干预接口
    """
    
    def __init__(self):
        self.interrupt_manager = InterruptManager()
        self.decision_handlers: Dict[HumanDecision, Callable] = {}
    
    async def request_approval(
        self,
        content: Any,
        title: str = "需要您的审核",
        description: str = "请审核以下内容",
        context: Optional[Dict[str, Any]] = None,
        interrupt_type: InterruptType = InterruptType.CONTENT_REVIEW
    ) -> Dict[str, Any]:
        """
        请求人工批准
        
        Args:
            content: 需要审核的内容
            title: 标题
            description: 描述
            context: 上下文
            interrupt_type: 中断类型
            
        Returns:
            {
                "approved": bool,
                "feedback": str,
                "modified_content": str,
                "decision": str
            }
        """
        interrupt = await self.interrupt_manager.create_interrupt(
            interrupt_type=interrupt_type,
            title=title,
            description=description,
            content=content,
            context=context,
            options=["approve", "reject", "modify", "stop"]
        )
        
        # 等待响应
        response = await self.interrupt_manager.wait_for_response(interrupt.id)
        
        if not response:
            # 超时，默认批准
            return {
                "approved": True,
                "feedback": "超时自动批准",
                "modified_content": None,
                "decision": "approve"
            }
        
        # 处理响应
        result = {
            "approved": response.decision == HumanDecision.APPROVE,
            "feedback": response.feedback,
            "modified_content": response.modified_content,
            "decision": response.decision.value
        }
        
        # 清理
        self.interrupt_manager.clear_interrupt(interrupt.id)
        
        return result
    
    async def request_decision(
        self,
        question: str,
        options: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        请求决策
        
        Args:
            question: 问题
            options: 选项列表
            context: 上下文
            
        Returns:
            选择的选项
        """
        interrupt = await self.interrupt_manager.create_interrupt(
            interrupt_type=InterruptType.PLOT_DECISION,
            title="需要您的决策",
            description=question,
            content=options,
            context=context,
            options=options
        )
        
        response = await self.interrupt_manager.wait_for_response(interrupt.id)
        
        decision = ""
        if response and response.feedback in options:
            decision = response.feedback
        elif options:
            decision = options[0]  # 默认选第一个
        
        self.interrupt_manager.clear_interrupt(interrupt.id)
        
        return decision
    
    def submit_human_feedback(
        self,
        interrupt_id: str,
        decision: str,
        feedback: str = "",
        modified_content: Optional[str] = None
    ) -> bool:
        """
        提交人工反馈（供前端调用）
        
        Args:
            interrupt_id: 中断点ID
            decision: 决策（approve/reject/modify/stop）
            feedback: 详细反馈
            modified_content: 修改后的内容
            
        Returns:
            是否成功
        """
        try:
            human_decision = HumanDecision(decision)
        except ValueError:
            human_decision = HumanDecision.APPROVE
        
        response = HumanResponse(
            interrupt_id=interrupt_id,
            decision=human_decision,
            feedback=feedback,
            modified_content=modified_content
        )
        
        return self.interrupt_manager.submit_response(response)
    
    def get_pending_reviews(self) -> List[Dict[str, Any]]:
        """获取待审核列表（供前端显示）"""
        interrupts = self.interrupt_manager.get_pending_interrupts()
        return [i.to_dict() for i in interrupts]


# 增强的 Human Review Node 函数
async def enhanced_human_review_node(
    state: Dict[str, Any],
    hitl: HumanInTheLoop
) -> Dict[str, Any]:
    """
    增强的人工审核节点
    
    Args:
        state: 工作流状态
        hitl: Human-in-the-loop 实例
        
    Returns:
        更新后的状态
    """
    plan_text = state.get("plan_text", "")
    
    # 请求人工审核
    result = await hitl.request_approval(
        content=plan_text,
        title="大纲审核",
        description="请审核 AI 生成的大纲，确认后将继续写作",
        context={
            "chapter_id": state.get("chapter_id"),
            "novel_id": state.get("novel_id"),
            "previous_chapters": state.get("previous_chapters", [])
        },
        interrupt_type=InterruptType.PLAN_REVIEW
    )
    
    # 根据决策更新状态
    if result["decision"] == "stop":
        return {
            **state,
            "status": "stopped",
            "human_approved": False,
            "human_feedback": result.get("feedback", "用户停止")
        }
    elif result["decision"] == "modify" and result.get("modified_content"):
        return {
            **state,
            "plan_text": result["modified_content"],
            "human_approved": True,
            "human_feedback": result.get("feedback", "")
        }
    else:
        return {
            **state,
            "human_approved": result["approved"],
            "human_feedback": result.get("feedback", ""),
            "status": "approved" if result["approved"] else "rejected"
        }


# 质量关卡中断
async def quality_gate_interrupt(
    state: Dict[str, Any],
    hitl: HumanInTheLoop,
    quality_score: float
) -> Dict[str, Any]:
    """
    质量关卡中断
    
    当质量分数低于阈值时触发人工审核
    """
    if quality_score >= 0.7:
        return {**state, "quality_approved": True}
    
    edited_text = state.get("edited_text", "")
    critic_feedback = state.get("critic_result", {}).get("feedback", "")
    
    result = await hitl.request_approval(
        content={
            "text": edited_text[:1000] + "...",
            "quality_score": quality_score,
            "feedback": critic_feedback
        },
        title="质量审核",
        description=f"质量评分 {quality_score:.2f} 低于阈值，请审核",
        context={"quality_score": quality_score},
        interrupt_type=InterruptType.QUALITY_GATE
    )
    
    return {
        **state,
        "quality_approved": result["approved"],
        "human_override": result["decision"] == "approve" and quality_score < 0.6
    }


# 全局 HITL 实例
_hitl_instance: Optional[HumanInTheLoop] = None


def get_hitl() -> HumanInTheLoop:
    """获取 HITL 实例"""
    global _hitl_instance
    if _hitl_instance is None:
        _hitl_instance = HumanInTheLoop()
    return _hitl_instance


# 便捷函数
async def request_human_approval(
    content: Any,
    title: str = "需要您的审核",
    description: str = "请审核以下内容"
) -> Dict[str, Any]:
    """请求人工批准"""
    hitl = get_hitl()
    return await hitl.request_approval(content, title, description)


def submit_feedback(
    interrupt_id: str,
    decision: str,
    feedback: str = "",
    modified_content: Optional[str] = None
) -> bool:
    """提交反馈"""
    hitl = get_hitl()
    return hitl.submit_human_feedback(interrupt_id, decision, feedback, modified_content)


def get_pending_reviews() -> List[Dict[str, Any]]:
    """获取待审核列表"""
    hitl = get_hitl()
    return hitl.get_pending_reviews()
