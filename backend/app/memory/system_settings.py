"""
System Settings - 系统设置管理
存储和管理系统级别的配置，包括 Token 限制
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


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
    """系统设置管理器"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.settings_file = self.data_dir / "system_settings.json"
        self.settings = SystemSettings()
        self._load()
    
    def _load(self):
        """加载设置"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.settings = self._dict_to_settings(data)
            except Exception as e:
                print(f"加载系统设置失败: {e}")
                self.settings = SystemSettings()
    
    def _save(self):
        """保存设置"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings_to_dict(self.settings), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存系统设置失败: {e}")
    
    def _dict_to_settings(self, data: Dict) -> SystemSettings:
        """字典转设置对象"""
        return SystemSettings(
            token=TokenSettings(**data.get('token', {})),
            discussion=DiscussionSettings(**data.get('discussion', {})),
            cache=CacheSettings(**data.get('cache', {})),
            generation=GenerationSettings(**data.get('generation', {}))
        )
    
    def _settings_to_dict(self, settings: SystemSettings) -> Dict:
        """设置对象转字典"""
        return {
            'token': asdict(settings.token),
            'discussion': asdict(settings.discussion),
            'cache': asdict(settings.cache),
            'generation': asdict(settings.generation)
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
