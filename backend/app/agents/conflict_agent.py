from typing import Any, Dict, List

from app.agents.base_agent import BaseAgent


class ConflictAgent(BaseAgent):
    """
    冲突 Agent：
    - 输入：edited_text 或 draft_text
    - 输出：conflict_suggestions（简单的冲突/反转建议列表）
    目前为占位逻辑，后续会用 LLM 基于剧情结构生成更智能的建议。
    """

    def __init__(self, llm: Any = None):
        super().__init__(name="conflict-agent", llm=llm)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        text = input_data.get("edited_text") or input_data.get("draft_text") or ""

        suggestions: List[str]
        if callable(self.llm):
            # 未来可以设计 prompt，让 llm 返回结构化建议
            result = self.llm(text)
            suggestions = [str(result)]
        else:
            suggestions = [
                "在本章中增加一次正面冲突，让主角与主要对手直接交锋。",
                "在结尾加入一个小型反转，颠覆读者对配角动机的预期。",
            ]

        return {
            "conflict_suggestions": suggestions,
            "agent": self.name,
            "message": f"提出了 {len(suggestions)} 条冲突建议",
            "type": "review"
        }

