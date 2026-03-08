"""
Global Asset Manager: 全局资产管理模块 (Supabase 版本)
管理跨小说的资产存储和映射关系
"""

import os
from typing import Dict, List, Optional, Set
from datetime import datetime
from pydantic import BaseModel, Field

# 尝试导入 supabase
try:
    from supabase import create_client
    from supabase._sync.client import SyncClient as Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None


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
    """全局资产管理器 - Supabase 版本"""
    
    def __init__(self):
        self.supabase: Optional[Any] = None
        self._init_supabase()
    
    def _init_supabase(self):
        """初始化 Supabase 客户端"""
        if not SUPABASE_AVAILABLE:
            print("Warning: Supabase not available, global asset management will be limited")
            return
        
        # 支持多种环境变量名（本地开发和 Vercel 部署）
        supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        
        if supabase_url and supabase_key:
            try:
                self.supabase = create_client(supabase_url, supabase_key)
                print("GlobalAssetManager: Connected to Supabase")
            except Exception as e:
                print(f"Error connecting to Supabase: {e}")
        else:
            print("Warning: Supabase credentials not found")
    
    # ==================== 资产CRUD操作 ====================
    
    def create_asset(self, asset: GlobalAsset) -> GlobalAsset:
        """创建新资产"""
        if not self.supabase:
            raise Exception("Supabase not available")
        
        try:
            # 创建资产
            asset_data = {
                "id": asset.id,
                "name": asset.name,
                "type": asset.type,
                "description": asset.description,
                "source_novel_id": asset.source_novel_id,
                "source_novel_name": asset.source_novel_name,
                "color": asset.color,
                "is_starred": asset.is_starred,
                "active_version_id": asset.active_version_id,
            }
            
            response = self.supabase.table("global_assets").insert(asset_data).execute()
            
            # 创建版本
            for version in asset.versions:
                version_data = {
                    "id": version.id,
                    "asset_id": asset.id,
                    "name": version.name,
                    "description": version.description,
                    "data": version.data,
                }
                self.supabase.table("asset_versions").insert(version_data).execute()
            
            return asset
        except Exception as e:
            print(f"Error creating asset: {e}")
            raise
    
    def get_asset(self, asset_id: str) -> Optional[GlobalAsset]:
        """获取单个资产"""
        if not self.supabase:
            return None
        
        try:
            # 获取资产
            response = self.supabase.table("global_assets").select("*").eq("id", asset_id).single().execute()
            if not response.data:
                return None
            
            asset_data = response.data
            
            # 获取版本
            versions_response = self.supabase.table("asset_versions").select("*").eq("asset_id", asset_id).execute()
            versions = []
            if versions_response.data:
                for v in versions_response.data:
                    versions.append(AssetVersion(
                        id=v["id"],
                        name=v["name"],
                        description=v.get("description"),
                        created_at=v["created_at"],
                        data=v.get("data", {}),
                    ))
            
            return GlobalAsset(
                id=asset_data["id"],
                name=asset_data["name"],
                type=asset_data["type"],
                description=asset_data.get("description"),
                source_novel_id=asset_data["source_novel_id"],
                source_novel_name=asset_data["source_novel_name"],
                color=asset_data.get("color"),
                is_starred=asset_data.get("is_starred", False),
                versions=versions,
                created_at=asset_data["created_at"],
                updated_at=asset_data["updated_at"],
                active_version_id=asset_data.get("active_version_id"),
            )
        except Exception as e:
            print(f"Error getting asset: {e}")
        return None
    
    def get_all_assets(self) -> List[GlobalAsset]:
        """获取所有资产"""
        if not self.supabase:
            return []
        
        try:
            response = self.supabase.table("global_assets").select("*").execute()
            if not response.data:
                return []
            
            assets = []
            for asset_data in response.data:
                asset = self.get_asset(asset_data["id"])
                if asset:
                    assets.append(asset)
            
            return assets
        except Exception as e:
            print(f"Error getting all assets: {e}")
        return []
    
    def get_assets_by_type(self, asset_type: str) -> List[GlobalAsset]:
        """按类型获取资产"""
        if not self.supabase:
            return []
        
        try:
            response = self.supabase.table("global_assets").select("*").eq("type", asset_type).execute()
            if not response.data:
                return []
            
            assets = []
            for asset_data in response.data:
                asset = self.get_asset(asset_data["id"])
                if asset:
                    assets.append(asset)
            
            return assets
        except Exception as e:
            print(f"Error getting assets by type: {e}")
        return []
    
    def get_assets_by_novel(self, novel_id: str) -> List[GlobalAsset]:
        """按原生小说获取资产"""
        if not self.supabase:
            return []
        
        try:
            response = self.supabase.table("global_assets").select("*").eq("source_novel_id", novel_id).execute()
            if not response.data:
                return []
            
            assets = []
            for asset_data in response.data:
                asset = self.get_asset(asset_data["id"])
                if asset:
                    assets.append(asset)
            
            return assets
        except Exception as e:
            print(f"Error getting assets by novel: {e}")
        return []
    
    def update_asset(self, asset_id: str, updates: Dict) -> Optional[GlobalAsset]:
        """更新资产"""
        if not self.supabase:
            return None
        
        try:
            # 过滤掉 versions 字段（单独处理）
            asset_updates = {k: v for k, v in updates.items() if k != "versions"}
            
            if asset_updates:
                response = self.supabase.table("global_assets").update(asset_updates).eq("id", asset_id).execute()
                if not response.data:
                    return None
            
            return self.get_asset(asset_id)
        except Exception as e:
            print(f"Error updating asset: {e}")
        return None
    
    def delete_asset(self, asset_id: str) -> bool:
        """删除资产"""
        if not self.supabase:
            return False
        
        try:
            # 删除资产（级联删除会处理版本和映射）
            self.supabase.table("global_assets").delete().eq("id", asset_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting asset: {e}")
        return False
    
    # ==================== 版本管理 ====================
    
    def create_asset_version(self, asset_id: str, version: AssetVersion) -> Optional[AssetVersion]:
        """为资产创建新版本"""
        if not self.supabase:
            return None
        
        try:
            version_data = {
                "id": version.id,
                "asset_id": asset_id,
                "name": version.name,
                "description": version.description,
                "data": version.data,
            }
            
            response = self.supabase.table("asset_versions").insert(version_data).execute()
            if response.data:
                return version
        except Exception as e:
            print(f"Error creating asset version: {e}")
        return None
    
    def set_active_version(self, asset_id: str, version_id: Optional[str]) -> bool:
        """设置资产的激活版本"""
        if not self.supabase:
            return False
        
        try:
            self.supabase.table("global_assets").update({
                "active_version_id": version_id
            }).eq("id", asset_id).execute()
            return True
        except Exception as e:
            print(f"Error setting active version: {e}")
        return False
    
    # ==================== 挂载/引用管理 ====================
    
    def mount_asset_to_novel(
        self, 
        asset_id: str, 
        novel_id: str, 
        reference_type: str = "linked",
        version_id: Optional[str] = None
    ) -> bool:
        """将资产挂载到小说"""
        if not self.supabase:
            return False
        
        try:
            mapping_data = {
                "novel_id": novel_id,
                "asset_id": asset_id,
                "reference_type": reference_type,
                "version_id": version_id,
            }
            
            self.supabase.table("novel_asset_mappings").insert(mapping_data).execute()
            return True
        except Exception as e:
            print(f"Error mounting asset: {e}")
        return False
    
    def unmount_asset_from_novel(self, asset_id: str, novel_id: str) -> bool:
        """从小说卸载资产"""
        if not self.supabase:
            return False
        
        try:
            self.supabase.table("novel_asset_mappings").delete().eq("novel_id", novel_id).eq("asset_id", asset_id).execute()
            return True
        except Exception as e:
            print(f"Error unmounting asset: {e}")
        return False
    
    def get_novel_assets(self, novel_id: str) -> List[GlobalAsset]:
        """获取小说挂载的所有资产"""
        if not self.supabase:
            return []
        
        try:
            response = self.supabase.table("novel_asset_mappings").select("asset_id").eq("novel_id", novel_id).execute()
            if not response.data:
                return []
            
            assets = []
            for mapping in response.data:
                asset = self.get_asset(mapping["asset_id"])
                if asset:
                    assets.append(asset)
            
            return assets
        except Exception as e:
            print(f"Error getting novel assets: {e}")
        return []
    
    def get_asset_mount_count(self, asset_id: str) -> int:
        """获取资产的挂载次数（被多少小说引用）"""
        if not self.supabase:
            return 0
        
        try:
            response = self.supabase.table("novel_asset_mappings").select("*", count="exact").eq("asset_id", asset_id).execute()
            return len(response.data) if response.data else 0
        except Exception as e:
            print(f"Error getting mount count: {e}")
        return 0
    
    def is_asset_mounted_to_novel(self, asset_id: str, novel_id: str) -> bool:
        """检查资产是否已挂载到指定小说"""
        if not self.supabase:
            return False
        
        try:
            response = self.supabase.table("novel_asset_mappings").select("*").eq("novel_id", novel_id).eq("asset_id", asset_id).execute()
            return len(response.data) > 0 if response.data else False
        except Exception as e:
            print(f"Error checking mount status: {e}")
        return False
    
    def get_mount_info(self, asset_id: str, novel_id: str) -> Optional[Dict]:
        """获取资产在小说中的挂载信息"""
        if not self.supabase:
            return None
        
        try:
            response = self.supabase.table("novel_asset_mappings").select("*").eq("novel_id", novel_id).eq("asset_id", asset_id).single().execute()
            if response.data:
                return {
                    "reference_type": response.data.get("reference_type", "linked"),
                    "version_id": response.data.get("version_id"),
                }
        except Exception as e:
            print(f"Error getting mount info: {e}")
        return None
    
    # ==================== 搜索功能 ====================
    
    def search_assets(self, query: str) -> List[GlobalAsset]:
        """搜索资产"""
        if not self.supabase:
            return []
        
        try:
            # 使用 ilike 进行模糊搜索
            response = self.supabase.table("global_assets").select("*").or_(
                f"name.ilike.%{query}%,description.ilike.%{query}%,source_novel_name.ilike.%{query}%"
            ).execute()
            
            if not response.data:
                return []
            
            assets = []
            for asset_data in response.data:
                asset = self.get_asset(asset_data["id"])
                if asset:
                    assets.append(asset)
            
            return assets
        except Exception as e:
            print(f"Error searching assets: {e}")
        return []
    
    def get_starred_assets(self) -> List[GlobalAsset]:
        """获取收藏的资产"""
        if not self.supabase:
            return []
        
        try:
            response = self.supabase.table("global_assets").select("*").eq("is_starred", True).execute()
            if not response.data:
                return []
            
            assets = []
            for asset_data in response.data:
                asset = self.get_asset(asset_data["id"])
                if asset:
                    assets.append(asset)
            
            return assets
        except Exception as e:
            print(f"Error getting starred assets: {e}")
        return []
    
    def toggle_star_asset(self, asset_id: str) -> Optional[bool]:
        """切换资产的收藏状态"""
        if not self.supabase:
            return None
        
        try:
            # 获取当前状态
            asset = self.get_asset(asset_id)
            if not asset:
                return None
            
            new_status = not asset.is_starred
            self.supabase.table("global_assets").update({"is_starred": new_status}).eq("id", asset_id).execute()
            return new_status
        except Exception as e:
            print(f"Error toggling star: {e}")
        return None


# 全局实例
asset_manager = GlobalAssetManager()
