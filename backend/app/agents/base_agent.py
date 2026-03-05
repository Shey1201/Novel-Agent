from typing import Any


class BaseAgent:
    """
    所有具体 Agent 的基础父类。

    统一约定：
    - name: Agent 名称（用于日志、调试、前端显示）
    - llm: 底层大模型客户端或可调用对象（后续会接 OpenAI / DeepSeek / Claude）
    - run(input_data): 同一入口，返回处理结果
    """

    def __init__(self, name: str, llm: Any):
        self.name = name
        self.llm = llm

    def run(self, input_data: Any) -> Any:
        """
        统一的执行入口，子类必须重写。
        """
        raise NotImplementedError("Subclasses must implement run()")

