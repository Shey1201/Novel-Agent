"""
Token Budget Manager - Token 预算管理器
用于章节生成过程中的 Token 分配和预算控制
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime


class AgentType(Enum):
    """Agent 类型"""
    PLANNER = "planner"
    DISCUSSION = "discussion"
    CONFLICT = "conflict"
    WRITING = "writing"
    EDITOR = "editor"
    READER = "reader"
    SUMMARY = "summary"
    CONSISTENCY = "consistency"


@dataclass
class TokenAllocation:
    """Token 分配配置"""
    agent: AgentType
    budget: int
    priority: int = 5  # 1-10，数字越大优先级越高
    min_tokens: int = 100
    max_tokens: int = 0  # 0 表示无限制
    
    
@dataclass
class TokenUsage:
    """Token 使用情况"""
    agent: AgentType
    allocated: int
    used: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def remaining(self) -> int:
        return self.allocated - self.used
    
    @property
    def usage_rate(self) -> float:
        if self.allocated == 0:
            return 0.0
        return self.used / self.allocated


@dataclass
class ChapterTokenBudget:
    """章节 Token 预算"""
    chapter_id: str
    total_budget: int
    allocations: Dict[AgentType, TokenAllocation] = field(default_factory=dict)
    usages: List[TokenUsage] = field(default_factory=list)
    is_enabled: bool = True
    
    def get_allocation(self, agent: AgentType) -> Optional[TokenAllocation]:
        return self.allocations.get(agent)
    
    def record_usage(self, agent: AgentType, used_tokens: int):
        """记录 Token 使用"""
        allocation = self.allocations.get(agent)
        if allocation:
            usage = TokenUsage(
                agent=agent,
                allocated=allocation.budget,
                used=used_tokens
            )
            self.usages.append(usage)
    
    def get_total_used(self) -> int:
        """获取总使用 Token 数"""
        return sum(u.used for u in self.usages)
    
    def get_remaining_budget(self) -> int:
        """获取剩余预算"""
        return self.total_budget - self.get_total_used()
    
    def is_over_budget(self, agent: AgentType) -> bool:
        """检查某个 Agent 是否超预算"""
        agent_usages = [u for u in self.usages if u.agent == agent]
        if not agent_usages:
            return False
        total_used = sum(u.used for u in agent_usages)
        allocation = self.allocations.get(agent)
        if allocation:
            return total_used > allocation.budget
        return False


class TokenBudgetManager:
    """
    Token 预算管理器
    
    管理章节生成过程中的 Token 分配、监控和优化
    """
    
    # 默认预算分配比例
    DEFAULT_ALLOCATIONS = {
        AgentType.PLANNER: 0.10,      # 10% - 规划
        AgentType.DISCUSSION: 0.13,   # 13% - 讨论
        AgentType.CONFLICT: 0.07,     # 7% - 冲突分析
        AgentType.WRITING: 0.47,      # 47% - 写作（最大头）
        AgentType.EDITOR: 0.13,       # 13% - 编辑
        AgentType.READER: 0.07,       # 7% - 读者反馈
        AgentType.SUMMARY: 0.03,      # 3% - 总结
    }
    
    def __init__(self, daily_limit: Optional[int] = None):
        """
        初始化
        
        Args:
            daily_limit: 每日 Token 限制，None 表示无限制
        """
        self.daily_limit = daily_limit
        self.daily_used = 0
        self.chapter_budgets: Dict[str, ChapterTokenBudget] = {}
        self.enabled = daily_limit is not None
        
    def set_daily_limit(self, limit: Optional[int]):
        """设置每日限制"""
        self.daily_limit = limit
        self.enabled = limit is not None
        
    def create_chapter_budget(
        self,
        chapter_id: str,
        total_budget: int = 15000,
        custom_allocations: Optional[Dict[AgentType, float]] = None
    ) -> ChapterTokenBudget:
        """
        创建章节预算
        
        Args:
            chapter_id: 章节 ID
            total_budget: 总预算，默认 15000 tokens
            custom_allocations: 自定义分配比例
            
        Returns:
            章节预算配置
        """
        allocations = {}
        ratios = custom_allocations or self.DEFAULT_ALLOCATIONS
        
        for agent, ratio in ratios.items():
            budget = int(total_budget * ratio)
            allocations[agent] = TokenAllocation(
                agent=agent,
                budget=budget,
                priority=self._get_agent_priority(agent),
                min_tokens=self._get_agent_min_tokens(agent),
                max_tokens=self._get_agent_max_tokens(agent)
            )
        
        chapter_budget = ChapterTokenBudget(
            chapter_id=chapter_id,
            total_budget=total_budget,
            allocations=allocations,
            is_enabled=self.enabled
        )
        
        self.chapter_budgets[chapter_id] = chapter_budget
        return chapter_budget
    
    def _get_agent_priority(self, agent: AgentType) -> int:
        """获取 Agent 优先级"""
        priorities = {
            AgentType.WRITING: 10,      # 写作最高优先级
            AgentType.PLANNER: 8,       # 规划次高
            AgentType.EDITOR: 7,        # 编辑
            AgentType.CONFLICT: 6,      # 冲突
            AgentType.DISCUSSION: 5,    # 讨论
            AgentType.READER: 4,        # 读者
            AgentType.SUMMARY: 3,       # 总结
            AgentType.CONSISTENCY: 6,   # 一致性
        }
        return priorities.get(agent, 5)
    
    def _get_agent_min_tokens(self, agent: AgentType) -> int:
        """获取 Agent 最小 Token 需求"""
        min_tokens = {
            AgentType.WRITING: 3000,
            AgentType.PLANNER: 500,
            AgentType.EDITOR: 800,
            AgentType.CONFLICT: 400,
            AgentType.DISCUSSION: 600,
            AgentType.READER: 300,
            AgentType.SUMMARY: 200,
            AgentType.CONSISTENCY: 400,
        }
        return min_tokens.get(agent, 100)
    
    def _get_agent_max_tokens(self, agent: AgentType) -> int:
        """获取 Agent 最大 Token 限制"""
        max_tokens = {
            AgentType.WRITING: 10000,
            AgentType.PLANNER: 2000,
            AgentType.EDITOR: 3000,
            AgentType.CONFLICT: 1500,
            AgentType.DISCUSSION: 2500,
            AgentType.READER: 1500,
            AgentType.SUMMARY: 800,
            AgentType.CONSISTENCY: 1500,
        }
        return max_tokens.get(agent, 0)
    
    def check_budget_available(self, required_tokens: int) -> Tuple[bool, str]:
        """
        检查预算是否充足
        
        Returns:
            (是否充足, 原因)
        """
        if not self.enabled:
            return True, "预算控制未启用"
        
        if self.daily_limit is None:
            return True, "无每日限制"
        
        remaining = self.daily_limit - self.daily_used
        if remaining < required_tokens:
            return False, f"每日 Token 不足: 需要 {required_tokens}, 剩余 {remaining}"
        
        return True, "预算充足"
    
    def record_usage(self, chapter_id: str, agent: AgentType, tokens: int):
        """记录 Token 使用"""
        # 更新每日使用
        self.daily_used += tokens
        
        # 更新章节使用
        chapter_budget = self.chapter_budgets.get(chapter_id)
        if chapter_budget:
            chapter_budget.record_usage(agent, tokens)
    
    def get_chapter_budget(self, chapter_id: str) -> Optional[ChapterTokenBudget]:
        """获取章节预算"""
        return self.chapter_budgets.get(chapter_id)
    
    def get_agent_remaining_budget(self, chapter_id: str, agent: AgentType) -> int:
        """获取 Agent 剩余预算"""
        chapter_budget = self.chapter_budgets.get(chapter_id)
        if not chapter_budget:
            return 0
        
        allocation = chapter_budget.get_allocation(agent)
        if not allocation:
            return 0
        
        agent_usages = [u for u in chapter_budget.usages if u.agent == agent]
        total_used = sum(u.used for u in agent_usages)
        
        return allocation.budget - total_used
    
    def should_stop_generation(self, chapter_id: str, agent: AgentType) -> Tuple[bool, str]:
        """
        检查是否应该停止生成
        
        Returns:
            (是否停止, 原因)
        """
        if not self.enabled:
            return False, "预算控制未启用"
        
        chapter_budget = self.chapter_budgets.get(chapter_id)
        if not chapter_budget or not chapter_budget.is_enabled:
            return False, "章节预算未启用"
        
        # 检查 Agent 是否超预算
        if chapter_budget.is_over_budget(agent):
            return True, f"{agent.value} 已超出预算"
        
        # 检查每日限制
        if self.daily_limit and self.daily_used >= self.daily_limit:
            return True, "已达到每日 Token 限制"
        
        return False, "可以继续生成"
    
    def get_budget_report(self, chapter_id: str) -> Dict[str, Any]:
        """获取预算使用报告"""
        chapter_budget = self.chapter_budgets.get(chapter_id)
        if not chapter_budget:
            return {}
        
        report = {
            "chapter_id": chapter_id,
            "total_budget": chapter_budget.total_budget,
            "total_used": chapter_budget.get_total_used(),
            "remaining": chapter_budget.get_remaining_budget(),
            "usage_rate": chapter_budget.get_total_used() / chapter_budget.total_budget if chapter_budget.total_budget > 0 else 0,
            "agents": {}
        }
        
        for agent, allocation in chapter_budget.allocations.items():
            agent_usages = [u for u in chapter_budget.usages if u.agent == agent]
            total_used = sum(u.used for u in agent_usages)
            
            report["agents"][agent.value] = {
                "allocated": allocation.budget,
                "used": total_used,
                "remaining": allocation.budget - total_used,
                "usage_rate": total_used / allocation.budget if allocation.budget > 0 else 0,
                "over_budget": total_used > allocation.budget
            }
        
        return report
    
    def reset_daily_usage(self):
        """重置每日使用"""
        self.daily_used = 0
    
    def get_daily_status(self) -> Dict[str, Any]:
        """获取每日状态"""
        return {
            "enabled": self.enabled,
            "daily_limit": self.daily_limit,
            "daily_used": self.daily_used,
            "daily_remaining": (self.daily_limit - self.daily_used) if self.daily_limit else None,
            "usage_rate": (self.daily_used / self.daily_limit) if self.daily_limit else 0
        }


# 全局实例
token_budget_manager = TokenBudgetManager()


def get_token_budget_manager() -> TokenBudgetManager:
    """获取 Token 预算管理器实例"""
    return token_budget_manager
