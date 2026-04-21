"""
Agent Communication Protocol - Agent 通信协议
基于 hello-agents 第10章：智能体通信协议

支持：
- Agent 注册与发现
- 消息格式定义
- 同步/异步通信
- 协议版本管理
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import uuid


class MessageType(Enum):
    """消息类型"""
    REQUEST = "request"           # 请求
    RESPONSE = "response"         # 响应
    NOTIFICATION = "notification" # 通知
    ERROR = "error"               # 错误


class AgentCapability(Enum):
    """Agent 能力类型"""
    WRITING = "writing"           # 写作
    PLANNING = "planning"         # 规划
    EDITING = "editing"           # 编辑
    CRITIQUE = "critique"         # 批评
    READING = "reading"           # 阅读
    SUMMARY = "summary"          # 总结
    MEMORY = "memory"            # 记忆
    REASONING = "reasoning"      # 推理
    CREATIVE = "creative"        # 创意


@dataclass
class AgentMessage:
    """Agent 消息"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.REQUEST
    
    # 发送者和接收者
    sender: str = ""
    receiver: str = ""
    
    # 消息内容
    action: str = ""              # 操作名称
    parameters: Dict[str, Any] = field(default_factory=dict)
    content: Any = None           # 消息内容
    
    # 元数据
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    correlation_id: str = ""      # 关联 ID，用于请求/响应配对
    reply_to: str = ""            # 回复地址
    
    # 协议版本
    protocol_version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "sender": self.sender,
            "receiver": self.receiver,
            "action": self.action,
            "parameters": self.parameters,
            "content": self.content,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "protocol_version": self.protocol_version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """从字典创建"""
        msg = cls()
        msg.message_id = data.get("message_id", str(uuid.uuid4()))
        msg.message_type = MessageType(data.get("message_type", "request"))
        msg.sender = data.get("sender", "")
        msg.receiver = data.get("receiver", "")
        msg.action = data.get("action", "")
        msg.parameters = data.get("parameters", {})
        msg.content = data.get("content")
        msg.timestamp = data.get("timestamp", datetime.now().isoformat())
        msg.correlation_id = data.get("correlation_id", "")
        msg.reply_to = data.get("reply_to", "")
        msg.protocol_version = data.get("protocol_version", "1.0")
        return msg


@dataclass
class AgentInfo:
    """Agent 信息"""
    agent_id: str
    name: str
    description: str
    capabilities: List[AgentCapability]
    
    # 连接信息
    endpoint: Optional[str] = None
    protocol_version: str = "1.0"
    
    # 状态
    status: str = "online"
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "capabilities": [c.value for c in self.capabilities],
            "endpoint": self.endpoint,
            "protocol_version": self.protocol_version,
            "status": self.status,
            "last_active": self.last_active,
            "metadata": self.metadata
        }


class AgentRegistry:
    """Agent 注册表 - 管理所有注册的 Agent"""
    
    def __init__(self):
        self._agents: Dict[str, AgentInfo] = {}
        self._handlers: Dict[str, Callable] = {}
    
    def register(self, agent_info: AgentInfo, handler: Callable = None):
        """注册 Agent"""
        self._agents[agent_info.agent_id] = agent_info
        if handler:
            self._handlers[agent_info.agent_id] = handler
    
    def unregister(self, agent_id: str):
        """注销 Agent"""
        if agent_id in self._agents:
            del self._agents[agent_id]
        if agent_id in self._handlers:
            del self._handlers[agent_id]
    
    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """获取 Agent 信息"""
        return self._agents.get(agent_id)
    
    def find_agents_by_capability(self, capability: AgentCapability) -> List[AgentInfo]:
        """根据能力查找 Agent"""
        return [
            agent for agent in self._agents.values()
            if capability in agent.capabilities and agent.status == "online"
        ]
    
    def list_agents(self) -> List[AgentInfo]:
        """列出所有 Agent"""
        return list(self._agents.values())
    
    def get_handler(self, agent_id: str) -> Optional[Callable]:
        """获取 Agent 的处理器"""
        return self._handlers.get(agent_id)
    
    def update_status(self, agent_id: str, status: str):
        """更新 Agent 状态"""
        if agent_id in self._agents:
            self._agents[agent_id].status = status
            self._agents[agent_id].last_active = datetime.now().isoformat()


class AgentRouter:
    """Agent 路由器 - 消息路由"""
    
    def __init__(self, registry: AgentRegistry):
        self.registry = registry
    
    def route(self, message: AgentMessage) -> Optional[AgentInfo]:
        """路由消息到目标 Agent"""
        if message.receiver:
            # 指定接收者
            return self.registry.get_agent(message.receiver)
        
        if message.action:
            # 根据动作路由
            capability = self._action_to_capability(message.action)
            if capability:
                agents = self.registry.find_agents_by_capability(capability)
                if agents:
                    return agents[0]  # 返回第一个匹配的
        
        return None
    
    def _action_to_capability(self, action: str) -> Optional[AgentCapability]:
        """将动作转换为能力"""
        mapping = {
            "write": AgentCapability.WRITING,
            "plan": AgentCapability.PLANNING,
            "edit": AgentCapability.EDITING,
            "critique": AgentCapability.CRITIQUE,
            "read": AgentCapability.READING,
            "summarize": AgentCapability.SUMMARY,
            "remember": AgentCapability.MEMORY,
            "reason": AgentCapability.REASONING,
            "create": AgentCapability.CREATIVE
        }
        return mapping.get(action.lower())


class AgentChannel:
    """Agent 通信通道"""
    
    def __init__(self, registry: AgentRegistry, router: AgentRouter):
        self.registry = registry
        self.router = router
        self._message_queue: List[AgentMessage] = []
        self._pending_requests: Dict[str, AgentMessage] = {}
    
    async def send_message(
        self,
        sender: str,
        receiver: str,
        action: str,
        content: Any = None,
        parameters: Dict[str, Any] = None,
        wait_response: bool = True,
        timeout: float = 30.0
    ) -> Optional[AgentMessage]:
        """
        发送消息
        
        Args:
            sender: 发送者 ID
            receiver: 接收者 ID
            action: 操作名称
            content: 消息内容
            parameters: 参数字典
            wait_response: 是否等待响应
            timeout: 超时时间（秒）
            
        Returns:
            响应消息或 None
        """
        # 创建消息
        message = AgentMessage(
            message_type=MessageType.REQUEST,
            sender=sender,
            receiver=receiver,
            action=action,
            content=content,
            parameters=parameters or {}
        )
        
        if not wait_response:
            # 发送通知，不等待响应
            await self._dispatch(message)
            return None
        
        # 保存待响应请求
        self._pending_requests[message.message_id] = message
        
        # 尝试发送
        response = await self._send_with_timeout(message, timeout)
        
        # 清理
        if message.message_id in self._pending_requests:
            del self._pending_requests[message.message_id]
        
        return response
    
    async def _send_with_timeout(
        self,
        message: AgentMessage,
        timeout: float
    ) -> Optional[AgentMessage]:
        """发送消息并等待响应"""
        await self._dispatch(message)
        
        # 在实际实现中，这里应该有异步等待机制
        # 简化版本，直接返回确认
        return AgentMessage(
            message_type=MessageType.RESPONSE,
            sender=message.receiver,
            receiver=message.sender,
            correlation_id=message.message_id,
            content={"status": "received"}
        )
    
    async def _dispatch(self, message: AgentMessage):
        """分发消息到目标 Agent"""
        target = self.router.route(message)
        if target:
            handler = self.registry.get_handler(target.agent_id)
            if handler:
                try:
                    if hasattr(handler, '__call__'):
                        await handler(message)
                except Exception as e:
                    # 发送错误响应
                    error_msg = AgentMessage(
                        message_type=MessageType.ERROR,
                        sender=target.agent_id,
                        receiver=message.sender,
                        correlation_id=message.message_id,
                        content={"error": str(e)}
                    )
                    # 在实际实现中，这里应该发送回错误消息
    
    def broadcast(self, sender: str, action: str, content: Any):
        """广播消息到所有在线 Agent"""
        for agent in self.registry.list_agents():
            if agent.agent_id != sender and agent.status == "online":
                message = AgentMessage(
                    message_type=MessageType.NOTIFICATION,
                    sender=sender,
                    receiver=agent.agent_id,
                    action=action,
                    content=content
                )
                # 异步发送
                # 在实际实现中，应该使用 asyncio


# 全局实例
_agent_registry: Optional[AgentRegistry] = None
_agent_router: Optional[AgentRouter] = None
_agent_channel: Optional[AgentChannel] = None


def get_agent_registry() -> AgentRegistry:
    """获取 Agent 注册表"""
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry


def get_agent_router() -> AgentRouter:
    """获取 Agent 路由器"""
    global _agent_router
    if _agent_router is None:
        _agent_router = AgentRouter(get_agent_registry())
    return _agent_router


def get_agent_channel() -> AgentChannel:
    """获取 Agent 通信通道"""
    global _agent_channel
    if _agent_channel is None:
        _agent_channel = AgentChannel(get_agent_registry(), get_agent_router())
    return _agent_channel


# 便捷函数
async def send_to_agent(
    sender: str,
    receiver: str,
    action: str,
    content: Any = None,
    parameters: Dict[str, Any] = None
) -> Optional[AgentMessage]:
    """发送消息到 Agent 的便捷函数"""
    channel = get_agent_channel()
    return await channel.send_message(
        sender=sender,
        receiver=receiver,
        action=action,
        content=content,
        parameters=parameters
    )


def register_agent(
    agent_id: str,
    name: str,
    description: str,
    capabilities: List[AgentCapability],
    handler: Callable = None
):
    """注册 Agent 的便捷函数"""
    registry = get_agent_registry()
    info = AgentInfo(
        agent_id=agent_id,
        name=name,
        description=description,
        capabilities=capabilities
    )
    registry.register(info, handler)
    return info


def find_available_agents(capability: AgentCapability) -> List[AgentInfo]:
    """查找具有特定能力的 Agent"""
    return get_agent_registry().find_agents_by_capability(capability)