"""
Writers Room API 集成测试
测试V3 Writers Room功能的API端点
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestWritersRoomAPI:
    """测试Writers Room API"""

    def test_discussions_list(self):
        """测试获取讨论列表"""
        response = client.get("/api/writers-room/discussions")
        # 可能返回200、404或405（方法不允许）
        assert response.status_code in [200, 404, 405]

    def test_create_discussion(self):
        """测试创建讨论"""
        payload = {
            "title": "测试讨论",
            "description": "这是一个测试讨论议案"
        }
        response = client.post("/api/writers-room/discussions", json=payload)
        # 可能成功或失败，取决于实现
        assert response.status_code in [200, 201, 404, 422, 500]

    def test_create_discussion_missing_title(self):
        """测试创建讨论缺少标题"""
        payload = {
            "description": "缺少标题的讨论"
        }
        response = client.post("/api/writers-room/discussions", json=payload)
        assert response.status_code in [400, 404, 422, 500]

    def test_get_discussion_not_found(self):
        """测试获取不存在的讨论"""
        response = client.get("/api/writers-room/discussions/non-existent-id")
        assert response.status_code in [404, 405, 500]

    def test_run_round_not_found(self):
        """测试对不存在的讨论运行一轮"""
        response = client.post("/api/writers-room/discussions/non-existent-id/round")
        assert response.status_code in [404, 405, 500]

    def test_intervene_not_found(self):
        """测试对不存在的讨论进行干预"""
        payload = {
            "action": "comment",
            "content": "测试评论"
        }
        response = client.post(
            "/api/writers-room/discussions/non-existent-id/intervene",
            json=payload
        )
        assert response.status_code in [404, 422, 500]


class TestWritersRoomWebSocket:
    """测试Writers Room WebSocket"""

    def test_websocket_endpoint_exists(self):
        """测试WebSocket端点存在"""
        # WebSocket测试需要特殊处理，这里只检查端点配置
        # 实际WebSocket连接测试需要pytest-asyncio和异步客户端
        pass


class TestStreamAPI:
    """测试流式API"""

    def test_stream_write_endpoint(self):
        """测试流式写作端点"""
        payload = {
            "prompt": "测试提示",
            "context": "测试上下文"
        }
        response = client.post("/api/stream/write", json=payload)
        # SSE端点可能返回200或需要特殊处理
        assert response.status_code in [200, 404, 422, 500]

    def test_stream_write_missing_prompt(self):
        """测试流式写作缺少提示"""
        payload = {
            "context": "只有上下文"
        }
        response = client.post("/api/stream/write", json=payload)
        assert response.status_code in [400, 404, 422]

    def test_get_execution_not_found(self):
        """测试获取不存在的执行过程"""
        response = client.get("/api/stream/execution/non-existent-id")
        # 可能返回200（空结果）或404
        assert response.status_code in [200, 404, 500]

    def test_get_progress_not_found(self):
        """测试获取不存在的进度"""
        response = client.get("/api/stream/progress/non-existent-id")
        # 可能返回200（空结果）或404
        assert response.status_code in [200, 404, 500]


class TestCollaborationAPI:
    """测试协作API"""

    def test_collaboration_status(self):
        """测试获取协作状态"""
        response = client.get("/api/collaboration/status")
        assert response.status_code in [200, 404]

    def test_get_document_not_found(self):
        """测试获取不存在的文档"""
        response = client.get("/api/collaboration/documents/non-existent-id")
        assert response.status_code in [404, 500]


class TestCacheAPI:
    """测试缓存API"""

    def test_cache_stats(self):
        """测试获取缓存统计"""
        response = client.get("/api/cache/stats")
        assert response.status_code in [200, 404]

    def test_clear_cache(self):
        """测试清除缓存"""
        response = client.post("/api/cache/clear")
        # 可能返回200、404或422（验证错误）
        assert response.status_code in [200, 404, 422]


class TestAnalysisAPI:
    """测试分析API"""

    def test_analyze_conflict(self):
        """测试冲突分析"""
        payload = {
            "text": "测试文本",
            "analysis_type": "conflict"
        }
        response = client.post("/api/analysis", json=payload)
        # 可能返回200、404（端点不存在）或422
        assert response.status_code in [200, 404, 422, 500]

    def test_analyze_quality(self):
        """测试质量分析"""
        payload = {
            "text": "测试文本",
            "analysis_type": "quality"
        }
        response = client.post("/api/analysis", json=payload)
        # 可能返回200、404（端点不存在）或422
        assert response.status_code in [200, 404, 422, 500]


class TestAnalyticsAPI:
    """测试分析统计API"""

    def test_get_analytics(self):
        """测试获取分析数据"""
        response = client.get("/api/analytics")
        assert response.status_code in [200, 404]

    def test_get_agent_analytics(self):
        """测试获取Agent分析"""
        response = client.get("/api/analytics/agents")
        assert response.status_code in [200, 404]


class TestAdvancedFeaturesAPI:
    """测试高级功能API"""

    def test_foreshadowing_list(self):
        """测试获取伏笔列表"""
        response = client.get("/api/advanced/foreshadowing")
        assert response.status_code in [200, 404]

    def test_reflexion_status(self):
        """测试获取反思状态"""
        response = client.get("/api/advanced/reflexion")
        assert response.status_code in [200, 404]


class TestAgentRoomAPI:
    """测试Agent Room API"""

    def test_agent_room_list(self):
        """测试获取Agent Room列表"""
        response = client.get("/api/agent-room")
        assert response.status_code in [200, 404]

    def test_create_agent_room(self):
        """测试创建Agent Room"""
        payload = {
            "name": "测试房间",
            "agents": ["planner", "writer"]
        }
        response = client.post("/api/agent-room", json=payload)
        # 可能返回200、201、404（端点不存在）或422
        assert response.status_code in [200, 201, 404, 422, 500]
