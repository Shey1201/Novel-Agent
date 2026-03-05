from typing import Any, Dict, List
from app.agents.base_agent import BaseAgent

class ReaderAgent(BaseAgent):
    """
    Reader Agent：
    - 输入：草稿文本
    - 输出：爽点评价、可读性建议
    目前是占位实现：如果有 llm 且可调用，就调用一次；否则简单包装。
    """

    def __init__(self, llm: Any = None):
        super().__init__(name="reader-agent", llm=llm)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        text = input_data.get("draft_text", "")
        if callable(self.llm):
            feedback = self.llm(text)
        else:
            feedback = ["这个剧情很有张力", "期待下一步的反转"]

        return {
            "reader_feedback": feedback,
            "agent": self.name,
            "message": "从读者视角完成了全篇审读",
            "type": "review"
        }
