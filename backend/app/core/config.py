from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """
    模块5：统一配置入口（仅占位，不强制要求环境变量存在）。
    后续会按需为不同环境提供 .env 文件。
    """

    # 基础
    app_name: str = "Multi-Agent Novel Backend"
    debug: bool = True

    # LLM 配置（占位）
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    deepseek_api_key: Optional[str] = Field(default=None, env="DEEPSEEK_API_KEY")
    claude_api_key: Optional[str] = Field(default=None, env="CLAUDE_API_KEY")

    # Postgres 配置（占位）
    postgres_dsn: Optional[str] = Field(default=None, env="POSTGRES_DSN")

    # Qdrant 配置（占位）
    qdrant_url: Optional[str] = Field(default=None, env="QDRANT_URL")
    qdrant_api_key: Optional[str] = Field(default=None, env="QDRANT_API_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

