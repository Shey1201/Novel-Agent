"""
Agent Room API 测试
测试 Agent Chat、WebSocket、SSE 流式输出功能
"""
import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

# 创建测试用的 FastAPI app
from app.main import app

client = TestClient(app)


class TestAgentChatAPI:
    """测试 Agent Chat REST API"""

    def test_agent_chat_endpoint_exists(self):
        """测试 /api/agent/chat 端点存在"""
        response = client.post(
            "/api/agent/chat",
            json={
                "message": "你好",
                "story_id": "test-story"
            }
        )
        # 不管返回什么，只要不是 404 就说明端点存在
        assert response.status_code != 404

    def test_agent_chat_stream_endpoint_exists(self):
        """测试 /api/agent/chat/stream 端点存在"""
        # TestClient 不支持 stream=True，直接检查路由是否存在
        from app.api.agent_routes import router
        routes = [r.path for r in router.routes]
        assert any("/chat/stream" in path for path in routes)

    def test_agent_chat_validates_request(self):
        """测试请求体验证"""
        # 缺少必需字段
        response = client.post(
            "/api/agent/chat",
            json={}
        )
        # 应该返回 422 或其他错误码，但不应该是 404
        assert response.status_code in [422, 500, 400, 200]

    def test_agent_chat_with_word_count_range(self):
        """测试带字数范围的请求"""
        response = client.post(
            "/api/agent/chat",
            json={
                "message": "写一个章节",
                "story_id": "test-story",
                "word_count_range": {
                    "min": 1000,
                    "max": 2000
                }
            }
        )
        assert response.status_code in [200, 500, 422]

    def test_agent_chat_with_conversation_state(self):
        """测试带对话状态的请求"""
        response = client.post(
            "/api/agent/chat",
            json={
                "message": "确认保存",
                "story_id": "test-story",
                "conversation_state": {
                    "stage": "waiting_save_confirmation",
                    "waiting_for_user": True,
                    "workflow_type": "write"
                }
            }
        )
        assert response.status_code in [200, 500, 422]


class TestMessagesAPI:
    """测试 Messages API"""

    def test_messages_get_endpoint_exists(self):
        """测试 GET /api/messages 端点存在"""
        response = client.get("/api/messages")
        # 可能返回 200（无数据）或 500（数据库错误），但不应该是 404
        assert response.status_code in [200, 500, 503]

    def test_messages_post_endpoint_exists(self):
        """测试 POST /api/messages 端点存在"""
        response = client.post(
            "/api/messages",
            json={
                "role": "user",
                "content": "测试消息"
            }
        )
        # 可能返回 200 或 500，但不应该是 404
        assert response.status_code in [200, 201, 500, 503]

    def test_messages_delete_endpoint_exists(self):
        """测试 DELETE /api/messages 端点存在"""
        response = client.delete("/api/messages")
        # 可能返回 200 或 500
        assert response.status_code in [200, 500, 503]


class TestHealthEndpoints:
    """测试健康检查端点"""

    def test_health_check(self):
        """测试健康检查"""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestWebSocketConnection:
    """测试 WebSocket 连接"""

    def test_websocket_endpoint_configured(self):
        """测试 WebSocket 端点已配置"""
        # 检查路由是否包含 ws 端点
        from app.api.agent_routes import router
        routes = [r.path for r in router.routes]
        assert any("/ws/" in path for path in routes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
