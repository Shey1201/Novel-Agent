from app.api import agent_routes


class DummyService:
    def __init__(self):
        self.kwargs = None

    def chat(self, message, story_id, chapter_id=None, word_count_range=None, conversation_state=None):
        self.kwargs = {
            "message": message,
            "story_id": story_id,
            "chapter_id": chapter_id,
            "word_count_range": word_count_range,
            "conversation_state": conversation_state,
        }
        return {"ok": True, "conversation_state": conversation_state}


def test_agent_chat_preserves_full_conversation_state(monkeypatch):
    service = DummyService()
    monkeypatch.setattr(agent_routes, "get_chat_service", lambda: service)

    payload = agent_routes.AgentChatRequest(
        message="确认保存",
        story_id="story-1",
        chapter_id="chapter-1",
        word_count_range=agent_routes.WordCountRange(min=1200, max=1500),
        conversation_state={
            "stage": "waiting_save_confirmation",
            "waiting_for_user": True,
            "workflow_type": "write",
            "pending_save": {
                "story_id": "story-1",
                "summary": ["世界观", "角色(2个)"],
                "logs": [{"auto_fill": {"type": "worldbuilding", "content": "x"}}],
            },
            "context_confirmed": True,
        },
    )

    result = agent_routes.agent_chat(payload)
    if hasattr(result, "__await__"):
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(result)

    assert result["ok"] is True
    assert service.kwargs is not None
    assert service.kwargs["conversation_state"]["stage"] == "waiting_save_confirmation"
    assert "pending_save" in service.kwargs["conversation_state"]
    assert service.kwargs["conversation_state"]["context_confirmed"] is True
