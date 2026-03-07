"""
Streaming Optimizer - 流式写作性能优化器
提供多线程/异步流水线优化
"""

import asyncio
import threading
from typing import AsyncIterator, Iterator, Callable, Any, Optional, List, Dict
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import time
import queue


@dataclass
class StreamingMetrics:
    """流式指标"""
    total_tokens: int
    total_time_ms: float
    tokens_per_second: float
    latency_ms: float
    buffer_size: int
    queue_size: int


class AsyncTokenPipeline:
    """
    异步 Token 流水线
    
    使用生产者-消费者模式优化流式输出
    """
    
    def __init__(self, max_buffer_size: int = 100):
        self.max_buffer_size = max_buffer_size
        self.token_queue: asyncio.Queue[str] = asyncio.Queue(maxsize=max_buffer_size)
        self.metrics = {
            "tokens_produced": 0,
            "tokens_consumed": 0,
            "start_time": None,
            "end_time": None
        }
        self._stop_event = asyncio.Event()
    
    async def produce_tokens(
        self,
        token_generator: AsyncIterator[str]
    ):
        """生产者：从生成器获取 Token"""
        self.metrics["start_time"] = time.time()
        
        try:
            async for token in token_generator:
                if self._stop_event.is_set():
                    break
                
                # 非阻塞放入队列
                try:
                    self.token_queue.put_nowait(token)
                    self.metrics["tokens_produced"] += 1
                except asyncio.QueueFull:
                    # 队列满时等待
                    await self.token_queue.put(token)
                    self.metrics["tokens_produced"] += 1
        finally:
            # 发送结束信号
            await self.token_queue.put(None)
            self.metrics["end_time"] = time.time()
    
    async def consume_tokens(self) -> AsyncIterator[str]:
        """消费者：产出 Token 给客户端"""
        while True:
            token = await self.token_queue.get()
            
            if token is None:  # 结束信号
                break
            
            self.metrics["tokens_consumed"] += 1
            yield token
    
    def stop(self):
        """停止流水线"""
        self._stop_event.set()
    
    def get_metrics(self) -> StreamingMetrics:
        """获取性能指标"""
        total_time = (self.metrics["end_time"] or time.time()) - self.metrics["start_time"]
        total_tokens = self.metrics["tokens_consumed"]
        
        return StreamingMetrics(
            total_tokens=total_tokens,
            total_time_ms=total_time * 1000,
            tokens_per_second=total_tokens / total_time if total_time > 0 else 0,
            latency_ms=0,  # 需要更精确的测量
            buffer_size=self.max_buffer_size,
            queue_size=self.token_queue.qsize()
        )


class ParallelChunkProcessor:
    """
    并行块处理器
    
    将长文本分成多个块并行处理，提高整体吞吐量
    """
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def process_chunks_parallel(
        self,
        chunks: List[str],
        process_func: Callable[[str], str]
    ) -> List[str]:
        """
        并行处理多个文本块
        
        Args:
            chunks: 文本块列表
            process_func: 处理函数
            
        Returns:
            处理后的文本块列表
        """
        loop = asyncio.get_event_loop()
        
        # 提交所有任务
        futures = [
            loop.run_in_executor(self.executor, process_func, chunk)
            for chunk in chunks
        ]
        
        # 等待所有完成
        results = await asyncio.gather(*futures, return_exceptions=True)
        
        # 处理异常
        processed = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Chunk {i} processing failed: {result}")
                processed.append(chunks[i])  # 返回原始块
            else:
                processed.append(result)
        
        return processed
    
    def split_text_into_chunks(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[str]:
        """
        将文本分割成重叠的块
        
        Args:
            text: 原始文本
            chunk_size: 每块大小
            overlap: 重叠大小
            
        Returns:
            文本块列表
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap  # 重叠部分
        
        return chunks


class StreamingOptimizer:
    """
    流式写作优化器
    
    提供多种优化策略：
    1. 异步流水线
    2. 预加载/预生成
    3. 智能缓冲
    4. 并行处理
    """
    
    def __init__(self):
        self.pipeline: Optional[AsyncTokenPipeline] = None
        self.chunk_processor = ParallelChunkProcessor()
        self._prefetch_buffer: List[str] = []
        self._prefetch_task: Optional[asyncio.Task] = None
    
    async def optimized_stream(
        self,
        token_generator: AsyncIterator[str],
        enable_pipeline: bool = True,
        enable_buffer: bool = True
    ) -> AsyncIterator[str]:
        """
        优化的流式输出
        
        Args:
            token_generator: 原始 Token 生成器
            enable_pipeline: 启用流水线优化
            enable_buffer: 启用缓冲优化
            
        Yields:
            优化后的 Token
        """
        if not enable_pipeline:
            # 直接透传
            async for token in token_generator:
                yield token
            return
        
        # 使用流水线优化
        self.pipeline = AsyncTokenPipeline(max_buffer_size=50)
        
        # 启动生产者
        producer_task = asyncio.create_task(
            self.pipeline.produce_tokens(token_generator)
        )
        
        try:
            # 消费 Token
            async for token in self.pipeline.consume_tokens():
                if enable_buffer:
                    # 智能缓冲：累积小 Token，批量发送
                    if len(token) < 3:
                        self._prefetch_buffer.append(token)
                        if len(self._prefetch_buffer) >= 5:
                            yield "".join(self._prefetch_buffer)
                            self._prefetch_buffer = []
                    else:
                        # 先发送缓冲区
                        if self._prefetch_buffer:
                            yield "".join(self._prefetch_buffer)
                            self._prefetch_buffer = []
                        yield token
                else:
                    yield token
            
            # 发送剩余缓冲
            if self._prefetch_buffer:
                yield "".join(self._prefetch_buffer)
                self._prefetch_buffer = []
        
        finally:
            # 清理
            if not producer_task.done():
                producer_task.cancel()
                try:
                    await producer_task
                except asyncio.CancelledError:
                    pass
    
    async def prefetch_content(
        self,
        generate_func: Callable[[], AsyncIterator[str]],
        prefetch_size: int = 100
    ):
        """
        预加载内容
        
        在需要前预先生成内容到缓冲区
        """
        self._prefetch_buffer = []
        
        async def _prefetch():
            count = 0
            async for token in generate_func():
                self._prefetch_buffer.append(token)
                count += 1
                if count >= prefetch_size:
                    break
        
        self._prefetch_task = asyncio.create_task(_prefetch())
    
    def get_prefetched(self) -> Optional[str]:
        """获取预加载的内容"""
        if self._prefetch_buffer:
            content = "".join(self._prefetch_buffer)
            self._prefetch_buffer = []
            return content
        return None
    
    def get_metrics(self) -> Optional[StreamingMetrics]:
        """获取性能指标"""
        if self.pipeline:
            return self.pipeline.get_metrics()
        return None


class BatchStreamingManager:
    """
    批量流式管理器
    
    同时管理多个流式请求，提高并发效率
    """
    
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_streams: Dict[str, StreamingOptimizer] = {}
    
    async def create_stream(
        self,
        stream_id: str,
        token_generator: AsyncIterator[str]
    ) -> AsyncIterator[str]:
        """
        创建新的优化流
        
        Args:
            stream_id: 流ID
            token_generator: Token 生成器
            
        Yields:
            Token
        """
        async with self.semaphore:
            optimizer = StreamingOptimizer()
            self.active_streams[stream_id] = optimizer
            
            try:
                async for token in optimizer.optimized_stream(token_generator):
                    yield token
            finally:
                del self.active_streams[stream_id]
    
    def get_stream_metrics(self, stream_id: str) -> Optional[StreamingMetrics]:
        """获取指定流的指标"""
        optimizer = self.active_streams.get(stream_id)
        if optimizer:
            return optimizer.get_metrics()
        return None
    
    def get_all_metrics(self) -> Dict[str, StreamingMetrics]:
        """获取所有活跃流的指标"""
        return {
            stream_id: optimizer.get_metrics()
            for stream_id, optimizer in self.active_streams.items()
            if optimizer.get_metrics()
        }


# 全局实例
_streaming_optimizer: Optional[StreamingOptimizer] = None
_batch_manager: Optional[BatchStreamingManager] = None


def get_streaming_optimizer() -> StreamingOptimizer:
    """获取流式优化器实例"""
    global _streaming_optimizer
    if _streaming_optimizer is None:
        _streaming_optimizer = StreamingOptimizer()
    return _streaming_optimizer


def get_batch_streaming_manager() -> BatchStreamingManager:
    """获取批量流式管理器实例"""
    global _batch_manager
    if _batch_manager is None:
        _batch_manager = BatchStreamingManager()
    return _batch_manager
