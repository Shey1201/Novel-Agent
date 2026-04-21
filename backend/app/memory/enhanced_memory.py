"""
Enhanced Memory System - 增强的记忆系统
基于 hello-agents 第8章：记忆与检索

增强功能：
- RAG 语义检索
- 长期记忆存储
- 记忆索引优化
- 主动记忆召回
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import hashlib


class MemoryType(Enum):
    """记忆类型"""
    EPISODIC = "episodic"         # 情节记忆
    SEMANTIC = "semantic"         # 语义记忆
    PROCEDURAL = "procedural"     # 程序记忆（操作流程）
    WORKING = "working"          # 工作记忆（当前任务）


class MemoryPriority(Enum):
    """记忆优先级"""
    HIGH = 3      # 高优先级（重要情节、关键角色）
    MEDIUM = 2    # 中等优先级（普通情节）
    LOW = 1       # 低优先级（细节）


@dataclass
class MemoryEntry:
    """记忆条目"""
    memory_id: str
    content: str
    memory_type: MemoryType
    
    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0
    
    # 关联
    novel_id: str = ""
    chapter_id: str = ""
    entity_ids: List[str] = field(default_factory=list)
    
    # 语义信息
    embedding: Optional[List[float]] = None
    keywords: List[str] = field(default_factory=list)
    summary: str = ""
    
    # 优先级
    priority: MemoryPriority = MemoryPriority.MEDIUM
    is_important: bool = False
    
    # 索引状态
    is_indexed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "novel_id": self.novel_id,
            "chapter_id": self.chapter_id,
            "entity_ids": self.entity_ids,
            "keywords": self.keywords,
            "summary": self.summary,
            "priority": self.priority.value,
            "is_important": self.is_important,
            "is_indexed": self.is_indexed
        }
    
    def update_access(self):
        """更新访问信息"""
        self.last_accessed = datetime.now().isoformat()
        self.access_count += 1


@dataclass
class RetrievalResult:
    """检索结果"""
    memory: MemoryEntry
    relevance_score: float
    recency_score: float
    importance_score: float
    combined_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory": self.memory.to_dict(),
            "relevance_score": self.relevance_score,
            "recency_score": self.recency_score,
            "importance_score": self.importance_score,
            "combined_score": self.combined_score
        }


class SemanticMemory:
    """
    语义记忆系统 - 基于 RAG 的语义检索
    
    功能：
    1. 存储记忆向量
    2. 语义相似度检索
    3. 混合检索（语义 + 关键词）
    """
    
    def __init__(self, embedding_dim: int = 768):
        self.embedding_dim = embedding_dim
        self._memories: Dict[str, MemoryEntry] = {}
        self._novel_index: Dict[str, List[str]] = {}  # novel_id -> [memory_ids]
        self._type_index: Dict[MemoryType, List[str]] = {
            mt: [] for mt in MemoryType
        }
        
    def add_memory(
        self,
        content: str,
        memory_type: MemoryType,
        novel_id: str = "",
        chapter_id: str = "",
        metadata: Dict[str, Any] = None
    ) -> MemoryEntry:
        """添加记忆"""
        # 生成 ID
        content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
        memory_id = f"mem_{memory_type.value}_{content_hash}_{datetime.now().timestamp()}"
        
        # 提取关键词（简化版）
        keywords = self._extract_keywords(content)
        
        # 生成摘要
        summary = content[:200] + "..." if len(content) > 200 else content
        
        entry = MemoryEntry(
            memory_id=memory_id,
            content=content,
            memory_type=memory_type,
            novel_id=novel_id,
            chapter_id=chapter_id,
            keywords=keywords,
            summary=summary,
            is_indexed=True
        )
        
        # 设置优先级
        if metadata:
            entry.priority = MemoryPriority(
                metadata.get("priority", MemoryPriority.MEDIUM.value)
            )
            entry.is_important = metadata.get("is_important", False)
        
        # 存储
        self._memories[memory_id] = entry
        
        # 更新索引
        if novel_id:
            if novel_id not in self._novel_index:
                self._novel_index[novel_id] = []
            self._novel_index[novel_id].append(memory_id)
        
        self._type_index[memory_type].append(memory_id)
        
        return entry
    
    def _extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """提取关键词（简化版）"""
        # 实际应该使用分词和 TF-IDF
        words = text.replace("\n", " ").split()[:top_k]
        return list(set(words))[:top_k]
    
    def search(
        self,
        query: str,
        novel_id: str = "",
        memory_type: Optional[MemoryType] = None,
        top_k: int = 5,
        use_hybrid: bool = True
    ) -> List[RetrievalResult]:
        """
        语义检索
        
        Args:
            query: 查询文本
            novel_id: 小说ID（可选）
            memory_type: 记忆类型（可选）
            top_k: 返回数量
            use_hybrid: 是否使用混合检索
            
        Returns:
            检索结果列表
        """
        results = []
        
        # 候选记忆
        candidates = self._get_candidates(novel_id, memory_type)
        
        if not candidates:
            return results
        
        # 计算相关性得分
        query_keywords = set(self._extract_keywords(query))
        
        for memory in candidates:
            # 语义相似度（简化版，实际应该用向量）
            relevance = self._calculate_relevance(memory, query_keywords)
            
            # 时效性得分
            recency = self._calculate_recency(memory)
            
            # 重要性得分
            importance = self._calculate_importance(memory)
            
            # 综合得分
            combined = relevance * 0.5 + recency * 0.2 + importance * 0.3
            
            results.append(RetrievalResult(
                memory=memory,
                relevance_score=relevance,
                recency_score=recency,
                importance_score=importance,
                combined_score=combined
            ))
        
        # 排序并返回 top_k
        results.sort(key=lambda x: x.combined_score, reverse=True)
        return results[:top_k]
    
    def _get_candidates(
        self,
        novel_id: str,
        memory_type: Optional[MemoryType]
    ) -> List[MemoryEntry]:
        """获取候选记忆"""
        candidates = []
        
        if novel_id:
            memory_ids = self._novel_index.get(novel_id, [])
            candidates = [self._memories[mid] for mid in memory_ids if mid in self._memories]
        elif memory_type:
            memory_ids = self._type_index.get(memory_type, [])
            candidates = [self._memories[mid] for mid in memory_ids if mid in self._memories]
        else:
            candidates = list(self._memories.values())
        
        return candidates
    
    def _calculate_relevance(
        self,
        memory: MemoryEntry,
        query_keywords: set
    ) -> float:
        """计算相关性得分"""
        memory_keywords = set(memory.keywords)
        
        # 关键词重叠
        overlap = len(query_keywords & memory_keywords)
        max_overlap = max(len(query_keywords), len(memory_keywords))
        
        if max_overlap == 0:
            return 0.5
        
        return overlap / max_overlap
    
    def _calculate_recency(self, memory: MemoryEntry) -> float:
        """计算时效性得分"""
        # 基于访问次数和最后访问时间
        try:
            last_access = datetime.fromisoformat(memory.last_accessed)
            now = datetime.now()
            days_ago = (now - last_access).days
            
            # 指数衰减
            recency = 1.0 / (1.0 + days_ago * 0.1)
            
            # 结合访问次数
            access_bonus = min(memory.access_count * 0.05, 0.5)
            
            return min(recency + access_bonus, 1.0)
        except:
            return 0.5
    
    def _calculate_importance(self, memory: MemoryEntry) -> float:
        """计算重要性得分"""
        score = 0.5
        
        # 优先级权重
        if memory.priority == MemoryPriority.HIGH:
            score += 0.3
        elif memory.priority == MemoryPriority.LOW:
            score -= 0.2
        
        # 重要标记
        if memory.is_important:
            score += 0.2
        
        return max(0.0, min(1.0, score))
    
    def update_memory(self, memory_id: str, updates: Dict[str, Any]):
        """更新记忆"""
        if memory_id in self._memories:
            for key, value in updates.items():
                if hasattr(self._memories[memory_id], key):
                    setattr(self._memories[memory_id], key, value)
    
    def delete_memory(self, memory_id: str):
        """删除记忆"""
        if memory_id in self._memories:
            memory = self._memories[memory_id]
            
            # 从索引中移除
            if memory.novel_id and memory.novel_id in self._novel_index:
                self._novel_index[memory.novel_id].remove(memory_id)
            
            if memory.memory_type in self._type_index:
                self._type_index[memory.memory_type].remove(memory_id)
            
            # 删除
            del self._memories[memory_id]
    
    def get_memory_stats(self, novel_id: str = "") -> Dict[str, Any]:
        """获取记忆统计"""
        if novel_id:
            memories = [
                self._memories[mid]
                for mid in self._novel_index.get(novel_id, [])
                if mid in self._memories
            ]
        else:
            memories = list(self._memories.values())
        
        return {
            "total_memories": len(memories),
            "by_type": {
                mt.value: len([
                    m for m in memories
                    if m.memory_type == mt
                ])
                for mt in MemoryType
            },
            "total_accesses": sum(m.access_count for m in memories),
            "important_count": sum(1 for m in memories if m.is_important)
        }


class ProceduralMemory:
    """
    程序记忆 - 存储 Agent 操作流程
    
    功能：
    1. 存储工作流
    2. 模式学习
    3. 最佳实践
    """
    
    def __init__(self):
        self._procedures: Dict[str, Dict[str, Any]] = {}
    
    def store_procedure(
        self,
        name: str,
        steps: List[Dict[str, Any]],
        description: str = "",
        success_criteria: Dict[str, Any] = None
    ):
        """存储程序"""
        self._procedures[name] = {
            "name": name,
            "description": description,
            "steps": steps,
            "success_criteria": success_criteria or {},
            "created_at": datetime.now().isoformat(),
            "usage_count": 0,
            "success_rate": 0.0,
            "total_runs": 0
        }
    
    def get_procedure(self, name: str) -> Optional[Dict[str, Any]]:
        """获取程序"""
        if name in self._procedures:
            self._procedures[name]["usage_count"] += 1
            return self._procedures[name]
        return None
    
    def update_success(self, name: str, success: bool):
        """更新成功率"""
        if name in self._procedures:
            proc = self._procedures[name]
            proc["total_runs"] += 1
            if success:
                proc["success_rate"] = (
                    (proc["success_rate"] * (proc["total_runs"] - 1) + 1)
                    / proc["total_runs"]
                )
            else:
                proc["success_rate"] = (
                    proc["success_rate"] * (proc["total_runs"] - 1)
                    / proc["total_runs"]
                )
    
    def find_similar_procedures(
        self,
        task_description: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """查找类似的程序"""
        # 简化版：基于关键词匹配
        task_keywords = set(task_description.lower().split())
        
        results = []
        for proc in self._procedures.values():
            # 计算相似度
            proc_keywords = set(proc.get("description", "").lower().split())
            similarity = len(task_keywords & proc_keywords) / max(
                len(task_keywords), len(proc_keywords), 1
            )
            
            results.append((similarity, proc))
        
        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:top_k]]


class ActiveRecall:
    """
    主动召回系统
    
    功能：
    1. 预测需要召回的记忆
    2. 主动提供相关信息
    3. 遗忘机制
    """

    def __init__(self, semantic_memory: SemanticMemory):
        self.semantic_memory = semantic_memory
        self._recall_patterns: Dict[str, List[str]] = {}
        self._context_history: List[Dict[str, Any]] = []
    
    def record_context(self, context: Dict[str, Any]):
        """记录上下文"""
        self._context_history.append({
            "context": context,
            "timestamp": datetime.now().isoformat()
        })
        
        # 只保留最近 20 个上下文
        if len(self._context_history) > 20:
            self._context_history = self._context_history[-20:]
    
    def predict_recall(
        self,
        current_context: Dict[str, Any],
        novel_id: str = ""
    ) -> List[RetrievalResult]:
        """
        预测需要召回的记忆
        
        基于当前上下文，预测可能需要召回的相关记忆
        """
        # 提取当前上下文的关键信息
        current_chapter = current_context.get("current_chapter", "")
        active_characters = current_context.get("active_characters", [])
        current_location = current_context.get("current_location", "")
        
        # 构建查询
        query_parts = [
            current_chapter,
            " ".join(active_characters),
            current_location
        ]
        query = " ".join([q for q in query_parts if q])
        
        # 语义检索
        results = self.semantic_memory.search(
            query=query,
            novel_id=novel_id,
            top_k=5
        )
        
        # 过滤：优先召回与当前上下文相关的
        filtered = []
        for result in results:
            memory = result.memory
            
            # 检查是否与当前角色相关
            char_match = any(
                char in memory.entity_ids
                for char in active_characters
            ) if active_characters else True
            
            # 检查章节是否接近
            chapter_match = (
                not current_chapter or
                abs(int(memory.chapter_id or 0) - int(current_chapter or 0)) <= 3
            )
            
            if char_match or chapter_match:
                filtered.append(result)
        
        return filtered[:3]
    
    def analyze_recall_effectiveness(self) -> Dict[str, Any]:
        """分析召回效果"""
        if not self._context_history:
            return {"status": "no_data"}
        
        # 简化版分析
        return {
            "total_contexts": len(self._context_history),
            "avg_context_length": sum(
                len(str(c.get("context", {})))
                for c in self._context_history
            ) / len(self._context_history)
        }


# 全局实例
_semantic_memory: Optional[SemanticMemory] = None
_procedural_memory: Optional[ProceduralMemory] = None
_active_recall: Optional[ActiveRecall] = None


def get_semantic_memory() -> SemanticMemory:
    """获取语义记忆实例"""
    global _semantic_memory
    if _semantic_memory is None:
        _semantic_memory = SemanticMemory()
    return _semantic_memory


def get_procedural_memory() -> ProceduralMemory:
    """获取程序记忆实例"""
    global _procedural_memory
    if _procedural_memory is None:
        _procedural_memory = ProceduralMemory()
    return _procedural_memory


def get_active_recall() -> ActiveRecall:
    """获取主动召回实例"""
    global _active_recall
    if _active_recall is None:
        _active_recall = ActiveRecall(get_semantic_memory())
    return _active_recall


# 便捷函数
def store_memory(
    content: str,
    memory_type: MemoryType,
    novel_id: str = "",
    chapter_id: str = "",
    **kwargs
) -> MemoryEntry:
    """存储记忆的便捷函数"""
    return get_semantic_memory().add_memory(
        content=content,
        memory_type=memory_type,
        novel_id=novel_id,
        chapter_id=chapter_id,
        metadata=kwargs
    )


def recall_memories(
    query: str,
    novel_id: str = "",
    top_k: int = 5
) -> List[RetrievalResult]:
    """召回记忆的便捷函数"""
    return get_semantic_memory().search(
        query=query,
        novel_id=novel_id,
        top_k=top_k
    )


def predict_and_recall(
    current_context: Dict[str, Any],
    novel_id: str = ""
) -> List[RetrievalResult]:
    """预测并召回的便捷函数"""
    recall = get_active_recall()
    recall.record_context(current_context)
    return recall.predict_recall(current_context, novel_id)