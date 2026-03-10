"""
小说数据管理模块
处理小说和章节的 CRUD 操作
"""
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from app.core.cache_manager import cached, cache_invalidate

try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
    print("[NovelMemory] Supabase imported successfully")
except ImportError as e:
    print(f"[NovelMemory] Failed to import supabase: {e}")
    # 尝试自动安装
    import subprocess
    import sys
    print("[NovelMemory] Attempting to install supabase...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase==2.15.0", "-q"])
        from supabase import create_client
        SUPABASE_AVAILABLE = True
        print("[NovelMemory] Supabase installed and imported successfully")
    except Exception as install_error:
        SUPABASE_AVAILABLE = False
        print(f"[NovelMemory] Failed to install supabase: {install_error}")


@dataclass
class Novel:
    id: str
    title: str
    locked: bool = False
    category_id: Optional[str] = None
    user_id: Optional[str] = None
    mounted_skills: Optional[list] = None
    deleted_at: Optional[str] = None
    outline: str = ""  # 小说大纲
    word_count: int = 0  # 字数统计
    status: str = "draft"  # 状态：draft, writing, completed
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Chapter:
    id: str
    novel_id: str
    title: str
    content: str = ""
    order_index: int = 0
    status: str = "draft"  # draft, writing, review, completed
    volume_name: str = "未分卷"  # 卷名称
    volume_order: int = 0  # 卷顺序
    word_count: int = 0  # 章节字数
    summary: str = ""  # 章节摘要
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Volume:
    id: str
    novel_id: str
    name: str = "未命名卷"
    order: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class NovelMemory:
    """小说内存管理器"""
    
    def __init__(self):
        self.supabase = None
        self._init_supabase()
    
    def _init_supabase(self):
        """初始化 Supabase 客户端"""
        if not SUPABASE_AVAILABLE:
            print("[NovelMemory] Warning: Supabase not available, novel management will be limited")
            return
        
        # 支持多种环境变量名（本地开发和 Vercel 部署）
        supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        
        # 详细日志
        print(f"[NovelMemory] Checking environment variables:")
        print(f"  SUPABASE_URL: {'Set' if os.getenv('SUPABASE_URL') else 'Not set'}")
        print(f"  NEXT_PUBLIC_SUPABASE_URL: {'Set' if os.getenv('NEXT_PUBLIC_SUPABASE_URL') else 'Not set'}")
        print(f"  SUPABASE_SERVICE_KEY: {'Set' if os.getenv('SUPABASE_SERVICE_KEY') else 'Not set'}")
        print(f"  SUPABASE_ANON_KEY: {'Set' if os.getenv('SUPABASE_ANON_KEY') else 'Not set'}")
        print(f"  NEXT_PUBLIC_SUPABASE_ANON_KEY: {'Set' if os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY') else 'Not set'}")
        print(f"  Final URL: {supabase_url[:20] + '...' if supabase_url else 'Not set'}")
        print(f"  Final KEY: {'Set' if supabase_key else 'Not set'}")
        
        if supabase_url and supabase_key:
            try:
                self.supabase = create_client(supabase_url, supabase_key)
                print("[NovelMemory] Connected to Supabase successfully")
            except Exception as e:
                print(f"[NovelMemory] Error connecting to Supabase: {e}")
        else:
            print("[NovelMemory] Warning - Supabase credentials not found, novel management will not work")
    
    def _ensure_connected(self):
        """确保 Supabase 已连接"""
        return self.supabase is not None
    
    # ========== 小说操作 ==========
    
    @cached(ttl=60, key_prefix="novels")
    def get_all_novels(self) -> List[Novel]:
        """获取所有小说（排除已删除的）"""
        print(f"[NovelMemory] get_all_novels called, supabase connected: {self.supabase is not None}")
        
        if not self.supabase:
            print("[NovelMemory] Error: Supabase not connected")
            return []
        
        try:
            print("[NovelMemory] Querying novels from Supabase...")
            # 只查询未删除的小说
            response = self.supabase.table("novels").select("*").is_("deleted_at", "null").order("created_at", desc=True).execute()
            print(f"[NovelMemory] Fetched {len(response.data) if response.data else 0} novels")
            if response.data:
                novels = []
                for novel_data in response.data:
                    try:
                        novel = Novel(**novel_data)
                        novels.append(novel)
                    except Exception as e:
                        print(f"[NovelMemory] Error parsing novel {novel_data.get('id')}: {e}")
                        print(f"[NovelMemory] Novel data: {novel_data}")
                return novels
        except Exception as e:
            print(f"[NovelMemory] Error fetching novels: {e}")
            import traceback
            traceback.print_exc()
        return []
    
    def get_novel(self, novel_id: str) -> Optional[Novel]:
        """根据ID获取小说"""
        if not self.supabase:
            return None
        
        try:
            response = self.supabase.table("novels").select("*").eq("id", novel_id).single().execute()
            if response.data:
                return Novel(**response.data)
        except Exception as e:
            print(f"NovelMemory: Error fetching novel: {e}")
        return None
    
    def create_novel(self, title: str, locked: bool = False, category_id: Optional[str] = None) -> Optional[Novel]:
        """创建新小说"""
        if not self.supabase:
            return None
        
        try:
            novel_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            data = {
                "id": novel_id,
                "title": title,
                "locked": locked,
                "category_id": category_id,
                "user_id": None,  # 匿名用户
                "created_at": now,
                "updated_at": now,
            }
            
            response = self.supabase.table("novels").insert(data).execute()
            if response.data:
                cache_invalidate("novels")
                return Novel(**response.data[0])
        except Exception as e:
            print(f"NovelMemory: Error creating novel: {e}")
        return None
    
    def update_novel(self, novel_id: str, **updates) -> Optional[Novel]:
        """更新小说"""
        if not self.supabase:
            return None
        
        try:
            updates["updated_at"] = datetime.now().isoformat()
            
            response = self.supabase.table("novels").update(updates).eq("id", novel_id).execute()
            if response.data:
                cache_invalidate("novels")
                return Novel(**response.data[0])
        except Exception as e:
            print(f"NovelMemory: Error updating novel: {e}")
        return None
    
    def delete_novel(self, novel_id: str) -> bool:
        """删除小说"""
        if not self.supabase:
            return False
        
        try:
            # 先删除所有章节
            self.supabase.table("chapters").delete().eq("novel_id", novel_id).execute()
            
            # 再删除小说
            response = self.supabase.table("novels").delete().eq("id", novel_id).execute()
            if len(response.data) > 0:
                cache_invalidate("novels")
                return True
        except Exception as e:
            print(f"NovelMemory: Error deleting novel: {e}")
        return False
    
    # ========== 章节操作 ==========
    
    def get_chapters_by_novel(self, novel_id: str) -> List[Chapter]:
        """获取小说的所有章节"""
        if not self.supabase:
            return []
        
        try:
            response = self.supabase.table("chapters").select("*").eq("novel_id", novel_id).order("order_index").execute()
            if response.data:
                return [Chapter(**chapter) for chapter in response.data]
        except Exception as e:
            print(f"NovelMemory: Error fetching chapters: {e}")
        return []
    
    def get_chapter(self, chapter_id: str) -> Optional[Chapter]:
        """根据ID获取章节"""
        if not self.supabase:
            return None
        
        try:
            response = self.supabase.table("chapters").select("*").eq("id", chapter_id).single().execute()
            if response.data:
                return Chapter(**response.data)
        except Exception as e:
            print(f"NovelMemory: Error fetching chapter: {e}")
        return None
    
    def create_chapter(self, novel_id: str, title: str, content: str = "", order_index: int = 0, status: str = "draft", volume_name: str = "未分卷", volume_order: int = 0) -> Optional[Chapter]:
        """创建新章节"""
        print(f"[NovelMemory] Creating chapter '{title}' in volume '{volume_name}' for novel: {novel_id}")
        
        if not self._ensure_connected():
            print("[NovelMemory] Error: Supabase not connected")
            return None
        
        try:
            chapter_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            data = {
                "id": chapter_id,
                "novel_id": novel_id,
                "title": title,
                "content": content,
                "order_index": order_index,
                "status": status,
                "volume_name": volume_name or "未分卷",
                "volume_order": volume_order or 0,
                "created_at": now,
                "updated_at": now,
            }
            
            response = self.supabase.table("chapters").insert(data).execute()
            if response.data:
                print(f"[NovelMemory] Chapter created: {chapter_id}")
                return Chapter(**response.data[0])
        except Exception as e:
            print(f"[NovelMemory] Error creating chapter: {e}")
            import traceback
            traceback.print_exc()
        return None
    
    def update_chapter(self, chapter_id: str, **updates) -> Optional[Chapter]:
        """更新章节"""
        if not self.supabase:
            return None
        
        try:
            updates["updated_at"] = datetime.now().isoformat()
            
            response = self.supabase.table("chapters").update(updates).eq("id", chapter_id).execute()
            if response.data:
                return Chapter(**response.data[0])
        except Exception as e:
            print(f"NovelMemory: Error updating chapter: {e}")
        return None
    
    def delete_chapter(self, chapter_id: str) -> bool:
        """删除章节"""
        if not self.supabase:
            return False
        
        try:
            response = self.supabase.table("chapters").delete().eq("id", chapter_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"NovelMemory: Error deleting chapter: {e}")
        return False

    # ========== 卷操作 ==========

    def get_volumes_by_novel(self, novel_id: str) -> List[Dict[str, Any]]:
        """获取小说的所有卷（包括空卷）"""
        print(f"[NovelMemory] get_volumes_by_novel called for novel: {novel_id}")
        
        if not self._ensure_connected():
            print("[NovelMemory] Error: Supabase not connected")
            return []

        try:
            # 1. 从 volumes 表中获取所有卷（包括空卷）
            volumes_response = self.supabase.table("volumes") \
                .select("*") \
                .eq("novel_id", novel_id) \
                .order("order") \
                .execute()
            
            volumes_map = {}
            if volumes_response.data:
                for vol in volumes_response.data:
                    vol_id = vol.get("id", f"vol-{vol.get('order', 0)}-{vol.get('name', '未命名')}")
                    volumes_map[vol_id] = {
                        "id": vol_id,
                        "name": vol.get("name", "未命名卷"),
                        "order": vol.get("order", 0),
                        "chapter_count": 0
                    }
            
            # 2. 从章节中统计每个卷的章节数量
            chapters_response = self.supabase.table("chapters") \
                .select("volume_name, volume_order") \
                .eq("novel_id", novel_id) \
                .execute()
            
            if chapters_response.data:
                for chapter in chapters_response.data:
                    vol_name = chapter.get("volume_name", "未分卷") or "未分卷"
                    vol_order = chapter.get("volume_order", 0) or 0
                    vol_id = f"vol-{vol_order}-{vol_name}"
                    
                    # 如果卷不存在于 volumes 表中，添加它
                    if vol_id not in volumes_map:
                        volumes_map[vol_id] = {
                            "id": vol_id,
                            "name": vol_name,
                            "order": vol_order,
                            "chapter_count": 0
                        }
                    volumes_map[vol_id]["chapter_count"] += 1
            
            # 3. 如果没有卷，返回默认卷
            if not volumes_map:
                return [{"id": "vol-default", "name": "未分卷", "order": 0, "chapter_count": 0}]
            
            # 4. 转换为列表并排序
            volumes = list(volumes_map.values())
            volumes.sort(key=lambda x: x["order"])
            
            print(f"[NovelMemory] Fetched {len(volumes)} volumes")
            return volumes
        except Exception as e:
            print(f"[NovelMemory] Error fetching volumes: {e}")
            import traceback
            traceback.print_exc()
        return [{"id": "vol-default", "name": "未分卷", "order": 0, "chapter_count": 0}]

    def create_volume(self, novel_id: str, volume_id: str, volume_name: str, volume_order: int) -> Optional[Volume]:
        """创建新卷（保存到 volumes 表）"""
        print(f"[NovelMemory] Creating volume '{volume_name}' (order: {volume_order}) for novel: {novel_id}")
        
        if not self._ensure_connected():
            print("[NovelMemory] Error: Supabase not connected")
            return None

        try:
            now = datetime.now().isoformat()
            data = {
                "id": volume_id,
                "novel_id": novel_id,
                "name": volume_name,
                "order": volume_order,
                "created_at": now,
                "updated_at": now,
            }
            
            response = self.supabase.table("volumes").insert(data).execute()
            if response.data:
                print(f"[NovelMemory] Volume created: {volume_id}")
                return Volume(**response.data[0])
        except Exception as e:
            print(f"[NovelMemory] Error creating volume: {e}")
            import traceback
            traceback.print_exc()
        return None
    
    def update_volume(self, volume_id: str, **updates) -> Optional[Volume]:
        """更新卷信息"""
        print(f"[NovelMemory] Updating volume: {volume_id}")
        
        if not self._ensure_connected():
            return None

        try:
            updates["updated_at"] = datetime.now().isoformat()
            
            response = self.supabase.table("volumes").update(updates).eq("id", volume_id).execute()
            if response.data:
                print(f"[NovelMemory] Volume updated: {volume_id}")
                return Volume(**response.data[0])
        except Exception as e:
            print(f"[NovelMemory] Error updating volume: {e}")
            import traceback
            traceback.print_exc()
        return None
    
    def delete_volume_from_db(self, volume_id: str) -> bool:
        """从数据库删除卷"""
        print(f"[NovelMemory] Deleting volume from DB: {volume_id}")
        
        if not self._ensure_connected():
            return False

        try:
            response = self.supabase.table("volumes").delete().eq("id", volume_id).execute()
            print(f"[NovelMemory] Volume deleted: {volume_id}")
            return True
        except Exception as e:
            print(f"[NovelMemory] Error deleting volume: {e}")
            import traceback
            traceback.print_exc()
        return False

    def update_volume_name(self, novel_id: str, old_name: str, new_name: str) -> bool:
        """更新卷名称（更新所有属于该卷的章节）"""
        print(f"[NovelMemory] Updating volume name from '{old_name}' to '{new_name}' for novel: {novel_id}")
        
        if not self._ensure_connected():
            return False

        try:
            response = self.supabase.table("chapters") \
                .update({"volume_name": new_name}) \
                .eq("novel_id", novel_id) \
                .eq("volume_name", old_name) \
                .execute()
            print(f"[NovelMemory] Updated {len(response.data) if response.data else 0} chapters")
            return True
        except Exception as e:
            print(f"[NovelMemory] Error updating volume name: {e}")
            import traceback
            traceback.print_exc()
        return False

    def move_chapter_to_volume(self, chapter_id: str, volume_name: str, volume_order: int) -> bool:
        """移动章节到指定卷"""
        print(f"[NovelMemory] Moving chapter {chapter_id} to volume: {volume_name} (order: {volume_order})")
        
        if not self._ensure_connected():
            return False

        try:
            response = self.supabase.table("chapters") \
                .update({
                    "volume_name": volume_name,
                    "volume_order": volume_order
                }) \
                .eq("id", chapter_id) \
                .execute()
            print(f"[NovelMemory] Chapter moved successfully")
            return True
        except Exception as e:
            print(f"[NovelMemory] Error moving chapter: {e}")
            import traceback
            traceback.print_exc()
        return False

    def delete_volume(self, novel_id: str, volume_name: str) -> bool:
        """删除卷（将该卷下的所有章节移动到未分卷）"""
        print(f"[NovelMemory] Deleting volume '{volume_name}' for novel: {novel_id}")
        
        if not self._ensure_connected():
            return False

        try:
            # 将该卷下的章节移动到未分卷
            response = self.supabase.table("chapters") \
                .update({
                    "volume_name": "未分卷",
                    "volume_order": 0
                }) \
                .eq("novel_id", novel_id) \
                .eq("volume_name", volume_name) \
                .execute()
            print(f"[NovelMemory] Moved {len(response.data) if response.data else 0} chapters to default volume")
            return True
        except Exception as e:
            print(f"[NovelMemory] Error deleting volume: {e}")
            import traceback
            traceback.print_exc()
        return False


# 全局实例 - 延迟初始化
_novel_memory_instance = None

def get_novel_memory():
    """获取 NovelMemory 实例（延迟初始化）"""
    global _novel_memory_instance
    if _novel_memory_instance is None:
        _novel_memory_instance = NovelMemory()
    return _novel_memory_instance

# 为了向后兼容，使用属性代理
class _NovelMemoryProxy:
    """代理类，实现真正的延迟初始化"""
    def _get_instance(self):
        return get_novel_memory()
    
    def __getattr__(self, name):
        return getattr(self._get_instance(), name)
    
    def __setattr__(self, name, value):
        if name in ('_get_instance',):
            super().__setattr__(name, value)
        else:
            setattr(self._get_instance(), name, value)

novel_memory = _NovelMemoryProxy()
