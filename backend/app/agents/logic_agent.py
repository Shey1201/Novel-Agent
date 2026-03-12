from typing import Any, Dict, List

from app.agents.base_agent import BaseAgent
from langchain.schema import HumanMessage


class LogicAgent(BaseAgent):
    """用于世界观阶段的逻辑一致性检查。"""

    def __init__(self, llm: Any = None):
        super().__init__(name="logic-agent", llm=llm)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        world_draft = input_data.get("world_draft", "")

        issues: List[str]
        if self.llm is not None:
            # 必须传 LangChain 消息对象列表，不能直接传字符串
            try:
                result = self.llm.invoke([HumanMessage(content=world_draft)])
                issues = [str(result.content)] if hasattr(result, 'content') else [str(result)]
            except Exception as e:
                issues = [f"LLM 调用失败: {str(e)}"]
        else:
            issues = [
                "若设定为人人都可修炼，需要解释为何仍存在明显阶层分化。",
                "若资源并不稀缺，需要补充限制条件，否则核心冲突会偏弱。",
            ]

        return {
            "logic_issues": issues,
            "agent": self.name,
            "message": f"识别了 {len(issues)} 条逻辑风险",
            "type": "review",
        }
