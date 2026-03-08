"""
Agent 管理 API 路由
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.memory.agent_memory import agent_memory

router = APIRouter(prefix="/api/agents", tags=["agents"])


# ========== 数据模型 ==========

class AgentUpdateRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    personality: Optional[str] = None
    temperature: Optional[float] = None
    prompt: Optional[str] = None
    enabled: Optional[bool] = None


class AgentConfigResponse(BaseModel):
    id: str
    agent_id: str
    name: str
    role: str
    personality: str
    temperature: float
    prompt: str
    enabled: bool
    created_at: str
    updated_at: str


# ========== Agent API ==========

@router.get("/configs", response_model=List[AgentConfigResponse])
async def get_agent_configs():
    """获取所有 Agent 配置"""
    print("[API] GET /api/agents/configs called")
    configs = agent_memory.get_all_configs()
    print(f"[API] Returning {len(configs)} agent configs")
    return [
        AgentConfigResponse(
            id=c.id,
            agent_id=c.agent_id,
            name=c.name,
            role=c.role,
            personality=c.personality,
            temperature=c.temperature,
            prompt=c.prompt,
            enabled=c.enabled,
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        for c in configs
    ]


@router.get("/configs/{agent_id}", response_model=AgentConfigResponse)
async def get_agent_config(agent_id: str):
    """获取单个 Agent 配置"""
    config = agent_memory.get_config(agent_id)
    if not config:
        raise HTTPException(status_code=404, detail="Agent config not found")
    return AgentConfigResponse(
        id=config.id,
        agent_id=config.agent_id,
        name=config.name,
        role=config.role,
        personality=config.personality,
        temperature=config.temperature,
        prompt=config.prompt,
        enabled=config.enabled,
        created_at=config.created_at,
        updated_at=config.updated_at
    )


@router.put("/configs/{agent_id}", response_model=AgentConfigResponse)
async def update_agent_config(agent_id: str, request: AgentUpdateRequest):
    """更新 Agent 配置"""
    try:
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.role is not None:
            updates["role"] = request.role
        if request.personality is not None:
            updates["personality"] = request.personality
        if request.temperature is not None:
            updates["temperature"] = request.temperature
        if request.prompt is not None:
            updates["prompt"] = request.prompt
        if request.enabled is not None:
            updates["enabled"] = request.enabled
        
        config = agent_memory.update_config(agent_id, **updates)
        if not config:
            raise HTTPException(status_code=404, detail="Agent config not found")
        
        return AgentConfigResponse(
            id=config.id,
            agent_id=config.agent_id,
            name=config.name,
            role=config.role,
            personality=config.personality,
            temperature=config.temperature,
            prompt=config.prompt,
            enabled=config.enabled,
            created_at=config.created_at,
            updated_at=config.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update agent config: {str(e)}")


@router.post("/configs", response_model=AgentConfigResponse)
async def create_agent_config(request: AgentUpdateRequest):
    """创建新的 Agent 配置"""
    try:
        # 生成 agent_id（使用时间戳和随机数）
        import uuid
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        
        config = agent_memory.create_config(
            agent_id=agent_id,
            name=request.name or agent_id,
            role=request.role or "",
            personality=request.personality or "balanced",
            temperature=request.temperature or 0.7,
            prompt=request.prompt or "",
            enabled=request.enabled if request.enabled is not None else True
        )
        
        if not config:
            raise HTTPException(status_code=500, detail="Failed to create agent config")
        
        return AgentConfigResponse(
            id=config.id,
            agent_id=config.agent_id,
            name=config.name,
            role=config.role,
            personality=config.personality,
            temperature=config.temperature,
            prompt=config.prompt,
            enabled=config.enabled,
            created_at=config.created_at,
            updated_at=config.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create agent config: {str(e)}")


@router.post("/configs/{agent_id}/sync", response_model=AgentConfigResponse)
async def sync_agent_config(agent_id: str, request: AgentUpdateRequest):
    """同步 Agent 配置（如果不存在则创建）"""
    print(f"[API] POST /api/agents/configs/{agent_id}/sync called")
    print(f"[API] Request data: {request}")
    try:
        # 先尝试获取
        config = agent_memory.get_config(agent_id)
        print(f"[API] Existing config: {config}")
        
        if config:
            # 存在则更新
            print(f"[API] Updating existing config for {agent_id}")
            updates = {}
            if request.name is not None:
                updates["name"] = request.name
            if request.role is not None:
                updates["role"] = request.role
            if request.personality is not None:
                updates["personality"] = request.personality
            if request.temperature is not None:
                updates["temperature"] = request.temperature
            if request.prompt is not None:
                updates["prompt"] = request.prompt
            if request.enabled is not None:
                updates["enabled"] = request.enabled
            
            config = agent_memory.update_config(agent_id, **updates)
            print(f"[API] Updated config: {config}")
        else:
            # 不存在则创建
            print(f"[API] Creating new config for {agent_id}")
            try:
                config = agent_memory.create_config(
                    agent_id=agent_id,
                    name=request.name or agent_id,
                    role=request.role or "",
                    personality=request.personality or "balanced",
                    temperature=request.temperature or 0.7,
                    prompt=request.prompt or "",
                    enabled=request.enabled if request.enabled is not None else True
                )
                print(f"[API] Created config: {config}")
            except Exception as create_error:
                # 如果创建失败（可能是唯一约束冲突），尝试再次查询
                print(f"[API] Create failed, retrying get: {create_error}")
                config = agent_memory.get_config(agent_id)
                if config:
                    # 现在存在了，执行更新
                    print(f"[API] Config now exists, updating instead")
                    updates = {}
                    if request.name is not None:
                        updates["name"] = request.name
                    if request.role is not None:
                        updates["role"] = request.role
                    if request.personality is not None:
                        updates["personality"] = request.personality
                    if request.temperature is not None:
                        updates["temperature"] = request.temperature
                    if request.prompt is not None:
                        updates["prompt"] = request.prompt
                    if request.enabled is not None:
                        updates["enabled"] = request.enabled
                    config = agent_memory.update_config(agent_id, **updates)
                else:
                    raise create_error
        
        if not config:
            print(f"[API] ERROR: Failed to sync config for {agent_id}")
            raise HTTPException(status_code=500, detail="Failed to sync agent config")
        
        return AgentConfigResponse(
            id=config.id,
            agent_id=config.agent_id,
            name=config.name,
            role=config.role,
            personality=config.personality,
            temperature=config.temperature,
            prompt=config.prompt,
            enabled=config.enabled,
            created_at=config.created_at,
            updated_at=config.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync agent config: {str(e)}")
