"""
分类管理内存模块 - 使用 Supabase
"""
import os
import sys
import subprocess
import uuid
from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime

# 尝试导入 supabase
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    print("[CategoryMemory] Failed to import supabase, attempting to install...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase", "-q"])
        from supabase import create_client
        SUPABASE_AVAILABLE = True
        print("[CategoryMemory] Supabase installed and imported successfully")
    except Exception as e:
        print(f"[CategoryMemory] Failed to install supabase: {e}")
        SUPABASE_AVAILABLE = False


@dataclass
class Category:
    id: str
    name: str
    color: str
    user_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    deleted_at: Optional[str] = None
    order: int = 0


class CategoryMemory:
    """分类内存管理器"""
    
    def __init__(self):
        self.supabase = None
        self._init_supabase()
    
    def _init_supabase(self):
        """初始化 Supabase 客户端"""
        if not SUPABASE_AVAILABLE:
            print("[CategoryMemory] Warning: Supabase not available")
            return
        
        # 支持多种环境变量名
        supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        
        if supabase_url and supabase_key:
            try:
                self.supabase = create_client(supabase_url, supabase_key)
                print("[CategoryMemory] Connected to Supabase successfully")
            except Exception as e:
                print(f"[CategoryMemory] Error connecting to Supabase: {e}")
        else:
            print("[CategoryMemory] Warning - Supabase credentials not found")
    
    def get_all_categories(self) -> List[Category]:
        """获取所有分类"""
        if not self.supabase:
            print("[CategoryMemory] Cannot fetch categories - Supabase not connected")
            return []
        
        try:
            print("[CategoryMemory] Fetching categories from Supabase...")
            response = self.supabase.table("categories").select("*").order("created_at").execute()
            print(f"[CategoryMemory] Response type: {type(response)}")
            print(f"[CategoryMemory] Response data: {response.data}")
            print(f"[CategoryMemory] Fetched {len(response.data) if response.data else 0} categories")
            if response.data:
                categories = []
                for cat in response.data:
                    print(f"[CategoryMemory] Processing category: {cat}")
                    try:
                        category = Category(**cat)
                        categories.append(category)
                    except Exception as e:
                        print(f"[CategoryMemory] Error parsing category {cat}: {e}")
                return categories
        except Exception as e:
            print(f"[CategoryMemory] Error fetching categories: {e}")
            import traceback
            traceback.print_exc()
        return []
    
    def create_category(self, name: str, color: str) -> Optional[Category]:
        """创建新分类"""
        if not self.supabase:
            print("[CategoryMemory] Cannot create category - Supabase not connected")
            return None
        
        try:
            category_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            data = {
                "id": category_id,
                "name": name,
                "color": color,
                "user_id": None,  # 匿名用户
                "created_at": now,
                "updated_at": now,
            }
            
            print(f"[CategoryMemory] Creating category: {data}")
            response = self.supabase.table("categories").insert(data).execute()
            if response.data:
                print(f"[CategoryMemory] Category created: {response.data[0]}")
                return Category(**response.data[0])
        except Exception as e:
            print(f"[CategoryMemory] Error creating category: {e}")
            import traceback
            traceback.print_exc()
        return None
    
    def update_category(self, category_id: str, **updates) -> Optional[Category]:
        """更新分类"""
        if not self.supabase:
            print("[CategoryMemory] Cannot update category - Supabase not connected")
            return None
        
        try:
            updates["updated_at"] = datetime.now().isoformat()
            
            print(f"[CategoryMemory] Updating category {category_id}: {updates}")
            response = self.supabase.table("categories").update(updates).eq("id", category_id).execute()
            if response.data:
                print(f"[CategoryMemory] Category updated: {response.data[0]}")
                return Category(**response.data[0])
        except Exception as e:
            print(f"[CategoryMemory] Error updating category: {e}")
            import traceback
            traceback.print_exc()
        return None
    
    def delete_category(self, category_id: str) -> bool:
        """删除分类"""
        if not self.supabase:
            print("[CategoryMemory] Cannot delete category - Supabase not connected")
            return False
        
        try:
            print(f"[CategoryMemory] Deleting category: {category_id}")
            response = self.supabase.table("categories").delete().eq("id", category_id).execute()
            print(f"[CategoryMemory] Category deleted: {category_id}")
            return True
        except Exception as e:
            print(f"[CategoryMemory] Error deleting category: {e}")
            import traceback
            traceback.print_exc()
        return False


# 全局实例
category_memory = CategoryMemory()
