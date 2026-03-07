"""
Discussion Controller - Agent 讨论控制器
控制讨论轮次、参与 Agent 和发言长度
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class DiscussionTopic(Enum):
    """讨论主题类型"""
    PLOT = "plot"           # 剧情讨论
    STRUCTURE = "structure" # 结构问题
    CHARACTER = "character" # 角色决策
    CONFLICT = "conflict"   # 冲突升级
    WRITING = "writing"     # 写作风格
    READER = "reader"       # 读者体验


class DiscussionPhase(Enum):
    """讨论阶段"""
    ROUND_1 = 1  # 第一轮：Planner + Conflict
    ROUND_2 = 2  # 第二轮：Writer + Editor
    FINISHED = 3 # 讨论结束


@dataclass
class DiscussionConfig:
    """讨论配置"""
    max_rounds: int = 2                    # 最大轮数
    max_tokens_per_response: int = 80      # 每次发言最大 tokens
    enable_short_mode: bool = True         # 启用短发言模式
    trigger_conditions: List[str] = field(default_factory=list)  # 触发条件
    
    # 各主题对应的参与 Agent
    topic_agents: Dict[DiscussionTopic, List[str]] = field(default_factory=lambda: {
        DiscussionTopic.PLOT: ["planner", "conflict", "writer"],
        DiscussionTopic.STRUCTURE: ["editor", "planner"],
        DiscussionTopic.CHARACTER: ["planner", "conflict", "writer"],
        DiscussionTopic.CONFLICT: ["conflict", "planner"],
        DiscussionTopic.WRITING: ["writer", "editor"],
        DiscussionTopic.READER: ["reader"],
    })


@dataclass
class DiscussionMessage:
    """讨论消息"""
    agent: str
    content: str
    round: int
    timestamp: datetime = field(default_factory=datetime.now)
    tokens_used: int = 0


@dataclass
class DiscussionSession:
    """讨论会话"""
    session_id: str
    topic: DiscussionTopic
    chapter_id: str
    config: DiscussionConfig
    current_round: int = 1
    messages: List[DiscussionMessage] = field(default_factory=list)
    participating_agents: Set[str] = field(default_factory=set)
    is_finished: bool = False
    
    def add_message(self, agent: str, content: str, tokens_used: int = 0):
        """添加消息"""
        message = DiscussionMessage(
            agent=agent,
            content=content,
            round=self.current_round,
            tokens_used=tokens_used
        )
        self.messages.append(message)
    
    def next_round(self) -> bool:
        """进入下一轮，返回是否成功"""
        if self.current_round >= self.config.max_rounds:
            self.is_finished = True
            return False
        self.current_round += 1
        return True
    
    def should_agent_participate(self, agent: str) -> bool:
        """检查 Agent 是否应该参与当前讨论"""
        if agent in self.participating_agents:
            return False  # 已经发言过
        
        expected_agents = self.config.topic_agents.get(self.topic, [])
        return agent in expected_agents
    
    def get_participating_agents(self) -> List[str]:
        """获取应该参与的 Agent 列表"""
        return self.config.topic_agents.get(self.topic, [])


class DiscussionTriggerChecker:
    """讨论触发条件检查器"""
    
    # 触发条件定义
    TRIGGERS = {
        "plot_critical": "剧情关键节点",
        "character_major_change": "角色重大变化",
        "conflict_escalation": "冲突升级",
        "new_arc_start": "新篇章开始",
        "climax_approaching": "接近高潮",
    }
    
    @staticmethod
    def should_trigger_discussion(
        chapter_number: int,
        is_critical_plot: bool = False,
        has_major_character_change: bool = False,
        is_conflict_escalation: bool = False,
        is_new_arc: bool = False,
        is_climax_approaching: bool = False,
        last_discussion_chapter: int = 0,
        min_chapter_interval: int = 3
    ) -> Tuple[bool, str]:
        """
        检查是否应该触发讨论
        
        Returns:
            (是否触发, 原因)
        """
        # 检查最小间隔
        if chapter_number - last_discussion_chapter < min_chapter_interval:
            return False, f"距离上次讨论仅 {chapter_number - last_discussion_chapter} 章"
        
        # 检查触发条件
        if is_critical_plot:
            return True, "剧情关键节点"
        
        if has_major_character_change:
            return True, "角色重大变化"
        
        if is_conflict_escalation:
            return True, "冲突升级"
        
        if is_new_arc:
            return True, "新篇章开始"
        
        if is_climax_approaching:
            return True, "接近高潮"
        
        return False, "不满足触发条件"


class DiscussionController:
    """
    Agent 讨论控制器
    
    管理讨论流程：
    1. 控制讨论轮次（最多2轮）
    2. 选择相关 Agent 参与
    3. 限制发言长度（80 tokens）
    4. 触发条件判断
    """
    
    def __init__(self):
        self.sessions: Dict[str, DiscussionSession] = {}
        self.default_config = DiscussionConfig()
        self.trigger_checker = DiscussionTriggerChecker()
        
    def create_session(
        self,
        session_id: str,
        topic: DiscussionTopic,
        chapter_id: str,
        config: Optional[DiscussionConfig] = None
    ) -> DiscussionSession:
        """创建讨论会话"""
        session = DiscussionSession(
            session_id=session_id,
            topic=topic,
            chapter_id=chapter_id,
            config=config or self.default_config
        )
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[DiscussionSession]:
        """获取讨论会话"""
        return self.sessions.get(session_id)
    
    def add_agent_response(
        self,
        session_id: str,
        agent: str,
        content: str,
        tokens_used: int = 0
    ) -> Dict[str, Any]:
        """
        添加 Agent 响应
        
        Returns:
            状态信息，包含是否需要进入下一轮
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "会话不存在"}
        
        if session.is_finished:
            return {"error": "讨论已结束"}
        
        # 检查发言长度
        if session.config.enable_short_mode and tokens_used > session.config.max_tokens_per_response:
            content = content[:session.config.max_tokens_per_response] + "..."
        
        # 添加消息
        session.add_message(agent, content, tokens_used)
        session.participating_agents.add(agent)
        
        # 检查是否需要进入下一轮
        expected_agents = session.get_participating_agents()
        current_round_agents = [m.agent for m in session.messages if m.round == session.current_round]
        
        # 当前轮所有 Agent 都已发言
        if set(current_round_agents) >= set(expected_agents):
            if session.next_round():
                return {
                    "status": "next_round",
                    "round": session.current_round,
                    "message": f"进入第 {session.current_round} 轮讨论"
                }
            else:
                return {
                    "status": "finished",
                    "message": "讨论结束"
                }
        
        # 还有 Agent 未发言
        remaining = set(expected_agents) - set(current_round_agents)
        return {
            "status": "continue",
            "remaining_agents": list(remaining),
            "message": f"等待 {', '.join(remaining)} 发言"
        }
    
    def get_discussion_summary(self, session_id: str) -> Dict[str, Any]:
        """获取讨论摘要"""
        session = self.sessions.get(session_id)
        if not session:
            return {}
        
        return {
            "session_id": session_id,
            "topic": session.topic.value,
            "chapter_id": session.chapter_id,
            "total_rounds": session.current_round,
            "is_finished": session.is_finished,
            "total_messages": len(session.messages),
            "total_tokens": sum(m.tokens_used for m in session.messages),
            "messages": [
                {
                    "agent": m.agent,
                    "content": m.content,
                    "round": m.round
                }
                for m in session.messages
            ]
        }
    
    def should_trigger_discussion(
        self,
        chapter_number: int,
        **conditions
    ) -> Tuple[bool, str]:
        """检查是否应该触发讨论"""
        return self.trigger_checker.should_trigger_discussion(
            chapter_number,
            **conditions
        )
    
    def get_short_response_prompt(self, topic: DiscussionTopic) -> str:
        """
        获取短发言模式的 prompt
        
        限制在 80 tokens 以内
        """
        prompts = {
            DiscussionTopic.PLOT: "请用一句话分析剧情走向，不超过80 tokens。",
            DiscussionTopic.STRUCTURE: "请用一句话指出结构问题，不超过80 tokens。",
            DiscussionTopic.CHARACTER: "请用一句话评价角色决策，不超过80 tokens。",
            DiscussionTopic.CONFLICT: "请用一句话分析冲突强度，不超过80 tokens。",
            DiscussionTopic.WRITING: "请用一句话给出写作建议，不超过80 tokens。",
            DiscussionTopic.READER: "请用一句话描述读者感受，不超过80 tokens。",
        }
        return prompts.get(topic, "请简短回答，不超过80 tokens。")
    
    def get_topic_agents(self, topic: DiscussionTopic) -> List[str]:
        """获取某主题相关的 Agent 列表"""
        return self.default_config.topic_agents.get(topic, [])


# 全局实例
discussion_controller = DiscussionController()


def get_discussion_controller() -> DiscussionController:
    """获取讨论控制器实例"""
    return discussion_controller
