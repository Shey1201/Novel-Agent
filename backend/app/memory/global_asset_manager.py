"""
Global Asset Manager: 全局资产管理模块
管理跨小说的资产存储和映射关系
"""

import json
import os
from typing import Dict, List, Optional, Set
from datetime import datetime
from pydantic import BaseModel, Field


class AssetVersion(BaseModel):
    """资产版本/快照"""
    id: str
    name: str
    description: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    data: Dict = Field(default_factory=dict)


class GlobalAsset(BaseModel):
    """全局资产定义"""
    id: str
    name: str
    type: str  # characters, worldbuilding, factions, locations, timeline
    description: Optional[str] = None
    source_novel_id: str  # 原生小说ID
    source_novel_name: str  # 原生小说名称
    color: Optional[str] = None  # 用于UI显示的标识色
    is_starred: bool = False
    versions: List[AssetVersion] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    # 当前激活的版本ID
    active_version_id: Optional[str] = None


class NovelAssetMapping(BaseModel):
    """小说与资产的映射关系"""
    novel_id: str
    asset_ids: Set[str] = Field(default_factory=set)
    # 记录每个资产的引用方式: "linked" | "cloned"
    reference_types: Dict[str, str] = Field(default_factory=dict)
    # 记录每个资产使用的版本
    version_selections: Dict[str, Optional[str]] = Field(default_factory=dict)


class GlobalAssetManager:
    """全局资产管理器"""
    
    DATA_DIR = "data"
    GLOBAL_ASSETS_DIR = "global_assets"
    MAPPING_FILE = "novel_asset_mapping.json"
    
    def __init__(self):
        self._assets: Dict[str, GlobalAsset] = {}
        self._mappings: Dict[str, NovelAssetMapping] = {}
        self._ensure_directories()
        self._load_data()
    
    def _ensure_directories(self):
        """确保数据目录存在"""
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(os.path.join(self.DATA_DIR, self.GLOBAL_ASSETS_DIR), exist_ok=True)
    
    def _get_assets_file_path(self) -> str:
        """获取资产文件路径"""
        return os.path.join(self.DATA_DIR, self.GLOBAL_ASSETS_DIR, "assets.json")
    
    def _get_mapping_file_path(self) -> str:
        """获取映射文件路径"""
        return os.path.join(self.DATA_DIR, self.GLOBAL_ASSETS_DIR, self.MAPPING_FILE)
    
    def _load_data(self):
        """从磁盘加载数据"""
        # 加载资产
        assets_path = self._get_assets_file_path()
        if os.path.exists(assets_path):
            with open(assets_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._assets = {
                    k: GlobalAsset(**v) for k, v in data.items()
                }
        
        # 加载映射
        mapping_path = self._get_mapping_file_path()
        if os.path.exists(mapping_path):
            with open(mapping_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._mappings = {
                    k: NovelAssetMapping(
                        novel_id=v['novel_id'],
                        asset_ids=set(v['asset_ids']),
                        reference_types=v.get('reference_types', {}),
                        version_selections=v.get('version_selections', {})
                    ) for k, v in data.items()
                }
    
    def _save_assets(self):
        """保存资产到磁盘"""
        assets_path = self._get_assets_file_path()
        with open(assets_path, 'w', encoding='utf-8') as f:
            json.dump(
                {k: v.model_dump() for k, v in self._assets.items()},
                f,
                ensure_ascii=False,
                indent=2
            )
    
    def _save_mappings(self):
        """保存映射到磁盘"""
        mapping_path = self._get_mapping_file_path()
        with open(mapping_path, 'w', encoding='utf-8') as f:
            json.dump(
                {
                    k: {
                        'novel_id': v.novel_id,
                        'asset_ids': list(v.asset_ids),
                        'reference_types': v.reference_types,
                        'version_selections': v.version_selections
                    } for k, v in self._mappings.items()
                },
                f,
                ensure_ascii=False,
                indent=2
            )
    
    # ==================== 资产CRUD操作 ====================
    
    def create_asset(self, asset: GlobalAsset) -> GlobalAsset:
        """创建新资产"""
        self._assets[asset.id] = asset
        self._save_assets()
        return asset
    
    def get_asset(self, asset_id: str) -> Optional[GlobalAsset]:
        """获取单个资产"""
        return self._assets.get(asset_id)
    
    def get_all_assets(self) -> List[GlobalAsset]:
        """获取所有资产"""
        return list(self._assets.values())
    
    def get_assets_by_type(self, asset_type: str) -> List[GlobalAsset]:
        """按类型获取资产"""
        return [a for a in self._assets.values() if a.type == asset_type]
    
    def get_assets_by_novel(self, novel_id: str) -> List[GlobalAsset]:
        """按原生小说获取资产"""
        return [a for a in self._assets.values() if a.source_novel_id == novel_id]
    
    def update_asset(self, asset_id: str, updates: Dict) -> Optional[GlobalAsset]:
        """更新资产"""
        if asset_id not in self._assets:
            return None
        
        asset = self._assets[asset_id]
        for key, value in updates.items():
            if hasattr(asset, key):
                setattr(asset, key, value)
        
        asset.updated_at = datetime.now().isoformat()
        self._save_assets()
        return asset
    
    def delete_asset(self, asset_id: str) -> bool:
        """删除资产"""
        if asset_id not in self._assets:
            return False
        
        del self._assets[asset_id]
        
        # 同时从所有映射中移除
        for mapping in self._mappings.values():
            if asset_id in mapping.asset_ids:
                mapping.asset_ids.discard(asset_id)
                mapping.reference_types.pop(asset_id, None)
                mapping.version_selections.pop(asset_id, None)
        
        self._save_assets()
        self._save_mappings()
        return True
    
    # ==================== 版本管理 ====================
    
    def create_asset_version(self, asset_id: str, version: AssetVersion) -> Optional[AssetVersion]:
        """为资产创建新版本"""
        asset = self._assets.get(asset_id)
        if not asset:
            return None
        
        asset.versions.append(version)
        asset.updated_at = datetime.now().isoformat()
        self._save_assets()
        return version
    
    def set_active_version(self, asset_id: str, version_id: Optional[str]) -> bool:
        """设置资产的激活版本"""
        asset = self._assets.get(asset_id)
        if not asset:
            return False
        
        if version_id is None:
            asset.active_version_id = None
        else:
            # 验证版本存在
            version_exists = any(v.id == version_id for v in asset.versions)
            if not version_exists:
                return False
            asset.active_version_id = version_id
        
        asset.updated_at = datetime.now().isoformat()
        self._save_assets()
        return True
    
    # ==================== 挂载/引用管理 ====================
    
    def mount_asset_to_novel(
        self, 
        asset_id: str, 
        novel_id: str, 
        reference_type: str = "linked",
        version_id: Optional[str] = None
    ) -> bool:
        """将资产挂载到小说"""
        if asset_id not in self._assets:
            return False
        
        # 获取或创建映射
        if novel_id not in self._mappings:
            self._mappings[novel_id] = NovelAssetMapping(novel_id=novel_id)
        
        mapping = self._mappings[novel_id]
        mapping.asset_ids.add(asset_id)
        mapping.reference_types[asset_id] = reference_type
        mapping.version_selections[asset_id] = version_id
        
        self._save_mappings()
        return True
    
    def unmount_asset_from_novel(self, asset_id: str, novel_id: str) -> bool:
        """从小说卸载资产"""
        if novel_id not in self._mappings:
            return False
        
        mapping = self._mappings[novel_id]
        if asset_id not in mapping.asset_ids:
            return False
        
        mapping.asset_ids.discard(asset_id)
        mapping.reference_types.pop(asset_id, None)
        mapping.version_selections.pop(asset_id, None)
        
        self._save_mappings()
        return True
    
    def get_novel_assets(self, novel_id: str) -> List[GlobalAsset]:
        """获取小说挂载的所有资产"""
        mapping = self._mappings.get(novel_id)
        if not mapping:
            return []
        
        return [
            self._assets[aid] for aid in mapping.asset_ids 
            if aid in self._assets
        ]
    
    def get_asset_mount_count(self, asset_id: str) -> int:
        """获取资产的挂载次数（被多少小说引用）"""
        count = 0
        for mapping in self._mappings.values():
            if asset_id in mapping.asset_ids:
                count += 1
        return count
    
    def is_asset_mounted_to_novel(self, asset_id: str, novel_id: str) -> bool:
        """检查资产是否已挂载到指定小说"""
        mapping = self._mappings.get(novel_id)
        if not mapping:
            return False
        return asset_id in mapping.asset_ids
    
    def get_mount_info(self, asset_id: str, novel_id: str) -> Optional[Dict]:
        """获取资产在小说中的挂载信息"""
        mapping = self._mappings.get(novel_id)
        if not mapping or asset_id not in mapping.asset_ids:
            return None
        
        return {
            'reference_type': mapping.reference_types.get(asset_id, 'linked'),
            'version_id': mapping.version_selections.get(asset_id)
        }
    
    # ==================== 搜索功能 ====================
    
    def search_assets(self, query: str) -> List[GlobalAsset]:
        """搜索资产"""
        query = query.lower()
        results = []
        
        for asset in self._assets.values():
            # 搜索名称
            if query in asset.name.lower():
                results.append(asset)
                continue
            
            # 搜索描述
            if asset.description and query in asset.description.lower():
                results.append(asset)
                continue
            
            # 搜索原生小说名称
            if query in asset.source_novel_name.lower():
                results.append(asset)
                continue
        
        return results
    
    def get_starred_assets(self) -> List[GlobalAsset]:
        """获取收藏的资产"""
        return [a for a in self._assets.values() if a.is_starred]
    
    def toggle_star_asset(self, asset_id: str) -> Optional[bool]:
        """切换资产的收藏状态"""
        asset = self._assets.get(asset_id)
        if not asset:
            return None
        
        asset.is_starred = not asset.is_starred
        asset.updated_at = datetime.now().isoformat()
        self._save_assets()
        return asset.is_starred


# 全局实例
asset_manager = GlobalAssetManager()
