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

    # ==================== 以下方法为兼容API路由而添加 ====================

    def get_assets_by_type(self, asset_type: str) -> List[Asset]:
        """按类型获取资产"""
        return self.get_global_assets(asset_type)

    def get_novel_assets(self, novel_id: str) -> List[Asset]:
        """获取小说已挂载的资产（当前实现为获取小说本地资产）"""
        return self.get_assets_by_novel(novel_id)

    def get_asset_mount_count(self, asset_id: str) -> int:
        """获取资产挂载次数"""
        if not self._ensure_connected():
            return 0
        try:
            # 检查 asset_mounts 表是否存在
            response = self.supabase.table("asset_mounts").select("*", count="exact").eq("asset_id", asset_id).execute()
            return response.count if response.count is not None else 0
        except Exception as e:
            error_msg = str(e)
            # 如果表不存在，返回 0 但不打印错误（避免日志刷屏）
            if "Could not find the table" in error_msg or "asset_mounts" in error_msg:
                # 尝试从 assets 表的 novel_id 字段计算挂载数
                try:
                    asset = self.get_asset(asset_id)
                    if asset and asset.novel_id:
                        return 1
                except:
                    pass
                return 0
            print(f"[AssetManager] Error getting mount count: {e}")
            return 0

    def search_assets(self, query: str) -> List[Asset]:
        """搜索资产"""
        if not self._ensure_connected():
            return []
        try:
            # 使用 ilike 进行模糊搜索
            response = self.supabase.table("assets").select("*").ilike("name", f"%{query}%").is_("deleted_at", "null").execute()
            if response.data:
                return [Asset(**item) for item in response.data]
        except Exception as e:
            print(f"[AssetManager] Error searching assets: {e}")
        return []

    def get_starred_assets(self) -> List[Asset]:
        """获取收藏的资产"""
        if not self._ensure_connected():
            return []
        try:
            response = self.supabase.table("assets").select("*").eq("is_starred", True).is_("deleted_at", "null").execute()
            if response.data:
                return [Asset(**item) for item in response.data]
        except Exception as e:
            print(f"[AssetManager] Error fetching starred assets: {e}")
        return []

    def mount_asset_to_novel(self, asset_id: str, novel_id: str, reference_type: str = "linked", version_id: Optional[str] = None) -> bool:
        """挂载资产到小说"""
        if not self._ensure_connected():
            return False
        try:
            # 尝试使用 asset_mounts 表
            data = {
                "asset_id": asset_id,
                "novel_id": novel_id,
                "reference_type": reference_type,
                "version_id": version_id
            }
            response = self.supabase.table("asset_mounts").insert(data).execute()
            return len(response.data) > 0
        except Exception as e:
            error_msg = str(e)
            # 如果表不存在，回退到更新 assets 表的 novel_id 字段
            if "Could not find the table" in error_msg or "asset_mounts" in error_msg:
                print("[AssetManager] asset_mounts table not found, falling back to novel_id update")
                try:
                    return self.update_asset(asset_id, {"novel_id": novel_id})
                except Exception as fallback_e:
                    print(f"[AssetManager] Fallback mount failed: {fallback_e}")
                    return False
            print(f"[AssetManager] Error mounting asset: {e}")
            return False

    def unmount_asset_from_novel(self, asset_id: str, novel_id: str) -> bool:
        """从小说卸载资产"""
        if not self._ensure_connected():
            return False
        try:
            response = self.supabase.table("asset_mounts").delete().eq("asset_id", asset_id).eq("novel_id", novel_id).execute()
            return len(response.data) > 0
        except Exception as e:
            error_msg = str(e)
            # 如果表不存在，回退到更新 assets 表
            if "Could not find the table" in error_msg or "asset_mounts" in error_msg:
                print("[AssetManager] asset_mounts table not found, falling back to novel_id clear")
                try:
                    asset = self.get_asset(asset_id)
                    if asset and asset.novel_id == novel_id:
                        return self.update_asset(asset_id, {"novel_id": None})
                    return True
                except Exception as fallback_e:
                    print(f"[AssetManager] Fallback unmount failed: {fallback_e}")
                    return False
            print(f"[AssetManager] Error unmounting asset: {e}")
            return False

    def get_mount_info(self, asset_id: str, novel_id: str) -> Optional[Dict[str, Any]]:
        """获取资产挂载信息"""
        if not self._ensure_connected():
            return None
        try:
            response = self.supabase.table("asset_mounts").select("*").eq("asset_id", asset_id).eq("novel_id", novel_id).execute()
            if response.data:
                return {"asset_id": asset_id, "novel_id": novel_id, "mounted": True, **response.data[0]}
            return None
        except Exception as e:
            error_msg = str(e)
            # 如果表不存在，回退到检查 assets 表的 novel_id 字段
            if "Could not find the table" in error_msg or "asset_mounts" in error_msg:
                try:
                    asset = self.get_asset(asset_id)
                    if asset and asset.novel_id == novel_id:
                        return {"asset_id": asset_id, "novel_id": novel_id, "mounted": True, "reference_type": "linked"}
                    return None
                except:
                    return None
            print(f"[AssetManager] Error getting mount info: {e}")
            return None

    def is_asset_mounted_to_novel(self, asset_id: str, novel_id: str) -> bool:
        """检查资产是否已挂载到小说"""
        if not self._ensure_connected():
            return False
        try:
            response = self.supabase.table("asset_mounts").select("*").eq("asset_id", asset_id).eq("novel_id", novel_id).execute()
            return len(response.data) > 0
        except Exception as e:
            error_msg = str(e)
            # 如果表不存在，回退到检查 assets 表的 novel_id 字段
            if "Could not find the table" in error_msg or "asset_mounts" in error_msg:
                try:
                    asset = self.get_asset(asset_id)
                    return asset is not None and asset.novel_id == novel_id
                except:
                    return False
            print(f"[AssetManager] Error checking mount status: {e}")
            return False

    def create_asset_version(self, asset_id: str, version: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """创建资产版本（当前实现为将版本信息存储在 content 中）"""
        asset = self.get_asset(asset_id)
        if not asset:
            return None
        
        versions = asset.content.get("versions", [])
        versions.append(version)
        
        if self.update_asset(asset_id, {"content": {**asset.content, "versions": versions}}):
            return version
        return None

    # ==================== 资产分类操作 ====================

    def get_asset_categories(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取资产分类列表"""
        print(f"[AssetManager] Getting asset categories")
        if not self._ensure_connected():
            return []

        try:
            # 尝试查询，如果 deleted_at 列不存在则忽略该条件
            try:
                query = self.supabase.table("asset_categories").select("*").is_("deleted_at", "null")
                if user_id:
                    query = query.eq("user_id", user_id)
                response = query.order("order").execute()
                if response.data:
                    return response.data
            except Exception as inner_e:
                # 如果是因为 deleted_at 列不存在，尝试不带该条件的查询
                if "deleted_at" in str(inner_e):
                    print("[AssetManager] deleted_at column not found, querying without it")
                    query = self.supabase.table("asset_categories").select("*")
                    if user_id:
                        query = query.eq("user_id", user_id)
                    response = query.order("order").execute()
                    if response.data:
                        return response.data
                else:
                    raise inner_e
        except Exception as e:
            print(f"[AssetManager] Error fetching asset categories: {e}")
        return []

    def create_asset_category(self, name: str, color: str = "#6366f1", order: int = 0, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """创建资产分类"""
        print(f"[AssetManager] Creating asset category: {name}")
        if not self._ensure_connected():
            return None

        try:
            data = {
                "name": name,
                "color": color,
                "order": order,
                "user_id": user_id,
            }
            response = self.supabase.table("asset_categories").insert(data).execute()
            if response.data:
                print(f"[AssetManager] Asset category created: {response.data[0]['id']}")
                return response.data[0]
        except Exception as e:
            print(f"[AssetManager] Error creating asset category: {e}")
            import traceback
            traceback.print_exc()
        return None

    def update_asset_category(self, category_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新资产分类"""
        if not self._ensure_connected():
            return None

        try:
            updates["updated_at"] = datetime.now().isoformat()
            response = self.supabase.table("asset_categories").update(updates).eq("id", category_id).execute()
            if response.data:
                return response.data[0]
        except Exception as e:
            print(f"[AssetManager] Error updating asset category: {e}")
        return None

    def delete_asset_category(self, category_id: str) -> bool:
        """删除资产分类（软删除）"""
        if not self._ensure_connected():
            return False

        try:
            updates = {
                "deleted_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            response = self.supabase.table("asset_categories").update(updates).eq("id", category_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"[AssetManager] Error deleting asset category: {e}")
        return False

    def set_asset_category(self, asset_id: str, category_id: Optional[str]) -> bool:
        """设置资产所属分类"""
        print(f"[AssetManager] Setting asset {asset_id} category to {category_id}")
        return self.update_asset(asset_id, {"category_id": category_id}) is not None

    def get_assets_by_category(self, category_id: str) -> List[Asset]:
        """获取指定分类下的所有资产"""
        print(f"[AssetManager] Getting assets by category: {category_id}")
        if not self._ensure_connected():
            return []

        try:
            response = self.supabase.table("assets").select("*").eq("category_id", category_id).is_("deleted_at", "null").execute()
            if response.data:
                return [Asset(**item) for item in response.data]
        except Exception as e:
            print(f"[AssetManager] Error fetching assets by category: {e}")
        return []


# 全局实例
asset_manager = AssetManager()
