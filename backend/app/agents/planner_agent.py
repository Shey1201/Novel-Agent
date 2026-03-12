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


class PlannerAgent(BaseAgent):
    """
    Planner Agent：
    - 输入：包含世界观、人物设定或初步想法
    - 输出：详细的大纲和计划
    """

    def __init__(self, llm: Any = None):
        super().__init__(name="planner-agent", llm=llm)

    def _call_llm(self, prompt: str) -> str:
        """调用 LLM 生成内容"""
        if self.llm is None:
            return f"[PlannerAgent plan - LLM 未配置]\n{prompt}"

        if not LANGCHAIN_AVAILABLE:
            return f"[PlannerAgent plan - langchain 未安装]\n{prompt}"

        try:
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"PlannerAgent LLM call error: {e}")
            return f"[PlannerAgent plan - 调用 LLM 出错: {str(e)}]\n{prompt}"

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        text = input_data.get("text", "")

        # 构建规划提示词
        prompt = f"""你是一位专业的故事策划师。请根据以下想法创作详细的故事大纲：

{text}

请提供：
1. 故事主题和核心概念
2. 主要角色设定（主角、配角）
3. 故事结构（开端、发展、高潮、结局）
4. 关键情节点（至少5个）
5. 世界观设定要点

请用中文详细描述，确保大纲足够完整，可以直接用于后续写作。"""

        plan = self._call_llm(prompt)

        return {
            "plan_text": plan,
            "agent": self.name,
            "message": "已生成详细的世界观和剧情大纲",
            "type": "planning"
        }
