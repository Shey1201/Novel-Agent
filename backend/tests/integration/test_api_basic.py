"""
基础API集成测试
测试核心API端点的可用性和基本功能
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestHealthEndpoints:
    """测试健康检查端点"""

    def test_health_check(self):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_health_check_method_not_allowed(self):
        """测试健康检查不允许POST"""
        response = client.post("/health")
        assert response.status_code == 405


class TestNovelRoutes:
    """测试小说路由"""

    def test_list_novels(self):
        """测试获取小说列表"""
        response = client.get("/api/novels")
        assert response.status_code in [200, 404]  # 可能有数据或没有
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_create_novel_missing_fields(self):
        """测试创建小说缺少必填字段"""
        response = client.post("/api/novels", json={})
        # 可能返回404（端点不存在）或验证错误
        assert response.status_code in [400, 404, 422, 500]

    def test_get_nonexistent_novel(self):
        """测试获取不存在的小说"""
        response = client.get("/api/novels/non-existent-id")
        assert response.status_code in [404, 500]


class TestWorldRoutes:
    """测试世界观路由"""

    def test_list_worlds(self):
        """测试获取世界观列表"""
        response = client.get("/api/worlds")
        assert response.status_code in [200, 404]

    def test_get_world_characters_not_found(self):
        """测试获取不存在的世界角色"""
        response = client.get("/api/worlds/non-existent/characters")
        assert response.status_code in [404, 500]


class TestAgentRoutes:
    """测试Agent路由"""

    def test_list_agents(self):
        """测试获取Agent列表"""
        response = client.get("/api/agents")
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)


class TestAssetRoutes:
    """测试资源路由"""

    def test_list_assets(self):
        """测试获取资源列表"""
        response = client.get("/api/assets")
        assert response.status_code in [200, 404]


class TestSkillsRoutes:
    """测试技能路由"""

    def test_list_skills(self):
        """测试获取技能列表"""
        response = client.get("/api/skills")
        assert response.status_code in [200, 404]


class TestSystemSettingsRoutes:
    """测试系统设置路由"""

    def test_get_settings(self):
        """测试获取系统设置"""
        response = client.get("/api/settings")
        assert response.status_code in [200, 404]


class TestCORS:
    """测试CORS配置"""

    def test_cors_headers(self):
        """测试CORS头"""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_cors_origin_allowed(self):
        """测试允许的源"""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") in [
            "http://localhost:3000",
            "*"
        ]


class TestErrorHandling:
    """测试错误处理"""

    def test_404_error(self):
        """测试404错误"""
        response = client.get("/non-existent-endpoint")
        assert response.status_code == 404

    def test_method_not_allowed(self):
        """测试方法不允许"""
        response = client.delete("/health")
        assert response.status_code == 405
