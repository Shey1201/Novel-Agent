"""
配置模块单元测试
测试配置加载和设置
"""
import pytest
from unittest.mock import patch, MagicMock

from app.core.config import Settings, get_settings


class TestSettings:
    """测试设置类"""

    def test_default_values(self):
        """测试默认值"""
        settings = Settings()
        assert settings.app_name == "Multi-Agent Novel Backend"
        assert settings.debug is True
        assert settings.openai_api_key is None
        assert settings.deepseek_api_key is None
        assert settings.claude_api_key is None

    def test_custom_values(self):
        """测试自定义值"""
        settings = Settings(
            app_name="Test App",
            debug=False,
            openai_api_key="test-key"
        )
        assert settings.app_name == "Test App"
        assert settings.debug is False
        assert settings.openai_api_key == "test-key"

    def test_optional_postgres_dsn(self):
        """测试可选的Postgres配置"""
        settings = Settings()
        assert settings.postgres_dsn is None
        
        settings_with_db = Settings(postgres_dsn="postgresql://user:pass@localhost/db")
        assert settings_with_db.postgres_dsn == "postgresql://user:pass@localhost/db"

    def test_optional_qdrant_config(self):
        """测试可选的Qdrant配置"""
        settings = Settings()
        assert settings.qdrant_url is None
        assert settings.qdrant_api_key is None
        
        settings_with_qdrant = Settings(
            qdrant_url="http://localhost:6333",
            qdrant_api_key="test-api-key"
        )
        assert settings_with_qdrant.qdrant_url == "http://localhost:6333"
        assert settings_with_qdrant.qdrant_api_key == "test-api-key"


class TestGetSettings:
    """测试获取设置函数"""

    def test_get_settings_returns_settings(self):
        """测试获取设置返回Settings实例"""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_caching(self):
        """测试设置缓存"""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2  # 应该是同一个实例（lru_cache）


class TestSettingsEnvVars:
    """测试环境变量加载"""

    @patch.dict("os.environ", {
        "OPENAI_API_KEY": "env-openai-key",
        "DEEPSEEK_API_KEY": "env-deepseek-key",
        "QDRANT_URL": "http://qdrant:6333"
    }, clear=True)
    def test_env_var_loading(self):
        """测试从环境变量加载"""
        # 注意：Settings使用pydantic，需要重新实例化
        settings = Settings()
        assert settings.openai_api_key == "env-openai-key"
        assert settings.deepseek_api_key == "env-deepseek-key"
        assert settings.qdrant_url == "http://qdrant:6333"
