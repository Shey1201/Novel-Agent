"""
Facilitator - 智能讨论调度系统
负责 Writers Room 中的发言调度、话题管理和共识评估
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.agents.base_agent import BaseAgent
from app.agents.consistency_agent import ConsistencyAgent


class SpeakerStrategy(str, Enum):
    """发言策略"""
    ROUND_ROBIN = "round_robin"           # 轮询
    EXPERTISE_BASED = "expertise_based"   # 基于专长
    PROACTIVITY_BASED = "proactivity_based"  # 基于主动性
    BALANCED = "balanced"                 # 平衡模式
    TOPIC_DRIVEN = "topic_driven"         # 话题驱动


class DiscussionPhase(str, Enum):
    """讨论阶段"""
    OPENING = "opening"           # 开场阶段
    BRAINSTORMING = "brainstorming"  # 头脑风暴
    DEBATING = "debating"         # 辩论阶段
    CONSENSUS_BUILDING = "consensus_building"  # 共识构建
    CLOSING = "closing"           # 收尾阶段


@dataclass
class TopicAnalysis:
    """话题分析结果"""
    primary_topic: str            # 主要话题
    secondary_topics: List[str]   # 次要话题
    sentiment: str                # 情感倾向 (positive/negative/neutral)
    tension_level: float          # 张力水平 0-1
    requires_expertise: List[str]  # 需要的专长领域
    urgency: float                # 紧急程度 0-1


@dataclass
class SpeakerScore:
    """发言者评分"""
    participant: Any              # AgentParticipant
    base_score: float             # 基础分数
    expertise_bonus: float        # 专长加成
    recency_penalty: float        # 最近发言惩罚
    proactivity_bonus: float      # 主动性加成
    diversity_bonus: float        # 多样性加成（避免重复）
    final_score: float            # 最终分数


class TopicAnalyzer:
    """话题分析器"""
    
    # 话题关键词映射
    TOPIC_KEYWORDS = {
        "conflict": ["冲突", "战斗", "对抗", "张力", "矛盾", "斗争", "敌人", "危机"],
        "character": ["角色", "人物", "性格", "心理", "动机", "成长", "转变", "情感"],
        "world": ["世界", "设定", "规则", "魔法", "地理", "历史", "文化", "种族"],
        "plot": ["剧情", "情节", "发展", "转折", "伏笔", "铺垫", "高潮", "结局"],
        "dialogue": ["对话", "台词", "语言", "交流", "沟通", "谈判", "辩论"],
        "pacing": ["节奏", "速度", "快慢", "紧张", "舒缓", "缓冲", "过渡"],
        "theme": ["主题", "思想", "寓意", "象征", "隐喻", "深度", "内涵"],
        "logic": ["逻辑", "合理", "因果", "连贯", "一致", "漏洞", "bug"],
    }
    
    # 情感关键词
    POSITIVE_KEYWORDS = ["好", "棒", "优秀", "同意", "支持", "赞成", "不错", "很好"]
    NEGATIVE_KEYWORDS = ["不好", "问题", "错误", "反对", "不行", "差", "糟糕", "失败"]
    
    def analyze(self, messages: List[Any]) -> TopicAnalysis:
        """
        分析最近讨论的话题
        
        Args:
            messages: 最近的消息列表
            
        Returns:
            TopicAnalysis
        """
        if not messages:
            return TopicAnalysis(
                primary_topic="general",
                secondary_topics=[],
                sentiment="neutral",
                tension_level=0.5,
                requires_expertise=[],
                urgency=0.5
            )
        
        # 合并最近消息内容
        content = " ".join([m.content for m in messages[-5:]])
        
        # 检测主要话题
        topic_scores = {}
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in content)
            if score > 0:
                topic_scores[topic] = score
        
        # 排序话题
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
        primary_topic = sorted_topics[0][0] if sorted_topics else "general"
        secondary_topics = [t[0] for t in sorted_topics[1:3]]
        
        # 分析情感
        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in content)
        negative_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in content)
        
        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        # 计算张力水平
        conflict_keywords = self.TOPIC_KEYWORDS["conflict"]
        tension_level = min(1.0, sum(1 for kw in conflict_keywords if kw in content) / 3)
        
        # 确定需要的专长
        requires_expertise = [primary_topic] + secondary_topics
        
        # 计算紧急程度
        urgency_keywords = ["紧急", "必须", "立即", "关键", "重要"]
        urgency = min(1.0, sum(1 for kw in urgency_keywords if kw in content) / 2)
        
        return TopicAnalysis(
            primary_topic=primary_topic,
            secondary_topics=secondary_topics,
            sentiment=sentiment,
            tension_level=tension_level,
            requires_expertise=requires_expertise,
            urgency=urgency
        )
    
    def detect_phase(self, messages: List[Any], round_num: int, max_rounds: int) -> DiscussionPhase:
        """
        检测当前讨论阶段
        
        Args:
            messages: 消息列表
            round_num: 当前轮数
            max_rounds: 最大轮数
            
        Returns:
            DiscussionPhase
        """
        if round_num == 0:
            return DiscussionPhase.OPENING
        
        if round_num >= max_rounds - 2:
            return DiscussionPhase.CLOSING
        
        if not messages:
            return DiscussionPhase.BRAINSTORMING
        
        # 分析最近消息
        recent_content = " ".join([m.content for m in messages[-5:]])
        
        # 检查是否正在达成共识
        consensus_keywords = ["同意", "赞成", "共识", "确定", "就这样", "没问题"]
        consensus_count = sum(1 for kw in consensus_keywords if kw in recent_content)
        
        if consensus_count >= 2:
            return DiscussionPhase.CONSENSUS_BUILDING
        
        # 检查是否有激烈辩论
        debate_keywords = ["但是", "不过", "反对", "不同", "质疑", "问题"]
        debate_count = sum(1 for kw in debate_keywords if kw in recent_content)
        
        if debate_count >= 2:
            return DiscussionPhase.DEBATING
        
        return DiscussionPhase.BRAINSTORMING


class ConsensusEvaluator:
    """共识评估器"""
    
    def evaluate(self, messages: List[Any], round_num: int, max_rounds: int) -> Dict[str, Any]:
        """
        评估共识度
        
        Args:
            messages: 所有消息
            round_num: 当前轮数
            max_rounds: 最大轮数
            
        Returns:
            {
                "consensus_reached": bool,
                "consensus_score": float,
                "reason": str,
                "confidence": float
            }
        """
        if len(messages) < 3:
            return {
                "consensus_reached": False,
                "consensus_score": 0.0,
                "reason": "讨论消息太少，无法评估共识",
                "confidence": 0.0
            }
        
        recent_messages = messages[-10:] if len(messages) > 10 else messages
        
        # 1. 检查明确的共识消息
        consensus_keywords = ["同意", "赞成", "支持", "没问题", "可以", "达成共识", "确定"]
        consensus_count = sum(
            1 for m in recent_messages
            if any(kw in m.content for kw in consensus_keywords)
        )
        
        # 2. 检查反对/批评消息
        critique_keywords = ["反对", "不同意", "但是", "问题", "错误", "不行"]
        critique_count = sum(
            1 for m in recent_messages
            if any(kw in m.content for kw in critique_keywords)
        )
        
        # 3. 计算共识分数
        total_messages = len(recent_messages)
        agreement_ratio = consensus_count / total_messages if total_messages > 0 else 0
        critique_ratio = critique_count / total_messages if total_messages > 0 else 0
        
        # 共识分数 = 同意比例 - 反对比例
        consensus_score = max(0, agreement_ratio - critique_ratio * 0.5)
        
        # 4. 检查是否达到最大轮数
        if round_num >= max_rounds:
            return {
                "consensus_reached": consensus_score > 0.5,
                "consensus_score": consensus_score,
                "reason": "达到最大讨论轮数",
                "confidence": consensus_score
            }
        
        # 5. 判断是否达成共识
        consensus_reached = consensus_score > 0.7 and critique_count == 0
        
        # 6. 计算置信度
        confidence = min(1.0, consensus_score * (1 + round_num / max_rounds) / 2)
        
        if consensus_reached:
            reason = f"讨论达成共识（共识度: {consensus_score:.2f}）"
        elif consensus_score > 0.5:
            reason = f"接近共识，但仍有分歧（共识度: {consensus_score:.2f}）"
        else:
            reason = f"讨论仍在进行中（共识度: {consensus_score:.2f}）"
        
        return {
            "consensus_reached": consensus_reached,
            "consensus_score": consensus_score,
            "reason": reason,
            "confidence": confidence
        }
    
    def generate_summary(self, messages: List[Any], proposal: Any) -> str:
        """
        生成共识总结
        
        Args:
            messages: 所有消息
            proposal: 原始议案
            
        Returns:
            总结文本
        """
        # 提取关键决策点
        key_points = []
        for m in messages:
            if any(kw in m.content for kw in ["决定", "确定", "采用", "选择", "方案"]):
                # 提取包含决策的句子
                sentences = re.split(r'[。！？]', m.content)
                for s in sentences:
                    if any(kw in s for kw in ["决定", "确定", "采用", "选择", "方案"]):
                        key_points.append(f"- {s.strip()}")
        
        # 去重并限制数量
        key_points = list(dict.fromkeys(key_points))[:5]
        
        if not key_points:
            # 如果没有明确的决策点，提取最后几条消息作为总结
            recent = messages[-3:]
            key_points = [f"- {m.agent_name}: {m.content[:100]}..." for m in recent]
        
        summary = f"""## 讨论总结

**原始议案**: {proposal.title}

**关键决策**:
{chr(10).join(key_points)}

**结论**: 讨论已达成共识，可以进入执行阶段。
"""
        
        return summary


class EnhancedFacilitator:
    """
    增强版讨论主持人
    
    功能：
    1. 智能发言调度（基于话题、专长、主动性）
    2. 话题分析和阶段检测
    3. 共识评估和总结生成
    4. 一致性检查触发
    5. 讨论流程控制
    """
    
    def __init__(self, strategy: SpeakerStrategy = SpeakerStrategy.BALANCED):
        self.strategy = strategy
        self.topic_analyzer = TopicAnalyzer()
        self.consensus_evaluator = ConsensusEvaluator()
        self.consistency_agent = ConsistencyAgent()
        self.discussion_history: List[Dict[str, Any]] = []
        
        # 策略权重配置
        self.strategy_weights = {
            SpeakerStrategy.ROUND_ROBIN: {
                "expertise": 0.1,
                "recency": 0.7,
                "proactivity": 0.1,
                "diversity": 0.1
            },
            SpeakerStrategy.EXPERTISE_BASED: {
                "expertise": 0.6,
                "recency": 0.2,
                "proactivity": 0.1,
                "diversity": 0.1
            },
            SpeakerStrategy.PROACTIVITY_BASED: {
                "expertise": 0.1,
                "recency": 0.2,
                "proactivity": 0.6,
                "diversity": 0.1
            },
            SpeakerStrategy.BALANCED: {
                "expertise": 0.3,
                "recency": 0.3,
                "proactivity": 0.2,
                "diversity": 0.2
            },
            SpeakerStrategy.TOPIC_DRIVEN: {
                "expertise": 0.5,
                "recency": 0.2,
                "proactivity": 0.2,
                "diversity": 0.1
            }
        }
    
    def select_next_speaker(
        self,
        participants: List[Any],
        messages: List[Any],
        story_bible: Dict[str, Any],
        round_num: int
    ) -> Tuple[Optional[Any], Optional[Dict[str, Any]]]:
        """
        选择下一个发言者
        
        Args:
            participants: 参与者列表
            messages: 消息历史
            story_bible: 故事圣经
            round_num: 当前轮数
            
        Returns:
            (选中的参与者, 选择原因)
        """
        if not participants:
            return None, None
        
        # 1. 话题分析
        topic_analysis = self.topic_analyzer.analyze(messages)
        
        # 2. 检测讨论阶段
        max_rounds = 10  # 默认值
        phase = self.topic_analyzer.detect_phase(messages, round_num, max_rounds)
        
        # 3. 检查是否需要 Consistency Agent 插话
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, 'message_type'):
                from app.workflow.writers_room import MessageType
                if last_message.message_type in [MessageType.SUGGESTION, MessageType.PROPOSAL]:
                    interruption = self.consistency_agent.quick_check_for_writers_room(
                        last_message.content,
                        story_bible
                    )
                    if interruption and interruption.get("should_interrupt"):
                        # 找到 Consistency Agent
                        for p in participants:
                            if isinstance(p.agent_instance, ConsistencyAgent):
                                return p, {
                                    "reason": "consistency_check",
                                    "description": interruption.get("message", "设定冲突提醒")
                                }
        
        # 4. 根据策略计算每个参与者的分数
        scores = self._calculate_speaker_scores(
            participants, messages, topic_analysis, phase
        )
        
        if not scores:
            return None, None
        
        # 5. 选择得分最高的
        best_score = max(scores, key=lambda x: x.final_score)
        
        reason = {
            "reason": "strategy_selection",
            "strategy": self.strategy.value,
            "phase": phase.value,
            "topic": topic_analysis.primary_topic,
            "score_breakdown": {
                "base": best_score.base_score,
                "expertise": best_score.expertise_bonus,
                "recency": best_score.recency_penalty,
                "proactivity": best_score.proactivity_bonus,
                "diversity": best_score.diversity_bonus,
                "final": best_score.final_score
            }
        }
        
        return best_score.participant, reason
    
    def _calculate_speaker_scores(
        self,
        participants: List[Any],
        messages: List[Any],
        topic_analysis: TopicAnalysis,
        phase: DiscussionPhase
    ) -> List[SpeakerScore]:
        """
        计算发言者分数
        """
        weights = self.strategy_weights[self.strategy]
        scores = []
        
        # 获取最近发言记录
        recent_speakers = set()
        for m in messages[-3:]:
            if hasattr(m, 'agent_id'):
                recent_speakers.add(m.agent_id)
        
        for p in participants:
            # 基础分数
            base_score = 0.5
            
            # 专长匹配加分
            expertise_bonus = 0.0
            if hasattr(p, 'expertise_areas'):
                matched = set(p.expertise_areas) & set(topic_analysis.requires_expertise)
                expertise_bonus = len(matched) * 0.2
            
            # 最近发言惩罚（避免连续发言）
            recency_penalty = 0.0
            if hasattr(p, 'agent_id') and p.agent_id in recent_speakers:
                recency_penalty = -0.3
            if hasattr(p, 'last_spoke_at') and p.last_spoke_at:
                time_since = (datetime.now() - p.last_spoke_at).total_seconds()
                if time_since < 5:  # 5秒内发言过
                    recency_penalty = -0.5
            
            # 主动性加分
            proactivity_bonus = 0.0
            if hasattr(p, 'proactivity'):
                proactivity_bonus = p.proactivity * 0.2
            
            # 多样性加分（还没发言过的优先）
            diversity_bonus = 0.0
            if hasattr(p, 'message_count'):
                if p.message_count == 0:
                    diversity_bonus = 0.3
                elif p.message_count < 2:
                    diversity_bonus = 0.1
            
            # 阶段调整
            if phase == DiscussionPhase.CONSENSUS_BUILDING:
                # 共识阶段，让发言少的 Agent 表态
                if hasattr(p, 'message_count') and p.message_count < 2:
                    diversity_bonus += 0.2
            
            # 计算最终分数
            final_score = (
                base_score * 0.2 +
                expertise_bonus * weights["expertise"] +
                recency_penalty * weights["recency"] +
                proactivity_bonus * weights["proactivity"] +
                diversity_bonus * weights["diversity"]
            )
            
            # 确保分数在合理范围内
            final_score = max(0.1, min(1.0, final_score))
            
            scores.append(SpeakerScore(
                participant=p,
                base_score=base_score,
                expertise_bonus=expertise_bonus,
                recency_penalty=recency_penalty,
                proactivity_bonus=proactivity_bonus,
                diversity_bonus=diversity_bonus,
                final_score=final_score
            ))
        
        return scores
    
    def evaluate_consensus(
        self,
        messages: List[Any],
        round_num: int,
        max_rounds: int
    ) -> Dict[str, Any]:
        """
        评估共识
        """
        return self.consensus_evaluator.evaluate(messages, round_num, max_rounds)
    
    def generate_consensus_summary(self, messages: List[Any], proposal: Any) -> str:
        """
        生成共识总结
        """
        return self.consensus_evaluator.generate_summary(messages, proposal)
    
    def should_intervene(self, messages: List[Any]) -> Tuple[bool, str]:
        """
        判断是否需要人工干预
        
        Returns:
            (是否需要干预, 原因)
        """
        if len(messages) < 5:
            return False, "讨论刚开始"
        
        recent = messages[-5:]
        content = " ".join([m.content for m in recent])
        
        # 检测僵局信号
        deadlock_signals = [
            "僵持", "无法决定", "各执己见", "没有共识",
            "循环", "重复", "同样", "一直在说"
        ]
        
        for signal in deadlock_signals:
            if signal in content:
                return True, f"检测到僵局信号: {signal}"
        
        # 检测激烈争论
        heated_keywords = ["荒谬", "愚蠢", "错误", "完全不对", "坚决反对"]
        heated_count = sum(1 for kw in heated_keywords if kw in content)
        
        if heated_count >= 2:
            return True, "讨论过于激烈，需要人工协调"
        
        return False, "讨论正常进行"
    
    def get_discussion_stats(self, messages: List[Any], participants: List[Any]) -> Dict[str, Any]:
        """
        获取讨论统计信息
        """
        if not messages:
            return {
                "total_messages": 0,
                "participant_activity": {},
                "topic_distribution": {},
                "sentiment": "neutral"
            }
        
        # 参与者活跃度
        activity = {}
        for p in participants:
            if hasattr(p, 'agent_id'):
                count = sum(1 for m in messages if hasattr(m, 'agent_id') and m.agent_id == p.agent_id)
                activity[p.agent_name] = count
        
        # 话题分布
        topic_analysis = self.topic_analyzer.analyze(messages)
        topic_distribution = {topic_analysis.primary_topic: 0.5}
        for i, topic in enumerate(topic_analysis.secondary_topics):
            topic_distribution[topic] = 0.3 - i * 0.1
        
        return {
            "total_messages": len(messages),
            "participant_activity": activity,
            "topic_distribution": topic_distribution,
            "sentiment": topic_analysis.sentiment,
            "tension_level": topic_analysis.tension_level
        }
    
    def set_strategy(self, strategy: SpeakerStrategy):
        """
        设置发言策略
        """
        self.strategy = strategy
    
    def get_strategy_description(self) -> str:
        """
        获取当前策略描述
        """
        descriptions = {
            SpeakerStrategy.ROUND_ROBIN: "轮询模式：确保每个Agent都有机会发言",
            SpeakerStrategy.EXPERTISE_BASED: "专家模式：优先选择相关领域的专家",
            SpeakerStrategy.PROACTIVITY_BASED: "主动模式：优先选择主动性高的Agent",
            SpeakerStrategy.BALANCED: "平衡模式：综合考虑多种因素",
            SpeakerStrategy.TOPIC_DRIVEN: "话题驱动：根据当前话题动态选择"
        }
        return descriptions.get(self.strategy, "未知策略")


# 便捷函数
def create_facilitator(strategy: str = "balanced") -> EnhancedFacilitator:
    """
    创建 Facilitator 实例
    
    Args:
        strategy: 策略名称 (round_robin/expertise_based/proactivity_based/balanced/topic_driven)
        
    Returns:
        EnhancedFacilitator
    """
    strategy_map = {
        "round_robin": SpeakerStrategy.ROUND_ROBIN,
        "expertise_based": SpeakerStrategy.EXPERTISE_BASED,
        "proactivity_based": SpeakerStrategy.PROACTIVITY_BASED,
        "balanced": SpeakerStrategy.BALANCED,
        "topic_driven": SpeakerStrategy.TOPIC_DRIVEN
    }
    
    selected_strategy = strategy_map.get(strategy, SpeakerStrategy.BALANCED)
    return EnhancedFacilitator(strategy=selected_strategy)
