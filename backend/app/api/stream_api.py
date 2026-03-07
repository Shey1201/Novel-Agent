"""
Stream API - SSE 流式写作接口
提供实时 AI 写作体验
"""

import json
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agents.writing_agent import WritingAgent
from app.memory.memory_manager import get_memory_manager, WritingContext
from app.memory.story_memory import StoryMemory


router = APIRouter(prefix="/api/stream", tags=["stream"])


# ==================== Pydantic Models ====================

class StreamWriteRequest(BaseModel):
    novel_id: str
    chapter_id: str
    plan_text: str
    conflict_suggestions: Optional[list] = None
    constraints: Optional[Dict[str, Any]] = None
    writing_mode: str = "ai-assisted"  # manual/ai-assisted/ai-writer


class StreamToken(BaseModel):
    type: str  # token/complete/error/progress
    content: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# ==================== SSE Streaming ====================

async def generate_stream(
    request: StreamWriteRequest,
    story_memory: StoryMemory
) -> AsyncGenerator[str, None]:
    """
    生成 SSE 流
    
    事件类型：
    - token: 生成的文本片段
    - progress: 进度更新
    - complete: 完成
    - error: 错误
    """
    try:
        # 1. 发送开始事件
        yield f"data: {json.dumps({'type': 'start', 'data': {'chapter_id': request.chapter_id}})}\n\n"
        
        # 2. 构建上下文
        memory_manager = get_memory_manager()
        
        # 构建查询文本
        query = f"{request.plan_text} {' '.join(request.conflict_suggestions or [])}"
        
        context = await memory_manager.build_writing_context(
            story_memory=story_memory,
            query=query,
            budget=6000
        )
        
        # 发送上下文准备完成
        yield f"data: {json.dumps({'type': 'progress', 'data': {'step': 'context_ready', 'tokens': context.total_tokens}})}\n\n"
        
        # 3. 初始化写作 Agent
        writing_agent = WritingAgent()
        
        # 构建输入
        base_input = f"[大纲]\n{request.plan_text}\n\n"
        if request.conflict_suggestions:
            base_input += f"[冲突建议]\n{request.conflict_suggestions}\n\n"
        
        # 添加上下文
        context_text = memory_manager.format_context_for_prompt(context)
        full_input = f"{context_text}\n\n{base_input}"
        
        # 4. 流式生成
        accumulated_text = ""
        token_count = 0
        
        # 这里模拟流式生成，实际应该调用支持 stream 的 LLM
        # 为了演示，我们将生成的文本分段发送
        
        # 先发送一个模拟的 "thinking" 阶段
        yield f"data: {json.dumps({'type': 'progress', 'data': {'step': 'generating', 'agent': 'writing'}})}\n\n"
        await asyncio.sleep(0.5)
        
        # 模拟流式输出（实际应该使用 LLM 的 stream 接口）
        # 这里使用非流式生成然后分段发送作为演示
        result = writing_agent.run({"text": full_input})
        generated_text = result.get("draft_text", "")
        
        # 分段发送（每 10-20 个字符一段，模拟打字效果）
        chunk_size = 15
        for i in range(0, len(generated_text), chunk_size):
            chunk = generated_text[i:i+chunk_size]
            accumulated_text += chunk
            token_count += len(chunk)
            
            yield f"data: {json.dumps({'type': 'token', 'content': chunk, 'data': {'total_tokens': token_count}})}\n\n"
            
            # 模拟打字延迟
            await asyncio.sleep(0.05)
        
        # 5. 发送完成事件
        yield f"data: {json.dumps({'type': 'complete', 'data': {'full_text': accumulated_text, 'total_tokens': token_count}})}\n\n"
        
    except Exception as e:
        # 发送错误事件
        yield f"data: {json.dumps({'type': 'error', 'data': {'message': str(e)}})}\n\n"


@router.post("/write")
async def stream_write(request: StreamWriteRequest):
    """
    流式写作接口
    
    使用 SSE (Server-Sent Events) 实时返回生成的文本
    """
    # 获取或创建 story_memory
    # 实际应该从数据库获取
    story_memory = StoryMemory(
        story_id=request.novel_id,
        global_summary="",
        chapter_summaries=[],
        character_profiles={},
        world_settings={}
    )
    
    return StreamingResponse(
        generate_stream(request, story_memory),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
        }
    )


# ==================== Agent Execution Stream ====================

class AgentExecutionStream:
    """
    Agent 执行流 - 用于可视化 Agent 执行过程
    """
    
    def __init__(self):
        self.subscribers: list = []
    
    def subscribe(self, callback):
        """订阅执行事件"""
        self.subscribers.append(callback)
    
    async def publish(self, event: Dict[str, Any]):
        """发布事件"""
        for callback in self.subscribers:
            try:
                await callback(event)
            except:
                pass
    
    async def agent_start(self, agent_name: str, input_data: Dict[str, Any]):
        """Agent 开始执行"""
        await self.publish({
            "type": "agent_start",
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "input": input_data
        })
    
    async def agent_thinking(self, agent_name: str, thought: str):
        """Agent 思考过程"""
        await self.publish({
            "type": "agent_thinking",
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "thought": thought
        })
    
    async def agent_complete(self, agent_name: str, output_data: Dict[str, Any]):
        """Agent 执行完成"""
        await self.publish({
            "type": "agent_complete",
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "output": output_data
        })
    
    async def quality_check(self, score: float, breakdown: Dict[str, float]):
        """质量检查结果"""
        await self.publish({
            "type": "quality_check",
            "timestamp": datetime.now().isoformat(),
            "score": score,
            "breakdown": breakdown
        })
    
    async def rewrite_triggered(self, reason: str, iteration: int):
        """触发重写"""
        await self.publish({
            "type": "rewrite",
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "iteration": iteration
        })


# 全局执行流实例
execution_stream = AgentExecutionStream()


@router.get("/execution/{workflow_id}")
async def stream_execution(workflow_id: str):
    """
    流式获取 Agent 执行过程
    
    用于可视化 Agent 执行时间线
    """
    async def event_generator():
        queue = asyncio.Queue()
        
        async def callback(event):
            await queue.put(event)
        
        execution_stream.subscribe(callback)
        
        try:
            while True:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.TimeoutError:
            yield f"data: {json.dumps({'type': 'timeout'})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


# ==================== Progress API ====================

@router.get("/progress/{workflow_id}")
async def get_progress(workflow_id: str):
    """获取工作流执行进度"""
    # 实际应该从工作流状态中获取
    return {
        "workflow_id": workflow_id,
        "status": "running",
        "current_agent": "writing",
        "progress": 0.6,
        "completed_agents": ["planner", "conflict"],
        "pending_agents": ["editor", "reader", "critic"]
    }
