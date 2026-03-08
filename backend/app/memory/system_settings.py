"""
System Settings - 系统设置管理 (Supabase 版本)
存储和管理系统级别的配置，包括 Token 限制
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

# 尝试导入 supabase
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


@dataclass
class TokenSettings:
    """Token 相关设置"""
    enabled: bool = False           # 是否启用 Token 限制
    daily_limit: int = 50000        # 每日 Token 限制（默认 50K）
    warning_threshold: float = 0.8  # 警告阈值（80%）
    
    # 各 Agent 预算分配比例
    budget_allocation: Dict[str, float] = None
    
    def __post_init__(self):
        if self.budget_allocation is None:
            self.budget_allocation = {
                "planner": 0.10,
                "discussion": 0.13,
                "conflict": 0.07,
                "writing": 0.47,
                "editor": 0.13,
                "reader": 0.07,
                "summary": 0.03,
            }


@dataclass
class DiscussionSettings:
    """讨论相关设置"""
    max_rounds: int = 2             # 最大讨论轮数
    max_tokens_per_response: int = 80  # 每次发言最大 tokens
    enable_short_mode: bool = True  # 启用短发言模式
    min_chapter_interval: int = 3   # 最小讨论间隔（章数）


@dataclass
class CacheSettings:
    """缓存相关设置"""
    enable_planner_cache: bool = True
    enable_conflict_cache: bool = True
    enable_consistency_cache: bool = True
    ttl_hours: int = 24


@dataclass
class GenerationSettings:
    """生成相关设置"""
    paragraph_length: int = 500     # 每段字数
    reader_interval: int = 3        # Reader Agent 调用间隔
    enable_streaming: bool = True   # 启用流式生成


@dataclass
class SystemSettings:
    """系统设置"""
    token: TokenSettings = None
    discussion: DiscussionSettings = None
    cache: CacheSettings = None
    generation: GenerationSettings = None
    
    def __post_init__(self):
        if self.token is None:
            self.token = TokenSettings()
        if self.discussion is None:
            self.discussion = DiscussionSettings()
        if self.cache is None:
            self.cache = CacheSettings()
        if self.generation is None:
            self.generation = GenerationSettings()


class SystemSettingsManager:
    """系统设置管理器 - Supabase 版本"""
    
    def __init__(self):
        self.supabase = None
        self.settings = SystemSettings()
        self._init_supabase()
        self._load()
    
    def _init_supabase(self):
        """初始化 Supabase 客户端"""
        if not SUPABASE_AVAILABLE:
            print("Warning: Supabase not available, using default settings")
            return
        
        # 支持多种环境变量名（本地开发和 Vercel 部署）
        supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        
        if supabase_url and supabase_key:
            try:
                self.supabase = create_client(supabase_url, supabase_key)
                print("SystemSettingsManager: Connected to Supabase")
            except Exception as e:
                print(f"Error connecting to Supabase: {e}")
        else:
            print("Warning: Supabase credentials not found, using default settings")
    
    def _load(self):
        """从 Supabase 加载设置（使用新表名 settings）"""
        if not self.supabase:
            self.settings = SystemSettings()
            return

        try:
            # 使用新表名 "settings"，过滤已删除的记录
            response = self.supabase.table("settings").select("*").is_("deleted_at", "null").limit(1).execute()

            if response.data and len(response.data) > 0:
                data = response.data[0]
                self.settings = self._dict_to_settings(data)
                print("System settings loaded from Supabase")
            else:
                # 没有设置，创建默认设置
                print("No system settings found, creating default...")
                self._create_default_settings()
        except Exception as e:
            print(f"Error loading system settings: {e}")
            self.settings = SystemSettings()
    
    def _create_default_settings(self):
        """创建默认设置（使用新表名 settings）"""
        if not self.supabase:
            return

        try:
            default_data = {
                "token_enabled": False,
                "token_daily_limit": 50000,
                "token_warning_threshold": 0.8,
                "token_budget_allocation": {
                    "planner": 0.10,
                    "discussion": 0.13,
                    "conflict": 0.07,
                    "writing": 0.47,
                    "editor": 0.13,
                    "reader": 0.07,
                    "summary": 0.03,
                },
                "discussion_max_rounds": 2,
                "discussion_max_tokens": 80,
                "discussion_enable_short_mode": True,
                "discussion_min_interval": 3,
                "cache_enable_planner": True,
                "cache_enable_conflict": True,
                "cache_enable_consistency": True,
                "deleted_at": None,  # 新表结构添加的字段
            }

            # 使用新表名 "settings"
            self.supabase.table("settings").insert(default_data).execute()
            print("Default system settings created")
        except Exception as e:
            print(f"Error creating default settings: {e}")
    
    def _save(self):
        """保存设置到 Supabase（使用新表名 settings）"""
        if not self.supabase:
            return

        try:
            data = self._settings_to_dict(self.settings)

            # 检查是否已有设置（使用新表名，过滤已删除的记录）
            response = self.supabase.table("settings").select("id").is_("deleted_at", "null").limit(1).execute()

            if response.data and len(response.data) > 0:
                # 更新现有设置
                setting_id = response.data[0]["id"]
                self.supabase.table("settings").update(data).eq("id", setting_id).execute()
            else:
                # 创建新设置
                data["deleted_at"] = None  # 新表结构添加的字段
                self.supabase.table("settings").insert(data).execute()

            print("System settings saved to Supabase")
        except Exception as e:
            print(f"Error saving system settings: {e}")
    
    def _dict_to_settings(self, data: Dict) -> SystemSettings:
        """字典转设置对象"""
        token_budget = data.get('token_budget_allocation', {})
        
        return SystemSettings(
            token=TokenSettings(
                enabled=data.get('token_enabled', False),
                daily_limit=data.get('token_daily_limit', 50000),
                warning_threshold=data.get('token_warning_threshold', 0.8),
                budget_allocation=token_budget if token_budget else {
                    "planner": 0.10,
                    "discussion": 0.13,
                    "conflict": 0.07,
                    "writing": 0.47,
                    "editor": 0.13,
                    "reader": 0.07,
                    "summary": 0.03,
                }
            ),
            discussion=DiscussionSettings(
                max_rounds=data.get('discussion_max_rounds', 2),
                max_tokens_per_response=data.get('discussion_max_tokens', 80),
                enable_short_mode=data.get('discussion_enable_short_mode', True),
                min_chapter_interval=data.get('discussion_min_interval', 3)
            ),
            cache=CacheSettings(
                enable_planner_cache=data.get('cache_enable_planner', True),
                enable_conflict_cache=data.get('cache_enable_conflict', True),
                enable_consistency_cache=data.get('cache_enable_consistency', True),
                ttl_hours=data.get('cache_ttl_hours', 24)
            ),
            generation=GenerationSettings(
                paragraph_length=data.get('generation_paragraph_length', 500),
                reader_interval=data.get('generation_reader_interval', 3),
                enable_streaming=data.get('generation_enable_streaming', True)
            )
        )
    
    def _settings_to_dict(self, settings: SystemSettings) -> Dict:
        """设置对象转字典"""
        return {
            'token_enabled': settings.token.enabled,
            'token_daily_limit': settings.token.daily_limit,
            'token_warning_threshold': settings.token.warning_threshold,
            'token_budget_allocation': settings.token.budget_allocation,
            'discussion_max_rounds': settings.discussion.max_rounds,
            'discussion_max_tokens': settings.discussion.max_tokens_per_response,
            'discussion_enable_short_mode': settings.discussion.enable_short_mode,
            'discussion_min_interval': settings.discussion.min_chapter_interval,
            'cache_enable_planner': settings.cache.enable_planner_cache,
            'cache_enable_conflict': settings.cache.enable_conflict_cache,
            'cache_enable_consistency': settings.cache.enable_consistency_cache,
            'cache_ttl_hours': settings.cache.ttl_hours,
            'generation_paragraph_length': settings.generation.paragraph_length,
            'generation_reader_interval': settings.generation.reader_interval,
            'generation_enable_streaming': settings.generation.enable_streaming,
        }
    
    def get_settings(self) -> SystemSettings:
        """获取所有设置"""
        return self.settings
    
    def update_token_settings(self, **kwargs) -> TokenSettings:
        """更新 Token 设置"""
        for key, value in kwargs.items():
            if hasattr(self.settings.token, key):
                setattr(self.settings.token, key, value)
        self._save()
        return self.settings.token
    
    def update_discussion_settings(self, **kwargs) -> DiscussionSettings:
        """更新讨论设置"""
        for key, value in kwargs.items():
            if hasattr(self.settings.discussion, key):
                setattr(self.settings.discussion, key, value)
        self._save()
        return self.settings.discussion
    
    def update_cache_settings(self, **kwargs) -> CacheSettings:
        """更新缓存设置"""
        for key, value in kwargs.items():
            if hasattr(self.settings.cache, key):
                setattr(self.settings.cache, key, value)
        self._save()
        return self.settings.cache
    
    def update_generation_settings(self, **kwargs) -> GenerationSettings:
        """更新生成设置"""
        for key, value in kwargs.items():
            if hasattr(self.settings.generation, key):
                setattr(self.settings.generation, key, value)
        self._save()
        return self.settings.generation
    
    def get_token_budget_manager_config(self) -> Dict[str, Any]:
        """获取 Token Budget Manager 配置"""
        return {
            'daily_limit': self.settings.token.daily_limit if self.settings.token.enabled else None,
            'budget_allocation': self.settings.token.budget_allocation
        }
    
    def get_discussion_controller_config(self) -> Dict[str, Any]:
        """获取 Discussion Controller 配置"""
        return {
            'max_rounds': self.settings.discussion.max_rounds,
            'max_tokens_per_response': self.settings.discussion.max_tokens_per_response,
            'enable_short_mode': self.settings.discussion.enable_short_mode,
            'min_chapter_interval': self.settings.discussion.min_chapter_interval
        }
    
    def get_agent_cache_config(self) -> Dict[str, Any]:
        """获取 Agent Cache 配置"""
        return {
            'enable_planner_cache': self.settings.cache.enable_planner_cache,
            'enable_conflict_cache': self.settings.cache.enable_conflict_cache,
            'enable_consistency_cache': self.settings.cache.enable_consistency_cache,
            'ttl_hours': self.settings.cache.ttl_hours
        }
    
    def reset_to_default(self):
        """重置为默认设置"""
        self.settings = SystemSettings()
        self._save()


# 全局实例
system_settings_manager = SystemSettingsManager()


def get_system_settings_manager() -> SystemSettingsManager:
    """获取系统设置管理器实例"""
    return system_settings_manager
