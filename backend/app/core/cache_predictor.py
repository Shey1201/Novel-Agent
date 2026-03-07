"""
Cache Predictor - 缓存命中预测器
预测 RAG 查询的缓存命中率，减少重复检索
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from collections import defaultdict
import hashlib
import time
import re


@dataclass
class QueryPattern:
    """查询模式"""
    pattern_type: str  # keyword/semantic/hybrid
    keywords: List[str]
    entity_mentions: List[str]
    context_similarity: float


@dataclass
class PredictionResult:
    """预测结果"""
    hit_probability: float  # 0-1 命中率预测
    confidence: float       # 预测置信度
    suggested_action: str   # suggested: cache/query/both
    similar_queries: List[str]  # 相似的历史查询


class QueryFeatureExtractor:
    """查询特征提取器"""
    
    def __init__(self):
        self.stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
    
    def extract_features(self, query: str) -> Dict[str, Any]:
        """提取查询特征"""
        features = {
            "length": len(query),
            "word_count": len(query.split()),
            "has_quotes": '"' in query or '"' in query,
            "has_question": '?' in query or '？' in query,
            "keywords": self._extract_keywords(query),
            "entities": self._extract_entities(query),
            "complexity_score": self._calculate_complexity(query)
        }
        return features
    
    def _extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        # 简单的中文分词（基于字符和停用词）
        words = []
        current_word = ""
        
        for char in query:
            if char.isalnum() or char in ['_', '-']:
                current_word += char
            else:
                if current_word and current_word not in self.stop_words and len(current_word) > 1:
                    words.append(current_word.lower())
                current_word = ""
        
        if current_word and current_word not in self.stop_words and len(current_word) > 1:
            words.append(current_word.lower())
        
        return list(set(words))
    
    def _extract_entities(self, query: str) -> List[str]:
        """提取实体提及"""
        entities = []
        
        # 提取引号内的内容
        quoted = re.findall(r'[""]([^""]+)[""]', query)
        entities.extend(quoted)
        
        # 提取书名号内的内容
        book_titles = re.findall(r'《([^》]+)》', query)
        entities.extend(book_titles)
        
        # 提取特定模式（如角色名、地点等）
        # 简单规则：2-4个中文字符的连续组合
        chinese_entities = re.findall(r'[\u4e00-\u9fa5]{2,4}', query)
        # 过滤停用词
        chinese_entities = [e for e in chinese_entities if e not in self.stop_words]
        entities.extend(chinese_entities)
        
        return list(set(entities))
    
    def _calculate_complexity(self, query: str) -> float:
        """计算查询复杂度"""
        score = 0.0
        
        # 长度因子
        score += min(len(query) / 100, 0.3)
        
        # 标点复杂度
        punctuation_count = sum(1 for c in query if c in '，。！？；：""''（）')
        score += min(punctuation_count / 10, 0.2)
        
        # 关键词密度
        keywords = self._extract_keywords(query)
        score += min(len(keywords) / 5, 0.3)
        
        # 实体密度
        entities = self._extract_entities(query)
        score += min(len(entities) / 3, 0.2)
        
        return min(score, 1.0)


class CacheHitPredictor:
    """
    缓存命中预测器
    
    基于历史查询模式和相似度预测缓存命中率
    """
    
    def __init__(self):
        self.feature_extractor = QueryFeatureExtractor()
        
        # 历史查询统计
        self.query_history: Dict[str, Dict[str, Any]] = {}  # query_hash -> stats
        self.entity_index: Dict[str, List[str]] = defaultdict(list)  # entity -> query_hashes
        self.keyword_index: Dict[str, List[str]] = defaultdict(list)  # keyword -> query_hashes
        
        # 预测模型参数
        self.similarity_threshold = 0.7
        self.min_history_count = 3
        
        # 性能统计
        self.prediction_stats = {
            "total_predictions": 0,
            "correct_predictions": 0,
            "false_positives": 0,  # 预测命中但实际未命中
            "false_negatives": 0   # 预测未命中但实际命中
        }
    
    def _generate_query_hash(self, query: str, novel_id: str) -> str:
        """生成查询哈希"""
        return hashlib.md5(f"{novel_id}:{query.lower().strip()}".encode()).hexdigest()
    
    def _calculate_similarity(self, query1: str, query2: str) -> float:
        """计算两个查询的相似度"""
        features1 = self.feature_extractor.extract_features(query1)
        features2 = self.feature_extractor.extract_features(query2)
        
        # 关键词 Jaccard 相似度
        keywords1 = set(features1["keywords"])
        keywords2 = set(features2["keywords"])
        
        if not keywords1 or not keywords2:
            return 0.0
        
        jaccard = len(keywords1 & keywords2) / len(keywords1 | keywords2)
        
        # 实体重叠度
        entities1 = set(features1["entities"])
        entities2 = set(features2["entities"])
        
        entity_overlap = 0.0
        if entities1 and entities2:
            entity_overlap = len(entities1 & entities2) / max(len(entities1), len(entities2))
        
        # 综合相似度
        similarity = jaccard * 0.6 + entity_overlap * 0.4
        
        return similarity
    
    def find_similar_queries(
        self,
        query: str,
        novel_id: str,
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """查找相似的历史查询"""
        features = self.feature_extractor.extract_features(query)
        
        # 基于实体和关键词快速筛选候选
        candidate_hashes = set()
        
        for entity in features["entities"]:
            candidate_hashes.update(self.entity_index.get(entity, []))
        
        for keyword in features["keywords"]:
            candidate_hashes.update(self.keyword_index.get(keyword, []))
        
        # 计算相似度并排序
        similarities = []
        for query_hash in candidate_hashes:
            if query_hash in self.query_history:
                history_query = self.query_history[query_hash]["query"]
                similarity = self._calculate_similarity(query, history_query)
                if similarity >= self.similarity_threshold:
                    similarities.append((query_hash, similarity))
        
        # 返回最相似的
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def predict_hit_probability(
        self,
        query: str,
        novel_id: str
    ) -> PredictionResult:
        """
        预测缓存命中率
        
        Args:
            query: 查询文本
            novel_id: 小说ID
            
        Returns:
            预测结果
        """
        query_hash = self._generate_query_hash(query, novel_id)
        
        # 查找相似查询
        similar = self.find_similar_queries(query, novel_id)
        
        if not similar:
            # 没有相似历史查询
            return PredictionResult(
                hit_probability=0.1,
                confidence=0.3,
                suggested_action="query",  # 直接查询
                similar_queries=[]
            )
        
        # 基于相似查询的历史命中率计算
        hit_count = 0
        total_count = 0
        similar_query_texts = []
        
        for query_hash, similarity in similar:
            stats = self.query_history.get(query_hash, {})
            cache_hits = stats.get("cache_hits", 0)
            total_queries = stats.get("total_queries", 0)
            
            if total_queries > 0:
                # 加权：相似度越高权重越大
                weight = similarity
                hit_count += (cache_hits / total_queries) * weight
                total_count += weight
            
            similar_query_texts.append(stats.get("query", ""))
        
        if total_count == 0:
            hit_probability = 0.2
        else:
            hit_probability = hit_count / total_count
        
        # 计算置信度（基于相似查询数量）
        confidence = min(len(similar) / self.min_history_count, 1.0)
        
        # 决定建议动作
        if hit_probability > 0.8:
            suggested_action = "cache"
        elif hit_probability > 0.5:
            suggested_action = "both"  # 先查缓存，未命中再查询
        else:
            suggested_action = "query"
        
        self.prediction_stats["total_predictions"] += 1
        
        return PredictionResult(
            hit_probability=hit_probability,
            confidence=confidence,
            suggested_action=suggested_action,
            similar_queries=similar_query_texts[:3]
        )
    
    def record_query_result(
        self,
        query: str,
        novel_id: str,
        cache_hit: bool,
        result_quality: float = 1.0
    ):
        """
        记录查询结果，用于改进预测
        
        Args:
            query: 查询文本
            novel_id: 小说ID
            cache_hit: 是否命中缓存
            result_quality: 结果质量 0-1
        """
        query_hash = self._generate_query_hash(query, novel_id)
        features = self.feature_extractor.extract_features(query)
        
        # 更新历史记录
        if query_hash not in self.query_history:
            self.query_history[query_hash] = {
                "query": query,
                "novel_id": novel_id,
                "total_queries": 0,
                "cache_hits": 0,
                "result_quality_sum": 0,
                "first_seen": time.time(),
                "last_seen": time.time()
            }
        
        stats = self.query_history[query_hash]
        stats["total_queries"] += 1
        if cache_hit:
            stats["cache_hits"] += 1
        stats["result_quality_sum"] += result_quality
        stats["last_seen"] = time.time()
        
        # 更新索引
        for entity in features["entities"]:
            if query_hash not in self.entity_index[entity]:
                self.entity_index[entity].append(query_hash)
        
        for keyword in features["keywords"]:
            if query_hash not in self.keyword_index[keyword]:
                self.keyword_index[keyword].append(query_hash)
    
    def get_prediction_stats(self) -> Dict[str, Any]:
        """获取预测统计信息"""
        total = self.prediction_stats["total_predictions"]
        
        return {
            "total_predictions": total,
            "history_queries": len(self.query_history),
            "indexed_entities": len(self.entity_index),
            "indexed_keywords": len(self.keyword_index),
            "average_confidence": self._calculate_average_confidence(),
            "top_repeated_queries": self._get_top_queries(5)
        }
    
    def _calculate_average_confidence(self) -> float:
        """计算平均置信度"""
        # 简化为基于历史查询数量的启发式
        if len(self.query_history) < 10:
            return 0.3
        elif len(self.query_history) < 50:
            return 0.6
        else:
            return 0.85
    
    def _get_top_queries(self, n: int) -> List[Dict[str, Any]]:
        """获取最频繁的查询"""
        sorted_queries = sorted(
            self.query_history.values(),
            key=lambda x: x["total_queries"],
            reverse=True
        )
        
        return [
            {
                "query": q["query"][:50] + "..." if len(q["query"]) > 50 else q["query"],
                "count": q["total_queries"],
                "hit_rate": q["cache_hits"] / q["total_queries"] if q["total_queries"] > 0 else 0
            }
            for q in sorted_queries[:n]
        ]
    
    def cleanup_old_history(self, max_age_days: int = 30):
        """清理旧的历史记录"""
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 3600
        
        expired_hashes = [
            hash_val for hash_val, stats in self.query_history.items()
            if current_time - stats["last_seen"] > max_age_seconds
        ]
        
        for hash_val in expired_hashes:
            del self.query_history[hash_val]
        
        return len(expired_hashes)


# 全局实例
_cache_predictor: Optional[CacheHitPredictor] = None


def get_cache_predictor() -> CacheHitPredictor:
    """获取缓存命中预测器实例"""
    global _cache_predictor
    if _cache_predictor is None:
        _cache_predictor = CacheHitPredictor()
    return _cache_predictor
