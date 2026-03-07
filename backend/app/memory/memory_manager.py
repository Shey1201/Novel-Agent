"""
Memory Manager - 统一记忆管理器
整合 L1 Short Memory, L2 Semantic Memory, L3 Knowledge Graph
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

from app.memory.story_memory import StoryMemory, ChapterSummary
from app.memory.vector_store import VectorStore, get_vector_store
from app.memory.knowledge_graph import KnowledgeGraph, get_knowledge_graph
from app.core.token_optimizer import TokenOptimizer, TokenBudgetManager


@dataclass
class WritingContext:
    """写作上下文"""
    short_memory: str           # L1: 近期摘要
    semantic_memories: List[Dict[str, Any]]  # L2: 向量检索结果
    character_context: Dict[str, Any]        # L3: 角色关系
    world_context: Dict[str, Any]            # L3: 世界设定
    foreshadowing: List[Dict[str, Any]]      # 伏笔提醒
    total_tokens: int


class MemoryManager:
    """
    记忆管理器
    
    职责：
    1. 统一管理三层记忆
    2. 构建写作上下文
    3. Token 预算控制
    4. 自动索引和检索
    """
    
    def __init__(self):
        self.vector_store = get_vector_store()
        self.knowledge_graph = get_knowledge_graph()
        self.token_optimizer = TokenOptimizer()
    
    async def build_writing_context(
        self,
        story_memory: StoryMemory,
        query: str,
        character_ids: List[str] = None,
        budget: int = 6000
    ) -> WritingContext:
        """
        构建写作上下文
        
        Args:
            story_memory: L1 短期记忆
            query: 查询文本（用于RAG）
            character_ids: 当前涉及的角色ID
            budget: Token 预算
            
        Returns:
            写作上下文
        """
        novel_id = story_memory.story_id
        total_tokens = 0
        
        # L1: 短期记忆（最近3章）
        short_memory = self._build_short_memory(story_memory)
        short_memory_tokens = self._estimate_tokens(short_memory)
        total_tokens += short_memory_tokens
        
        # L2: 语义检索
        remaining_budget = budget - total_tokens
        semantic_memories = await self._retrieve_semantic_memories(
            novel_id, query, remaining_budget * 0.5
        )
        semantic_tokens = sum(
            self._estimate_tokens(m["content"]) for m in semantic_memories
        )
        total_tokens += semantic_tokens
        
        # L3: 角色上下文
        remaining_budget = budget - total_tokens
        character_context = {}
        if character_ids:
            for char_id in character_ids[:2]:  # 限制角色数量
                context = self.knowledge_graph.get_character_context(
                    novel_id, char_id
                )
                char_tokens = self._estimate_tokens(json.dumps(context))
                if total_tokens + char_tokens < budget * 0.8:
                    character_context[char_id] = context
                    total_tokens += char_tokens
        
        # L3: 世界上下文（简化版）
        world_context = self._get_world_context(novel_id)
        world_tokens = self._estimate_tokens(json.dumps(world_context))
        if total_tokens + world_tokens < budget:
            total_tokens += world_tokens
        else:
            world_context = {}
        
        # 伏笔提醒
        foreshadowing = self._get_active_foreshadowing(story_memory)
        
        return WritingContext(
            short_memory=short_memory,
            semantic_memories=semantic_memories,
            character_context=character_context,
            world_context=world_context,
            foreshadowing=foreshadowing,
            total_tokens=total_tokens
        )
    
    def _build_short_memory(self, story_memory: StoryMemory) -> str:
        """构建短期记忆文本"""
        if not story_memory.chapter_summaries:
            return "这是小说的开头，没有前文。"
        
        # 获取最近3章
        recent = story_memory.chapter_summaries[-3:]
        parts = []
        for i, summary in enumerate(recent, 1):
            parts.append(f"第{i}章（最近）: {summary.summary}")
        
        return "\n\n".join(parts)
    
    async def _retrieve_semantic_memories(
        self,
        novel_id: str,
        query: str,
        token_budget: float
    ) -> List[Dict[str, Any]]:
        """检索语义记忆"""
        memories = await self.vector_store.search(
            query=query,
            novel_id=novel_id,
            top_k=5
        )
        
        results = []
        total_tokens = 0
        
        for memory in memories:
            content_tokens = self._estimate_tokens(memory.content)
            if total_tokens + content_tokens > token_budget:
                break
            
            results.append({
                "content": memory.content,
                "category": memory.metadata.get("category", "unknown"),
                "score": memory.score,
                "metadata": memory.metadata
            })
            total_tokens += content_tokens
        
        return results
    
    def _get_world_context(self, novel_id: str) -> Dict[str, Any]:
        """获取世界上下文"""
        # 简化版，实际应该从知识图谱查询关键设定
        return {
            "world_rules": "世界基本规则",
            "current_location": "当前地点",
            "time_period": "时间段"
        }
    
    def _get_active_foreshadowing(
        self,
        story_memory: StoryMemory
    ) -> List[Dict[str, Any]]:
        """获取需要处理的伏笔"""
        # 从 StoryMemory 中提取未解决的伏笔
        active_clues = []
        for clue in story_memory.unresolved_clues:
            if clue["status"] == "unresolved":
                active_clues.append(clue)
        return active_clues
    
    def _estimate_tokens(self, text: str) -> int:
        """估算 Token 数量（使用 TokenOptimizer）"""
        return self.token_optimizer.estimator.estimate(text)
    
    def _compress_text(self, text: str, target_tokens: int) -> str:
        """压缩文本到目标 Token 数"""
        return self.token_optimizer.compressor.compress(text, target_tokens, "smart")
    
    async def index_chapter(
        self,
        novel_id: str,
        chapter_id: str,
        chapter_content: str,
        chapter_summary: str,
        characters: List[str],
        locations: List[str]
    ):
        """
        索引章节内容到记忆系统
        
        Args:
            novel_id: 小说ID
            chapter_id: 章节ID
            chapter_content: 章节内容
            chapter_summary: 章节摘要
            characters: 出现的角色
            locations: 出现的地点
        """
        # 1. 更新 L1: StoryMemory（在外部完成）
        
        # 2. 索引到 L2: 向量存储
        # 索引章节摘要
        await self.vector_store.add_memory(
            content=chapter_summary,
            category="plot",
            metadata={
                "chapter_id": chapter_id,
                "type": "chapter_summary",
                "characters": characters,
                "locations": locations
            },
            novel_id=novel_id
        )
        
        # 索引角色信息
        for char in characters:
            await self.vector_store.add_memory(
                content=f"角色 {char} 在第 {chapter_id} 章出现",
                category="characters",
                metadata={
                    "chapter_id": chapter_id,
                    "character_name": char,
                    "type": "appearance"
                },
                novel_id=novel_id
            )
        
        # 3. 更新 L3: 知识图谱
        # 更新角色状态（位置等）
        for char in characters:
            if locations:
                self.knowledge_graph.update_character_state(
                    novel_id=novel_id,
                    character_id=char,
                    state_updates={
                        "current_location": locations[0],
                        "last_appeared": chapter_id
                    }
                )
    
    async def extract_and_index_entities(
        self,
        novel_id: str,
        text: str,
        entity_type: str
    ):
        """
        提取并索引实体
        
        Args:
            novel_id: 小说ID
            text: 文本内容
            entity_type: 实体类型
        """
        # 这里应该使用 NER 模型提取实体
        # 简化版：假设文本中已经标记了实体
        
        if entity_type == "character":
            # 提取角色信息并索引
            pass
        elif entity_type == "location":
            # 提取地点信息并索引
            pass
    
    def format_context_for_prompt(self, context: WritingContext) -> str:
        """
        将上下文格式化为提示词
        
        Args:
            context: 写作上下文
            
        Returns:
            格式化后的提示词
        """
        parts = []
        
        # L1: 短期记忆
        parts.append("【前文摘要】\n" + context.short_memory)
        
        # L2: 语义记忆
        if context.semantic_memories:
            parts.append("\n【相关设定】")
            for mem in context.semantic_memories:
                parts.append(f"- [{mem['category']}] {mem['content']}")
        
        # L3: 角色关系
        if context.character_context:
            parts.append("\n【角色关系】")
            for char_id, char_data in context.character_context.items():
                parts.append(f"- {char_data.get('name', char_id)}")
                if char_data.get('relationships'):
                    for rel in char_data['relationships'][:3]:  # 限制数量
                        parts.append(f"  • {rel['relation']}: {rel['target']}")
        
        # 伏笔提醒
        if context.foreshadowing:
            parts.append("\n【待回收伏笔】")
            for clue in context.foreshadowing[:3]:  # 限制数量
                parts.append(f"- {clue.get('clue', '')}")
        
        return "\n\n".join(parts)
    
    def clear_novel_memory(self, novel_id: str):
        """清空某小说的所有记忆"""
        self.vector_store.clear_novel_memory(novel_id)
        self.knowledge_graph.clear_novel_graph(novel_id)


# 便捷函数
_memory_manager_instance = None

def get_memory_manager() -> MemoryManager:
    """获取记忆管理器实例（单例）"""
    global _memory_manager_instance
    if _memory_manager_instance is None:
        _memory_manager_instance = MemoryManager()
    return _memory_manager_instance
