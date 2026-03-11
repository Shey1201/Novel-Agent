"""
Agent Room 消息 API
通过后端写入 Supabase messages 表，使用 service_role 绕过 RLS，避免前端 anon key 导致 401。
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.memory.novel_memory import novel_memory

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.get("")
def list_messages():
    """获取 Agent Room 历史消息列表（按时间升序）。"""
    if not novel_memory.supabase:
        raise HTTPException(status_code=503, detail="Supabase 未配置或未连接")
    try:
        r = (
            novel_memory.supabase.table("messages")
            .select("id, role, content, agent_id, agent_name, timestamp, created_at")
            .order("created_at", desc=False)
            .execute()
        )
        items = r.data or []
        return {"messages": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CreateMessageRequest(BaseModel):
    role: str
    content: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    timestamp: Optional[str] = None


@router.post("")
def create_message(req: CreateMessageRequest):
    """创建一条消息（Agent Room 输入内容写入 Supabase）。"""
    if not novel_memory.supabase:
        raise HTTPException(status_code=503, detail="Supabase 未配置或未连接")
    try:
        # 与前端一致的匿名用户 ID
        user_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        ts = req.timestamp or datetime.utcnow().isoformat() + "Z"
        if "T" not in ts:
            ts = datetime.utcnow().isoformat() + "Z"
        row = {
            "user_id": user_id,
            "role": req.role,
            "content": req.content,
            "agent_id": req.agent_id,
            "agent_name": req.agent_name,
            "timestamp": ts,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        r = novel_memory.supabase.table("messages").insert(row).execute()
        if not r.data or len(r.data) == 0:
            raise HTTPException(status_code=500, detail="Insert failed, no id returned")
        return {"id": r.data[0]["id"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("")
def clear_messages():
    """清空所有消息（与前端「清空消息」一致）。"""
    if not novel_memory.supabase:
        raise HTTPException(status_code=503, detail="Supabase 未配置或未连接")
    try:
        # 删除所有消息（与前端原逻辑一致：neq 一个不存在的 id 即全删）
        novel_memory.supabase.table("messages").delete().neq(
            "id", "00000000-0000-0000-0000-000000000000"
        ).execute()
        return {"message": "Messages cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
