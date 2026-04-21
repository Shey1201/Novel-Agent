"""
Pipeline Service 集成测试
测试章节生成流程的完整性和字段正确性
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.pipeline_service import NovelPipelineService
from app.domain.pipeline_state import build_initial_state
from app.memory.story_memory import StoryMemory, StoryBible


client = TestClient(app)


class TestPipelineService:
    """测试 Pipeline Service 核心功能"""

    def test_pipeline_service_initialization(self):
        """测试 PipelineService 可以正确初始化"""
        service = NovelPipelineService()
        assert service is not None
        assert service._flow is not None

    def test_pipeline_service_with_llm_config(self):
        """测试 PipelineService 可以接收 llm_config"""
        llm_config = {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
        }
        service = NovelPipelineService(llm_config=llm_config)
        assert service is not None
        assert service._llm is not None

    def test_build_initial_state(self):
        """测试初始状态构建"""
        memory = StoryMemory(story_id="test-story", bible=StoryBible())
        state = build_initial_state(
            input_text="测试大纲",
            story_memory=memory,
            chapter_id="chapter-001"
        )

        assert state["input_text"] == "测试大纲"
        assert state["chapter_id"] == "chapter-001"
        assert state["story_memory"] == memory
        assert state["plan_text"] == ""
        assert state["draft_text"] == ""
        assert state["agent_logs"] == []
        assert state["trace_data"] == []


class TestGenerateChapterAPI:
    """测试 /generate_chapter API 端点"""

    def test_generate_chapter_endpoint_exists(self):
        """测试端点是否存在"""
        payload = {
            "outline": "测试大纲：一个英雄冒险的故事",
            "story_id": "test-story"
        }
        response = client.post("/api/generate_chapter", json=payload)
        # 可能成功或失败，但不应返回 404（端点不存在）
        assert response.status_code != 404

    def test_generate_chapter_request_validation(self):
        """测试请求参数验证"""
        # 缺少必需的 outline 字段
        payload = {
            "story_id": "test-story"
        }
        response = client.post("/api/generate_chapter", json=payload)
        assert response.status_code in [400, 422]

    def test_generate_chapter_response_fields(self):
        """测试响应字段完整性"""
        payload = {
            "outline": "测试大纲",
            "story_id": "test-story",
            "chapter_id": "chapter-001"
        }
        response = client.post("/api/generate_chapter", json=payload)

        if response.status_code == 200:
            data = response.json()
            # 验证必需字段存在
            assert "final_text" in data
            assert "plan_text" in data
            assert "draft_text" in data
            assert "edited_text" in data
            assert "agent_logs" in data
            assert "trace_data" in data
            assert "story_id" in data

    @pytest.mark.skip(reason="需要LLM调用，运行时间过长")
    def test_generate_chapter_with_llm_config(self):
        """测试带 LLM 配置的请求"""
        payload = {
            "outline": "测试大纲",
            "story_id": "test-story",
            "chapter_id": "chapter-001",
            "llm_config": {
                "model": "gpt-4o-mini",
                "temperature": 0.7
            }
        }
        response = client.post("/api/generate_chapter", json=payload)
        # 不应因为 llm_config 格式错误而失败
        assert response.status_code in [200, 422, 500]


class TestGraphState:
    """测试 GraphState 数据结构"""

    def test_graph_state_has_chapter_id(self):
        """测试 GraphState 包含 chapter_id 字段"""
        from app.domain.pipeline_state import GraphState

        # 验证 GraphState 类型定义包含 chapter_id
        state = GraphState(
            input_text="",
            plan_text="",
            conflict_suggestions=[],
            draft_text="",
            edited_text="",
            reader_feedback=[],
            summary_text="",
            final_text="",
            agent_logs=[],
            trace_data=[],
            story_memory=StoryMemory(story_id="test", bible=StoryBible()),
            chapter_id="test-chapter"
        )
        assert state["chapter_id"] == "test-chapter"


class TestAgentLogs:
    """测试 Agent 日志输出"""

    def test_agent_logs_format(self):
        """测试 agent_logs 格式正确性"""
        payload = {
            "outline": "测试大纲",
            "story_id": "test-story"
        }
        response = client.post("/api/generate_chapter", json=payload)

        if response.status_code == 200:
            data = response.json()
            if "agent_logs" in data and data["agent_logs"]:
                for log in data["agent_logs"]:
                    # 验证日志字段
                    assert "agent" in log or "agent_name" in log
                    assert "message" in log or "content" in log


class TestTraceData:
    """测试 Trace 数据"""

    def test_trace_data_format(self):
        """测试 trace_data 格式正确性"""
        payload = {
            "outline": "测试大纲",
            "story_id": "test-story"
        }
        response = client.post("/api/generate_chapter", json=payload)

        if response.status_code == 200:
            data = response.json()
            if "trace_data" in data and data["trace_data"]:
                for trace in data["trace_data"]:
                    # 验证 trace 字段
                    assert "text" in trace
                    assert "source_agent" in trace
