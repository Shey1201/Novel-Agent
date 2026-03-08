"""
API 功能测试
测试后端 API 是否正常工作
"""

import pytest
import requests
import uuid
from datetime import datetime

# 测试配置
BASE_URL = "http://127.0.0.1:8000"
TEST_USER_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


class TestHealth:
    """健康检查测试"""

    def test_health_endpoint(self):
        """测试健康检查端点"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"


class TestAgentsAPI:
    """Agent API 测试"""

    def test_get_agents(self):
        """测试获取 Agent 列表"""
        response = requests.get(f"{BASE_URL}/api/agents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_agent(self):
        """测试创建 Agent"""
        agent_data = {
            "agent_id": f"test-agent-{uuid.uuid4().hex[:8]}",
            "name": "测试Agent",
            "role": "writer",
            "prompt": "你是一个测试Agent",
            "temperature": 0.7,
            "enabled": True,
            "personality": "creative"
        }
        response = requests.post(f"{BASE_URL}/api/agents", json=agent_data)
        assert response.status_code in [200, 201]
        data = response.json()
        assert data.get("name") == "测试Agent"
        return data.get("id")

    def test_update_agent(self):
        """测试更新 Agent"""
        # 先创建
        agent_id = self.test_create_agent()

        # 再更新
        update_data = {"name": "更新的测试Agent", "temperature": 0.8}
        response = requests.put(f"{BASE_URL}/api/agents/{agent_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data.get("name") == "更新的测试Agent"


class TestAssetsAPI:
    """Asset API 测试"""

    def test_get_assets(self):
        """测试获取资产列表"""
        response = requests.get(f"{BASE_URL}/api/assets")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_local_asset(self):
        """测试创建本地资产"""
        asset_data = {
            "name": "测试角色",
            "type": "characters",
            "content": {"description": "这是一个测试角色"},
            "is_global": False,
            "color": "#ff0000"
        }
        response = requests.post(f"{BASE_URL}/api/assets", json=asset_data)
        assert response.status_code in [200, 201]
        data = response.json()
        assert data.get("name") == "测试角色"
        assert data.get("is_global") == False

    def test_create_global_asset(self):
        """测试创建全局资产"""
        asset_data = {
            "name": "测试世界观",
            "type": "worldbuilding",
            "description": "这是一个测试世界观",
            "is_global": True,
            "is_starred": True,
            "color": "#00ff00"
        }
        response = requests.post(f"{BASE_URL}/api/assets", json=asset_data)
        assert response.status_code in [200, 201]
        data = response.json()
        assert data.get("name") == "测试世界观"
        assert data.get("is_global") == True


class TestSettingsAPI:
    """Settings API 测试"""

    def test_get_settings(self):
        """测试获取设置"""
        response = requests.get(f"{BASE_URL}/api/settings")
        assert response.status_code == 200
        data = response.json()
        # 检查关键字段
        assert "token_enabled" in data or "token_daily_limit" in data

    def test_update_settings(self):
        """测试更新设置"""
        settings_data = {
            "token_enabled": True,
            "token_daily_limit": 100000,
            "discussion_max_rounds": 3
        }
        response = requests.put(f"{BASE_URL}/api/settings", json=settings_data)
        assert response.status_code == 200
        data = response.json()
        assert data.get("token_daily_limit") == 100000


class TestNovelsAPI:
    """Novel API 测试"""

    def test_get_novels(self):
        """测试获取小说列表"""
        response = requests.get(f"{BASE_URL}/api/novels")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_novel(self):
        """测试创建小说"""
        novel_data = {
            "title": "测试小说",
            "description": "这是一个测试小说",
            "category_id": None
        }
        response = requests.post(f"{BASE_URL}/api/novels", json=novel_data)
        assert response.status_code in [200, 201]
        data = response.json()
        assert data.get("title") == "测试小说"
        return data.get("id")


class TestChaptersAPI:
    """Chapter API 测试"""

    def test_get_chapters(self):
        """测试获取章节列表"""
        # 使用一个测试小说ID
        novel_id = "test-novel-id"
        response = requests.get(f"{BASE_URL}/api/novels/{novel_id}/chapters")
        # 可能返回 200 或 404
        assert response.status_code in [200, 404]


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
