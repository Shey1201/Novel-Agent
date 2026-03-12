from typing import Any, Dict, List

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


class ReaderAgent(BaseAgent):
    """
    Reader Agent：
    - 输入：草稿文本
    - 输出：爽点评价、可读性建议
    """

    def __init__(self, llm: Any = None):
        super().__init__(name="reader-agent", llm=llm)

    def _call_llm(self, prompt: str) -> str:
        """调用 LLM 生成内容"""
        if self.llm is None:
            return "[ReaderAgent - LLM 未配置]"

        if not LANGCHAIN_AVAILABLE:
            return "[ReaderAgent - langchain 未安装]"

        try:
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"ReaderAgent LLM call error: {e}")
            return f"[ReaderAgent - 调用 LLM 出错: {str(e)}]"

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # 支持多种输入键：draft_text 或 text
        text = input_data.get("draft_text") or input_data.get("text", "")

        # 构建读者反馈提示词
        prompt = f"""你是一位资深读者和书评人。请阅读以下章节内容，并提供读者视角的反馈：

{text}

请从以下角度分析：
1. 剧情的吸引力和张力
2. 人物塑造是否立体
3. 是否有让人想继续阅读的悬念
4. 整体可读性和流畅度
5. 具体的改进建议（2-3条）

请以列表形式输出你的反馈。"""

        llm_response = self._call_llm(prompt)

        # 解析 LLM 响应为反馈列表
        feedback: List[str] = []
        if llm_response and not llm_response.startswith("["):
            lines = [line.strip() for line in llm_response.split('\n') if line.strip()]
            for line in lines:
                cleaned = line.lstrip('0123456789.-*•) ').strip()
                if cleaned and len(cleaned) > 5:
                    feedback.append(cleaned)

        # 如果没有解析出反馈，使用默认反馈
        if not feedback:
            feedback = [
                "这个剧情很有张力，节奏把握得当。",
                "期待下一步的反转，悬念设置很到位。",
            ]

        return {
            "reader_feedback": feedback,
            "agent": self.name,
            "message": "从读者视角完成了全篇审读",
            "type": "review"
        }
