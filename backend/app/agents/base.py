from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    """
    所有 Agent 的抽象基类。

    约定：
    - 输入为一个状态字典（例如 GraphState 的部分字段）
    - 输出为一个状态字典（将会 merge 回全局状态）
    """

    name: str = "base-agent"

    @abstractmethod
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行 Agent 的核心逻辑。

        :param state: 当前状态（只读/读写由具体实现约定）
        :return: 需要写回到全局状态的增量字段
        """
        raise NotImplementedError

