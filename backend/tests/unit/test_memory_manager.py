"""
Memory Manager 单元测试
测试记忆管理系统的核心功能
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock

from app.memory.memory_manager import MemoryManager, WritingContext
from app.memory.story_memory import StoryMemory, Character, StoryBible


class TestMemoryManager:
    """测试记忆管理器"""

    @pytest.fixture
    def memory_manager(self):
        """创建记忆管理器实例"""
        with patch('app.memory.memory_manager.get_vector_store') as mock_vs, \
             patch('app.memory.memory_manager.get_knowledge_graph') as mock_kg:
            mock_vs.return_value = Mock()
            mock_kg.return_value = Mock()
            return MemoryManager()

    def test_memory_manager_creation(self, memory_manager):
        """测试记忆管理器创建"""
        assert memory_manager is not None
        assert memory_manager.vector_store is not None
        assert memory_manager.knowledge_graph is not None

    def test_build_short_memory(self, memory_manager):
        """测试构建短期记忆"""
        story_memory = StoryMemory(story_id="test-novel")
        
        # 添加章节摘要
        from app.memory.story_memory import ChapterSummary
        summary = ChapterSummary(
            chapter_id="ch-001",
            title="第一章",
            summary="主角开始了冒险"
        )
        story_memory.chapter_summaries.append(summary)
        
        short_memory = memory_manager._build_short_memory(story_memory)
        assert isinstance(short_memory, str)

    def test_estimate_tokens(self, memory_manager):
        """测试Token估算"""
        text = "这是一个测试文本"
        tokens = memory_manager._estimate_tokens(text)
        assert isinstance(tokens, int)
        assert tokens > 0

    def test_get_world_context(self, memory_manager):
        """测试获取世界上下文"""
        with patch.object(memory_manager.knowledge_graph, 'get_world_context') as mock_get:
            mock_get.return_value = {"rules": ["魔法守恒"]}
            context = memory_manager._get_world_context("novel-001")
            assert isinstance(context, dict)


class TestWritingContext:
    """测试写作上下文"""

    def test_writing_context_creation(self):
        """测试写作上下文创建"""
        context = WritingContext(
            short_memory="短期记忆",
            semantic_memories=[{"content": "记忆1"}],
            character_context={"char-001": {"name": "主角"}},
            world_context={"rules": []},
            foreshadowing=[],
            total_tokens=1000
        )
        assert context.short_memory == "短期记忆"
        assert context.total_tokens == 1000


class TestMemoryManagerIntegration:
    """测试记忆管理器集成场景"""

    @pytest.fixture
    def populated_memory(self):
        """创建包含数据的StoryMemory"""
        story_memory = StoryMemory(story_id="test-novel-001")
        
        # 添加多个角色
        characters = [
            Character(id="char-001", name="主角", role="protagonist", age=20),
            Character(id="char-002", name="反派", role="antagonist", age=35),
            Character(id="char-003", name="导师", role="mentor", age=60)
        ]
        
        for char in characters:
            story_memory.characters.append(char)
        
        return story_memory

    def test_multiple_characters(self, populated_memory):
        """测试多个角色管理"""
        assert len(populated_memory.characters) == 3

    def test_character_relationships(self, populated_memory):
        """测试角色关系"""
        from app.memory.story_memory import CharacterRelationship
        
        protagonist = populated_memory.characters[0]
        mentor = populated_memory.characters[2]
        
        # 添加关系
        relationship = CharacterRelationship(
            target_character_id=mentor.id,
            relationship_type="mentor",
            description="导师与学生",
            strength=0.9
        )
        protagonist.relationships.append(relationship)
        
        # 验证
        assert len(protagonist.relationships) == 1
        assert protagonist.relationships[0].relationship_type == "mentor"

    def test_build_writing_context_exists(self):
        """测试构建写作上下文方法存在"""
        with patch('app.memory.memory_manager.get_vector_store') as mock_vs, \
             patch('app.memory.memory_manager.get_knowledge_graph') as mock_kg:
            
            mock_vs.return_value = Mock()
            mock_kg.return_value = Mock()
            
            manager = MemoryManager()
            
            # 验证方法存在
            assert hasattr(manager, 'build_writing_context')
            assert callable(getattr(manager, 'build_writing_context'))
