"""
Agent 配置数据管理模块
"""
import os
import sys
import subprocess
import uuid
import time
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field

# 创建模块级别的 logger
logger = logging.getLogger(__name__)

# 日志级别控制（生产环境可设为 WARNING）
_DEBUG = os.getenv("AGENT_MEMORY_DEBUG", "false").lower() == "true"


def _log(level: str, msg: str):
    """统一日志输出"""
    if _DEBUG or level in ("ERROR", "WARNING"):
        # 使用 print 保证可见性
        print(f"[AgentMemory] {msg}")
    else:
        getattr(logger, level.lower(), logger.info)(msg)

try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    _log("INFO", "Failed to import supabase, attempting to install...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase", "-q"])
        from supabase import create_client
        SUPABASE_AVAILABLE = True
        _log("INFO", "Supabase installed and imported successfully")
    except Exception as e:
        _log("ERROR", f"Failed to install supabase: {e}")
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
    avatar_url: str = ""
    description: str = ""
    deleted_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class AgentMemory:
    """Agent 配置内存管理器"""
    
    # 类级别的缓存
    _all_configs_cache: Tuple[List["AgentConfig"], float] = (None, 0)
    _config_cache: Dict[str, Tuple["AgentConfig", float]] = {}
    _CACHE_TTL = 300  # 5分钟缓存

    def __init__(self):
        self.supabase = None
        self._init_supabase()
    
    def _init_supabase(self):
        """初始化 Supabase 客户端"""
        _log("DEBUG", "_init_supabase called")
        if not SUPABASE_AVAILABLE:
            _log("WARNING", "Supabase not available, agent management will be limited")
            return
        
        # 支持多种环境变量名（本地开发和 Vercel 部署）
        supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        
        _log("DEBUG", f"URL: {supabase_url[:30] + '...' if supabase_url else 'Not set'}")
        _log("DEBUG", f"KEY: {'Set' if supabase_key else 'Not set'}")
        
        if supabase_url and supabase_key:
            try:
                self.supabase = create_client(supabase_url, supabase_key)
                _log("INFO", "Connected to Supabase successfully")
            except Exception as e:
                _log("ERROR", f"Error connecting to Supabase: {e}")
        else:
            _log("WARNING", "Supabase credentials not found")
    
    def get_all_configs(self) -> List[AgentConfig]:
        """获取所有 Agent 配置（带缓存）"""
        # 检查缓存
        if self._all_configs_cache[0] is not None:
            cached_configs, timestamp = self._all_configs_cache
            if time.time() - timestamp < self._CACHE_TTL:
                _log("DEBUG", f"Returning cached configs: {len(cached_configs)}")
                return cached_configs
        
        _log("DEBUG", f"get_all_configs called, supabase: {self.supabase is not None}")
        if not self.supabase:
            return []
        
        try:
            # 使用新表名 "agents"，过滤已删除的记录
            response = self.supabase.table("agents").select("*").is_("deleted_at", "null").execute()
            _log("DEBUG", f"Fetched {len(response.data) if response.data else 0} configs")
            if response.data:
                configs = [AgentConfig(**config) for config in response.data]
                # 存入缓存
                self._all_configs_cache = (configs, time.time())
                return configs
        except Exception as e:
            _log("ERROR", f"Error fetching configs: {e}")
        return []
    
    def get_config(self, agent_id: str) -> Optional[AgentConfig]:
        """根据 agent_id 获取配置（带缓存）"""
        # 检查缓存
        if agent_id in self._config_cache:
            cached_config, timestamp = self._config_cache[agent_id]
            if time.time() - timestamp < self._CACHE_TTL:
                return cached_config
        
        _log("DEBUG", f"get_config called for {agent_id}")
        if not self.supabase:
            _log("ERROR", "Supabase not connected")
            return None
        
        try:
            # 使用新表名 "agents"，过滤已删除的记录
            response = self.supabase.table("agents").select("*").eq("agent_id", agent_id).is_("deleted_at", "null").limit(1).execute()
            _log("DEBUG", f"Query response: {response}")
            if response.data and len(response.data) > 0:
                _log("DEBUG", f"Found config: {response.data[0]}")
                config = AgentConfig(**response.data[0])
                # 存入缓存
                self._config_cache[agent_id] = (config, time.time())
                return config
            else:
                _log("DEBUG", f"No config found for {agent_id}")
        except Exception as e:
            _log("ERROR", f"ERROR fetching config: {e}")
            import traceback
            traceback.print_exc()
        return None
    
    def create_config(self, agent_id: str, name: str, role: str, personality: str,
                      temperature: float, prompt: str, enabled: bool = True) -> Optional[AgentConfig]:
        """创建新配置"""
        # 清除缓存
        self._all_configs_cache = (None, 0)
        
        _log("DEBUG", f"create_config called for {agent_id}")
        if not self.supabase:
            _log("ERROR", "Supabase not connected")
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
                "deleted_at": None,  # 新表结构添加的字段
            }
            _log("DEBUG", f"Inserting data: {data}")

            # 使用新表名 "agents"
            response = self.supabase.table("agents").insert(data).execute()
            _log("DEBUG", f"Insert response: {response}")
            if response.data:
                return AgentConfig(**response.data[0])
        except Exception as e:
            _log("ERROR", f"ERROR creating config: {e}")
            import traceback
            traceback.print_exc()
            # 抛出异常让调用者处理
            raise
        return None
    
    def update_config(self, agent_id: str, **updates) -> Optional[AgentConfig]:
        """更新配置"""
        # 清除缓存
        self._all_configs_cache = (None, 0)
        self._config_cache.pop(agent_id, None)
        
        if not self.supabase:
            return None

        try:
            updates["updated_at"] = datetime.now().isoformat()

            # 使用新表名 "agents"，只更新未删除的记录
            response = self.supabase.table("agents").update(updates).eq("agent_id", agent_id).is_("deleted_at", "null").execute()
            if response.data:
                return AgentConfig(**response.data[0])
        except Exception as e:
            _log("ERROR", f"Error updating config: {e}")
        return None

    def delete_config(self, agent_id: str) -> bool:
        """删除配置（软删除）"""
        if not self.supabase:
            return False

        try:
            # 使用软删除而不是硬删除
            updates = {
                "deleted_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            response = self.supabase.table("agents").update(updates).eq("agent_id", agent_id).is_("deleted_at", "null").execute()
            return len(response.data) > 0
        except Exception as e:
            _log("ERROR", f"Error deleting config: {e}")
        return False


# 全局实例
agent_memory = AgentMemory()
