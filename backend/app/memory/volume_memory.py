"""
Volume 存储管理模块 - 使用 Supabase
"""
import os
import sys
import subprocess
from typing import List, Optional
from datetime import datetime

from app.models.volume import Volume

# 尝试导入 supabase
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    print("[VolumeMemory] Failed to import supabase, attempting to install...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase", "-q"])
        from supabase import create_client
        SUPABASE_AVAILABLE = True
        print("[VolumeMemory] Supabase installed and imported successfully")
    except Exception as e:
        print(f"[VolumeMemory] Failed to install supabase: {e}")
        SUPABASE_AVAILABLE = False


class VolumeMemory:
    """卷存储管理器"""

    def __init__(self):
        self.supabase = None
        self._initialized = False
        self._init_supabase()

    def _init_supabase(self):
        """初始化 Supabase 客户端"""
        if not SUPABASE_AVAILABLE:
            print("Warning: Supabase not available, volume management will be limited")
            return

        supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

        if supabase_url and supabase_key:
            try:
                self.supabase = create_client(supabase_url, supabase_key)
                self._initialized = True
                print("[VolumeMemory] Connected to Supabase successfully")
            except Exception as e:
                print(f"[VolumeMemory] Error connecting to Supabase: {e}")
                self.supabase = None
                self._initialized = False
        else:
            print("[VolumeMemory] Warning - Supabase credentials not found")
            self.supabase = None
            self._initialized = False

    def _ensure_connected(self):
        """确保 Supabase 已连接"""
        if not self._initialized or self.supabase is None:
            print("[VolumeMemory] Attempting to reconnect to Supabase...")
            self._init_supabase()
        return self.supabase is not None

    def get_volumes_by_novel(self, novel_id: str) -> List[Volume]:
        """获取小说的所有卷"""
        print(f"[VolumeMemory] get_volumes_by_novel called for novel: {novel_id}")
        
        if not self._ensure_connected():
            print("[VolumeMemory] Error: Supabase not connected")
            return []

        try:
            response = self.supabase.table("volumes").select("*").eq("novel_id", novel_id).order("order").execute()
            print(f"[VolumeMemory] Fetched {len(response.data) if response.data else 0} volumes")
            if response.data:
                volumes = []
                for vol_data in response.data:
                    try:
                        volume = Volume(**vol_data)
                        volumes.append(volume)
                    except Exception as e:
                        print(f"[VolumeMemory] Error parsing volume {vol_data.get('id')}: {e}")
                return volumes
        except Exception as e:
            print(f"[VolumeMemory] Error fetching volumes: {e}")
            import traceback
            traceback.print_exc()
        return []

    def get_volume_by_id(self, volume_id: str) -> Optional[Volume]:
        """根据ID获取卷"""
        if not self._ensure_connected():
            return None

        try:
            response = self.supabase.table("volumes").select("*").eq("id", volume_id).single().execute()
            if response.data:
                return Volume(**response.data)
        except Exception as e:
            print(f"[VolumeMemory] Error fetching volume: {e}")
        return None

    def create_volume(self, volume: Volume) -> Optional[Volume]:
        """创建卷"""
        print(f"[VolumeMemory] Creating volume: {volume.name} for novel: {volume.novel_id}")
        
        if not self._ensure_connected():
            print("[VolumeMemory] Error: Supabase not connected")
            return None

        try:
            data = volume.model_dump()
            response = self.supabase.table("volumes").insert(data).execute()
            if response.data:
                print(f"[VolumeMemory] Volume created: {response.data[0]['id']}")
                return Volume(**response.data[0])
        except Exception as e:
            print(f"[VolumeMemory] Error creating volume: {e}")
            import traceback
            traceback.print_exc()
        return None

    def update_volume(self, volume_id: str, updates: dict) -> Optional[Volume]:
        """更新卷"""
        if not self._ensure_connected():
            return None

        try:
            updates["updated_at"] = datetime.now().isoformat()
            response = self.supabase.table("volumes").update(updates).eq("id", volume_id).execute()
            if response.data:
                return Volume(**response.data[0])
        except Exception as e:
            print(f"[VolumeMemory] Error updating volume: {e}")
        return None

    def delete_volume(self, volume_id: str) -> bool:
        """删除卷"""
        if not self._ensure_connected():
            return False

        try:
            # 将卷下的章节移动到未分卷（volume_id设为null）
            self.supabase.table("chapters").update({"volume_id": None}).eq("volume_id", volume_id).execute()
            
            # 删除卷
            self.supabase.table("volumes").delete().eq("id", volume_id).execute()
            return True
        except Exception as e:
            print(f"[VolumeMemory] Error deleting volume: {e}")
        return False

    def move_chapter_to_volume(self, chapter_id: str, volume_id: Optional[str]) -> bool:
        """移动章节到指定卷"""
        if not self._ensure_connected():
            return False

        try:
            self.supabase.table("chapters").update({"volume_id": volume_id}).eq("id", chapter_id).execute()
            return True
        except Exception as e:
            print(f"[VolumeMemory] Error moving chapter: {e}")
        return False


# 全局实例
volume_memory = VolumeMemory()
