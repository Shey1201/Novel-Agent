"""
Incremental Cache - 增量缓存管理器
只更新变化部分，而不是全量刷新
"""

from typing import Dict, Any, Optional, List, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
import difflib


@dataclass
class CacheDelta:
    """缓存增量"""
    added: Dict[str, Any] = field(default_factory=dict)
    modified: Dict[str, Any] = field(default_factory=dict)
    deleted: Set[str] = field(default_factory=set)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CacheVersion:
    """缓存版本"""
    version_id: str
    data_hash: str
    timestamp: str
    delta_from_previous: Optional[CacheDelta] = None


class DiffCalculator:
    """差异计算器"""
    
    @staticmethod
    def calculate_dict_diff(
        old_data: Dict[str, Any],
        new_data: Dict[str, Any]
    ) -> CacheDelta:
        """
        计算两个字典的差异
        
        Returns:
            包含 added, modified, deleted 的 CacheDelta
        """
        delta = CacheDelta()
        
        old_keys = set(old_data.keys())
        new_keys = set(new_data.keys())
        
        # 新增的键
        delta.added = {k: new_data[k] for k in new_keys - old_keys}
        
        # 删除的键
        delta.deleted = old_keys - new_keys
        
        # 修改的键
        for key in old_keys & new_keys:
            if old_data[key] != new_data[key]:
                delta.modified[key] = {
                    "old": old_data[key],
                    "new": new_data[key]
                }
        
        return delta
    
    @staticmethod
    def calculate_text_diff(old_text: str, new_text: str) -> List[Dict[str, Any]]:
        """
        计算文本差异（行级）
        
        Returns:
            差异操作列表
        """
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        
        diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=''))
        
        operations = []
        for line in diff:
            if line.startswith('@@'):
                # 解析差异块信息
                operations.append({"type": "header", "content": line})
            elif line.startswith('+'):
                operations.append({"type": "add", "content": line[1:]})
            elif line.startswith('-'):
                operations.append({"type": "delete", "content": line[1:]})
            elif line.startswith(' '):
                operations.append({"type": "context", "content": line[1:]})
        
        return operations
    
    @staticmethod
    def apply_delta(base_data: Dict[str, Any], delta: CacheDelta) -> Dict[str, Any]:
        """将增量应用到基础数据"""
        result = dict(base_data)
        
        # 应用新增
        result.update(delta.added)
        
        # 应用修改
        for key, change in delta.modified.items():
            result[key] = change["new"]
        
        # 应用删除
        for key in delta.deleted:
            if key in result:
                del result[key]
        
        return result


class IncrementalCacheManager:
    """
    增量缓存管理器
    
    支持：
    1. 增量更新（只更新变化部分）
    2. 版本历史
    3. 差异回滚
    4. 智能合并
    """
    
    def __init__(self, max_versions: int = 10):
        self.max_versions = max_versions
        
        # 当前数据
        self.current_data: Dict[str, Any] = {}
        
        # 版本历史
        self.versions: List[CacheVersion] = []
        
        # 增量历史
        self.delta_history: Dict[str, CacheDelta] = {}  # version_id -> delta
        
        # 数据哈希缓存
        self.data_hashes: Dict[str, str] = {}
        
        self.diff_calculator = DiffCalculator()
    
    def _calculate_hash(self, data: Any) -> str:
        """计算数据哈希"""
        return hashlib.md5(
            json.dumps(data, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
    
    def update(
        self,
        key: str,
        new_value: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CacheDelta:
        """
        增量更新缓存
        
        Args:
            key: 缓存键
            new_value: 新值
            metadata: 元数据
            
        Returns:
            产生的增量
        """
        old_value = self.current_data.get(key)
        
        # 计算增量
        delta = CacheDelta()
        
        if old_value is None:
            # 新增
            delta.added[key] = new_value
        elif old_value != new_value:
            # 修改
            if isinstance(old_value, dict) and isinstance(new_value, dict):
                # 字典类型，计算详细差异
                nested_delta = self.diff_calculator.calculate_dict_diff(
                    old_value, new_value
                )
                delta.modified[key] = {
                    "type": "dict_diff",
                    "details": nested_delta
                }
            elif isinstance(old_value, str) and isinstance(new_value, str):
                # 字符串类型，计算文本差异
                text_diff = self.diff_calculator.calculate_text_diff(
                    old_value, new_value
                )
                delta.modified[key] = {
                    "type": "text_diff",
                    "details": text_diff
                }
            else:
                # 其他类型，简单替换
                delta.modified[key] = {
                    "old": old_value,
                    "new": new_value
                }
        else:
            # 无变化
            return CacheDelta()
        
        # 应用更新
        self.current_data[key] = new_value
        
        # 创建新版本
        self._create_version(key, delta, metadata)
        
        return delta
    
    def update_batch(
        self,
        updates: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> CacheDelta:
        """
        批量增量更新
        
        Args:
            updates: 更新字典
            metadata: 元数据
            
        Returns:
            合并的增量
        """
        combined_delta = CacheDelta()
        
        for key, new_value in updates.items():
            delta = self.update(key, new_value, metadata)
            combined_delta.added.update(delta.added)
            combined_delta.modified.update(delta.modified)
            combined_delta.deleted.update(delta.deleted)
        
        return combined_delta
    
    def _create_version(
        self,
        key: str,
        delta: CacheDelta,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """创建新版本"""
        version_id = f"v{len(self.versions) + 1}_{datetime.now().timestamp()}"
        data_hash = self._calculate_hash(self.current_data)
        
        version = CacheVersion(
            version_id=version_id,
            data_hash=data_hash,
            timestamp=datetime.now().isoformat(),
            delta_from_previous=delta if delta.added or delta.modified or delta.deleted else None
        )
        
        self.versions.append(version)
        self.delta_history[version_id] = delta
        
        # 限制版本数量
        if len(self.versions) > self.max_versions:
            old_version = self.versions.pop(0)
            if old_version.version_id in self.delta_history:
                del self.delta_history[old_version.version_id]
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        return self.current_data.get(key)
    
    def get_full_cache(self) -> Dict[str, Any]:
        """获取完整缓存"""
        return dict(self.current_data)
    
    def get_changes_since(
        self,
        since_version_id: str
    ) -> CacheDelta:
        """
        获取自指定版本以来的所有变化
        
        Args:
            since_version_id: 起始版本ID
            
        Returns:
            合并的增量
        """
        # 找到版本索引
        version_indices = {v.version_id: i for i, v in enumerate(self.versions)}
        
        if since_version_id not in version_indices:
            # 版本不存在，返回全量
            return CacheDelta(added=self.current_data)
        
        start_idx = version_indices[since_version_id] + 1
        
        # 合并所有后续版本的增量
        combined = CacheDelta()
        for version in self.versions[start_idx:]:
            delta = self.delta_history.get(version.version_id, CacheDelta())
            combined.added.update(delta.added)
            combined.modified.update(delta.modified)
            combined.deleted.update(delta.deleted)
        
        return combined
    
    def rollback_to_version(
        self,
        version_id: str
    ) -> bool:
        """
        回滚到指定版本
        
        Args:
            version_id: 目标版本ID
            
        Returns:
            是否成功
        """
        # 找到版本
        target_version = None
        target_idx = -1
        
        for i, v in enumerate(self.versions):
            if v.version_id == version_id:
                target_version = v
                target_idx = i
                break
        
        if target_version is None:
            return False
        
        # 重建数据（从空开始应用所有增量到目标版本）
        reconstructed = {}
        for version in self.versions[:target_idx + 1]:
            delta = self.delta_history.get(version.version_id, CacheDelta())
            reconstructed = self.diff_calculator.apply_delta(reconstructed, delta)
        
        self.current_data = reconstructed
        
        # 删除后续版本
        self.versions = self.versions[:target_idx + 1]
        for v in self.versions[target_idx + 1:]:
            if v.version_id in self.delta_history:
                del self.delta_history[v.version_id]
        
        return True
    
    def get_version_history(self) -> List[Dict[str, Any]]:
        """获取版本历史"""
        return [
            {
                "version_id": v.version_id,
                "timestamp": v.timestamp,
                "data_hash": v.data_hash[:8] + "...",
                "has_changes": v.delta_from_previous is not None
            }
            for v in self.versions
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_keys = len(self.current_data)
        total_versions = len(self.versions)
        
        # 计算变化统计
        total_additions = sum(
            len(d.added) for d in self.delta_history.values()
        )
        total_modifications = sum(
            len(d.modified) for d in self.delta_history.values()
        )
        total_deletions = sum(
            len(d.deleted) for d in self.delta_history.values()
        )
        
        return {
            "total_keys": total_keys,
            "total_versions": total_versions,
            "max_versions": self.max_versions,
            "total_additions": total_additions,
            "total_modifications": total_modifications,
            "total_deletions": total_deletions,
            "version_history": self.get_version_history()
        }
    
    def clear(self):
        """清空缓存"""
        self.current_data.clear()
        self.versions.clear()
        self.delta_history.clear()
        self.data_hashes.clear()


class SmartCacheUpdater:
    """
    智能缓存更新器
    
    自动检测变化并选择最优更新策略
    """
    
    def __init__(self):
        self.incremental_manager = IncrementalCacheManager()
        self.update_threshold = 0.3  # 变化比例阈值
    
    def smart_update(
        self,
        key: str,
        new_data: Any,
        old_data: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        智能更新缓存
        
        根据变化程度选择：
        - 增量更新（小变化）
        - 全量替换（大变化）
        
        Returns:
            更新结果信息
        """
        if old_data is None:
            old_data = self.incremental_manager.get(key)
        
        if old_data is None:
            # 新增数据
            delta = self.incremental_manager.update(key, new_data)
            return {
                "strategy": "full_insert",
                "delta": delta,
                "message": "新增数据"
            }
        
        # 计算变化比例
        change_ratio = self._calculate_change_ratio(old_data, new_data)
        
        if change_ratio < self.update_threshold:
            # 小变化，使用增量更新
            delta = self.incremental_manager.update(key, new_data)
            return {
                "strategy": "incremental",
                "change_ratio": change_ratio,
                "delta": delta,
                "message": f"增量更新 (变化比例: {change_ratio:.2%})"
            }
        else:
            # 大变化，全量替换
            delta = CacheDelta(
                added={key: new_data},
                modified={},
                deleted={key}
            )
            self.incremental_manager.update(key, new_data)
            return {
                "strategy": "full_replace",
                "change_ratio": change_ratio,
                "delta": delta,
                "message": f"全量替换 (变化比例: {change_ratio:.2%})"
            }
    
    def _calculate_change_ratio(self, old_data: Any, new_data: Any) -> float:
        """计算数据变化比例"""
        if type(old_data) != type(new_data):
            return 1.0  # 类型不同，100%变化
        
        if isinstance(old_data, dict):
            old_keys = set(old_data.keys())
            new_keys = set(new_data.keys())
            
            all_keys = old_keys | new_keys
            changed_keys = (old_keys ^ new_keys) | {
                k for k in old_keys & new_keys
                if old_data[k] != new_data[k]
            }
            
            return len(changed_keys) / len(all_keys) if all_keys else 0.0
        
        elif isinstance(old_data, str):
            if len(old_data) == 0:
                return 1.0 if len(new_data) > 0 else 0.0
            
            # 使用编辑距离估算
            max_len = max(len(old_data), len(new_data))
            diff_count = sum(
                1 for a, b in zip(old_data, new_data) if a != b
            )
            diff_count += abs(len(old_data) - len(new_data))
            
            return min(diff_count / max_len, 1.0)
        
        else:
            return 0.0 if old_data == new_data else 1.0


# 全局实例
_incremental_cache: Optional[IncrementalCacheManager] = None
_smart_updater: Optional[SmartCacheUpdater] = None


def get_incremental_cache() -> IncrementalCacheManager:
    """获取增量缓存管理器实例"""
    global _incremental_cache
    if _incremental_cache is None:
        _incremental_cache = IncrementalCacheManager()
    return _incremental_cache


def get_smart_cache_updater() -> SmartCacheUpdater:
    """获取智能缓存更新器实例"""
    global _smart_updater
    if _smart_updater is None:
        _smart_updater = SmartCacheUpdater()
    return _smart_updater
