"""
Planner Agent - 计划 Agent
基于 hello-agents 最佳实践：
- 计划执行模式 (Plan-and-Execute)
- 反思机制
- 工具调用
"""

from typing import Any, Dict, List, Optional

from app.agents.base_agent import BaseAgent, AgentMode, Tool

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
    
    支持模式：
    - PLAN_EXECUTE: 计划执行模式（默认）
    - REACT: ReAct 推理模式
    - REFLECTION: 反思模式
    """

    def __init__(self, llm: Any = None, mode: AgentMode = AgentMode.PLAN_EXECUTE):
        super().__init__(
            name="planner-agent", 
            llm=llm, 
            mode=mode,
            tools=[]  # 不传递 tools，避免 langchain 序列化问题
        )

    def _get_default_tools(self) -> List[Tool]:
        """获取默认工具"""
        return [
            Tool(
                name="create_outline",
                description="创建故事大纲",
                function=self._create_outline_tool
            ),
            Tool(
                name="design_characters",
                description="设计角色设定",
                function=self._design_characters_tool
            ),
            Tool(
                name="plan_structure",
                description="规划故事结构",
                function=self._plan_structure_tool
            ),
            Tool(
                name="add_plot_points",
                description="添加情节点",
                function=self._add_plot_points_tool
            )
        ]

    def _create_outline_tool(self, idea: str, genre: str = "general") -> str:
        """创建大纲的工具"""
        prompt = f"""请根据以下创意创建一个详细的故事大纲：

创意：{idea}
类型：{genre}

请提供：
1. 故事主题和核心概念
2. 主要情节线
3. 关键情节点（至少5个）
4. 故事弧线（起承转合）

请用中文详细描述。"""

        return self._call_llm(prompt)

    def _design_characters_tool(self, outline: str) -> str:
        """设计角色的工具"""
        prompt = f"""请根据以下大纲设计主要角色：

{outline}

请提供：
1. 主角设定（性格、背景、目标）
2. 配角设定（至少3个）
3. 对立角色（如果有）
4. 角色关系图

请用中文描述。"""

        return self._call_llm(prompt)

    def _plan_structure_tool(self, outline: str, target_chapters: int = 20) -> str:
        """规划结构的工具"""
        prompt = f"""请将以下大纲规划为 {target_chapters} 章的结构：

{outline}

请提供：
1. 每章的标题和简介
2. 章节之间的衔接
3. 高潮和转折点位置
4. 各章节的字数预估

请用中文输出。"""

        return self._call_llm(prompt)

    def _add_plot_points_tool(self, outline: str, count: int = 5) -> str:
        """添加情节点"""
        prompt = f"""请为以下大纲添加 {count} 个关键情节点：

{outline}

每个情节点应包含：
- 事件描述
- 发生时机
- 对故事的影响

请用列表格式输出。"""

        return self._call_llm(prompt)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行计划任务"""
        if self.mode == AgentMode.PLAN_EXECUTE:
            return self._run_plan_execute_mode(input_data)
        elif self.mode == AgentMode.REACT:
            return self._run_react_mode(input_data)
        elif self.mode == AgentMode.REFLECTION:
            return self._run_reflection_mode(input_data)
        else:
            return self._run_plan_execute_mode(input_data)

    def _run_plan_execute_mode(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """计划执行模式（单次 LLM 调用优化版）"""
        text = input_data.get("text", "")

        # 单次 LLM 调用完成所有内容
        prompt = f"""你是一位专业的故事策划师。请根据以下想法创作完整的故事规划：

{text}

请一次性提供（用中文）：
1. 故事主题和核心概念
2. 主要角色设定（主角、配角）及背景
3. 故事结构（开端、发展、高潮、结局）
4. 关键情节点（至少5个）
5. 章节规划（10章左右的大纲）
6. 世界观设定要点

确保内容完整，可以直接用于后续写作。"""

        # 使用原始 openai API，绕过 langchain
        from openai import OpenAI
        
        # 提取 LLM 配置
        model = getattr(self.llm, 'model_name', None) or getattr(self.llm, 'model', 'deepseek-chat')
        api_key = getattr(self.llm, 'openai_api_key', None)
        base_url = getattr(self.llm, 'openai_api_base', None)
        
        # 处理 SecretStr
        if hasattr(api_key, 'get_secret_value'):
            api_key = api_key.get_secret_value()
        
        # 调用 API
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        plan_text = response.choices[0].message.content

        return {
            "plan_text": plan_text,
            "outline": plan_text,
            "characters": "",
            "structure": "",
            "agent": self.name,
            "message": "已完成创作计划",
            "type": "planning"
        }

    def _run_react_mode(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """ReAct 模式"""
        from app.agents.base_agent import ReasoningStep
        
        result = self.run_react(input_data, max_steps=6)
        
        return {
            "plan_text": result.get("result", {}).get("plan_text", "") if isinstance(result.get("result"), dict) else result.get("result", ""),
            "agent": self.name,
            "message": "使用 ReAct 模式完成规划",
            "type": "planning",
            "reasoning_steps": result.get("reasoning_steps", []),
            "success": result.get("success", False)
        }

    def _run_reflection_mode(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """反思模式"""
        result = self.run_with_reflection(input_data, max_retries=2)
        
        final = result.get("final_result", {})
        if isinstance(final, dict):
            plan = final.get("plan_text", "")
        else:
            plan = str(final)
        
        return {
            "plan_text": plan,
            "agent": self.name,
            "message": "使用反思模式完成规划",
            "type": "planning",
            "reflection_history": result.get("reflection_history", []),
            "attempts": result.get("attempts", 1),
            "success": result.get("success", False)
        }
