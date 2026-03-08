"""
资产管理模块 (优化版)
合并 story_assets 和 global_assets 为统一的 assets 表
"""
import os
import sys
import subprocess
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

# 尝试导入 supabase
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    print("[AssetManager] Failed to import supabase, attempting to install...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase", "-q"])
        from supabase import create_client
        SUPABASE_AVAILABLE = True
        print("[AssetManager] Supabase installed and imported successfully")
    except Exception as e:
        print(f"[AssetManager] Failed to install supabase: {e}")
        SUPABASE_AVAILABLE = False


class AssetVersion(BaseModel):
    """资产版本/快照"""
    id: str
    name: str
    description: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    data: Dict = Field(default_factory=dict)


class Asset(BaseModel):
    """统一资产定义（合并 story_assets 和 global_assets）"""
    id: str
    user_id: Optional[str] = None
    novel_id: Optional[str] = None  # 关联的小说ID（本地资产）
    type: str  # characters, worldbuilding, factions, locations, timeline
    name: str
    content: Dict = Field(default_factory=dict)  # 资产内容
    description: str = ""
    is_global: bool = False  # 是否为全局资产
    is_starred: bool = False  # 是否收藏
    source_novel_id: Optional[str] = None  # 原生小说ID（全局资产）
    color: str = "#6366f1"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class AssetManager:
    """资产管理器 - 适配优化后的数据库结构"""

    def __init__(self):
        self.supabase = None
        self._init_supabase()

    def _init_supabase(self):
        """初始化 Supabase 客户端"""
        if not SUPABASE_AVAILABLE:
            print("[AssetManager] Warning: Supabase not available")
            return

        supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

        if supabase_url and supabase_key:
            try:
                self.supabase = create_client(supabase_url, supabase_key)
                print("[AssetManager] Connected to Supabase")
            except Exception as e:
                print(f"[AssetManager] Error connecting to Supabase: {e}")
        else:
            print("[AssetManager] Warning: Supabase credentials not found")

    def _ensure_connected(self):
        """确保 Supabase 已连接"""
        if self.supabase is None:
            self._init_supabase()
        return self.supabase is not None

    # ==================== 资产CRUD操作 ====================

    def create_asset(self, asset: Asset) -> Optional[Asset]:
        """创建新资产"""
        print(f"[AssetManager] Creating asset: {asset.name}")
        if not self._ensure_connected():
            print("[AssetManager] Error: Supabase not connected")
            return None

        try:
            data = {
                "id": asset.id,
                "user_id": asset.user_id,
                "novel_id": asset.novel_id,
                "type": asset.type,
                "name": asset.name,
                "content": asset.content,
                "description": asset.description,
                "is_global": asset.is_global,
                "is_starred": asset.is_starred,
                "source_novel_id": asset.source_novel_id,
                "color": asset.color,
                "created_at": asset.created_at,
                "updated_at": asset.updated_at,
                "deleted_at": None,
            }

            response = self.supabase.table("assets").insert(data).execute()
            if response.data:
                print(f"[AssetManager] Asset created: {asset.id}")
                return Asset(**response.data[0])
        except Exception as e:
            print(f"[AssetManager] Error creating asset: {e}")
            import traceback
            traceback.print_exc()
        return None

    def get_asset(self, asset_id: str) -> Optional[Asset]:
        """获取单个资产"""
        if not self._ensure_connected():
            return None

        try:
            response = self.supabase.table("assets").select("*").eq("id", asset_id).is_("deleted_at", "null").single().execute()
            if response.data:
                return Asset(**response.data)
        except Exception as e:
            print(f"[AssetManager] Error fetching asset: {e}")
        return None

    def get_assets_by_novel(self, novel_id: str) -> List[Asset]:
        """获取小说的所有本地资产"""
        print(f"[AssetManager] Getting assets for novel: {novel_id}")
        if not self._ensure_connected():
            return []

        try:
            response = self.supabase.table("assets").select("*").eq("novel_id", novel_id).is_("deleted_at", "null").execute()
            if response.data:
                return [Asset(**item) for item in response.data]
        except Exception as e:
            print(f"[AssetManager] Error fetching assets: {e}")
        return []

    def get_global_assets(self, asset_type: Optional[str] = None) -> List[Asset]:
        """获取全局资产"""
        print(f"[AssetManager] Getting global assets, type: {asset_type}")
        if not self._ensure_connected():
            return []

        try:
            query = self.supabase.table("assets").select("*").eq("is_global", True).is_("deleted_at", "null")
            if asset_type:
                query = query.eq("type", asset_type)
            response = query.execute()
            if response.data:
                return [Asset(**item) for item in response.data]
        except Exception as e:
            print(f"[AssetManager] Error fetching global assets: {e}")
        return []

    def update_asset(self, asset_id: str, updates: Dict[str, Any]) -> Optional[Asset]:
        """更新资产"""
        if not self._ensure_connected():
            return None

        try:
            updates["updated_at"] = datetime.now().isoformat()
            response = self.supabase.table("assets").update(updates).eq("id", asset_id).is_("deleted_at", "null").execute()
            if response.data:
                return Asset(**response.data[0])
        except Exception as e:
            print(f"[AssetManager] Error updating asset: {e}")
        return None

    def delete_asset(self, asset_id: str) -> bool:
        """删除资产（软删除）"""
        if not self._ensure_connected():
            return False

        try:
            updates = {
                "deleted_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            response = self.supabase.table("assets").update(updates).eq("id", asset_id).is_("deleted_at", "null").execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"[AssetManager] Error deleting asset: {e}")
        return False

    def toggle_star(self, asset_id: str) -> bool:
        """切换收藏状态"""
        asset = self.get_asset(asset_id)
        if not asset:
            return False
        return self.update_asset(asset_id, {"is_starred": not asset.is_starred}) is not None


# 全局实例
asset_manager = AssetManager()
