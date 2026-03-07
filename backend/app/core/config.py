from functools import lru_cache
from typing import Optional

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import Field
    PYDANTIC_V2 = True
except ImportError:
    from pydantic import BaseSettings, Field
    PYDANTIC_V2 = False


class Settings(BaseSettings):
    """
    模块5：统一配置入口（仅占位，不强制要求环境变量存在）。
    后续会按需为不同环境提供 .env 文件。
    """

    # 基础
    app_name: str = "Multi-Agent Novel Backend"
    debug: bool = True

    # LLM 配置（占位）
    openai_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None

    # Postgres 配置（占位）
    postgres_dsn: Optional[str] = None

    # Qdrant 配置（占位）
    qdrant_url: Optional[str] = None
    qdrant_api_key: Optional[str] = None

    if PYDANTIC_V2:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            env_prefix="",
            case_sensitive=False
        )
    else:
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
