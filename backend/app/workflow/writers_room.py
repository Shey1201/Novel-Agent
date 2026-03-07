"""
Writers Room - 自治讨论系统
实现 Agent 之间的自由讨论和共识达成
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.agents.base_agent import BaseAgent
from app.agents.consistency_agent import ConsistencyAgent
from app.workflow.facilitator import EnhancedFacilitator, create_facilitator


class MessageType(str, Enum):
    """消息类型"""
    PROPOSAL = "proposal"           # 议案
    SUGGESTION = "suggestion"       # 建议
    CRITIQUE = "critique"           # 批评
    CONSENSUS = "consensus"         # 共识
    INTERRUPTION = "interruption"   # 插话
    SUMMARY = "summary"             # 总结


class DiscussionStatus(str, Enum):
    """讨论状态"""
    ONGOING = "ongoing"
    REACHED = "reached"
    TIMEOUT = "timeout"
    STALEMATE = "stalemate"


@dataclass
class AgentParticipant:
    """讨论参与者"""
    agent_id: str
    agent_name: str
    agent_role: str
    agent_instance: BaseAgent
    personality: str = "neutral"    # sarcastic/strict/passionate/analytical
    proactivity: float = 0.5        # 主动性 0-1
    expertise_areas: List[str] = field(default_factory=list)
    last_spoke_at: Optional[datetime] = None
    message_count: int = 0


@dataclass
class AgentMessage:
    """Agent 消息"""
    id: str
    agent_id: str
    agent_name: str
    content: str
    message_type: MessageType
    timestamp: datetime
    internal_monologue: Optional[str] = None  # 心理活动
    references: List[Dict[str, Any]] = field(default_factory=list)
    reply_to: Optional[str] = None            # 回复哪条消息


@dataclass
class Proposal:
    """议案"""
    id: str
    title: str
    description: str
    proposed_by: str
    created_at: datetime
    status: str = "open"  # open/accepted/rejected


@dataclass
class DiscussionState:
    """讨论状态"""
    proposal: Proposal
    messages: List[AgentMessage] = field(default_factory=list)
    participants: List[AgentParticipant] = field(default_factory=list)
    consensus_score: float = 0.0
    proposed_changes: List[Dict[str, Any]] = field(default_factory=list)
    status: DiscussionStatus = DiscussionStatus.ONGOING
    round: int = 0
    max_rounds: int = 10
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_message(self, message: AgentMessage):
        """添加消息"""
        self.messages.append(message)
        # 更新参与者发言统计
        for p in self.participants:
            if p.agent_id == message.agent_id:
                p.last_spoke_at = message.timestamp
                p.message_count += 1
    
    def get_recent_messages(self, n: int = 5) -> List[AgentMessage]:
        """获取最近 n 条消息"""
        return self.messages[-n:]


class Facilitator:
    """
    讨论主持人 - 使用增强版 Facilitator
    保留此类以兼容现有代码，实际功能委托给 EnhancedFacilitator
    """
    
    def __init__(self, strategy: str = "balanced"):
        self._enhanced = create_facilitator(strategy)
    
    def select_next_speaker(
        self, 
        state: DiscussionState,
        story_bible: Dict[str, Any]
    ) -> Optional[AgentParticipant]:
        """
        选择下一个发言者（使用增强版）
        """
        speaker, reason = self._enhanced.select_next_speaker(
            state.participants,
            state.messages,
            story_bible,
            state.round
        )
        return speaker
    
    def evaluate_consensus(self, state: DiscussionState) -> Dict[str, Any]:
        """
        评估共识度（使用增强版）
        """
        return self._enhanced.evaluate_consensus(
            state.messages,
            state.round,
            state.max_rounds
        )
    
    def should_intervene(self, state: DiscussionState) -> Dict[str, Any]:
        """
        判断是否需要人工干预
        """
        should_intervene, reason = self._enhanced.should_intervene(state.messages)
        return {
            "should_intervene": should_intervene,
            "reason": reason
        }
    
    def get_discussion_stats(self, state: DiscussionState) -> Dict[str, Any]:
        """
        获取讨论统计信息
        """
        return self._enhanced.get_discussion_stats(state.messages, state.participants)
    
    def set_strategy(self, strategy: str):
        """
        设置发言策略
        """
        self._enhanced = create_facilitator(strategy)


class WritersRoom:
    """
    Writers Room - Agent 讨论房间
    """
    
    def __init__(self):
        self.discussions: Dict[str, DiscussionState] = {}
        self.facilitator = Facilitator()
        self.message_callbacks: List[Callable] = []
    
    def register_callback(self, callback: Callable):
        """注册消息回调（用于实时推送到前端）"""
        self.message_callbacks.append(callback)
    
    async def create_discussion(
        self,
        proposal_title: str,
        proposal_description: str,
        proposed_by: str,
        participants: List[AgentParticipant],
        max_rounds: int = 10
    ) -> str:
        """
        创建新讨论
        
        Returns:
            discussion_id
        """
        discussion_id = f"disc_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        proposal = Proposal(
            id=f"prop_{discussion_id}",
            title=proposal_title,
            description=proposal_description,
            proposed_by=proposed_by,
            created_at=datetime.now()
        )
        
        state = DiscussionState(
            proposal=proposal,
            participants=participants,
            max_rounds=max_rounds
        )
        
        self.discussions[discussion_id] = state
        
        # 添加初始议案消息
        initial_message = AgentMessage(
            id=f"msg_{discussion_id}_0",
            agent_id=proposed_by,
            agent_name="System",
            content=f"议案: {proposal_title}\n{proposal_description}",
            message_type=MessageType.PROPOSAL,
            timestamp=datetime.now()
        )
        state.add_message(initial_message)
        
        await self._notify_callbacks(discussion_id, initial_message)
        
        return discussion_id
    
    async def run_discussion_round(
        self,
        discussion_id: str,
        story_bible: Dict[str, Any]
    ) -> bool:
        """
        运行一轮讨论
        
        Returns:
            是否继续讨论
        """
        state = self.discussions.get(discussion_id)
        if not state:
            return False
        
        if state.status != DiscussionStatus.ONGOING:
            return False
        
        state.round += 1
        
        # 检查是否需要人工干预
        intervene_result = self.facilitator.should_intervene(state)
        if intervene_result.get("should_intervene"):
            # 发送干预提醒
            intervene_message = AgentMessage(
                id=f"msg_{discussion_id}_intervene",
                agent_id="system",
                agent_name="系统",
                content=f"⚠️ {intervene_result.get('reason', '建议人工干预')}",
                message_type=MessageType.INTERRUPTION,
                timestamp=datetime.now()
            )
            state.add_message(intervene_message)
            await self._notify_callbacks(discussion_id, intervene_message)
        
        # 选择发言者
        speaker = self.facilitator.select_next_speaker(state, story_bible)
        if not speaker:
            return False
        
        # 生成发言内容
        message = await self._generate_message(speaker, state, story_bible)
        
        # 添加消息
        state.add_message(message)
        await self._notify_callbacks(discussion_id, message)
        
        # 评估共识
        consensus_result = self.facilitator.evaluate_consensus(state)
        state.consensus_score = consensus_result["consensus_score"]
        
        if consensus_result["consensus_reached"]:
            state.status = DiscussionStatus.REACHED
            # 生成共识总结
            await self._generate_consensus_summary(state)
            return False
        
        if state.round >= state.max_rounds:
            state.status = DiscussionStatus.TIMEOUT
            return False
        
        return True
    
    async def _generate_message(
        self,
        speaker: AgentParticipant,
        state: DiscussionState,
        story_bible: Dict[str, Any]
    ) -> AgentMessage:
        """生成 Agent 发言"""
        
        # 构建上下文
        recent_messages = state.get_recent_messages(5)
        context = self._build_discussion_context(state, recent_messages, story_bible)
        
        # 构建提示
        prompt = f"""你是一位{speaker.agent_role}，正在参与 Writers Room 讨论。

你的性格: {speaker.personality}
你的专长: {', '.join(speaker.expertise_areas)}

[当前议案]
{state.proposal.title}
{state.proposal.description}

[最近讨论]
{context}

[故事设定]
{json.dumps(story_bible, ensure_ascii=False)[:1000]}

请发表你的看法：
1. 分析当前方案的优缺点
2. 提出具体建议或改进意见
3. 如果同意，明确表示支持

请用中文回复，保持专业且有建设性。"""
        
        # 调用 Agent
        response = speaker.agent_instance.llm.invoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)
        
        # 确定消息类型
        message_type = self._determine_message_type(content)
        
        # 生成心理活动（可选）
        internal_monologue = None
        if speaker.proactivity > 0.7:  # 主动性高的 Agent 显示思考过程
            mono_prompt = f"""基于以上内容，简要说明你的思考过程（50字以内）：
{content[:200]}"""
            try:
                mono_response = speaker.agent_instance.llm.invoke(mono_prompt)
                internal_monologue = mono_response.content if hasattr(mono_response, 'content') else None
            except:
                pass
        
        return AgentMessage(
            id=f"msg_{state.proposal.id}_{len(state.messages)}",
            agent_id=speaker.agent_id,
            agent_name=speaker.agent_name,
            content=content,
            message_type=message_type,
            timestamp=datetime.now(),
            internal_monologue=internal_monologue,
            reply_to=recent_messages[-1].id if recent_messages else None
        )
    
    def _build_discussion_context(
        self,
        state: DiscussionState,
        recent_messages: List[AgentMessage],
        story_bible: Dict[str, Any]
    ) -> str:
        """构建讨论上下文"""
        context_parts = []
        for msg in recent_messages:
            context_parts.append(f"{msg.agent_name}: {msg.content[:200]}...")
        return "\n".join(context_parts)
    
    def _determine_message_type(self, content: str) -> MessageType:
        """确定消息类型"""
        agreement_keywords = ["同意", "赞成", "支持", "没问题", "可以", "达成共识"]
        critique_keywords = ["但是", "不过", "问题", "缺点", "不足", "建议改进"]
        
        if any(kw in content for kw in agreement_keywords):
            return MessageType.CONSENSUS
        elif any(kw in content for kw in critique_keywords):
            return MessageType.CRITIQUE
        else:
            return MessageType.SUGGESTION
    
    async def _generate_consensus_summary(self, state: DiscussionState):
        """生成共识总结"""
        # 使用最后一个 Agent 生成总结
        if state.participants:
            summarizer = state.participants[0]
            
            all_messages = "\n".join([
                f"{m.agent_name}: {m.content[:150]}"
                for m in state.messages
            ])
            
            prompt = f"""基于以下讨论，总结达成的共识：

[议案]
{state.proposal.title}

[讨论记录]
{all_messages}

请总结：
1. 最终决定的方案
2. 关键要点
3. 待执行的行动"""
            
            try:
                response = summarizer.agent_instance.llm.invoke(prompt)
                summary_content = response.content if hasattr(response, 'content') else "讨论已达成共识"
                
                summary_message = AgentMessage(
                    id=f"msg_{state.proposal.id}_summary",
                    agent_id="system",
                    agent_name="讨论总结",
                    content=summary_content,
                    message_type=MessageType.SUMMARY,
                    timestamp=datetime.now()
                )
                state.add_message(summary_message)
            except:
                pass
    
    async def _notify_callbacks(self, discussion_id: str, message: AgentMessage):
        """通知所有回调"""
        for callback in self.message_callbacks:
            try:
                await callback(discussion_id, message)
            except:
                pass
    
    def get_discussion(self, discussion_id: str) -> Optional[DiscussionState]:
        """获取讨论状态"""
        return self.discussions.get(discussion_id)
    
    def get_discussion_stats(self, discussion_id: str) -> Dict[str, Any]:
        """获取讨论统计信息"""
        state = self.discussions.get(discussion_id)
        if not state:
            return {"error": "Discussion not found"}
        
        return self.facilitator.get_discussion_stats(state)
    
    def set_facilitator_strategy(self, discussion_id: str, strategy: str):
        """
        设置讨论调度策略
        
        Args:
            strategy: round_robin/expertise_based/proactivity_based/balanced/topic_driven
        """
        state = self.discussions.get(discussion_id)
        if state:
            self.facilitator.set_strategy(strategy)
            return True
        return False
    
    def human_intervene(
        self,
        discussion_id: str,
        message: str,
        action: str = "comment"  # comment/accept/reject/end
    ):
        """人工干预讨论"""
        state = self.discussions.get(discussion_id)
        if not state:
            return
        
        human_message = AgentMessage(
            id=f"msg_{discussion_id}_human",
            agent_id="human",
            agent_name="作者",
            content=f"[{action}] {message}",
            message_type=MessageType.INTERRUPTION,
            timestamp=datetime.now()
        )
        
        state.add_message(human_message)
        
        if action == "accept":
            state.status = DiscussionStatus.REACHED
        elif action == "end":
            state.status = DiscussionStatus.STALEMATE


# 全局 Writers Room 实例
writers_room = WritersRoom()
