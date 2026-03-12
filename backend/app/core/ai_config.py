"""
AI 配置管理模块
从数据库读取 AI 配置并创建 LLM 实例
"""

from typing import Optional, Dict, Any


def get_ai_config_from_db() -> Optional[Dict[str, Any]]:
    """从数据库读取 AI 配置（兼容 settings/system_settings 两种表结构）。"""
    try:
        from app.memory.system_settings import supabase

        if supabase is None:
            return None

        def _read_from_table(table_name: str) -> Optional[Dict[str, Any]]:
            query = supabase.table(table_name).select(
                "ai_chat_model, ai_api_key, ai_base_url, ai_is_active"
            )
            # 尝试添加 deleted_at 过滤（表可能没有此字段）
            try:
                if table_name == "settings":
                    query = query.is_("deleted_at", "null")
            except Exception:
                pass  # 如果字段不存在，跳过过滤

            result = query.limit(1).execute()
            if not result.data:
                return None

            data = result.data[0]
            is_active = bool(data.get("ai_is_active", False))
            api_key = data.get("ai_api_key")
            print(f"[DEBUG] _read_from_table({table_name}): is_active={is_active}, has_api_key={bool(api_key)}")
            if is_active and api_key:
                return {
                    "model": data.get("ai_chat_model", "gpt-4o-mini"),
                    "api_key": api_key,
                    "base_url": data.get("ai_base_url"),
                    "is_active": True,
                }
            return None

        return _read_from_table("settings") or _read_from_table("system_settings")
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
        
        llm_kwargs: Dict[str, Any] = {
            "api_key": config["api_key"],
            "model": config.get("model", "gpt-4o-mini"),
            "temperature": 0.7,
        }

        # 避免网络/模型端异常导致请求无限期卡住
        # 不同版本的 langchain_openai 可能使用不同参数名，这里做兼容尝试
        llm_kwargs.setdefault("max_retries", 2)
        llm_kwargs.setdefault("timeout", 30)
        llm_kwargs.setdefault("request_timeout", 30)
        
        # 如果提供了 base_url，则使用它
        if config.get("base_url"):
            llm_kwargs["base_url"] = config["base_url"]
        
        try:
            return ChatOpenAI(**llm_kwargs)
        except TypeError:
            # 回退：移除不兼容的参数名
            fallback_kwargs = dict(llm_kwargs)
            fallback_kwargs.pop("request_timeout", None)
            fallback_kwargs.pop("timeout", None)
            fallback_kwargs.pop("max_retries", None)
            return ChatOpenAI(**fallback_kwargs)
    except Exception as e:
        print(f"创建 LLM 实例失败: {e}")
        return None


def get_llm_with_fallback():
    """
    获取 LLM 实例（仅使用数据库配置）。

    Returns:
        LLM 实例或 None
    """
    db_config = get_ai_config_from_db()
    if not db_config:
        return None

    return create_llm_from_config(db_config)
