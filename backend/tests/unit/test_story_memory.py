"""
Story Memory 单元测试
测试故事记忆系统的核心功能
"""
import pytest
from datetime import datetime

from app.memory.story_memory import (
    Character, CharacterArc, CharacterRelationship,
    WorldRule, WorldLocation, WorldFaction,
    TimelineEvent, StoryTheme, StoryBible, StoryMemory
)


class TestCharacter:
    """测试角色模型"""

    def test_character_creation(self, sample_character_data):
        """测试角色创建"""
        char = Character(**sample_character_data)
        assert char.id == "char-001"
        assert char.name == "测试角色"
        assert char.age == 25
        assert char.gender == "male"

    def test_character_default_values(self):
        """测试角色默认值"""
        char = Character(id="char-002", name="默认角色")
        assert char.aliases == []
        assert char.values == []
        assert char.fears == []
        assert char.abilities == []
        assert char.tags == []
        assert char.created_at is not None

    def test_character_arc(self):
        """测试角色弧线"""
        arc = CharacterArc(
            start_state="普通人",
            end_state="英雄",
            key_moments=["获得力量", "失去导师", "最终决战"]
        )
        assert arc.start_state == "普通人"
        assert arc.end_state == "英雄"
        assert len(arc.key_moments) == 3

    def test_character_relationship(self):
        """测试角色关系"""
        rel = CharacterRelationship(
            target_character_id="char-002",
            relationship_type="friend",
            description="从小一起长大的好友",
            strength=0.8
        )
        assert rel.target_character_id == "char-002"
        assert rel.relationship_type == "friend"
        assert rel.strength == 0.8


class TestWorldRule:
    """测试世界规则"""

    def test_world_rule_creation(self, sample_world_rule_data):
        """测试世界规则创建"""
        rule = WorldRule(**sample_world_rule_data)
        assert rule.id == "rule-001"
        assert rule.name == "魔法能量守恒"
        assert rule.category == "magic"
        assert rule.importance == "high"

    def test_world_rule_default_exceptions(self):
        """测试世界规则默认例外"""
        rule = WorldRule(
            id="rule-002",
            name="测试规则",
            description="测试描述",
            category="physics"
        )
        assert rule.exceptions == []
        assert rule.importance == "medium"


class TestWorldLocation:
    """测试世界地点"""

    def test_location_creation(self):
        """测试地点创建"""
        location = WorldLocation(
            id="loc-001",
            name="魔法学院",
            description="著名的魔法学习场所",
            location_type="city",
            significance="主角学习魔法的地方",
            connected_locations=["loc-002", "loc-003"]
        )
        assert location.name == "魔法学院"
        assert location.location_type == "city"
        assert len(location.connected_locations) == 2

    def test_location_parent(self):
        """测试地点层级关系"""
        child = WorldLocation(
            id="loc-002",
            name="魔法学院图书馆",
            description="藏书丰富",
            location_type="building",
            parent_location="loc-001"
        )
        assert child.parent_location == "loc-001"


class TestWorldFaction:
    """测试世界势力"""

    def test_faction_creation(self):
        """测试势力创建"""
        faction = WorldFaction(
            id="faction-001",
            name="光明教会",
            description="维护正义的宗教组织",
            faction_type="religion",
            goals=["消灭邪恶", "传播光明"],
            relationships={"faction-002": "enemy"}
        )
        assert faction.name == "光明教会"
        assert len(faction.goals) == 2
        assert faction.relationships["faction-002"] == "enemy"


class TestTimelineEvent:
    """测试时间线事件"""

    def test_event_creation(self):
        """测试事件创建"""
        event = TimelineEvent(
            id="event-001",
            chapter_id="ch-001",
            title="主角觉醒",
            summary="主角在危机中觉醒魔法力量",
            order=1,
            timestamp="第一卷第三章",
            involved_characters=["char-001"],
            location="loc-001"
        )
        assert event.title == "主角觉醒"
        assert event.order == 1
        assert "char-001" in event.involved_characters


class TestStoryTheme:
    """测试故事主题"""

    def test_theme_creation(self):
        """测试主题创建"""
        theme = StoryTheme(
            name="成长与牺牲",
            description="主角在成长过程中必须做出牺牲",
            manifestations=["放弃力量拯救朋友", "选择正义而非复仇"]
        )
        assert theme.name == "成长与牺牲"
        assert len(theme.manifestations) == 2


class TestStoryBible:
    """测试故事圣经"""

    def test_story_bible_creation(self):
        """测试故事圣经创建"""
        bible = StoryBible()
        assert bible.title == ""
        assert bible.world_rules == []
        assert bible.locations == []
        assert bible.factions == []

    def test_add_world_rule(self, sample_world_rule_data):
        """测试添加世界规则"""
        bible = StoryBible()
        rule = WorldRule(**sample_world_rule_data)
        bible.world_rules.append(rule)
        assert len(bible.world_rules) == 1
        assert bible.world_rules[0].category == "magic"

    def test_get_world_rules_text(self):
        """测试获取世界规则文本"""
        bible = StoryBible(
            world_view="这是一个魔法世界",
            world_rules=[
                WorldRule(
                    id="rule-001",
                    name="魔法守恒",
                    description="魔法能量守恒",
                    category="magic"
                )
            ]
        )
        text = bible.get_world_rules_text()
        assert "魔法世界" in text
        assert "魔法守恒" in text

    def test_to_dict(self):
        """测试转换为字典"""
        bible = StoryBible(title="测试小说", genre="fantasy")
        data = bible.to_dict()
        assert data["title"] == "测试小说"
        assert data["genre"] == "fantasy"

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "title": "从字典创建",
            "genre": "sci-fi",
            "world_rules": []
        }
        bible = StoryBible.from_dict(data)
        assert bible.title == "从字典创建"
        assert bible.genre == "sci-fi"


class TestStoryMemory:
    """测试故事记忆"""

    def test_story_memory_creation(self, sample_novel_id):
        """测试故事记忆创建"""
        memory = StoryMemory(story_id=sample_novel_id)
        assert memory.story_id == sample_novel_id
        assert isinstance(memory.bible, StoryBible)
        assert memory.characters == []
        assert memory.timeline == []
        assert memory.chapter_summaries == []
        assert memory.world_locked is False

    def test_add_character(self, sample_novel_id, sample_character_data):
        """测试添加角色"""
        memory = StoryMemory(story_id=sample_novel_id)
        char = Character(**sample_character_data)
        memory.characters.append(char)
        
        assert len(memory.characters) == 1
        assert memory.characters[0].name == "测试角色"

    def test_get_character_by_id(self, sample_novel_id, sample_character_data):
        """测试通过ID获取角色"""
        memory = StoryMemory(story_id=sample_novel_id)
        char = Character(**sample_character_data)
        memory.characters.append(char)
        
        found = next((c for c in memory.characters if c.id == "char-001"), None)
        assert found is not None
        assert found.name == "测试角色"

    def test_get_character_not_found(self, sample_novel_id):
        """测试获取不存在的角色"""
        memory = StoryMemory(story_id=sample_novel_id)
        found = next((c for c in memory.characters if c.id == "non-existent"), None)
        assert found is None

    def test_world_locked(self, sample_novel_id):
        """测试世界锁定状态"""
        memory = StoryMemory(story_id=sample_novel_id)
        assert memory.world_locked is False
        
        memory.world_locked = True
        assert memory.world_locked is True
