"""
测试配置和共享fixture
"""
import pytest
import asyncio
from typing import Generator, Any
from unittest.mock import Mock, MagicMock


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环fixture"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_llm_response():
    """模拟LLM响应"""
    return {
        "content": "这是模拟的LLM响应内容",
        "usage": {"prompt_tokens": 100, "completion_tokens": 50}
    }


@pytest.fixture
def sample_novel_id():
    """示例小说ID"""
    return "test-novel-001"


@pytest.fixture
def sample_chapter_id():
    """示例章节ID"""
    return "test-chapter-001"


@pytest.fixture
def sample_character_data():
    """示例角色数据"""
    return {
        "id": "char-001",
        "name": "测试角色",
        "aliases": ["小测"],
        "age": 25,
        "gender": "male",
        "appearance": "高大英俊，黑发",
        "personality": "勇敢、正直",
        "values": ["正义", "友情"],
        "fears": ["失去亲人"],
        "desires": ["成为英雄"],
        "background": "出身平凡，但心怀大志",
        "abilities": ["剑术", "魔法"],
        "weaknesses": ["过于冲动"],
        "current_state": "正在修炼",
        "tags": ["主角", "战士"]
    }


@pytest.fixture
def sample_world_rule_data():
    """示例世界规则数据"""
    return {
        "id": "rule-001",
        "name": "魔法能量守恒",
        "description": "魔法使用需要消耗精神力",
        "category": "magic",
        "importance": "high",
        "exceptions": ["神级魔法", "禁咒"]
    }


@pytest.fixture
def sample_proposal_data():
    """示例议案数据"""
    return {
        "id": "proposal-001",
        "title": "主角如何脱困",
        "description": "主角被困在密室中，需要设计合理的逃脱方案",
        "proposed_by": "user",
        "status": "open"
    }


@pytest.fixture
def sample_discussion_message():
    """示例讨论消息"""
    return {
        "id": "msg-001",
        "agent_id": "agent-planner",
        "agent_name": "Planner",
        "content": "我认为主角可以使用之前获得的魔法道具脱困",
        "message_type": "suggestion",
        "references": []
    }
