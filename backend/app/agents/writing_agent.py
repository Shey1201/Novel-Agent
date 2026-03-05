from typing import Any, Dict

from app.agents.base_agent import BaseAgent


class WritingAgent(BaseAgent):
    """
    写作 Agent：
    - 输入：包含 text（原始提示或大纲）、可选的 meta 信息
    - 输出：草稿文本 draft_text
    目前是占位实现：如果有 llm 且可调用，就调用一次；否则简单包装。
    """

    def __init__(self, llm: Any = None):
        super().__init__(name="writing-agent", llm=llm)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        text = input_data.get("text", "")
        if callable(self.llm):
            draft = self.llm(text)
        else:
            draft = f"[WritingAgent draft]\n{text}"

        trace_item = {
            "text": draft,
            "source_agent": self.name,
            "revisions": []
        }

        return {
            "draft_text": draft,
            "trace_data": [trace_item],
            "agent": self.name,
            "message": "已根据大纲生成草稿",
            "type": "generation"
        }

