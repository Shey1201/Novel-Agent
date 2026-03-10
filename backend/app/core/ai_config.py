"""
AI 配置管理模块
从数据库读取 AI 配置并创建 LLM 实例
"""

from typing import Optional, Dict, Any


def get_ai_config_from_db() -> Optional[Dict[str, Any]]:
    """
    从数据库读取 AI 配置
    
    Returns:
        如果配置存在且激活，返回配置字典；否则返回 None
    """
    try:
        from app.memory.system_settings import supabase
        
        result = supabase.table("settings").select(
            "ai_chat_model, ai_api_key, ai_base_url, ai_is_active"
        ).limit(1).execute()
        
        if result.data and len(result.data) > 0:
            data = result.data[0]
            is_active = data.get("ai_is_active", False)
            api_key = data.get("ai_api_key")
            
            # 只有当配置激活且有 API Key 时才返回配置
            if is_active and api_key:
                return {
                    "model": data.get("ai_chat_model", "gpt-4o-mini"),
                    "api_key": api_key,
                    "base_url": data.get("ai_base_url"),
                    "is_active": True
                }
        
        return None
    except Exception as e:
        print(f"从数据库读取 AI 配置失败: {e}")
        return None


def create_llm_from_config(config: Optional[Dict[str, Any]] = None):
    """
    根据配置创建 LLM 实例
    
    Args:
        config: AI 配置字典，如果为 None 则从数据库读取
        
    Returns:
        LangChain ChatOpenAI 实例，或 None（如果配置无效）
    """
    if config is None:
        config = get_ai_config_from_db()
    
    if not config:
        return None
    
    try:
        from langchain_openai import ChatOpenAI
        
        llm_kwargs = {
            "api_key": config["api_key"],
            "model": config.get("model", "gpt-4o-mini"),
            "temperature": 0.7,
        }
        
        # 如果提供了 base_url，则使用它
        if config.get("base_url"):
            llm_kwargs["base_url"] = config["base_url"]
        
        return ChatOpenAI(**llm_kwargs)
    except Exception as e:
        print(f"创建 LLM 实例失败: {e}")
        return None


def get_llm_with_fallback():
    """
    获取 LLM 实例，优先使用数据库配置，其次使用环境变量
    
    Returns:
        LLM 实例或 None
    """
    # 首先尝试从数据库获取配置
    db_config = get_ai_config_from_db()
    if db_config:
        llm = create_llm_from_config(db_config)
        if llm:
            return llm
    
    # 如果数据库配置无效，尝试使用环境变量
    try:
        from app.core.llm import get_llm
        return get_llm()
    except Exception as e:
        print(f"从环境变量获取 LLM 失败: {e}")
        return None
