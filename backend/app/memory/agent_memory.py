"""
Agent 配置数据管理模块
"""
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


@dataclass
class AgentConfig:
    id: str
    agent_id: str
    name: str
    role: str
    personality: str
    temperature: float
    prompt: str
    enabled: bool
    user_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class AgentMemory:
    """Agent 配置内存管理器"""
    
    def __init__(self):
        self.supabase = None
        self._init_supabase()
    
    def _init_supabase(self):
        """初始化 Supabase 客户端"""
        print("[AgentMemory] _init_supabase called")
        if not SUPABASE_AVAILABLE:
            print("[AgentMemory] Warning: Supabase not available, agent management will be limited")
            return
        
        # 支持多种环境变量名（本地开发和 Vercel 部署）
        supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        
        print(f"[AgentMemory] URL: {supabase_url[:30] + '...' if supabase_url else 'Not set'}")
        print(f"[AgentMemory] KEY: {'Set' if supabase_key else 'Not set'}")
        
        if supabase_url and supabase_key:
            try:
                self.supabase = create_client(supabase_url, supabase_key)
                print("[AgentMemory] Connected to Supabase successfully")
            except Exception as e:
                print(f"[AgentMemory] Error connecting to Supabase: {e}")
        else:
            print("[AgentMemory] Warning - Supabase credentials not found")
    
    def get_all_configs(self) -> List[AgentConfig]:
        """获取所有 Agent 配置"""
        print(f"[AgentMemory] get_all_configs called, supabase: {self.supabase is not None}")
        if not self.supabase:
            return []
        
        try:
            response = self.supabase.table("agent_configs").select("*").execute()
            print(f"[AgentMemory] Fetched {len(response.data) if response.data else 0} configs")
            if response.data:
                return [AgentConfig(**config) for config in response.data]
        except Exception as e:
            print(f"[AgentMemory] Error fetching configs: {e}")
        return []
    
    def get_config(self, agent_id: str) -> Optional[AgentConfig]:
        """根据 agent_id 获取配置"""
        print(f"[AgentMemory] get_config called for {agent_id}")
        if not self.supabase:
            print("[AgentMemory] ERROR: Supabase not connected")
            return None
        
        try:
            # 不使用 .single()，改用 .limit(1) 避免记录不存在时抛出异常
            response = self.supabase.table("agent_configs").select("*").eq("agent_id", agent_id).limit(1).execute()
            print(f"[AgentMemory] Query response: {response}")
            if response.data and len(response.data) > 0:
                print(f"[AgentMemory] Found config: {response.data[0]}")
                return AgentConfig(**response.data[0])
            else:
                print(f"[AgentMemory] No config found for {agent_id}")
        except Exception as e:
            print(f"[AgentMemory] ERROR fetching config: {e}")
            import traceback
            traceback.print_exc()
        return None
    
    def create_config(self, agent_id: str, name: str, role: str, personality: str, 
                      temperature: float, prompt: str, enabled: bool = True) -> Optional[AgentConfig]:
        """创建新配置"""
        print(f"[AgentMemory] create_config called for {agent_id}")
        if not self.supabase:
            print("[AgentMemory] ERROR: Supabase not connected")
            return None
        
        try:
            config_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            data = {
                "id": config_id,
                "agent_id": agent_id,
                "name": name,
                "role": role,
                "personality": personality,
                "temperature": temperature,
                "prompt": prompt,
                "enabled": enabled,
                "user_id": None,  # 匿名用户
                "created_at": now,
                "updated_at": now,
            }
            print(f"[AgentMemory] Inserting data: {data}")
            
            response = self.supabase.table("agent_configs").insert(data).execute()
            print(f"[AgentMemory] Insert response: {response}")
            if response.data:
                return AgentConfig(**response.data[0])
        except Exception as e:
            print(f"[AgentMemory] ERROR creating config: {e}")
            import traceback
            traceback.print_exc()
            # 抛出异常让调用者处理
            raise
        return None
    
    def update_config(self, agent_id: str, **updates) -> Optional[AgentConfig]:
        """更新配置"""
        if not self.supabase:
            return None
        
        try:
            updates["updated_at"] = datetime.now().isoformat()
            
            response = self.supabase.table("agent_configs").update(updates).eq("agent_id", agent_id).execute()
            if response.data:
                return AgentConfig(**response.data[0])
        except Exception as e:
            print(f"AgentMemory: Error updating config: {e}")
        return None
    
    def delete_config(self, agent_id: str) -> bool:
        """删除配置"""
        if not self.supabase:
            return False
        
        try:
            response = self.supabase.table("agent_configs").delete().eq("agent_id", agent_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"AgentMemory: Error deleting config: {e}")
        return False


# 全局实例
agent_memory = AgentMemory()
