"""
LLM 模块 - 统一大语言模型接口
从数据库读取 AI 配置
"""

from typing import Any, Optional
from functools import lru_cache

from langchain_openai import ChatOpenAI


def _get_ai_config_from_db() -> dict:
    """从数据库获取 AI 配置"""
    try:
        import os
        from supabase import create_client
        
        # 获取 Supabase 连接信息
        supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            print("[LLM] Supabase credentials not found")
            return {}
        
        # 创建客户端
        supabase = create_client(supabase_url, supabase_key)
        
        # 查询 AI 配置
        result = supabase.table("settings").select("ai_chat_model, ai_api_key, ai_base_url, ai_is_active").is_("deleted_at", "null").limit(1).execute()
        
        if result.data and len(result.data) > 0:
            data = result.data[0]
            return {
                "chat_model": data.get("ai_chat_model"),
                "api_key": data.get("ai_api_key"),
                "base_url": data.get("ai_base_url"),
                "is_active": data.get("ai_is_active", False)
            }
    except Exception as e:
        print(f"[LLM] Error loading AI config from DB: {e}")
    
    return {}


def get_llm() -> Optional[Any]:
    """
    获取 LLM 实例
    从数据库读取配置，如果没有则返回 None
    """
    config = _get_ai_config_from_db()
    
    if not config.get("is_active"):
        print("[LLM] AI is not active in settings")
        return None
    
    api_key = config.get("api_key")
    if not api_key:
        print("[LLM] API key not found in settings")
        return None
    
    chat_model = config.get("chat_model", "gpt-4o-mini")
    base_url = config.get("base_url")
    
    try:
        # 根据模型选择不同的客户端
        if "deepseek" in chat_model.lower() or (base_url and "deepseek" in base_url.lower()):
            # DeepSeek 使用 OpenAI 兼容接口
            return ChatOpenAI(
                api_key=api_key,
                model=chat_model,
                base_url=base_url or "https://api.deepseek.com/v1",
                temperature=0.7,
            )
        else:
            # 默认使用 OpenAI
            return ChatOpenAI(
                api_key=api_key,
                model=chat_model,
                base_url=base_url,
                temperature=0.7,
            )
    except Exception as e:
        print(f"[LLM] Error creating LLM client: {e}")
        return None


def get_llm_or_raise() -> Any:
    """获取 LLM，如果没有配置则抛出异常"""
    llm = get_llm()
    if llm is None:
        raise ValueError(
            "LLM not configured. Please configure AI settings in the system settings page."
        )
    return llm
