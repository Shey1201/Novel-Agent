"""
Agent Analytics - Agent 行为分析和效果评估
分析哪个 Agent 贡献最多，哪种策略效果最好
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import json


class AgentActionType(Enum):
    """Agent 动作类型"""
    GENERATE = "generate"           # 生成内容
    EDIT = "edit"                   # 编辑内容
    REVIEW = "review"               # 审核内容
    SUGGEST = "suggest"             # 提供建议
    DISCUSS = "discuss"             # 参与讨论
    INTERRUPT = "interrupt"         # 插话
    REWRITE = "rewrite"             # 重写
    APPROVE = "approve"             # 批准
    REJECT = "reject"               # 拒绝


class StrategyType(Enum):
    """策略类型"""
    FACILITATOR_ROUND_ROBIN = "round_robin"
    FACILITATOR_EXPERT = "expert"
    FACILITATOR_PROACTIVE = "proactive"
    FACILITATOR_BALANCED = "balanced"
    CONSENSUS_THRESHOLD = "consensus_threshold"
    QUALITY_GATE = "quality_gate"


@dataclass
class AgentAction:
    """Agent 动作记录"""
    action_id: str
    agent_type: str
    action_type: AgentActionType
    novel_id: str
    chapter_id: Optional[str] = None
    content_length: int = 0
    quality_score: float = 0.0  # 质量评分 0-1
    execution_time_ms: int = 0
    tokens_consumed: int = 0
    strategy_used: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "agent_type": self.agent_type,
            "action_type": self.action_type.value,
            "novel_id": self.novel_id,
            "chapter_id": self.chapter_id,
            "content_length": self.content_length,
            "quality_score": self.quality_score,
            "execution_time_ms": self.execution_time_ms,
            "tokens_consumed": self.tokens_consumed,
            "strategy_used": self.strategy_used,
            "timestamp": self.timestamp
        }


@dataclass
class AgentContribution:
    """Agent 贡献统计"""
    agent_type: str
    total_actions: int = 0
    total_content_generated: int = 0
    average_quality: float = 0.0
    total_tokens_consumed: int = 0
    total_execution_time_ms: int = 0
    action_breakdown: Dict[str, int] = field(default_factory=dict)
    
    @property
    def efficiency_score(self) -> float:
        """效率分数 = 内容量 / 执行时间"""
        if self.total_execution_time_ms == 0:
            return 0.0
        return self.total_content_generated / self.total_execution_time_ms * 1000
    
    @property
    def quality_efficiency(self) -> float:
        """质量效率 = 平均质量 / Token消耗"""
        if self.total_tokens_consumed == 0:
            return 0.0
        return self.average_quality / self.total_tokens_consumed * 1000


@dataclass
class StrategyEffectiveness:
    """策略效果评估"""
    strategy_type: str
    usage_count: int = 0
    average_quality: float = 0.0
    average_execution_time: float = 0.0
    success_rate: float = 0.0  # 成功/总次数
    user_satisfaction: float = 0.0  # 用户满意度


class AgentBehaviorTracker:
    """
    Agent 行为追踪器
    
    记录和分析 Agent 的各种行为
    """
    
    def __init__(self):
        self.actions: List[AgentAction] = []
        self.agent_contributions: Dict[str, AgentContribution] = defaultdict(
            lambda: AgentContribution(agent_type="")
        )
        self.strategy_effectiveness: Dict[str, StrategyEffectiveness] = defaultdict(
            lambda: StrategyEffectiveness(strategy_type="")
        )
        
        # 实时统计
        self.daily_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_actions": 0,
            "total_tokens": 0,
            "agent_breakdown": defaultdict(int)
        })
    
    def record_action(self, action: AgentAction):
        """记录 Agent 动作"""
        self.actions.append(action)
        
        # 更新 Agent 贡献统计
        contrib = self.agent_contributions[action.agent_type]
        contrib.agent_type = action.agent_type
        contrib.total_actions += 1
        contrib.total_content_generated += action.content_length
        contrib.total_tokens_consumed += action.tokens_consumed
        contrib.total_execution_time_ms += action.execution_time_ms
        
        # 更新平均质量
        old_avg = contrib.average_quality
        n = contrib.total_actions
        contrib.average_quality = (old_avg * (n - 1) + action.quality_score) / n
        
        # 动作类型分解
        action_type_str = action.action_type.value
        contrib.action_breakdown[action_type_str] = contrib.action_breakdown.get(action_type_str, 0) + 1
        
        # 更新策略效果
        if action.strategy_used:
            strategy = self.strategy_effectiveness[action.strategy_used]
            strategy.strategy_type = action.strategy_used
            strategy.usage_count += 1
            
            # 更新平均质量
            old_avg_quality = strategy.average_quality
            n = strategy.usage_count
            strategy.average_quality = (old_avg_quality * (n - 1) + action.quality_score) / n
            
            # 更新平均执行时间
            old_avg_time = strategy.average_execution_time
            strategy.average_execution_time = (old_avg_time * (n - 1) + action.execution_time_ms) / n
        
        # 更新每日统计
        today = datetime.now().strftime("%Y-%m-%d")
        self.daily_stats[today]["total_actions"] += 1
        self.daily_stats[today]["total_tokens"] += action.tokens_consumed
        self.daily_stats[today]["agent_breakdown"][action.agent_type] += 1
    
    def get_agent_ranking(self) -> List[AgentContribution]:
        """获取 Agent 贡献排名"""
        return sorted(
            self.agent_contributions.values(),
            key=lambda x: (x.average_quality * 0.4 + x.efficiency_score * 0.3 + x.total_content_generated * 0.3),
            reverse=True
        )
    
    def get_strategy_ranking(self) -> List[StrategyEffectiveness]:
        """获取策略效果排名"""
        return sorted(
            self.strategy_effectiveness.values(),
            key=lambda x: (x.average_quality * 0.5 + x.success_rate * 0.3 + x.user_satisfaction * 0.2),
            reverse=True
        )
    
    def get_agent_insights(self, agent_type: str) -> Dict[str, Any]:
        """获取特定 Agent 的深度洞察"""
        contrib = self.agent_contributions.get(agent_type)
        if not contrib:
            return {"error": f"No data for agent type: {agent_type}"}
        
        # 获取该 Agent 的所有动作
        agent_actions = [a for a in self.actions if a.agent_type == agent_type]
        
        # 计算趋势
        quality_trend = self._calculate_trend([a.quality_score for a in agent_actions])
        speed_trend = self._calculate_trend([a.execution_time_ms for a in agent_actions])
        
        # 最佳表现
        best_action = max(agent_actions, key=lambda a: a.quality_score) if agent_actions else None
        
        return {
            "agent_type": agent_type,
            "summary": {
                "total_actions": contrib.total_actions,
                "total_content": contrib.total_content_generated,
                "average_quality": round(contrib.average_quality, 3),
                "efficiency_score": round(contrib.efficiency_score, 3),
                "tokens_per_action": contrib.total_tokens_consumed // max(contrib.total_actions, 1)
            },
            "trends": {
                "quality": quality_trend,
                "speed": speed_trend
            },
            "action_distribution": contrib.action_breakdown,
            "best_performance": best_action.to_dict() if best_action else None,
            "recommendations": self._generate_recommendations(agent_type, contrib)
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """计算趋势（上升/下降/稳定）"""
        if len(values) < 5:
            return "insufficient_data"
        
        # 比较前半段和后半段的平均值
        mid = len(values) // 2
        first_half_avg = sum(values[:mid]) / mid
        second_half_avg = sum(values[mid:]) / (len(values) - mid)
        
        diff_ratio = (second_half_avg - first_half_avg) / first_half_avg if first_half_avg != 0 else 0
        
        if diff_ratio > 0.1:
            return "improving"
        elif diff_ratio < -0.1:
            return "declining"
        else:
            return "stable"
    
    def _generate_recommendations(
        self,
        agent_type: str,
        contrib: AgentContribution
    ) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if contrib.average_quality < 0.6:
            recommendations.append(f"{agent_type} 的平均质量较低，建议优化提示词或增加审核步骤")
        
        if contrib.efficiency_score < 0.5:
            recommendations.append(f"{agent_type} 的执行效率有待提升，建议检查是否有冗余计算")
        
        if contrib.total_tokens_consumed / max(contrib.total_actions, 1) > 2000:
            recommendations.append(f"{agent_type} 的 Token 消耗较高，建议优化上下文长度")
        
        # 检查动作分布
        if contrib.action_breakdown.get("generate", 0) > contrib.total_actions * 0.8:
            recommendations.append(f"{agent_type} 主要进行生成任务，建议增加审核和编辑动作")
        
        return recommendations
    
    def generate_full_report(self) -> Dict[str, Any]:
        """生成完整分析报告"""
        agent_ranking = self.get_agent_ranking()
        strategy_ranking = self.get_strategy_ranking()
        
        return {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_actions_recorded": len(self.actions),
                "unique_agents": len(self.agent_contributions),
                "unique_strategies": len(self.strategy_effectiveness),
                "total_tokens_consumed": sum(
                    c.total_tokens_consumed for c in self.agent_contributions.values()
                )
            },
            "agent_ranking": [
                {
                    "rank": i + 1,
                    "agent_type": c.agent_type,
                    "total_actions": c.total_actions,
                    "average_quality": round(c.average_quality, 3),
                    "efficiency_score": round(c.efficiency_score, 3),
                    "quality_efficiency": round(c.quality_efficiency, 6)
                }
                for i, c in enumerate(agent_ranking[:5])
            ],
            "strategy_ranking": [
                {
                    "rank": i + 1,
                    "strategy_type": s.strategy_type,
                    "usage_count": s.usage_count,
                    "average_quality": round(s.average_quality, 3),
                    "average_execution_time_ms": round(s.average_execution_time, 1)
                }
                for i, s in enumerate(strategy_ranking[:5])
            ],
            "daily_activity": [
                {
                    "date": date,
                    "total_actions": stats["total_actions"],
                    "total_tokens": stats["total_tokens"]
                }
                for date, stats in sorted(self.daily_stats.items())[-7:]  # 最近7天
            ],
            "insights": self._generate_system_insights()
        }
    
    def _generate_system_insights(self) -> Dict[str, Any]:
        """生成系统级洞察"""
        insights = {
            "top_performer": None,
            "bottleneck": None,
            "optimization_opportunities": []
        }
        
        if self.agent_contributions:
            # 最佳表现者
            best = max(self.agent_contributions.values(), key=lambda x: x.average_quality)
            insights["top_performer"] = {
                "agent_type": best.agent_type,
                "average_quality": round(best.average_quality, 3)
            }
            
            # 瓶颈
            worst = min(self.agent_contributions.values(), key=lambda x: x.efficiency_score)
            insights["bottleneck"] = {
                "agent_type": worst.agent_type,
                "efficiency_score": round(worst.efficiency_score, 3)
            }
        
        # 优化机会
        for agent_type, contrib in self.agent_contributions.items():
            if contrib.average_quality < 0.7:
                insights["optimization_opportunities"].append(
                    f"{agent_type} 质量偏低，需要优化"
                )
        
        return insights


class RealTimeAgentMonitor:
    """
    实时 Agent 监控器
    
    监控当前活跃的 Agent 和系统状态
    """
    
    def __init__(self):
        self.active_agents: Dict[str, Dict[str, Any]] = {}
        self.current_session_id: Optional[str] = None
        self.session_start_time: Optional[str] = None
    
    def start_session(self, session_id: str, novel_id: str):
        """开始新的会话"""
        self.current_session_id = session_id
        self.session_start_time = datetime.now().isoformat()
        self.active_agents.clear()
    
    def agent_join(self, agent_type: str, task: str):
        """Agent 加入会话"""
        self.active_agents[agent_type] = {
            "joined_at": datetime.now().isoformat(),
            "task": task,
            "status": "active",
            "actions_count": 0
        }
    
    def agent_action(self, agent_type: str, action_type: str):
        """记录 Agent 动作"""
        if agent_type in self.active_agents:
            self.active_agents[agent_type]["actions_count"] += 1
            self.active_agents[agent_type]["last_action"] = action_type
            self.active_agents[agent_type]["last_action_time"] = datetime.now().isoformat()
    
    def agent_leave(self, agent_type: str):
        """Agent 离开会话"""
        if agent_type in self.active_agents:
            self.active_agents[agent_type]["status"] = "inactive"
            self.active_agents[agent_type]["left_at"] = datetime.now().isoformat()
    
    def get_session_status(self) -> Dict[str, Any]:
        """获取当前会话状态"""
        return {
            "session_id": self.current_session_id,
            "started_at": self.session_start_time,
            "duration_seconds": self._calculate_duration(),
            "active_agents_count": sum(
                1 for a in self.active_agents.values() if a["status"] == "active"
            ),
            "agents": self.active_agents
        }
    
    def _calculate_duration(self) -> int:
        """计算会话持续时间"""
        if not self.session_start_time:
            return 0
        
        start = datetime.fromisoformat(self.session_start_time)
        now = datetime.now()
        return int((now - start).total_seconds())


# 全局实例
_agent_tracker: Optional[AgentBehaviorTracker] = None
_realtime_monitor: Optional[RealTimeAgentMonitor] = None


def get_agent_tracker() -> AgentBehaviorTracker:
    """获取 Agent 行为追踪器实例"""
    global _agent_tracker
    if _agent_tracker is None:
        _agent_tracker = AgentBehaviorTracker()
    return _agent_tracker


def get_realtime_monitor() -> RealTimeAgentMonitor:
    """获取实时监控器实例"""
    global _realtime_monitor
    if _realtime_monitor is None:
        _realtime_monitor = RealTimeAgentMonitor()
    return _realtime_monitor
