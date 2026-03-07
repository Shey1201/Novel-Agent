"""
Enhanced Memory System - 增强版记忆系统
RAG + Embedding + 长篇逻辑一致性
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import json
import numpy as np

from langchain_openai import OpenAIEmbeddings


class MemoryTier(Enum):
    """记忆层级"""
    EPISODIC = "episodic"      # 情节记忆（具体事件）
    SEMANTIC = "semantic"      # 语义记忆（概念知识）
    PROCEDURAL = "procedural"  # 程序记忆（写作风格）


class ConsistencyType(Enum):
    """一致性类型"""
    CHARACTER = "character"    # 角色一致性
    PLOT = "plot"             # 情节一致性
    WORLD = "world"           # 世界观一致性
    TIMELINE = "timeline"     # 时间线一致性


@dataclass
class MemoryChunk:
    """记忆块"""
    chunk_id: str
    content: str
    tier: MemoryTier
    novel_id: str
    chapter_id: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance_score: float = 0.5  # 0-1 重要性分数
    access_count: int = 0
    last_accessed: str = field(default_factory=lambda: datetime.now().isoformat())
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "tier": self.tier.value,
            "chapter_id": self.chapter_id,
            "importance_score": self.importance_score,
            "access_count": self.access_count
        }


@dataclass
class LongRangeDependency:
    """长程依赖关系"""
    source_chunk_id: str
    target_chunk_id: str
    dependency_type: str  # cause/effect/parallel/contrast
    strength: float  # 0-1 依赖强度
    chapters_apart: int  # 相隔章节数


@dataclass
class ConsistencyConstraint:
    """一致性约束"""
    constraint_type: ConsistencyType
    entity_id: str  # 角色ID/情节ID等
    attribute: str  # 属性名
    expected_value: Any
    current_value: Any
    violation_severity: float  # 0-1 违规严重程度
    chapter_location: str


class EmbeddingBasedRetriever:
    """
    基于 Embedding 的检索器
    
    支持：
    1. 语义相似度检索
    2. 长程依赖发现
    3. 多跳推理
    """
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.memory_chunks: Dict[str, MemoryChunk] = {}
        self.dependency_graph: Dict[str, List[LongRangeDependency]] = defaultdict(list)
        self.consistency_constraints: Dict[str, List[ConsistencyConstraint]] = defaultdict(list)
    
    async def add_chunk(self, chunk: MemoryChunk) -> str:
        """添加记忆块并生成 Embedding"""
        # 生成 embedding
        chunk.embedding = await self.embeddings.aembed_query(chunk.content)
        
        self.memory_chunks[chunk.chunk_id] = chunk
        
        # 发现长程依赖
        await self._discover_dependencies(chunk)
        
        return chunk.chunk_id
    
    async def retrieve_relevant(
        self,
        query: str,
        novel_id: str,
        top_k: int = 5,
        consistency_check: bool = True
    ) -> Tuple[List[MemoryChunk], List[ConsistencyConstraint]]:
        """
        检索相关记忆块
        
        Args:
            query: 查询文本
            novel_id: 小说ID
            top_k: 返回数量
            consistency_check: 是否检查一致性
            
        Returns:
            (相关记忆块列表, 一致性违规列表)
        """
        # 生成查询 embedding
        query_embedding = await self.embeddings.aembed_query(query)
        
        # 计算相似度
        candidates = [
            chunk for chunk in self.memory_chunks.values()
            if chunk.novel_id == novel_id
        ]
        
        scored_chunks = []
        for chunk in candidates:
            if chunk.embedding:
                similarity = self._cosine_similarity(query_embedding, chunk.embedding)
                # 考虑重要性分数
                final_score = similarity * 0.7 + chunk.importance_score * 0.3
                scored_chunks.append((chunk, final_score))
        
        # 排序并取 top_k
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        top_chunks = [chunk for chunk, _ in scored_chunks[:top_k]]
        
        # 发现长程依赖
        for chunk in top_chunks:
            dependencies = self.dependency_graph.get(chunk.chunk_id, [])
            for dep in dependencies:
                if dep.strength > 0.7 and dep.chapters_apart > 3:
                    # 强长程依赖，添加相关块
                    related_chunk = self.memory_chunks.get(dep.target_chunk_id)
                    if related_chunk and related_chunk not in top_chunks:
                        top_chunks.append(related_chunk)
        
        # 一致性检查
        violations = []
        if consistency_check:
            violations = self._check_consistency(top_chunks, novel_id)
        
        # 更新访问统计
        for chunk in top_chunks:
            chunk.access_count += 1
            chunk.last_accessed = datetime.now().isoformat()
        
        return top_chunks, violations
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """计算余弦相似度"""
        a_array = np.array(a)
        b_array = np.array(b)
        
        dot_product = np.dot(a_array, b_array)
        norm_a = np.linalg.norm(a_array)
        norm_b = np.linalg.norm(b_array)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
    
    async def _discover_dependencies(self, new_chunk: MemoryChunk):
        """发现新记忆块与其他块的依赖关系"""
        if not new_chunk.embedding:
            return
        
        # 查找语义相似的块（可能是因果关系）
        for chunk_id, chunk in self.memory_chunks.items():
            if chunk_id == new_chunk.chunk_id or chunk.novel_id != new_chunk.novel_id:
                continue
            
            if not chunk.embedding:
                continue
            
            similarity = self._cosine_similarity(new_chunk.embedding, chunk.embedding)
            
            # 如果相似度适中（0.5-0.8），可能是相关但不重复的内容
            if 0.5 < similarity < 0.8:
                # 计算章节间隔
                new_chapter = int(new_chunk.chapter_id.split('_')[-1]) if '_' in new_chunk.chapter_id else 0
                old_chapter = int(chunk.chapter_id.split('_')[-1]) if '_' in chunk.chapter_id else 0
                chapters_apart = abs(new_chapter - old_chapter)
                
                if chapters_apart > 0:
                    # 创建依赖关系
                    dependency = LongRangeDependency(
                        source_chunk_id=chunk.chunk_id,
                        target_chunk_id=new_chunk.chunk_id,
                        dependency_type="related",
                        strength=similarity,
                        chapters_apart=chapters_apart
                    )
                    
                    self.dependency_graph[chunk.chunk_id].append(dependency)
    
    def _check_consistency(
        self,
        chunks: List[MemoryChunk],
        novel_id: str
    ) -> List[ConsistencyConstraint]:
        """检查记忆块之间的一致性"""
        violations = []
        
        # 按实体分组检查
        entity_chunks: Dict[str, List[MemoryChunk]] = defaultdict(list)
        
        for chunk in chunks:
            entity_id = chunk.metadata.get("entity_id")
            if entity_id:
                entity_chunks[entity_id].append(chunk)
        
        # 检查每个实体的一致性
        for entity_id, entity_chunk_list in entity_chunks.items():
            if len(entity_chunk_list) < 2:
                continue
            
            # 检查属性一致性
            attributes: Dict[str, List[Any]] = defaultdict(list)
            
            for chunk in entity_chunk_list:
                for attr, value in chunk.metadata.get("attributes", {}).items():
                    attributes[attr].append((value, chunk.chapter_id))
            
            # 发现不一致
            for attr, values in attributes.items():
                if len(values) >= 2:
                    unique_values = set(v[0] for v in values)
                    if len(unique_values) > 1:
                        # 发现不一致
                        violation = ConsistencyConstraint(
                            constraint_type=ConsistencyType.CHARACTER,
                            entity_id=entity_id,
                            attribute=attr,
                            expected_value=values[0][0],
                            current_value=values[-1][0],
                            violation_severity=0.7,
                            chapter_location=values[-1][1]
                        )
                        violations.append(violation)
        
        return violations
    
    def add_consistency_constraint(
        self,
        novel_id: str,
        constraint: ConsistencyConstraint
    ):
        """添加一致性约束"""
        self.consistency_constraints[novel_id].append(constraint)
    
    def get_long_range_context(
        self,
        current_chapter: int,
        novel_id: str,
        lookback_chapters: int = 10
    ) -> List[MemoryChunk]:
        """
        获取长程上下文
        
        检索当前章节之前 lookback_chapters 章的重要记忆
        """
        relevant_chunks = []
        
        for chunk in self.memory_chunks.values():
            if chunk.novel_id != novel_id:
                continue
            
            # 解析章节号
            chunk_chapter = int(chunk.chapter_id.split('_')[-1]) if '_' in chunk.chapter_id else 0
            
            # 检查是否在范围内
            if current_chapter - lookback_chapters <= chunk_chapter < current_chapter:
                # 只选择高重要性或频繁访问的
                if chunk.importance_score > 0.7 or chunk.access_count > 3:
                    relevant_chunks.append(chunk)
        
        # 按重要性排序
        relevant_chunks.sort(key=lambda x: x.importance_score, reverse=True)
        
        return relevant_chunks[:10]  # 最多返回10个


class StoryMemoryEnhancer:
    """
    Story Memory 增强器
    
    结合 Embedding 和 RAG 的长篇逻辑一致性支持
    """
    
    def __init__(self):
        self.retriever = EmbeddingBasedRetriever()
        self.cross_chapter_dependencies: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    async def index_chapter(
        self,
        novel_id: str,
        chapter_id: str,
        chapter_content: str,
        chapter_summary: str,
        key_events: List[Dict[str, Any]]
    ):
        """
        索引章节内容
        
        将章节内容分割成多个记忆块并建立索引
        """
        # 创建章节摘要块
        summary_chunk = MemoryChunk(
            chunk_id=f"{novel_id}_{chapter_id}_summary",
            content=chapter_summary,
            tier=MemoryTier.SEMANTIC,
            novel_id=novel_id,
            chapter_id=chapter_id,
            importance_score=0.9,  # 摘要很重要
            metadata={
                "type": "summary",
                "events": key_events
            }
        )
        
        await self.retriever.add_chunk(summary_chunk)
        
        # 分割内容成情节块
        segments = self._segment_content(chapter_content)
        
        for i, segment in enumerate(segments):
            chunk = MemoryChunk(
                chunk_id=f"{novel_id}_{chapter_id}_seg_{i}",
                content=segment["content"],
                tier=MemoryTier.EPISODIC,
                novel_id=novel_id,
                chapter_id=chapter_id,
                importance_score=segment.get("importance", 0.5),
                metadata=segment.get("metadata", {})
            )
            
            await self.retriever.add_chunk(chunk)
        
        # 建立跨章节依赖
        await self._build_cross_chapter_dependencies(novel_id, chapter_id, key_events)
    
    def _segment_content(self, content: str) -> List[Dict[str, Any]]:
        """将内容分割成段落"""
        segments = []
        
        # 按场景分割（简单实现：按空行分割）
        scenes = content.split('\n\n')
        
        for i, scene in enumerate(scenes):
            if not scene.strip():
                continue
            
            # 估算重要性
            importance = 0.5
            
            # 包含对话的重要性更高
            if '"' in scene or '"' in scene:
                importance += 0.2
            
            # 包含动作描述的重要性更高
            action_keywords = ['突然', '立刻', '立即', '瞬间', '猛地']
            if any(kw in scene for kw in action_keywords):
                importance += 0.15
            
            segments.append({
                "content": scene,
                "importance": min(importance, 1.0),
                "metadata": {
                    "scene_index": i,
                    "has_dialogue": '"' in scene or '"' in scene
                }
            })
        
        return segments
    
    async def _build_cross_chapter_dependencies(
        self,
        novel_id: str,
        chapter_id: str,
        key_events: List[Dict[str, Any]]
    ):
        """建立跨章节依赖关系"""
        current_chapter_num = int(chapter_id.split('_')[-1]) if '_' in chapter_id else 0
        
        for event in key_events:
            # 查找之前章节的关联事件
            for dep in self.cross_chapter_dependencies[novel_id]:
                if dep["event_type"] == event.get("type"):
                    chapters_apart = current_chapter_num - dep["chapter_num"]
                    
                    if 0 < chapters_apart <= 10:  # 10章内的关联
                        self.cross_chapter_dependencies[novel_id].append({
                            "source_chapter": dep["chapter_id"],
                            "target_chapter": chapter_id,
                            "event_type": event.get("type"),
                            "chapters_apart": chapters_apart,
                            "relation": "continuation"
                        })
            
            # 记录当前事件
            self.cross_chapter_dependencies[novel_id].append({
                "chapter_id": chapter_id,
                "chapter_num": current_chapter_num,
                "event_type": event.get("type"),
                "event_description": event.get("description", "")
            })
    
    async def get_enhanced_context(
        self,
        novel_id: str,
        current_chapter: int,
        query: str,
        character_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        获取增强的写作上下文
        
        结合 RAG 检索和长程逻辑一致性检查
        """
        # 1. 语义检索相关记忆
        relevant_chunks, violations = await self.retriever.retrieve_relevant(
            query=query,
            novel_id=novel_id,
            top_k=5,
            consistency_check=True
        )
        
        # 2. 获取长程上下文
        long_range_chunks = self.retriever.get_long_range_context(
            current_chapter=current_chapter,
            novel_id=novel_id,
            lookback_chapters=10
        )
        
        # 3. 获取跨章节依赖
        cross_chapter_deps = [
            dep for dep in self.cross_chapter_dependencies[novel_id]
            if isinstance(dep, dict) and dep.get("target_chapter", "").endswith(str(current_chapter))
        ]
        
        # 4. 组装上下文
        context = {
            "relevant_memories": [c.to_dict() for c in relevant_chunks],
            "long_range_context": [c.to_dict() for c in long_range_chunks],
            "cross_chapter_dependencies": cross_chapter_deps[:5],  # 最多5个
            "consistency_violations": [
                {
                    "entity_id": v.entity_id,
                    "attribute": v.attribute,
                    "expected": v.expected_value,
                    "current": v.current_value,
                    "severity": v.violation_severity
                }
                for v in violations
            ],
            "warnings": self._generate_warnings(violations),
            "suggestions": self._generate_suggestions(relevant_chunks, long_range_chunks)
        }
        
        return context
    
    def _generate_warnings(self, violations: List[ConsistencyConstraint]) -> List[str]:
        """生成一致性警告"""
        warnings = []
        
        for v in violations:
            if v.violation_severity > 0.8:
                warnings.append(
                    f"⚠️ 严重不一致：{v.entity_id} 的 {v.attribute} "
                    f"从 '{v.expected_value}' 变为 '{v.current_value}'"
                )
            elif v.violation_severity > 0.5:
                warnings.append(
                    f"💡 可能不一致：{v.entity_id} 的 {v.attribute} 有变化"
                )
        
        return warnings
    
    def _generate_suggestions(
        self,
        relevant_chunks: List[MemoryChunk],
        long_range_chunks: List[MemoryChunk]
    ) -> List[str]:
        """生成写作建议"""
        suggestions = []
        
        # 基于长程上下文建议
        if long_range_chunks:
            important_past = [c for c in long_range_chunks if c.importance_score > 0.8]
            if important_past:
                suggestions.append(
                    f"📚 建议回顾：第{important_past[0].chapter_id}章的重要情节 "
                    f"'{important_past[0].content[:50]}...'"
                )
        
        # 基于相关记忆建议
        if relevant_chunks:
            foreshadowing_chunks = [
                c for c in relevant_chunks
                if c.metadata.get("type") == "foreshadowing"
            ]
            if foreshadowing_chunks:
                suggestions.append(
                    f"🔮 伏笔提醒：之前埋下的伏笔 "
                    f"'{foreshadowing_chunks[0].content[:50]}...' 还未解决"
                )
        
        return suggestions


# 全局实例
_enhanced_memory: Optional[StoryMemoryEnhancer] = None


def get_enhanced_memory() -> StoryMemoryEnhancer:
    """获取增强版记忆系统实例"""
    global _enhanced_memory
    if _enhanced_memory is None:
        _enhanced_memory = StoryMemoryEnhancer()
    return _enhanced_memory
