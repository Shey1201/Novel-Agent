"""
L2: Semantic Memory - 向量存储
使用 Qdrant 存储和检索语义记忆
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import hashlib

import numpy as np

# 尝试导入 Qdrant，如果没有则使用内存存储
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print("Qdrant not available, using in-memory storage")

from langchain_openai import OpenAIEmbeddings


@dataclass
class MemoryItem:
    """记忆项"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    score: float = 0.0


class VectorStore:
    """
    向量存储 - L2 语义记忆
    
    存储三类索引：
    - 角色索引 (characters)
    - 设定索引 (world)
    - 剧情索引 (plot)
    """
    
    def __init__(self, collection_name: str = "novel_memory"):
        self.collection_name = collection_name
        self.embeddings = OpenAIEmbeddings()
        self._rag_optimizer = None
        
        # 初始化存储
        if QDRANT_AVAILABLE:
            self._init_qdrant()
        else:
            self._init_memory()
    
    @property
    def rag_optimizer(self):
        """延迟加载 rag_optimizer 避免循环导入"""
        if self._rag_optimizer is None:
            from app.memory.rag_optimizer import get_rag_optimizer
            self._rag_optimizer = get_rag_optimizer()
        return self._rag_optimizer
    
    def _init_qdrant(self):
        """初始化 Qdrant"""
        try:
            # 尝试连接本地 Qdrant
            self.client = QdrantClient(host="localhost", port=6333)
            
            # 检查集合是否存在
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                # 创建集合
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
                )
            
            self.storage_type = "qdrant"
        except Exception as e:
            print(f"Qdrant connection failed: {e}, falling back to memory")
            self._init_memory()
    
    def _init_memory(self):
        """初始化内存存储"""
        self.memory_store: Dict[str, List[MemoryItem]] = {
            "characters": [],
            "world": [],
            "plot": []
        }
        self.storage_type = "memory"
    
    def _generate_id(self, content: str, category: str) -> str:
        """生成唯一ID"""
        hash_input = f"{category}:{content}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    async def add_memory(
        self,
        content: str,
        category: str,  # characters/world/plot
        metadata: Dict[str, Any],
        novel_id: str
    ) -> str:
        """
        添加记忆
        
        Args:
            content: 记忆内容
            category: 类别
            metadata: 元数据
            novel_id: 小说ID
            
        Returns:
            memory_id
        """
        memory_id = self._generate_id(content, category)
        
        # 生成向量
        embedding = await self.embeddings.aembed_query(content)
        
        # 添加 novel_id 到 metadata
        metadata["novel_id"] = novel_id
        metadata["category"] = category
        
        if self.storage_type == "qdrant":
            # 存储到 Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=memory_id,
                        vector=embedding,
                        payload={
                            "content": content,
                            **metadata
                        }
                    )
                ]
            )
        else:
            # 存储到内存
            item = MemoryItem(
                id=memory_id,
                content=content,
                metadata=metadata,
                embedding=embedding
            )
            if category not in self.memory_store:
                self.memory_store[category] = []
            self.memory_store[category].append(item)
        
        return memory_id
    
    async def search(
        self,
        query: str,
        novel_id: str,
        category: Optional[str] = None,
        top_k: int = 5,
        min_score: float = 0.7,
        use_optimizer: bool = True
    ) -> List[MemoryItem]:
        """
        搜索记忆
        
        Args:
            query: 查询文本
            novel_id: 小说ID（过滤）
            category: 类别过滤
            top_k: 返回数量
            min_score: 最小相似度
            use_optimizer: 是否使用 RAG 优化
            
        Returns:
            记忆项列表
        """
        # 如果使用优化器，通过优化器执行搜索
        if use_optimizer:
            results, metrics = await self.rag_optimizer.optimize_search(
                query=query,
                search_func=self._raw_search,
                novel_id=novel_id,
                top_k=top_k,
                category=category,
                min_score=min_score
            )
            return results
        
        # 否则直接搜索
        return await self._raw_search(query, novel_id, top_k, category, min_score)
    
    async def _raw_search(
        self,
        query: str,
        novel_id: str,
        top_k: int = 5,
        category: Optional[str] = None,
        min_score: float = 0.7
    ) -> List[MemoryItem]:
        """原始搜索（供优化器使用）"""
        # 生成查询向量
        query_embedding = await self.embeddings.aembed_query(query)
        
        if self.storage_type == "qdrant":
            # 构建过滤条件
            filter_condition = {
                "must": [
                    {"key": "novel_id", "match": {"value": novel_id}}
                ]
            }
            if category:
                filter_condition["must"].append(
                    {"key": "category", "match": {"value": category}}
                )
            
            # 搜索
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=filter_condition,
                limit=top_k,
                score_threshold=min_score
            )
            
            return [
                MemoryItem(
                    id=r.id,
                    content=r.payload.get("content", ""),
                    metadata={k: v for k, v in r.payload.items() if k != "content"},
                    score=r.score
                )
                for r in results
            ]
        else:
            # 内存搜索
            all_items = []
            categories = [category] if category else self.memory_store.keys()
            
            for cat in categories:
                items = self.memory_store.get(cat, [])
                for item in items:
                    if item.metadata.get("novel_id") == novel_id:
                        # 计算相似度
                        if item.embedding:
                            similarity = self._cosine_similarity(
                                query_embedding,
                                item.embedding
                            )
                            if similarity >= min_score:
                                item.score = similarity
                                all_items.append(item)
            
            # 排序并返回 top_k
            all_items.sort(key=lambda x: x.score, reverse=True)
            return all_items[:top_k]
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """计算余弦相似度"""
        a_array = np.array(a)
        b_array = np.array(b)
        return float(np.dot(a_array, b_array) / (np.linalg.norm(a_array) * np.linalg.norm(b_array)))
    
    async def batch_add_memories(
        self,
        items: List[Dict[str, Any]],
        novel_id: str
    ) -> List[str]:
        """批量添加记忆"""
        ids = []
        for item in items:
            memory_id = await self.add_memory(
                content=item["content"],
                category=item["category"],
                metadata=item.get("metadata", {}),
                novel_id=novel_id
            )
            ids.append(memory_id)
        return ids
    
    def delete_memory(self, memory_id: str):
        """删除记忆"""
        if self.storage_type == "qdrant":
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[memory_id]
            )
        else:
            # 内存删除
            for category in self.memory_store:
                self.memory_store[category] = [
                    item for item in self.memory_store[category]
                    if item.id != memory_id
                ]
    
    def clear_novel_memory(self, novel_id: str):
        """清空某小说的所有记忆"""
        if self.storage_type == "qdrant":
            self.client.delete(
                collection_name=self.collection_name,
                points_selector={
                    "filter": {
                        "must": [
                            {"key": "novel_id", "match": {"value": novel_id}}
                        ]
                    }
                }
            )
        else:
            for category in self.memory_store:
                self.memory_store[category] = [
                    item for item in self.memory_store[category]
                    if item.metadata.get("novel_id") != novel_id
                ]


# 便捷函数
_vector_store_instance = None

def get_vector_store() -> VectorStore:
    """获取向量存储实例（单例）"""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance
