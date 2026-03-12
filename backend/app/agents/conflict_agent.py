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


class ConflictAgent(BaseAgent):
    """
    冲突 Agent：
    - 输入：edited_text 或 draft_text
    - 输出：conflict_suggestions（冲突/反转建议列表）
    """

    def __init__(self, llm: Any = None):
        super().__init__(name="conflict-agent", llm=llm)

    def _call_llm(self, prompt: str) -> str:
        """调用 LLM 生成内容"""
        if self.llm is None:
            return "[ConflictAgent - LLM 未配置]"

        if not LANGCHAIN_AVAILABLE:
            return "[ConflictAgent - langchain 未安装]"

        try:
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"ConflictAgent LLM call error: {e}")
            return f"[ConflictAgent - 调用 LLM 出错: {str(e)}]"

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        text = input_data.get("edited_text") or input_data.get("draft_text") or ""

        # 构建冲突分析提示词
        prompt = f"""你是一位擅长剧情设计的创意顾问。请分析以下章节内容，并提供冲突和反转建议：

{text}

请提供：
1. 分析当前章节的冲突强度和类型
2. 提出2-3条具体的冲突增强建议（如何让情节更紧张）
3. 提出1-2个反转点子（让读者意想不到）
4. 建议如何为下一章铺垫悬念

请以列表形式输出，每条建议简洁明了。"""

        llm_response = self._call_llm(prompt)

        # 解析 LLM 响应为建议列表
        suggestions: List[str] = []
        if llm_response and not llm_response.startswith("["):
            # 按行分割并清理
            lines = [line.strip() for line in llm_response.split('\n') if line.strip()]
            # 过滤掉标题行，保留建议内容
            for line in lines:
                # 移除常见的列表标记
                cleaned = line.lstrip('0123456789.-*•) ').strip()
                if cleaned and len(cleaned) > 10:  # 确保是有意义的建议
                    suggestions.append(cleaned)

        # 如果没有解析出建议，使用默认建议
        if not suggestions:
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
