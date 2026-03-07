"""
Streaming Writer - 流式/分段写作生成器
将长章节分段生成，控制 Token 使用
"""

from typing import Dict, List, Optional, Any, AsyncGenerator, Callable
from dataclasses import dataclass
from enum import Enum
import asyncio


class ParagraphStatus(Enum):
    """段落状态"""
    PENDING = "pending"      # 等待生成
    GENERATING = "generating" # 生成中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"        # 失败


@dataclass
class Paragraph:
    """段落"""
    index: int
    target_length: int       # 目标字数
    content: str = ""
    status: ParagraphStatus = ParagraphStatus.PENDING
    tokens_used: int = 0


@dataclass
class StreamingConfig:
    """流式生成配置"""
    paragraph_length: int = 500      # 每段目标字数
    max_paragraphs: int = 10         # 最大段落数
    overlap_sentences: int = 1       # 段落间重叠句子数（保持连贯）
    enable_streaming: bool = True    # 启用流式输出


class StreamingWriter:
    """
    流式/分段写作生成器
    
    将章节写作分解为多个小段：
    1. 段落1 (500字)
    2. 段落2 (500字) - 承接上文
    3. 段落3 (500字) - 承接上文
    ...
    
    优势：
    - Token 更可控
    - 避免一次性生成失败
    - 支持流式输出
    """
    
    def __init__(self, config: Optional[StreamingConfig] = None):
        self.config = config or StreamingConfig()
        self.paragraphs: List[Paragraph] = []
        
    def plan_paragraphs(
        self,
        chapter_outline: str,
        target_total_length: int = 3000
    ) -> List[Paragraph]:
        """
        规划段落结构
        
        Args:
            chapter_outline: 章节大纲
            target_total_length: 目标总字数
            
        Returns:
            段落列表
        """
        # 计算需要的段落数
        num_paragraphs = max(
            1,
            min(
                target_total_length // self.config.paragraph_length,
                self.config.max_paragraphs
            )
        )
        
        # 调整每段长度
        actual_paragraph_length = target_total_length // num_paragraphs
        
        self.paragraphs = [
            Paragraph(
                index=i,
                target_length=actual_paragraph_length
            )
            for i in range(num_paragraphs)
        ]
        
        return self.paragraphs
    
    def build_paragraph_prompt(
        self,
        paragraph: Paragraph,
        chapter_context: str,
        previous_content: str = "",
        plot_progress: str = ""
    ) -> str:
        """
        构建段落生成提示词
        
        Args:
            paragraph: 当前段落
            chapter_context: 章节上下文
            previous_content: 上一段内容（用于连贯）
            plot_progress: 当前剧情进展
            
        Returns:
            提示词
        """
        prompt = f"""[章节上下文]
{chapter_context}

"""
        
        # 添加上文（用于连贯）
        if previous_content:
            # 提取上一段最后几句
            sentences = previous_content.split("。")
            overlap = "。".join(sentences[-self.config.overlap_sentences:])
            prompt += f"""[上文结尾]
{overlap}

"""
        
        # 添加剧情进展提示
        if plot_progress:
            prompt += f"""[剧情进展]
{plot_progress}

"""
        
        # 段落生成指令
        prompt += f"""[写作任务]
请继续创作第 {paragraph.index + 1} 段，约 {paragraph.target_length} 字。

要求：
1. 承接上文，保持情节连贯
2. 推进剧情发展
3. 控制字数在 {paragraph.target_length - 50} 到 {paragraph.target_length + 50} 字之间
4. 段落结尾要有自然的过渡

请直接输出段落内容，不要添加标题或说明。
"""
        
        return prompt
    
    async def generate_paragraph(
        self,
        paragraph: Paragraph,
        prompt: str,
        generate_func: Callable[[str], Any],
        token_budget: Optional[int] = None
    ) -> Paragraph:
        """
        生成单个段落
        
        Args:
            paragraph: 段落对象
            prompt: 提示词
            generate_func: 生成函数
            token_budget: Token 预算
            
        Returns:
            更新后的段落
        """
        paragraph.status = ParagraphStatus.GENERATING
        
        try:
            # 调用生成函数
            result = await generate_func(prompt)
            
            # 提取内容
            if isinstance(result, dict):
                content = result.get("content", "")
                tokens_used = result.get("tokens_used", 0)
            else:
                content = str(result)
                tokens_used = len(content) * 1.5  # 估算
            
            paragraph.content = content
            paragraph.tokens_used = int(tokens_used)
            paragraph.status = ParagraphStatus.COMPLETED
            
        except Exception as e:
            paragraph.status = ParagraphStatus.FAILED
            paragraph.content = f"[生成失败: {str(e)}]"
        
        return paragraph
    
    async def generate_chapter(
        self,
        chapter_outline: str,
        chapter_context: str,
        generate_func: Callable[[str], Any],
        target_length: int = 3000,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        生成完整章节
        
        Args:
            chapter_outline: 章节大纲
            chapter_context: 章节上下文
            generate_func: 生成函数
            target_length: 目标字数
            progress_callback: 进度回调函数(current, total)
            
        Returns:
            生成结果
        """
        # 规划段落
        paragraphs = self.plan_paragraphs(chapter_outline, target_length)
        total_paragraphs = len(paragraphs)
        
        full_content = []
        total_tokens = 0
        
        for i, paragraph in enumerate(paragraphs):
            # 构建提示词
            previous_content = full_content[-1] if full_content else ""
            plot_progress = f"已完成 {i}/{total_paragraphs} 段"
            
            prompt = self.build_paragraph_prompt(
                paragraph,
                chapter_context,
                previous_content,
                plot_progress
            )
            
            # 生成段落
            result = await self.generate_paragraph(
                paragraph,
                prompt,
                generate_func
            )
            
            if result.status == ParagraphStatus.COMPLETED:
                full_content.append(result.content)
                total_tokens += result.tokens_used
            
            # 更新进度
            if progress_callback:
                progress_callback(i + 1, total_paragraphs)
        
        return {
            "content": "\n\n".join(full_content),
            "paragraphs": [
                {
                    "index": p.index,
                    "content": p.content,
                    "tokens_used": p.tokens_used,
                    "status": p.status.value
                }
                for p in paragraphs
            ],
            "total_tokens": total_tokens,
            "total_paragraphs": total_paragraphs,
            "completed_paragraphs": sum(
                1 for p in paragraphs
                if p.status == ParagraphStatus.COMPLETED
            )
        }
    
    async def generate_streaming(
        self,
        chapter_outline: str,
        chapter_context: str,
        stream_func: Callable[[str], AsyncGenerator[str, None]],
        target_length: int = 3000
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式生成章节
        
        逐段生成并流式输出
        
        Args:
            chapter_outline: 章节大纲
            chapter_context: 章节上下文
            stream_func: 流式生成函数
            target_length: 目标字数
            
        Yields:
            生成进度和段落内容
        """
        paragraphs = self.plan_paragraphs(chapter_outline, target_length)
        total_paragraphs = len(paragraphs)
        
        full_content = []
        
        for i, paragraph in enumerate(paragraphs):
            previous_content = full_content[-1] if full_content else ""
            plot_progress = f"已完成 {i}/{total_paragraphs} 段"
            
            prompt = self.build_paragraph_prompt(
                paragraph,
                chapter_context,
                previous_content,
                plot_progress
            )
            
            # 流式生成
            paragraph_content = []
            async for chunk in stream_func(prompt):
                paragraph_content.append(chunk)
                yield {
                    "type": "chunk",
                    "paragraph_index": i,
                    "content": chunk,
                    "progress": {
                        "current": i + 1,
                        "total": total_paragraphs
                    }
                }
            
            # 段落完成
            full_text = "".join(paragraph_content)
            full_content.append(full_text)
            
            yield {
                "type": "paragraph_complete",
                "paragraph_index": i,
                "content": full_text,
                "progress": {
                    "current": i + 1,
                    "total": total_paragraphs
                }
            }
        
        # 全部完成
        yield {
            "type": "complete",
            "content": "\n\n".join(full_content),
            "total_paragraphs": total_paragraphs
        }


class ReaderAgentScheduler:
    """
    Reader Agent 调度器
    
    控制 Reader Agent 的调用频率
    每3章调用一次，而不是每章
    """
    
    def __init__(self, interval: int = 3):
        self.interval = interval  # 调用间隔（章数）
        self.last_call_chapter: Dict[str, int] = {}  # novel_id -> chapter_number
        
    def should_call_reader(
        self,
        novel_id: str,
        chapter_number: int,
        force: bool = False
    ) -> bool:
        """
        检查是否应该调用 Reader Agent
        
        Args:
            novel_id: 小说 ID
            chapter_number: 当前章节号
            force: 强制调用
            
        Returns:
            是否应该调用
        """
        if force:
            return True
        
        last_call = self.last_call_chapter.get(novel_id, 0)
        
        # 检查是否达到间隔
        if chapter_number - last_call >= self.interval:
            return True
        
        # 特殊章节也调用（如关键剧情节点）
        if chapter_number % 10 == 0:  # 每10章
            return True
        
        return False
    
    def record_call(self, novel_id: str, chapter_number: int):
        """记录调用"""
        self.last_call_chapter[novel_id] = chapter_number
    
    def get_next_call_chapter(self, novel_id: str, current_chapter: int) -> int:
        """获取下次应该调用的章节"""
        return current_chapter + self.interval


# 全局实例
streaming_writer = StreamingWriter()
reader_scheduler = ReaderAgentScheduler()


def get_streaming_writer() -> StreamingWriter:
    """获取流式写作器实例"""
    return streaming_writer


def get_reader_scheduler() -> ReaderAgentScheduler:
    """获取 Reader 调度器实例"""
    return reader_scheduler
