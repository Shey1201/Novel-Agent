from typing import Any, Dict
from app.agents.base_agent import BaseAgent

class PlannerAgent(BaseAgent):
    """
    Planner Agent：
    - 输入：包含世界观、人物设定或初步想法
    - 输出：详细的大纲和计划
    目前是占位实现：如果有 llm 且可调用，就调用一次；否则简单包装。
    """

    def __init__(self, llm: Any = None):
        super().__init__(name="planner-agent", llm=llm)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        text = input_data.get("text", "")
        if callable(self.llm):
            plan = self.llm(text)
        else:
            plan = f"[PlannerAgent plan]\nWorld: Fantasy, Character: Hero, Plot: {text}"

        return {
            "plan_text": plan,
            "agent": self.name,
            "message": "已生成详细的世界观和剧情大纲",
            "type": "planning"
        }
