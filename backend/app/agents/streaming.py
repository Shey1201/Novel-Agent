"""
流式输出支持 - Streaming Response
为 Agent 添加实时流式输出能力
"""
import asyncio
from typing import AsyncGenerator, Generator, Callable, Any, Dict, Optional
import json


class StreamingHandler:
    """流式输出处理器"""
    
    def __init__(self):
        self.chunks: list = []
        
    async def stream_text(self, text: str, delay: float = 0.01) -> AsyncGenerator[str, None]:
        """流式输出文本"""
        for i in range(0, len(text), 10):
            chunk = text[i:i+10]
            self.chunks.append(chunk)
            yield chunk
            await asyncio.sleep(delay)
            
    def get_full_text(self) -> str:
        """获取完整文本"""
        return "".join(self.chunks)


class StreamCallback:
    """流式回调类"""
    
    def __init__(self, on_chunk: Callable[[str], None] = None):
        self.on_chunk = on_chunk
        self.chunks: list = []
        
    def __call__(self, chunk: str):
        """处理每个 chunk"""
        self.chunks.append(chunk)
        if self.on_chunk:
            self.on_chunk(chunk)


def create_stream_response(response_text: str, chunk_size: int = 10) -> Generator[str, None, None]:
    """
    创建流式响应生成器
    
    Args:
        response_text: 完整响应文本
        chunk_size: 每个块的大小
        
    Yields:
        文本块
    """
    for i in range(0, len(response_text), chunk_size):
        yield response_text[i:i+chunk_size]


async def stream_agent_response(
    agent,
    input_data: Dict[str, Any],
    chunk_size: int = 20,
    delay: float = 0.005
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    异步流式运行 Agent
    
    Args:
        agent: Agent 实例
        input_data: 输入数据
        chunk_size: 块大小
        delay: 延迟秒数
        
    Yields:
        包含流式内容的字典
    """
    # 先获取完整结果
    result = agent.run(input_data)
    
    # 提取文本
    text = ""
    if "draft_text" in result:
        text = result["draft_text"]
    elif "plan_text" in result:
        text = result["plan_text"]
    elif "edited_text" in result:
        text = result["edited_text"]
    elif isinstance(result, str):
        text = result
    else:
        # 尝试序列化
        text = json.dumps(result, ensure_ascii=False)
    
    # 流式输出
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i+chunk_size]
        yield {
            "type": "chunk",
            "content": chunk,
            "progress": min(i + chunk_size, len(text)) / len(text) * 100,
            "total": len(text)
        }
        await asyncio.sleep(delay)
    
    # 完成
    yield {
        "type": "done",
        "content": text,
        "progress": 100
    }


# ============ 在 API 中使用流式输出 ============

async def generate_chapter_stream(
    llm,
    outline: str,
    story_id: str = "demo",
    chapter_id: str = "new"
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    流式生成章节
    
    使用示例:
        async for chunk in generate_chapter_stream(llm, "故事大纲"):
            if chunk["type"] == "chunk":
                print(chunk["content"], end="")
    """
    from app.agents.planner_agent import PlannerAgent
    from app.agents.writing_agent import WritingAgent
    from app.agents.conflict_agent import ConflictAgent
    from app.agents.editor_agent import EditorAgent
    from app.agents.summary_agent import SummaryAgent
    
    # Step 1: Planner
    yield {"step": "planner", "status": "started", "message": "正在生成大纲..."}
    planner = PlannerAgent(llm=llm)
    plan_result = planner.run({"text": outline})
    plan_text = plan_result.get("plan_text", "")
    
    yield {"step": "planner", "status": "done", "content": plan_text}
    
    # Step 2: Writing - 流式输出
    yield {"step": "writing", "status": "started", "message": "正在写作..."}
    writer = WritingAgent(llm=llm)
    
    async for chunk in stream_agent_response(writer, {"text": plan_text}):
        yield {"step": "writing", "type": "chunk", "content": chunk.get("content", "")}
    
    write_result = writer.run({"text": plan_text})
    draft_text = write_result.get("draft_text", "")
    
    yield {"step": "writing", "status": "done", "content": draft_text}
    
    # Step 3: Conflict
    yield {"step": "conflict", "status": "started", "message": "分析冲突..."}
    conflict = ConflictAgent(llm=llm)
    conflict_result = conflict.run({"draft_text": draft_text[:500]})
    
    yield {"step": "conflict", "status": "done", "suggestions": conflict_result.get("conflict_suggestions", [])}
    
    # Step 4: Editor
    yield {"step": "editor", "status": "started", "message": "编辑中..."}
    editor = EditorAgent(llm=llm)
    
    async for chunk in stream_agent_response(editor, {"draft_text": draft_text}):
        yield {"step": "editor", "type": "chunk", "content": chunk.get("content", "")}
    
    edit_result = editor.run({"draft_text": draft_text})
    edited_text = edit_result.get("edited_text", "")
    
    yield {"step": "editor", "status": "done", "content": edited_text}
    
    # Step 5: Summary
    yield {"step": "summary", "status": "started", "message": "生成摘要..."}
    summary = SummaryAgent(llm=llm)
    summary_text = summary.run(edited_text)
    
    yield {"step": "summary", "status": "done", "content": summary_text}
    
    # 完成
    yield {"step": "done", "status": "completed", "message": "章节生成完成!"}


# ============ FastAPI 流式响应端点 ============

"""
在 FastAPI 中使用示例:

from fastapi.responses import StreamingResponse

@app.post("/api/generate-chapter/stream")
async def generate_chapter_stream_endpoint(request: GenerateRequest):
    async def event_generator():
        async for chunk in generate_chapter_stream(llm, request.outline):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
"""