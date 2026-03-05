from typing import Any, Dict

from app.agents.base_agent import BaseAgent
from app.agents.planner_agent import PlannerAgent


class StrategistAgent(BaseAgent):
    """用户可见的一级策划 Agent，封装原 Planner 能力。"""

    def __init__(self, llm: Any = None):
        super().__init__(name="strategist-agent", llm=llm)
        self._planner = PlannerAgent(llm=llm)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        result = self._planner.run(input_data)
        return {
            **result,
            "agent": self.name,
            "message": "已完成策划（世界观/大纲/结构）",
        }
