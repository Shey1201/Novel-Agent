from typing import Any, Dict
from app.agents.base_agent import BaseAgent

class SummaryAgent(BaseAgent):
    """
    SummaryAgent: 总结章节内容
    """
    def __init__(self, llm: Any = None):
        super().__init__(name="summary-agent", llm=llm)

    def run(self, chapter: str) -> str:
        prompt = f"""
        总结下面章节：

        {chapter}
        """
        if callable(self.llm):
            result = self.llm(prompt)
        else:
            # 占位逻辑
            result = f"[Summary] 这是对章节内容的自动总结：主角在这一章经历了..."
        
        return result
