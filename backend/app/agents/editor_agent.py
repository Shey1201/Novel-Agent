from typing import Any, Dict

from app.agents.base_agent import BaseAgent

# 尝试导入 langchain，如果失败则在运行时处理
try:
    from langchain.schema import HumanMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    HumanMessage = None


class EditorAgent(BaseAgent):
    """
    编辑 Agent：
    - 输入：draft_text（草稿）、可选的 style/constraints
    - 输出：edited_text（润色版），以及修改历史
    """

    def __init__(self, llm: Any = None):
        super().__init__(name="editor-agent", llm=llm)

    def _call_llm(self, prompt: str) -> str:
        """调用 LLM 生成内容"""
        if self.llm is None:
            return f"[EditorAgent polished - LLM 未配置]\n{prompt}"

        if not LANGCHAIN_AVAILABLE:
            return f"[EditorAgent polished - langchain 未安装]\n{prompt}"

        try:
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"EditorAgent LLM call error: {e}")
            return f"[EditorAgent polished - 调用 LLM 出错: {str(e)}]\n{prompt}"

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        draft = input_data.get("draft_text", "")
        trace_data = input_data.get("trace_data", [])

        # 构建编辑提示词
        prompt = f"""你是一位资深的小说编辑。请对以下草稿进行润色和优化：

{draft}

润色要求：
1. 修正语法错误和错别字
2. 优化句子结构，使表达更流畅
3. 增强描写细节，提升画面感
4. 保持原文的风格和语气
5. 确保人物对话自然真实

请直接输出润色后的内容，不要添加说明。"""

        edited = self._call_llm(prompt)

        # 更新 trace_data
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
