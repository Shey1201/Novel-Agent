"""
RAG Optimizer - RAG 性能优化器
提供向量检索性能优化、查询优化和结果重排序
"""

import time
import hashlib
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from functools import lru_cache
import asyncio

if TYPE_CHECKING:
    from app.memory.vector_store import MemoryItem


@dataclass
class SearchResult:
    """搜索结果"""
    item: Any  # MemoryItem
    score: float
    rerank_score: Optional[float] = None


@dataclass
class SearchMetrics:
    """搜索指标"""
    query_time_ms: float
    embedding_time_ms: float
    search_time_ms: float
    rerank_time_ms: float
    total_results: int
    filtered_results: int
    cache_hit: bool


class QueryOptimizer:
    """
    查询优化器
    
    优化查询文本以提高检索质量
    """
    
    # 停用词
    STOP_WORDS = {
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
        "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
        "你", "会", "着", "没有", "看", "好", "自己", "这", "那"
    }
    
    # 关键词扩展映射
    KEYWORD_EXPANSION = {
        "主角": ["主人公", "男主", "女主", "主角", "主要角色"],
        "战斗": ["战斗", "打斗", "战争", "冲突", "对抗"],
        "魔法": ["魔法", "法术", "魔力", "咒语", "巫术"],
        "修炼": ["修炼", "修行", "练功", "打坐", "闭关"],
        "门派": ["门派", "宗门", "教派", "势力", "组织"],
    }
    
    def optimize(self, query: str) -> str:
        """
        优化查询文本
        
        Args:
            query: 原始查询
            
        Returns:
            优化后的查询
        """
        # 1. 去除多余空白
        optimized = " ".join(query.split())
        
        # 2. 提取关键词
        keywords = self._extract_keywords(optimized)
        
        # 3. 扩展关键词
        expanded = self._expand_keywords(keywords)
        
        # 4. 重组查询
        if expanded:
            optimized = " ".join(expanded)
        
        return optimized
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        words = []
        for word in text.split():
            # 去除停用词
            if word not in self.STOP_WORDS and len(word) > 1:
                words.append(word)
        return words
    
    def _expand_keywords(self, keywords: List[str]) -> List[str]:
        """扩展关键词"""
        expanded = []
        for kw in keywords:
            expanded.append(kw)
            # 查找扩展词
            for key, expansions in self.KEYWORD_EXPANSION.items():
                if key in kw or kw in key:
                    expanded.extend(expansions)
        
        # 去重
        return list(dict.fromkeys(expanded))
    
    def generate_variations(self, query: str) -> List[str]:
        """
        生成查询变体
        
        Args:
            query: 原始查询
            
        Returns:
            查询变体列表
        """
        variations = [query]
        
        # 同义词替换
        for key, expansions in self.KEYWORD_EXPANSION.items():
            if key in query:
                for exp in expansions[:2]:  # 限制变体数量
                    if exp != key:
                        variations.append(query.replace(key, exp))
        
        return variations[:3]  # 最多返回3个变体


class ResultReranker:
    """
    结果重排序器
    
    对向量检索结果进行重排序以提高相关性
    """
    
    def __init__(self):
        self.weights = {
            "vector_score": 0.4,
            "recency": 0.2,
            "category_match": 0.2,
            "length_bonus": 0.1,
            "diversity": 0.1
        }
    
    def rerank(
        self,
        results: List[SearchResult],
        query: str,
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        重排序结果
        
        Args:
            results: 原始结果
            query: 查询文本
            top_k: 返回数量
            
        Returns:
            重排序后的结果
        """
        if not results:
            return []
        
        # 计算重排序分数
        for result in results:
            result.rerank_score = self._calculate_rerank_score(result, query, results)
        
        # 按重排序分数排序
        results.sort(key=lambda x: x.rerank_score or 0, reverse=True)
        
        # 多样性重排序（避免重复内容）
        diversified = self._diversify_results(results[:top_k * 2], top_k)
        
        return diversified
    
    def _calculate_rerank_score(
        self,
        result: SearchResult,
        query: str,
        all_results: List[SearchResult]
    ) -> float:
        """计算重排序分数"""
        scores = []
        
        # 1. 向量相似度分数
        scores.append(("vector_score", result.score))
        
        # 2. 时效性分数
        recency_score = self._calculate_recency(result)
        scores.append(("recency", recency_score))
        
        # 3. 类别匹配分数
        category_score = self._calculate_category_match(result, query)
        scores.append(("category_match", category_score))
        
        # 4. 长度奖励（适中的长度）
        length_score = self._calculate_length_bonus(result)
        scores.append(("length_bonus", length_score))
        
        # 5. 多样性分数（与其他结果的差异）
        diversity_score = self._calculate_diversity(result, all_results)
        scores.append(("diversity", diversity_score))
        
        # 加权求和
        total_score = sum(
            self.weights.get(name, 0) * score for name, score in scores
        )
        
        return total_score
    
    def _calculate_recency(self, result: SearchResult) -> float:
        """计算时效性分数"""
        metadata = result.item.metadata
        
        # 如果有时间戳，基于时间计算
        if "timestamp" in metadata:
            # 这里简化处理，实际应该计算时间差
            return 0.8
        
        # 如果有章节号，基于章节计算
        if "chapter_number" in metadata:
            # 越新的章节分数越高
            return 0.7
        
        return 0.5
    
    def _calculate_category_match(self, result: SearchResult, query: str) -> float:
        """计算类别匹配分数"""
        category = result.item.metadata.get("category", "")
        
        # 查询类别映射
        category_keywords = {
            "characters": ["角色", "人物", "性格"],
            "world": ["世界", "设定", "规则"],
            "plot": ["剧情", "情节", "发展"],
        }
        
        for cat, keywords in category_keywords.items():
            if cat == category and any(kw in query for kw in keywords):
                return 1.0
        
        return 0.5
    
    def _calculate_length_bonus(self, result: SearchResult) -> float:
        """计算长度奖励"""
        content_length = len(result.item.content)
        
        # 理想长度：100-500 字符
        if 100 <= content_length <= 500:
            return 1.0
        elif content_length < 50:
            return 0.5
        elif content_length > 1000:
            return 0.7
        else:
            return 0.8
    
    def _calculate_diversity(
        self,
        result: SearchResult,
        all_results: List[SearchResult]
    ) -> float:
        """计算多样性分数"""
        # 计算与已选结果的平均相似度
        similarities = []
        for other in all_results[:5]:  # 只比较前5个
            if other != result:
                sim = self._text_similarity(
                    result.item.content,
                    other.item.content
                )
                similarities.append(sim)
        
        if not similarities:
            return 1.0
        
        avg_similarity = sum(similarities) / len(similarities)
        # 相似度越低，多样性分数越高
        return 1.0 - avg_similarity
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算两段文本的相似度"""
        # 简单的 Jaccard 相似度
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _diversify_results(
        self,
        results: List[SearchResult],
        top_k: int
    ) -> List[SearchResult]:
        """多样化结果"""
        if len(results) <= top_k:
            return results
        
        diversified = [results[0]]  # 选择最高分
        remaining = results[1:]
        
        while len(diversified) < top_k and remaining:
            # 选择与已选结果最不相似的
            best_candidate = None
            best_diversity_score = -1
            
            for candidate in remaining:
                # 计算与已选结果的平均相似度
                avg_sim = sum(
                    self._text_similarity(
                        candidate.item.content,
                        selected.item.content
                    )
                    for selected in diversified
                ) / len(diversified)
                
                diversity_score = 1.0 - avg_sim
                
                if diversity_score > best_diversity_score:
                    best_diversity_score = diversity_score
                    best_candidate = candidate
            
            if best_candidate:
                diversified.append(best_candidate)
                remaining.remove(best_candidate)
            else:
                break
        
        return diversified


class RAGCache:
    """
    RAG 缓存
    
    缓存查询结果以提高性能
    """
    
    def __init__(self, max_size: int = 100, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl  # 缓存时间（秒）
        self.cache: Dict[str, Tuple[List[Any], float]] = {}
        self.access_count: Dict[str, int] = {}
    
    def _generate_key(self, query: str, novel_id: str, **kwargs) -> str:
        """生成缓存键"""
        key_data = f"{novel_id}:{query}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(
        self,
        query: str,
        novel_id: str,
        **kwargs
    ) -> Optional[List[Any]]:
        """获取缓存结果"""
        key = self._generate_key(query, novel_id, **kwargs)
        
        if key in self.cache:
            results, timestamp = self.cache[key]
            
            # 检查是否过期
            if time.time() - timestamp < self.ttl:
                self.access_count[key] = self.access_count.get(key, 0) + 1
                return results
            else:
                # 过期，删除
                del self.cache[key]
                if key in self.access_count:
                    del self.access_count[key]
        
        return None
    
    def set(
        self,
        query: str,
        novel_id: str,
        results: List[Any],
        **kwargs
    ):
        """设置缓存"""
        # 清理旧缓存
        self._cleanup()
        
        key = self._generate_key(query, novel_id, **kwargs)
        self.cache[key] = (results, time.time())
        self.access_count[key] = 1
    
    def _cleanup(self):
        """清理缓存"""
        current_time = time.time()
        
        # 删除过期项
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp > self.ttl
        ]
        for key in expired_keys:
            del self.cache[key]
            if key in self.access_count:
                del self.access_count[key]
        
        # 如果还是太多，删除最少访问的
        if len(self.cache) >= self.max_size:
            sorted_keys = sorted(
                self.access_count.keys(),
                key=lambda k: self.access_count[k]
            )
            keys_to_remove = sorted_keys[:len(sorted_keys) // 4]  # 删除25%
            for key in keys_to_remove:
                if key in self.cache:
                    del self.cache[key]
                if key in self.access_count:
                    del self.access_count[key]
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_count.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": self._calculate_hit_rate(),
            "ttl": self.ttl
        }
    
    def _calculate_hit_rate(self) -> float:
        """计算命中率"""
        if not self.access_count:
            return 0.0
        
        # 简化计算：有访问次数的视为命中
        return sum(1 for count in self.access_count.values() if count > 1) / len(self.access_count)


class RAGOptimizer:
    """
    RAG 优化器主类
    
    提供统一的 RAG 优化接口
    """
    
    def __init__(
        self,
        enable_cache: bool = True,
        enable_rerank: bool = True,
        enable_query_optimize: bool = True
    ):
        self.query_optimizer = QueryOptimizer()
        self.reranker = ResultReranker()
        self.cache = RAGCache() if enable_cache else None
        self.enable_rerank = enable_rerank
        self.enable_query_optimize = enable_query_optimize
        self.metrics: List[SearchMetrics] = []
    
    async def optimize_search(
        self,
        query: str,
        search_func,
        novel_id: str,
        top_k: int = 5,
        **search_kwargs
    ) -> Tuple[List[Any], SearchMetrics]:
        """
        优化搜索
        
        Args:
            query: 查询文本
            search_func: 搜索函数
            novel_id: 小说ID
            top_k: 返回数量
            **search_kwargs: 搜索参数
            
        Returns:
            (结果列表, 搜索指标)
        """
        start_time = time.time()
        
        # 1. 检查缓存
        if self.cache:
            cached_results = self.cache.get(query, novel_id, **search_kwargs)
            if cached_results is not None:
                metrics = SearchMetrics(
                    query_time_ms=(time.time() - start_time) * 1000,
                    embedding_time_ms=0,
                    search_time_ms=0,
                    rerank_time_ms=0,
                    total_results=len(cached_results),
                    filtered_results=len(cached_results),
                    cache_hit=True
                )
                return cached_results, metrics
        
        # 2. 优化查询
        query_start = time.time()
        if self.enable_query_optimize:
            optimized_query = self.query_optimizer.optimize(query)
        else:
            optimized_query = query
        query_time = (time.time() - query_start) * 1000
        
        # 3. 执行搜索
        search_start = time.time()
        results = await search_func(optimized_query, novel_id, top_k=top_k * 2, **search_kwargs)
        search_time = (time.time() - search_start) * 1000
        
        total_results = len(results)
        
        # 4. 重排序
        rerank_time = 0
        if self.enable_rerank and results:
            rerank_start = time.time()
            search_results = [SearchResult(item=r, score=r.score) for r in results]
            reranked = self.reranker.rerank(search_results, query, top_k)
            results = [r.item for r in reranked]
            rerank_time = (time.time() - rerank_start) * 1000
        else:
            results = results[:top_k]
        
        filtered_results = len(results)
        
        # 5. 更新缓存
        if self.cache:
            self.cache.set(query, novel_id, results, **search_kwargs)
        
        total_time = (time.time() - start_time) * 1000
        
        metrics = SearchMetrics(
            query_time_ms=total_time,
            embedding_time_ms=0,  # 嵌入时间由 search_func 内部计算
            search_time_ms=search_time,
            rerank_time_ms=rerank_time,
            total_results=total_results,
            filtered_results=filtered_results,
            cache_hit=False
        )
        
        self.metrics.append(metrics)
        
        return results, metrics
    
    def get_average_metrics(self) -> Dict[str, float]:
        """获取平均指标"""
        if not self.metrics:
            return {}
        
        return {
            "avg_query_time_ms": sum(m.query_time_ms for m in self.metrics) / len(self.metrics),
            "avg_search_time_ms": sum(m.search_time_ms for m in self.metrics) / len(self.metrics),
            "avg_rerank_time_ms": sum(m.rerank_time_ms for m in self.metrics) / len(self.metrics),
            "cache_hit_rate": sum(1 for m in self.metrics if m.cache_hit) / len(self.metrics),
            "total_queries": len(self.metrics)
        }
    
    def clear_metrics(self):
        """清除指标记录"""
        self.metrics.clear()
    
    def clear_cache(self):
        """清除缓存"""
        if self.cache:
            self.cache.clear()


# 便捷函数
def optimize_query(query: str) -> str:
    """优化查询"""
    optimizer = QueryOptimizer()
    return optimizer.optimize(query)


def rerank_results(
    results: List[Any],
    query: str,
    top_k: int = 5
) -> List[Any]:
    """重排序结果"""
    reranker = ResultReranker()
    search_results = [SearchResult(item=r, score=r.score) for r in results]
    reranked = reranker.rerank(search_results, query, top_k)
    return [r.item for r in reranked]


# 全局优化器实例
_rag_optimizer: Optional[RAGOptimizer] = None


def get_rag_optimizer() -> RAGOptimizer:
    """获取 RAG 优化器实例"""
    global _rag_optimizer
    if _rag_optimizer is None:
        _rag_optimizer = RAGOptimizer()
    return _rag_optimizer
