from typing import Any, Dict

from app.agents.base_agent import BaseAgent

# 尝试导入 langchain，兼容新旧版本
try:
    from langchain_core.messages import HumanMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        from langchain.schema import HumanMessage
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False
        HumanMessage = None


class SummaryAgent(BaseAgent):
    """
    SummaryAgent: 总结章节内容
    """
    def __init__(self, llm: Any = None):
        super().__init__(name="summary-agent", llm=llm)

    def _call_llm(self, prompt: str) -> str:
        """调用 LLM 生成内容"""
        if self.llm is None:
            return "[SummaryAgent - LLM 未配置]"

        if not LANGCHAIN_AVAILABLE:
            return "[SummaryAgent - langchain 未安装]"

        try:
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"SummaryAgent LLM call error: {e}")
            return f"[SummaryAgent - 调用 LLM 出错: {str(e)}]"

    def run(self, chapter: str) -> str:
        prompt = f"""请对以下章节内容进行简洁的总结：

{chapter}

要求：
1. 概括主要情节发展
2. 点明关键事件和转折点
3. 控制在100-200字以内

请直接输出总结内容。"""

        result = self._call_llm(prompt)

        # 如果 LLM 调用失败，返回占位符
        if result.startswith("["):
            return f"[Summary] 这是对章节内容的自动总结：主角在这一章经历了..."

        return result
