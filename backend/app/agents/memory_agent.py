from typing import Any, Dict

from app.agents.base_agent import BaseAgent


class MemoryAgent(BaseAgent):
    """用户可见的一级 Memory Agent：负责故事记忆落盘入口。"""

    def __init__(self, llm: Any = None):
        super().__init__(name="memory-agent", llm=llm)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "agent": self.name,
            "message": "故事记忆已同步",
            "type": "memory",
            **input_data,
        }
