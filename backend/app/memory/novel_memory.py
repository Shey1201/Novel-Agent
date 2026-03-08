"""
小说数据管理模块
处理小说和章节的 CRUD 操作
"""
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = Any


@dataclass
class Novel:
    id: str
    title: str
    locked: bool = False
    category_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Chapter:
    id: str
    novel_id: str
    title: str
    content: str = ""
    order: int = 0
    status: str = "draft"  # draft, writing, review, completed
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class NovelMemory:
    """小说内存管理器"""
    
    def __init__(self):
        self.supabase: Optional[Client] = None
        self._init_supabase()
    
    def _init_supabase(self):
        """初始化 Supabase 客户端"""
        if not SUPABASE_AVAILABLE:
            print("Warning: Supabase not available, novel management will be limited")
            return
        
        # 支持多种环境变量名（本地开发和 Vercel 部署）
        supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        
        if supabase_url and supabase_key:
            try:
                self.supabase = create_client(supabase_url, supabase_key)
                print("NovelMemory: Connected to Supabase")
            except Exception as e:
                print(f"NovelMemory: Error connecting to Supabase: {e}")
        else:
            print("NovelMemory: Warning - Supabase credentials not found")
    
    # ========== 小说操作 ==========
    
    def get_all_novels(self) -> List[Novel]:
        """获取所有小说"""
        if not self.supabase:
            return []
        
        try:
            response = self.supabase.table("novels").select("*").order("created_at", desc=True).execute()
            if response.data:
                return [Novel(**novel) for novel in response.data]
        except Exception as e:
            print(f"NovelMemory: Error fetching novels: {e}")
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
                "created_at": now,
                "updated_at": now,
            }
            
            response = self.supabase.table("novels").insert(data).execute()
            if response.data:
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
            return len(response.data) > 0
        except Exception as e:
            print(f"NovelMemory: Error deleting novel: {e}")
        return False
    
    # ========== 章节操作 ==========
    
    def get_chapters_by_novel(self, novel_id: str) -> List[Chapter]:
        """获取小说的所有章节"""
        if not self.supabase:
            return []
        
        try:
            response = self.supabase.table("chapters").select("*").eq("novel_id", novel_id).order("order").execute()
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
    
    def create_chapter(self, novel_id: str, title: str, content: str = "", order: int = 0, status: str = "draft") -> Optional[Chapter]:
        """创建新章节"""
        if not self.supabase:
            return None
        
        try:
            chapter_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            data = {
                "id": chapter_id,
                "novel_id": novel_id,
                "title": title,
                "content": content,
                "order": order,
                "status": status,
                "created_at": now,
                "updated_at": now,
            }
            
            response = self.supabase.table("chapters").insert(data).execute()
            if response.data:
                return Chapter(**response.data[0])
        except Exception as e:
            print(f"NovelMemory: Error creating chapter: {e}")
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


# 全局实例
novel_memory = NovelMemory()
