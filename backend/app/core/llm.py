"""
LLM 模块 - 统一大语言模型接口
"""

from typing import Any, Optional
from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.core.config import get_settings


@lru_cache()
def get_llm() -> Optional[Any]:
    """
    获取 LLM 实例（单例）
    
    优先使用 OpenAI，如果没有配置则返回 None
    """
    settings = get_settings()
    
    # 尝试 OpenAI
    if settings.openai_api_key:
        return ChatOpenAI(
            api_key=settings.openai_api_key,
            model="gpt-4o-mini",  # 或其他合适的模型
            temperature=0.7,
        )
    
    # 如果没有配置，返回 None
    # 实际使用时可以在这里添加其他 LLM 支持
    return None


def get_llm_or_raise() -> Any:
    """获取 LLM，如果没有配置则抛出异常"""
    llm = get_llm()
    if llm is None:
        raise ValueError(
            "LLM not configured. Please set OPENAI_API_KEY or other LLM API keys."
        )
    return llm
