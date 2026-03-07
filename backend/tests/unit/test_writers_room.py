"""
Writers Room 单元测试
测试自治讨论系统的核心功能
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, AsyncMock

from app.workflow.writers_room import (
    MessageType, DiscussionStatus,
    AgentParticipant, AgentMessage, Proposal, DiscussionState
)


class TestMessageType:
    """测试消息类型枚举"""

    def test_message_type_values(self):
        """测试消息类型值"""
        assert MessageType.PROPOSAL == "proposal"
        assert MessageType.SUGGESTION == "suggestion"
        assert MessageType.CRITIQUE == "critique"
        assert MessageType.CONSENSUS == "consensus"
        assert MessageType.INTERRUPTION == "interruption"
        assert MessageType.SUMMARY == "summary"


class TestDiscussionStatus:
    """测试讨论状态枚举"""

    def test_discussion_status_values(self):
        """测试讨论状态值"""
        assert DiscussionStatus.ONGOING == "ongoing"
        assert DiscussionStatus.REACHED == "reached"
        assert DiscussionStatus.TIMEOUT == "timeout"
        assert DiscussionStatus.STALEMATE == "stalemate"


class TestAgentParticipant:
    """测试讨论参与者"""

    def test_participant_creation(self):
        """测试参与者创建"""
        mock_agent = Mock()
        participant = AgentParticipant(
            agent_id="agent-001",
            agent_name="Planner",
            agent_role="规划者",
            agent_instance=mock_agent,
            personality="analytical",
            proactivity=0.7,
            expertise_areas=["plot", "structure"]
        )
        assert participant.agent_id == "agent-001"
        assert participant.agent_name == "Planner"
        assert participant.proactivity == 0.7
        assert participant.message_count == 0

    def test_participant_default_values(self):
        """测试参与者默认值"""
        mock_agent = Mock()
        participant = AgentParticipant(
            agent_id="agent-002",
            agent_name="Writer",
            agent_role="写作者",
            agent_instance=mock_agent
        )
        assert participant.personality == "neutral"
        assert participant.proactivity == 0.5
        assert participant.expertise_areas == []
        assert participant.last_spoke_at is None


class TestAgentMessage:
    """测试Agent消息"""

    def test_message_creation(self):
        """测试消息创建"""
        message = AgentMessage(
            id="msg-001",
            agent_id="agent-001",
            agent_name="Planner",
            content="这是一个建议",
            message_type=MessageType.SUGGESTION,
            timestamp=datetime.now(),
            internal_monologue="我觉得这个方案不错",
            references=[{"type": "chapter", "id": "ch-001"}],
            reply_to="msg-000"
        )
        assert message.agent_name == "Planner"
        assert message.message_type == MessageType.SUGGESTION
        assert message.reply_to == "msg-000"

    def test_message_minimal_creation(self):
        """测试最小消息创建"""
        message = AgentMessage(
            id="msg-002",
            agent_id="agent-002",
            agent_name="Writer",
            content="简单消息",
            message_type=MessageType.PROPOSAL,
            timestamp=datetime.now()
        )
        assert message.internal_monologue is None
        assert message.references == []
        assert message.reply_to is None


class TestProposal:
    """测试议案"""

    def test_proposal_creation(self, sample_proposal_data):
        """测试议案创建"""
        proposal = Proposal(
            id=sample_proposal_data["id"],
            title=sample_proposal_data["title"],
            description=sample_proposal_data["description"],
            proposed_by=sample_proposal_data["proposed_by"],
            created_at=datetime.now(),
            status=sample_proposal_data["status"]
        )
        assert proposal.title == "主角如何脱困"
        assert proposal.proposed_by == "user"
        assert proposal.status == "open"


class TestDiscussionState:
    """测试讨论状态"""

    @pytest.fixture
    def sample_proposal(self):
        """示例议案"""
        return Proposal(
            id="proposal-001",
            title="测试议案",
            description="测试描述",
            proposed_by="user",
            created_at=datetime.now()
        )

    def test_state_creation(self, sample_proposal):
        """测试状态创建"""
        state = DiscussionState(proposal=sample_proposal)
        assert state.proposal.title == "测试议案"
        assert state.messages == []
        assert state.participants == []
        assert state.consensus_score == 0.0
        assert state.status == DiscussionStatus.ONGOING
        assert state.round == 0
        assert state.max_rounds == 10

    def test_add_message(self, sample_proposal):
        """测试添加消息"""
        state = DiscussionState(proposal=sample_proposal)
        message = AgentMessage(
            id="msg-001",
            agent_id="agent-001",
            agent_name="Planner",
            content="测试消息",
            message_type=MessageType.SUGGESTION,
            timestamp=datetime.now()
        )
        state.add_message(message)
        assert len(state.messages) == 1
        assert state.messages[0].content == "测试消息"

    def test_add_message_updates_participant(self, sample_proposal):
        """测试添加消息更新参与者统计"""
        state = DiscussionState(proposal=sample_proposal)
        mock_agent = Mock()
        participant = AgentParticipant(
            agent_id="agent-001",
            agent_name="Planner",
            agent_role="规划者",
            agent_instance=mock_agent
        )
        state.participants.append(participant)
        
        message = AgentMessage(
            id="msg-001",
            agent_id="agent-001",
            agent_name="Planner",
            content="测试消息",
            message_type=MessageType.SUGGESTION,
            timestamp=datetime.now()
        )
        state.add_message(message)
        
        assert participant.message_count == 1
        assert participant.last_spoke_at is not None

    def test_get_recent_messages(self, sample_proposal):
        """测试获取最近消息"""
        state = DiscussionState(proposal=sample_proposal)
        
        # 添加10条消息
        for i in range(10):
            message = AgentMessage(
                id=f"msg-{i}",
                agent_id=f"agent-{i % 3}",
                agent_name=f"Agent{i % 3}",
                content=f"消息{i}",
                message_type=MessageType.SUGGESTION,
                timestamp=datetime.now()
            )
            state.add_message(message)
        
        recent = state.get_recent_messages(n=5)
        assert len(recent) == 5
        assert recent[0].content == "消息5"
        assert recent[-1].content == "消息9"

    def test_get_recent_messages_less_than_n(self, sample_proposal):
        """测试获取最近消息（消息数少于n）"""
        state = DiscussionState(proposal=sample_proposal)
        
        # 添加3条消息
        for i in range(3):
            message = AgentMessage(
                id=f"msg-{i}",
                agent_id="agent-001",
                agent_name="Planner",
                content=f"消息{i}",
                message_type=MessageType.SUGGESTION,
                timestamp=datetime.now()
            )
            state.add_message(message)
        
        recent = state.get_recent_messages(n=5)
        assert len(recent) == 3

    def test_consensus_score_update(self, sample_proposal):
        """测试共识分数更新"""
        state = DiscussionState(proposal=sample_proposal)
        state.consensus_score = 0.85
        assert state.consensus_score == 0.85

    def test_status_transition(self, sample_proposal):
        """测试状态转换"""
        state = DiscussionState(proposal=sample_proposal)
        assert state.status == DiscussionStatus.ONGOING
        
        state.status = DiscussionStatus.REACHED
        assert state.status == DiscussionStatus.REACHED
        
        state.status = DiscussionStatus.TIMEOUT
        assert state.status == DiscussionStatus.TIMEOUT


class TestDiscussionStateIntegration:
    """测试讨论状态集成场景"""

    @pytest.fixture
    def populated_state(self):
        """创建包含数据的讨论状态"""
        proposal = Proposal(
            id="proposal-001",
            title="主角如何脱困",
            description="设计逃脱方案",
            proposed_by="user",
            created_at=datetime.now()
        )
        state = DiscussionState(proposal=proposal)
        
        # 添加参与者
        mock_agents = {
            "planner": Mock(),
            "conflict": Mock(),
            "writer": Mock()
        }
        
        for i, (role, agent) in enumerate(mock_agents.items()):
            participant = AgentParticipant(
                agent_id=f"agent-{role}",
                agent_name=role.capitalize(),
                agent_role=role,
                agent_instance=agent,
                proactivity=0.6 + i * 0.1
            )
            state.participants.append(participant)
        
        return state

    def test_full_discussion_flow(self, populated_state):
        """测试完整讨论流程"""
        state = populated_state
        
        # 模拟多轮讨论
        for round_num in range(3):
            state.round = round_num + 1
            
            for participant in state.participants:
                message = AgentMessage(
                    id=f"msg-r{round_num}-{participant.agent_id}",
                    agent_id=participant.agent_id,
                    agent_name=participant.agent_name,
                    content=f"{participant.agent_name}的第{round_num + 1}轮发言",
                    message_type=MessageType.SUGGESTION if round_num < 2 else MessageType.CONSENSUS,
                    timestamp=datetime.now()
                )
                state.add_message(message)
        
        # 验证
        assert state.round == 3
        assert len(state.messages) == 9  # 3轮 x 3参与者
        assert len(state.get_recent_messages(3)) == 3
        
        # 验证参与者统计
        for p in state.participants:
            assert p.message_count == 3
            assert p.last_spoke_at is not None
