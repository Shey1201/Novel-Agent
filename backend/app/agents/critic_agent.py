from typing import Any, Dict

from app.agents.base_agent import BaseAgent
from app.agents.reader_agent import ReaderAgent


class CriticAgent(BaseAgent):
    """用户可见的一级读者评估 Agent，封装原 Reader 能力。"""

    def __init__(self, llm: Any = None):
        super().__init__(name="critic-agent", llm=llm)
        self._reader = ReaderAgent(llm=llm)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        result = self._reader.run(input_data)
        return {
            **result,
            "agent": self.name,
            "message": "已完成读者视角评估",
        }
