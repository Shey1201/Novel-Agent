"""
Agent Discussion Engine - Agent自我讨论引擎
支持多轮讨论和共识机制
"""

from typing import Dict, Any, Optional, List, Tuple, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import json


class DiscussionRound(Enum):
    """讨论轮次"""
    PLANNING = "planning"           # Planner 提出计划
    CONFLICT_ANALYSIS = "conflict"  # Conflict 分析冲突
    WRITING_STRATEGY = "writing"    # Writer 提出写作策略
    EDITING = "editing"             # Editor 评估结构
    READER_FEEDBACK = "reader"      # Reader 模拟读者反馈
    AUTHOR_INPUT = "author"         # 作者输入
    CONSENSUS = "consensus"         # 达成共识


class AgentPersonality(Enum):
    """Agent立场/性格"""
    STRUCTURE = "structure"     # 结构派 - Planner
    DRAMA = "drama"            # 戏剧派 - Conflict
    LITERARY = "literary"      # 文学派 - Writer
    LOGIC = "logic"            # 逻辑派 - Editor
    READER = "reader"          # 爽感派 - ReaderProxy


class ConsensusStatus(Enum):
    """共识状态"""
    REACHED = "reached"         # 已达成共识
    PARTIAL = "partial"         # 部分共识
    DISAGREEMENT = "disagreement"  # 存在分歧
    NEEDS_AUTHOR = "needs_author"  # 需要作者决策


@dataclass
class AgentOpinion:
    """Agent意见"""
    agent_type: str
    personality: AgentPersonality
    opinion: str
    position: str  # support/oppose/neutral
    confidence: float
    key_points: List[str]
    concerns: List[str]
    suggestions: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DiscussionMessage:
    """讨论消息"""
    message_id: str
    round: DiscussionRound
    agent_type: str
    personality: AgentPersonality
    content: str
    reply_to: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ConsensusResult:
    """共识结果"""
    consensus_id: str
    status: ConsensusStatus
    consensus_score: float  # 0-1
    agreed_points: List[str]
    disputed_points: List[str]
    final_decision: str
    requires_author_decision: bool
    author_question: Optional[Dict[str, Any]] = None
    participating_agents: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "consensus_id": self.consensus_id,
            "status": self.status.value,
            "consensus_score": round(self.consensus_score, 2),
            "agreed_points": self.agreed_points,
            "disputed_points": self.disputed_points,
            "final_decision": self.final_decision,
            "requires_author_decision": self.requires_author_decision,
            "author_question": self.author_question,
            "participating_agents": self.participating_agents,
            "timestamp": self.timestamp
        }


@dataclass
class DiscussionContext:
    """讨论上下文"""
    novel_id: str
    chapter_id: str
    topic: str
    current_draft: Optional[str] = None
    previous_discussion: List[Dict[str, Any]] = field(default_factory=list)
    author_preferences: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)


class AgentDiscussionEngine:
    """
    Agent讨论引擎
    
    支持多轮讨论：
    1. Planner 提出章节计划
    2. Conflict 分析冲突
    3. Writer 提出写作策略
    4. Editor 评估结构
    5. Reader 模拟读者反馈
    6. 达成共识或向作者提问
    """
    
    def __init__(self):
        self.discussions: Dict[str, List[DiscussionMessage]] = {}
        self.opinions: Dict[str, List[AgentOpinion]] = {}
        self.consensus_results: Dict[str, ConsensusResult] = {}
        self.max_rounds = 3
        self.consensus_threshold = 0.7
        
        # Agent性格配置
        self.agent_personalities = {
            "planner": AgentPersonality.STRUCTURE,
            "conflict": AgentPersonality.DRAMA,
            "writer": AgentPersonality.LITERARY,
            "editor": AgentPersonality.LOGIC,
            "reader": AgentPersonality.READER
        }
    
    async def start_discussion(
        self,
        context: DiscussionContext,
        max_rounds: int = 3
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        开始讨论
        
        Yields:
            每轮讨论的消息和中间结果
        """
        discussion_id = f"disc_{datetime.now().timestamp()}"
        self.discussions[discussion_id] = []
        self.opinions[discussion_id] = []
        
        rounds = [
            DiscussionRound.PLANNING,
            DiscussionRound.CONFLICT_ANALYSIS,
            DiscussionRound.WRITING_STRATEGY,
            DiscussionRound.EDITING,
            DiscussionRound.READER_FEEDBACK
        ]
        
        for round_num, current_round in enumerate(rounds[:max_rounds]):
            # 执行当前轮次
            message = await self._execute_round(
                discussion_id,
                current_round,
                context,
                round_num
            )
            
            yield {
                "type": "message",
                "round": current_round.value,
                "message": {
                    "agent_type": message.agent_type,
                    "personality": message.personality.value,
                    "content": message.content
                }
            }
            
            # 检查是否达成共识
            if round_num >= 2:  # 至少进行3轮后检查
                consensus = self._calculate_consensus(discussion_id)
                
                yield {
                    "type": "consensus_check",
                    "consensus_score": consensus["score"],
                    "status": consensus["status"]
                }
                
                if consensus["score"] >= self.consensus_threshold:
                    final_consensus = self._finalize_consensus(
                        discussion_id, context, consensus
                    )
                    self.consensus_results[discussion_id] = final_consensus
                    
                    yield {
                        "type": "final_consensus",
                        "consensus": final_consensus.to_dict()
                    }
                    return
        
        # 达到最大轮数，生成最终共识
        final_consensus = self._finalize_consensus(
            discussion_id, context, self._calculate_consensus(discussion_id)
        )
        self.consensus_results[discussion_id] = final_consensus
        
        yield {
            "type": "final_consensus",
            "consensus": final_consensus.to_dict()
        }
    
    async def _execute_round(
        self,
        discussion_id: str,
        round_type: DiscussionRound,
        context: DiscussionContext,
        round_num: int
    ) -> DiscussionMessage:
        """执行单轮讨论"""
        
        agent_mapping = {
            DiscussionRound.PLANNING: "planner",
            DiscussionRound.CONFLICT_ANALYSIS: "conflict",
            DiscussionRound.WRITING_STRATEGY: "writer",
            DiscussionRound.EDITING: "editor",
            DiscussionRound.READER_FEEDBACK: "reader"
        }
        
        agent_type = agent_mapping.get(round_type, "planner")
        personality = self.agent_personalities.get(agent_type, AgentPersonality.STRUCTURE)
        
        # 生成Agent发言内容
        content = await self._generate_agent_response(
            agent_type,
            personality,
            round_type,
            context,
            self.discussions[discussion_id]
        )
        
        # 提取意见
        opinion = self._extract_opinion(agent_type, personality, content)
        self.opinions[discussion_id].append(opinion)
        
        # 创建消息
        message = DiscussionMessage(
            message_id=f"msg_{discussion_id}_{round_num}",
            round=round_type,
            agent_type=agent_type,
            personality=personality,
            content=content
        )
        
        self.discussions[discussion_id].append(message)
        
        return message
    
    async def _generate_agent_response(
        self,
        agent_type: str,
        personality: AgentPersonality,
        round_type: DiscussionRound,
        context: DiscussionContext,
        previous_messages: List[DiscussionMessage]
    ) -> str:
        """生成Agent响应内容"""
        
        # 基于Agent性格和轮次生成内容
        templates = {
            ("planner", DiscussionRound.PLANNING): [
                "建议本章安排{topic}，这样可以推进主线剧情。",
                "从结构角度，本章应该重点描写{topic}。",
                "我规划本章目标：{topic}，预计字数控制在{word_count}字。"
            ],
            ("conflict", DiscussionRound.CONFLICT_ANALYSIS): [
                "这样会提前推进主线，可能失去悬念。",
                "剧情推进过快，读者可能跟不上。",
                "冲突设计可以更有张力，建议加入反转。"
            ],
            ("writer", DiscussionRound.WRITING_STRATEGY): [
                "可以加入误导线索，增加悬疑感。",
                "建议用细腻的心理描写来展现角色。",
                "这个场景适合用快节奏的叙述方式。"
            ],
            ("editor", DiscussionRound.EDITING): [
                "建议结尾加入悬念，吸引读者继续。",
                "结构上需要更强的起承转合。",
                "节奏控制很好，但中段略显拖沓。"
            ],
            ("reader", DiscussionRound.READER_FEEDBACK): [
                "读者更喜欢反转，建议增加意外元素。",
                "这个情节很有吸引力，会抓住读者。",
                "从读者角度，这里需要更多情感共鸣。"
            ]
        }
        
        import random
        template_list = templates.get((agent_type, round_type), ["继续推进剧情。"])
        template = random.choice(template_list)
        
        # 填充变量
        content = template.format(
            topic=context.topic,
            word_count=context.constraints.get("target_word_count", 3000)
        )
        
        # 如果有之前的消息，添加回应
        if previous_messages:
            last_message = previous_messages[-1]
            responses = {
                AgentPersonality.STRUCTURE: f"我认同{last_message.agent_type}的观点，",
                AgentPersonality.DRAMA: f"{last_message.agent_type}说得有道理，但我认为",
                AgentPersonality.LITERARY: f"从文学性角度，{last_message.agent_type}的想法",
                AgentPersonality.LOGIC: f"逻辑上{last_message.agent_type}的提议",
                AgentPersonality.READER: f"读者可能会觉得{last_message.agent_type}的方案"
            }
            
            response_prefix = responses.get(personality, "")
            if response_prefix and random.random() > 0.5:
                content = response_prefix + content[0].lower() + content[1:]
        
        return content
    
    def _extract_opinion(
        self,
        agent_type: str,
        personality: AgentPersonality,
        content: str
    ) -> AgentOpinion:
        """从内容中提取结构化意见"""
        
        # 分析立场
        position = "neutral"
        if any(word in content for word in ["建议", "应该", "可以"]):
            position = "support"
        elif any(word in content for word in ["但是", "不过", "可能"]):
            position = "neutral"
        elif any(word in content for word in ["反对", "不行", "错误"]):
            position = "oppose"
        
        # 提取要点
        key_points = []
        if "结构" in content or "规划" in content:
            key_points.append("关注结构")
        if "冲突" in content or "张力" in content:
            key_points.append("强调冲突")
        if "描写" in content or "细节" in content:
            key_points.append("注重描写")
        if "读者" in content or "吸引" in content:
            key_points.append("读者导向")
        
        # 提取担忧
        concerns = []
        if "过快" in content or "提前" in content:
            concerns.append("节奏过快")
        if "拖沓" in content or "缓慢" in content:
            concerns.append("节奏拖沓")
        
        # 提取建议
        suggestions = []
        if "加入" in content:
            suggestions.append("增加新元素")
        if "控制" in content:
            suggestions.append("控制节奏")
        
        return AgentOpinion(
            agent_type=agent_type,
            personality=personality,
            opinion=content,
            position=position,
            confidence=0.7 + (0.2 if position == "support" else 0),
            key_points=key_points,
            concerns=concerns,
            suggestions=suggestions
        )
    
    def _calculate_consensus(self, discussion_id: str) -> Dict[str, Any]:
        """计算共识度"""
        opinions = self.opinions.get(discussion_id, [])
        
        if len(opinions) < 2:
            return {"score": 0, "status": "insufficient_data"}
        
        # 分析立场一致性
        positions = [o.position for o in opinions]
        support_count = positions.count("support")
        oppose_count = positions.count("oppose")
        neutral_count = positions.count("neutral")
        
        # 计算共识分数
        total = len(positions)
        if total == 0:
            return {"score": 0, "status": "no_opinions"}
        
        # 如果大多数支持，共识度高
        if support_count / total >= 0.6:
            score = 0.7 + (support_count / total) * 0.3
            status = ConsensusStatus.REACHED
        # 如果有明显分歧
        elif oppose_count >= 2:
            score = 0.3
            status = ConsensusStatus.DISAGREEMENT
        # 部分共识
        else:
            score = 0.5 + (support_count / total) * 0.2
            status = ConsensusStatus.PARTIAL
        
        # 收集一致和不一致的观点
        agreed_points = []
        disputed_points = []
        
        all_key_points = []
        for op in opinions:
            all_key_points.extend(op.key_points)
        
        from collections import Counter
        point_counts = Counter(all_key_points)
        
        for point, count in point_counts.items():
            if count >= len(opinions) * 0.6:
                agreed_points.append(point)
            elif count <= len(opinions) * 0.3:
                disputed_points.append(point)
        
        return {
            "score": score,
            "status": status.value,
            "agreed_points": agreed_points,
            "disputed_points": disputed_points,
            "support_ratio": support_count / total,
            "oppose_ratio": oppose_count / total
        }
    
    def _finalize_consensus(
        self,
        discussion_id: str,
        context: DiscussionContext,
        consensus_data: Dict[str, Any]
    ) -> ConsensusResult:
        """生成最终共识结果"""
        
        opinions = self.opinions.get(discussion_id, [])
        score = consensus_data.get("score", 0)
        
        # 确定最终决策
        if score >= self.consensus_threshold:
            final_decision = f"继续按讨论结果推进：{context.topic}"
            requires_author = False
            author_question = None
            status = ConsensusStatus.REACHED
        elif score >= 0.4:
            final_decision = "存在分歧，建议作者选择方向"
            requires_author = True
            status = ConsensusStatus.NEEDS_AUTHOR
            
            # 生成作者问题
            disputed = consensus_data.get("disputed_points", [])
            author_question = {
                "question": f"关于{context.topic}，Agent们存在分歧",
                "options": [
                    "按Planner方案：注重结构推进",
                    "按Conflict方案：强化戏剧冲突",
                    "按Writer方案：侧重文学描写",
                    "需要更多讨论"
                ],
                "context": {
                    "agreed_points": consensus_data.get("agreed_points", []),
                    "disputed_points": disputed
                },
                "importance": "high" if score < 0.5 else "medium",
                "blocking": score < 0.5
            }
        else:
            final_decision = "分歧严重，需要作者明确指导"
            requires_author = True
            status = ConsensusStatus.DISAGREEMENT
            
            author_question = {
                "question": f"关于{context.topic}，Agent们无法达成共识",
                "options": [
                    "优先剧情推进",
                    "优先角色塑造",
                    "优先文学性",
                    "暂停讨论，等待作者详细指示"
                ],
                "importance": "high",
                "blocking": True
            }
        
        return ConsensusResult(
            consensus_id=f"consensus_{discussion_id}",
            status=status,
            consensus_score=score,
            agreed_points=consensus_data.get("agreed_points", []),
            disputed_points=consensus_data.get("disputed_points", []),
            final_decision=final_decision,
            requires_author_decision=requires_author,
            author_question=author_question,
            participating_agents=list(set(o.agent_type for o in opinions))
        )
    
    def get_discussion_history(self, discussion_id: str) -> List[Dict[str, Any]]:
        """获取讨论历史"""
        messages = self.discussions.get(discussion_id, [])
        return [
            {
                "round": msg.round.value,
                "agent_type": msg.agent_type,
                "personality": msg.personality.value,
                "content": msg.content,
                "timestamp": msg.timestamp
            }
            for msg in messages
        ]
    
    def get_consensus_result(self, discussion_id: str) -> Optional[Dict[str, Any]]:
        """获取共识结果"""
        result = self.consensus_results.get(discussion_id)
        return result.to_dict() if result else None


# 全局实例
_discussion_engine: Optional[AgentDiscussionEngine] = None


def get_agent_discussion_engine() -> AgentDiscussionEngine:
    """获取Agent讨论引擎实例"""
    global _discussion_engine
    if _discussion_engine is None:
        _discussion_engine = AgentDiscussionEngine()
    return _discussion_engine
