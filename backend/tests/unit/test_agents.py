"""
Agent 单元测试
测试各个 Agent 的基本功能
"""
import pytest
from unittest.mock import Mock, MagicMock, patch

from app.agents.base_agent import BaseAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.writing_agent import WritingAgent
from app.agents.editor_agent import EditorAgent
from app.agents.conflict_agent import ConflictAgent
from app.agents.reader_agent import ReaderAgent
from app.agents.summary_agent import SummaryAgent


class TestBaseAgent:
    """测试基类"""

    def test_base_agent_initialization(self):
        """测试基类初始化"""
        mock_llm = Mock()
        agent = BaseAgent(name="test-agent", llm=mock_llm)

        assert agent.name == "test-agent"
        assert agent.llm == mock_llm

    def test_base_agent_run_not_implemented(self):
        """测试基类 run 方法抛出 NotImplementedError"""
        mock_llm = Mock()
        agent = BaseAgent(name="test-agent", llm=mock_llm)

        with pytest.raises(NotImplementedError):
            agent.run({})


class TestPlannerAgent:
    """测试 PlannerAgent"""

    def test_planner_agent_initialization(self):
        """测试 PlannerAgent 初始化"""
        mock_llm = Mock()
        agent = PlannerAgent(llm=mock_llm)

        assert agent.name == "planner-agent"
        assert agent.llm == mock_llm

    def test_planner_agent_run_without_llm(self):
        """测试 PlannerAgent 在没有 LLM 时的行为"""
        agent = PlannerAgent(llm=None)
        result = agent.run({"text": "测试输入"})

        assert "plan_text" in result
        assert "agent" in result
        assert "message" in result
        assert result["agent"] == "planner-agent"

    @patch('app.agents.planner_agent.LANGCHAIN_AVAILABLE', True)
    @patch('app.agents.planner_agent.HumanMessage')
    def test_planner_agent_run_with_llm(self, mock_human_message_class):
        """测试 PlannerAgent 在有 LLM 时的行为"""
        # 创建 mock LLM，模拟 langchain 的 invoke 方法
        mock_response = Mock()
        mock_response.content = "生成的计划"
        mock_llm = Mock()
        mock_llm.invoke = Mock(return_value=mock_response)

        # 模拟 HumanMessage 类
        mock_msg_instance = Mock()
        mock_human_message_class.return_value = mock_msg_instance

        agent = PlannerAgent(llm=mock_llm)
        result = agent.run({"text": "测试输入"})

        assert "plan_text" in result
        assert result["plan_text"] == "生成的计划"
        mock_llm.invoke.assert_called_once()
        mock_human_message_class.assert_called_once()


class TestWritingAgent:
    """测试 WritingAgent"""

    def test_writing_agent_initialization(self):
        """测试 WritingAgent 初始化"""
        mock_llm = Mock()
        agent = WritingAgent(llm=mock_llm)

        assert agent.name == "writing-agent"
        assert agent.llm == mock_llm

    def test_writing_agent_run_without_llm(self):
        """测试 WritingAgent 在没有 LLM 时的行为"""
        agent = WritingAgent(llm=None)
        result = agent.run({"text": "测试输入"})

        assert "draft_text" in result
        assert "trace_data" in result
        assert "agent" in result
        assert result["agent"] == "writing-agent"

    def test_writing_agent_trace_data_format(self):
        """测试 WritingAgent 返回的 trace_data 格式"""
        agent = WritingAgent(llm=None)
        result = agent.run({"text": "测试"})

        assert "trace_data" in result
        assert isinstance(result["trace_data"], list)
        if result["trace_data"]:
            trace = result["trace_data"][0]
            assert "text" in trace
            assert "source_agent" in trace
            assert "revisions" in trace


class TestEditorAgent:
    """测试 EditorAgent"""

    def test_editor_agent_initialization(self):
        """测试 EditorAgent 初始化"""
        mock_llm = Mock()
        agent = EditorAgent(llm=mock_llm)

        assert agent.name == "editor-agent"
        assert agent.llm == mock_llm

    def test_editor_agent_run(self):
        """测试 EditorAgent 基本运行"""
        agent = EditorAgent(llm=None)
        result = agent.run({"draft_text": "测试草稿"})

        assert "edited_text" in result
        assert "agent" in result
        assert result["agent"] == "editor-agent"


class TestConflictAgent:
    """测试 ConflictAgent"""

    def test_conflict_agent_initialization(self):
        """测试 ConflictAgent 初始化"""
        mock_llm = Mock()
        agent = ConflictAgent(llm=mock_llm)

        assert agent.name == "conflict-agent"
        assert agent.llm == mock_llm

    def test_conflict_agent_run(self):
        """测试 ConflictAgent 基本运行"""
        agent = ConflictAgent(llm=None)
        result = agent.run({"draft_text": "测试草稿"})

        assert "conflict_suggestions" in result
        assert isinstance(result["conflict_suggestions"], list)
        assert "agent" in result
        assert result["agent"] == "conflict-agent"


class TestReaderAgent:
    """测试 ReaderAgent"""

    def test_reader_agent_initialization(self):
        """测试 ReaderAgent 初始化"""
        mock_llm = Mock()
        agent = ReaderAgent(llm=mock_llm)

        assert agent.name == "reader-agent"
        assert agent.llm == mock_llm

    def test_reader_agent_run(self):
        """测试 ReaderAgent 基本运行"""
        agent = ReaderAgent(llm=None)
        result = agent.run({"draft_text": "测试草稿"})

        assert "reader_feedback" in result
        assert isinstance(result["reader_feedback"], list)
        assert "agent" in result
        assert result["agent"] == "reader-agent"


class TestSummaryAgent:
    """测试 SummaryAgent"""

    def test_summary_agent_initialization(self):
        """测试 SummaryAgent 初始化"""
        mock_llm = Mock()
        agent = SummaryAgent(llm=mock_llm)

        assert agent.name == "summary-agent"
        assert agent.llm == mock_llm

    def test_summary_agent_run(self):
        """测试 SummaryAgent 基本运行"""
        agent = SummaryAgent(llm=None)
        result = agent.run("测试文本")

        assert isinstance(result, str)
        assert len(result) > 0
