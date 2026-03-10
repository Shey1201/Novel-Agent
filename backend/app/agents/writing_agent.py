from typing import Any, Dict

from app.agents.base_agent import BaseAgent

# 尝试导入 langchain，如果失败则在运行时处理
try:
    from langchain.schema import HumanMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    HumanMessage = None


class WritingAgent(BaseAgent):
    """
    写作 Agent：
    - 输入：包含 text（原始提示或大纲）、可选的 meta 信息
    - 输出：草稿文本 draft_text
    """

    def __init__(self, llm: Any = None):
        super().__init__(name="writing-agent", llm=llm)

    def _call_llm(self, prompt: str) -> str:
        """调用 LLM 生成内容"""
        if self.llm is None:
            return f"[WritingAgent draft - LLM 未配置]\n{prompt}"

        if not LANGCHAIN_AVAILABLE:
            return f"[WritingAgent draft - langchain 未安装]\n{prompt}"

        try:
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"WritingAgent LLM call error: {e}")
            return f"[WritingAgent draft - 调用 LLM 出错: {str(e)}]\n{prompt}"

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        text = input_data.get("text", "")

        # 构建写作提示词
        prompt = f"""你是一位专业的小说作家。请根据以下大纲创作章节内容：

{text}

要求：
1. 保持情节连贯，人物性格一致
2. 语言流畅，描写生动
3. 适当加入对话和心理描写
4. 控制字数在 2000-3000 字左右

请直接输出章节正文内容，不要添加标题或说明。"""

        draft = self._call_llm(prompt)

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
