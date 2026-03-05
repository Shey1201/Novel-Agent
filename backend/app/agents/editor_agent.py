from typing import Any, Dict

from app.agents.base_agent import BaseAgent


class EditorAgent(BaseAgent):
    """
    编辑 Agent：
    - 输入：draft_text（草稿）、可选的 style/constraints
    - 输出：edited_text（基础润色版），以及简单的说明
    当前为占位实现，后续接入真正的 LLM 做 rewrite / polish。
    """

    def __init__(self, llm: Any = None):
        super().__init__(name="editor-agent", llm=llm)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        draft = input_data.get("draft_text", "")
        trace_data = input_data.get("trace_data", [])
        
        if callable(self.llm):
            edited = self.llm(draft)
        else:
            edited = f"[EditorAgent polished]\n{draft}"

        # 这里的简单实现是将修改历史存入 trace_data
        updated_trace_data = []
        if trace_data:
            # 假设只修改第一个片段
            for item in trace_data:
                new_item = item.copy()
                new_item["revisions"] = item.get("revisions", []) + [item["text"]]
                new_item["text"] = edited
                new_item["source_agent"] = self.name
                updated_trace_data.append(new_item)
        else:
            # 如果之前没有 trace_data，新造一个
            updated_trace_data = [{
                "text": edited,
                "source_agent": self.name,
                "revisions": []
            }]

        return {
            "edited_text": edited,
            "trace_data": updated_trace_data,
            "agent": self.name,
            "message": "已完成语法和文风优化",
            "type": "polishing"
        }

