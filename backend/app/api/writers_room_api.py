"""
Writers Room API
提供讨论创建、消息获取、人工干预等接口
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel

from app.workflow.writers_room import (
    WritersRoom, DiscussionState, AgentMessage, 
    AgentParticipant, Proposal, writers_room
)
from app.agents.base_agent import BaseAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.conflict_agent import ConflictAgent
from app.agents.writing_agent import WritingAgent
from app.agents.consistency_agent import ConsistencyAgent


router = APIRouter(prefix="/api/writers-room", tags=["writers-room"])


# ==================== Pydantic Models ====================

class CreateDiscussionRequest(BaseModel):
    novel_id: str
    title: str
    description: str
    proposed_by: str = "user"
    max_rounds: int = 10
    participant_types: List[str] = ["planner", "conflict", "writing", "consistency"]


class HumanInterventionRequest(BaseModel):
    discussion_id: str
    message: str
    action: str = "comment"  # comment/accept/reject/end


class AgentMessageResponse(BaseModel):
    id: str
    agent_id: str
    agent_name: str
    content: str
    message_type: str
    timestamp: str
    internal_monologue: Optional[str] = None
    reply_to: Optional[str] = None


class DiscussionResponse(BaseModel):
    id: str
    proposal: Dict[str, Any]
    status: str
    consensus_score: float
    round: int
    max_rounds: int
    messages: List[AgentMessageResponse]


# ==================== Helper Functions ====================

def create_agent_participants(types: List[str]) -> List[AgentParticipant]:
    """创建 Agent 参与者"""
    participants = []
    
    # 获取全局 LLM 实例
    from app.core.llm import get_llm
    llm = get_llm()
    
    agent_configs = {
        "planner": {
            "name": "Planner",
            "role": "规划师",
            "instance": PlannerAgent(llm=llm),
            "personality": "analytical",
            "proactivity": 0.7,
            "expertise": ["plot", "structure"]
        },
        "conflict": {
            "name": "Conflict",
            "role": "冲突设计师",
            "instance": ConflictAgent(llm=llm),
            "personality": "passionate",
            "proactivity": 0.8,
            "expertise": ["conflict", "tension"]
        },
        "writing": {
            "name": "Writing",
            "role": "写作专家",
            "instance": WritingAgent(llm=llm),
            "personality": "strict",
            "proactivity": 0.6,
            "expertise": ["prose", "style"]
        },
        "consistency": {
            "name": "Consistency",
            "role": "一致性检查员",
            "instance": ConsistencyAgent(llm=llm),
            "personality": "strict",
            "proactivity": 0.9,
            "expertise": ["world", "character", "plot"]
        }
    }
    
    for agent_type in types:
        if agent_type in agent_configs:
            config = agent_configs[agent_type]
            participants.append(AgentParticipant(
                agent_id=f"agent_{agent_type}",
                agent_name=config["name"],
                agent_role=config["role"],
                agent_instance=config["instance"],
                personality=config["personality"],
                proactivity=config["proactivity"],
                expertise_areas=config["expertise"]
            ))
    
    return participants


def discussion_to_response(state: DiscussionState) -> DiscussionResponse:
    """转换 DiscussionState 为响应格式"""
    return DiscussionResponse(
        id=state.proposal.id.replace("prop_", ""),
        proposal={
            "id": state.proposal.id,
            "title": state.proposal.title,
            "description": state.proposal.description,
            "proposed_by": state.proposal.proposed_by,
            "created_at": state.proposal.created_at.isoformat()
        },
        status=state.status.value,
        consensus_score=state.consensus_score,
        round=state.round,
        max_rounds=state.max_rounds,
        messages=[
            AgentMessageResponse(
                id=msg.id,
                agent_id=msg.agent_id,
                agent_name=msg.agent_name,
                content=msg.content,
                message_type=msg.message_type.value,
                timestamp=msg.timestamp.isoformat(),
                internal_monologue=msg.internal_monologue,
                reply_to=msg.reply_to
            )
            for msg in state.messages
        ]
    )


# ==================== REST API ====================

@router.post("/discussions", response_model=DiscussionResponse)
async def create_discussion(request: CreateDiscussionRequest):
    """创建新讨论"""
    participants = create_agent_participants(request.participant_types)
    
    discussion_id = await writers_room.create_discussion(
        proposal_title=request.title,
        proposal_description=request.description,
        proposed_by=request.proposed_by,
        participants=participants,
        max_rounds=request.max_rounds
    )
    
    state = writers_room.get_discussion(discussion_id)
    return discussion_to_response(state)


@router.get("/discussions/{discussion_id}", response_model=DiscussionResponse)
async def get_discussion(discussion_id: str):
    """获取讨论状态"""
    state = writers_room.get_discussion(discussion_id)
    if not state:
        raise HTTPException(status_code=404, detail="Discussion not found")
    return discussion_to_response(state)


@router.post("/discussions/{discussion_id}/run")
async def run_discussion_round(discussion_id: str):
    """运行一轮讨论"""
    state = writers_room.get_discussion(discussion_id)
    if not state:
        raise HTTPException(status_code=404, detail="Discussion not found")
    
    # 模拟 story_bible（实际应该从数据库获取）
    story_bible = {
        "world_rules": "基本世界规则",
        "character_rules": "角色设定规则"
    }
    
    continue_discussion = await writers_room.run_discussion_round(
        discussion_id, story_bible
    )
    
    state = writers_room.get_discussion(discussion_id)
    return {
        "continue": continue_discussion,
        "discussion": discussion_to_response(state)
    }


@router.post("/discussions/{discussion_id}/intervene")
async def human_intervene(discussion_id: str, request: HumanInterventionRequest):
    """人工干预讨论"""
    state = writers_room.get_discussion(discussion_id)
    if not state:
        raise HTTPException(status_code=404, detail="Discussion not found")
    
    writers_room.human_intervene(
        discussion_id=discussion_id,
        message=request.message,
        action=request.action
    )
    
    state = writers_room.get_discussion(discussion_id)
    return discussion_to_response(state)


@router.post("/discussions/{discussion_id}/run-all")
async def run_full_discussion(discussion_id: str):
    """运行完整讨论直到结束"""
    state = writers_room.get_discussion(discussion_id)
    if not state:
        raise HTTPException(status_code=404, detail="Discussion not found")
    
    story_bible = {
        "world_rules": "基本世界规则",
        "character_rules": "角色设定规则"
    }
    
    # 运行讨论直到结束
    max_iterations = 20
    for _ in range(max_iterations):
        continue_discussion = await writers_room.run_discussion_round(
            discussion_id, story_bible
        )
        if not continue_discussion:
            break
        await asyncio.sleep(0.5)  # 避免请求过快
    
    state = writers_room.get_discussion(discussion_id)
    return discussion_to_response(state)


@router.get("/discussions/{discussion_id}/stats")
async def get_discussion_stats(discussion_id: str):
    """获取讨论统计信息"""
    state = writers_room.get_discussion(discussion_id)
    if not state:
        raise HTTPException(status_code=404, detail="Discussion not found")
    
    stats = writers_room.get_discussion_stats(discussion_id)
    return stats


@router.post("/discussions/{discussion_id}/strategy")
async def set_discussion_strategy(discussion_id: str, strategy: str):
    """
    设置讨论调度策略
    
    Args:
        strategy: round_robin/expertise_based/proactivity_based/balanced/topic_driven
    """
    state = writers_room.get_discussion(discussion_id)
    if not state:
        raise HTTPException(status_code=404, detail="Discussion not found")
    
    valid_strategies = ["round_robin", "expertise_based", "proactivity_based", "balanced", "topic_driven"]
    if strategy not in valid_strategies:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid strategy. Must be one of: {', '.join(valid_strategies)}"
        )
    
    success = writers_room.set_facilitator_strategy(discussion_id, strategy)
    if success:
        return {"message": f"Strategy set to {strategy}", "strategy": strategy}
    else:
        raise HTTPException(status_code=500, detail="Failed to set strategy")


@router.get("/discussions/{discussion_id}/consensus")
async def evaluate_consensus(discussion_id: str):
    """评估当前共识度"""
    state = writers_room.get_discussion(discussion_id)
    if not state:
        raise HTTPException(status_code=404, detail="Discussion not found")
    
    from app.workflow.writers_room import Facilitator
    facilitator = Facilitator()
    result = facilitator.evaluate_consensus(state)
    return result


# ==================== WebSocket ====================

class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, discussion_id: str, websocket: WebSocket):
        await websocket.accept()
        if discussion_id not in self.active_connections:
            self.active_connections[discussion_id] = []
        self.active_connections[discussion_id].append(websocket)
    
    def disconnect(self, discussion_id: str, websocket: WebSocket):
        if discussion_id in self.active_connections:
            self.active_connections[discussion_id].remove(websocket)
    
    async def broadcast(self, discussion_id: str, message: Dict[str, Any]):
        if discussion_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[discussion_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)
            
            # 清理断开的连接
            for conn in disconnected:
                self.active_connections[discussion_id].remove(conn)


manager = ConnectionManager()


@router.websocket("/ws/{discussion_id}")
async def websocket_endpoint(websocket: WebSocket, discussion_id: str):
    """WebSocket 实时讨论"""
    await manager.connect(discussion_id, websocket)
    
    # 注册消息回调
    async def on_new_message(disc_id: str, message: AgentMessage):
        if disc_id == discussion_id:
            await manager.broadcast(disc_id, {
                "type": "new_message",
                "data": {
                    "id": message.id,
                    "agent_id": message.agent_id,
                    "agent_name": message.agent_name,
                    "content": message.content,
                    "message_type": message.message_type.value,
                    "timestamp": message.timestamp.isoformat(),
                    "internal_monologue": message.internal_monologue
                }
            })
    
    writers_room.register_callback(on_new_message)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            
            action = data.get("action")
            
            if action == "intervene":
                # 人工干预
                writers_room.human_intervene(
                    discussion_id=discussion_id,
                    message=data.get("message", ""),
                    action=data.get("intervention_type", "comment")
                )
                
                await manager.broadcast(discussion_id, {
                    "type": "human_intervention",
                    "data": data
                })
            
            elif action == "run_round":
                # 运行一轮
                story_bible = data.get("story_bible", {})
                continue_discussion = await writers_room.run_discussion_round(
                    discussion_id, story_bible
                )
                
                await manager.broadcast(discussion_id, {
                    "type": "round_complete",
                    "data": {"continue": continue_discussion}
                })
            
            elif action == "get_status":
                # 获取状态
                state = writers_room.get_discussion(discussion_id)
                if state:
                    await websocket.send_json({
                        "type": "status",
                        "data": discussion_to_response(state).dict()
                    })
    
    except WebSocketDisconnect:
        manager.disconnect(discussion_id, websocket)
