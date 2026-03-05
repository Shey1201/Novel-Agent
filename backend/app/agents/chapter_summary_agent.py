from typing import Any, Dict
from app.agents.base_agent import BaseAgent

class ChapterSummaryAgent(BaseAgent):
    """
    Chapter Summary Agent：
    - 输入：章节文本
    - 输出：章节总结
    目前是占位实现：如果有 llm 且可调用，就调用一次；否则简单包装。
    """

    def __init__(self, llm: Any = None):
        super().__init__(name="chapter-summary-agent", llm=llm)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        text = input_data.get("final_text", input_data.get("draft_text", ""))
        if callable(self.llm):
            summary = self.llm(text)
        else:
            summary = f"Summary:主角开始了他的旅程"

        return {
            "summary_text": summary,
            "agent": self.name,
            "message": "已完成本章核心内容总结",
            "type": "summary"
        }
