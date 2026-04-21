"""
Writing Agent - 写作 Agent
基于 hello-agents 最佳实践：
- ReAct 推理模式
- 反思机制 (Reflection)
- 工具调用能力
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from app.agents.base_agent import BaseAgent, AgentMode, Tool, ActionResultStatus

if TYPE_CHECKING:
    from app.agents.base_agent import Action, Observation, ReasoningStep

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


class WritingAgent(BaseAgent):
    """
    写作 Agent：
    - 输入：包含 text（原始提示或大纲）、可选的 meta 信息
    - 输出：草稿文本 draft_text
    
    支持模式：
    - CHAIN: 链式调用（默认）
    - REACT: ReAct 推理模式
    - REFLECTION: 反思模式
    - PLAN_EXECUTE: 计划执行模式
    """

    def __init__(self, llm: Any = None, mode: AgentMode = AgentMode.CHAIN):
        super().__init__(
            name="writing-agent", 
            llm=llm, 
            mode=mode,
            tools=self._get_default_tools()
        )

    def _get_default_tools(self) -> List[Tool]:
        """获取默认工具"""
        return [
            Tool(
                name="generate_draft",
                description="生成章节草稿",
                function=self._generate_draft_tool
            ),
            Tool(
                name="enhance_description",
                description="增强场景描写",
                function=self._enhance_description_tool
            ),
            Tool(
                name="improve_dialogue",
                description="改进角色对话",
                function=self._improve_dialogue_tool
            ),
            Tool(
                name="adjust_tone",
                description="调整文风/语气",
                function=self._adjust_tone_tool
            )
        ]

    def _generate_draft_tool(self, outline: str, style: str = "standard") -> str:
        """生成草稿的工具函数"""
        prompts = {
            "standard": "保持情节连贯，人物性格一致",
            "vivid": "语言流畅，描写生动",
            "intense": "节奏紧凑，冲突强烈",
            "emotional": "注重情感描写，心理刻画"
        }
        
        prompt = f"""你是一位专业的小说作家。请根据以下大纲创作章节内容：

{outline}

要求：
1. {prompts.get(style, prompts['standard'])}
2. 适当加入对话和心理描写
3. 控制字数在 2000-3000 字左右

请直接输出章节正文内容，不要添加标题或说明。"""

        return self._call_llm(prompt)

    def _enhance_description_tool(self, text: str, focus: str = "scene") -> str:
        """增强描写的工具函数"""
        prompt = f"""请增强以下文本的{focus}描写：

{text}

让描写更加生动、具体、有画面感。"""

        return self._call_llm(prompt)

    def _improve_dialogue_tool(self, text: str) -> str:
        """改进对话的工具函数"""
        prompt = f"""请改进以下文本中的对话，使其更符合角色性格和情境：

{text}

确保对话：- 符合角色身份和性格
- 推动情节发展
- 有适当的潜台词"""

        return self._call_llm(prompt)

    def _adjust_tone_tool(self, text: str, tone: str) -> str:
        """调整文风的工具函数"""
        tone_map = {
            "serious": "严肃、正式",
            "humorous": "幽默、轻松",
            "romantic": "浪漫、温馨",
            "dark": "黑暗、压抑",
            "heroic": "热血、激昂"
        }
        
        prompt = f"""请将以下文本的风格调整为 {tone_map.get(tone, '标准')}：

{text}

保持原文的意思，但改变表达方式。"""

        return self._call_llm(prompt)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行写作任务
        
        根据模式选择执行方式：
        - CHAIN: 直接生成
        - REACT: 使用 ReAct 模式
        - REFLECTION: 使用反思模式
        """
        if self.mode == AgentMode.REACT:
            return self._run_react_mode(input_data)
        elif self.mode == AgentMode.REFLECTION:
            return self._run_reflection_mode(input_data)
        elif self.mode == AgentMode.PLAN_EXECUTE:
            return self._run_plan_execute_mode(input_data)
        else:
            return self._run_chain_mode(input_data)

    def _run_chain_mode(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """链式模式 - 直接生成"""
        text = input_data.get("text", "")
        style = input_data.get("style", "standard")

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

    def _run_react_mode(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """ReAct 模式"""
        # 使用基类的 ReAct 执行
        from app.agents.base_agent import ReasoningStep
        
        result = self.run_react(input_data, max_steps=8)
        
        return {
            "draft_text": result.get("result", {}).get("draft_text", "") if isinstance(result.get("result"), dict) else result.get("result", ""),
            "trace_data": [],
            "agent": self.name,
            "message": "使用 ReAct 模式完成写作",
            "type": "generation",
            "reasoning_steps": result.get("reasoning_steps", []),
            "success": result.get("success", False)
        }

    def _run_reflection_mode(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """反思模式"""
        # 使用基类的反思执行，但是传入链式执行的方法避免递归
        result = self.run_with_reflection(
            input_data, 
            max_retries=2,
            execute_func=self._run_chain_mode  # 传入实际执行函数
        )
        
        # 尝试获取 draft_text
        final = result.get("final_result", {})
        if isinstance(final, dict):
            draft = final.get("draft_text", "")
        else:
            draft = str(final)
        
        return {
            "draft_text": draft,
            "trace_data": [],
            "agent": self.name,
            "message": "使用反思模式完成写作",
            "type": "generation",
            "reflection_history": result.get("reflection_history", []),
            "attempts": result.get("attempts", 1),
            "success": result.get("success", False)
        }

    def _run_plan_execute_mode(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """计划执行模式"""
        # 1. 计划阶段
        plan_prompt = f"""请为以下写作任务制定详细计划：

{input_data.get('text', '')}

请提供：
1. 章节结构（大纲）
2. 重点场景
3. 关键对话
4. 预期字数

请用中文输出。"""

        plan = self._call_llm(plan_prompt)
        
        # 2. 执行阶段
        execute_prompt = f"""请根据以下计划创作章节：

{plan}

要求：
1. 严格按照计划执行
2. 保持文风一致
3. 控制字数在 2000-3000 字

请直接输出正文。"""

        draft = self._call_llm(execute_prompt)

        return {
            "draft_text": draft,
            "plan": plan,
            "agent": self.name,
            "message": "使用计划执行模式完成写作",
            "type": "generation"
        }

    def run_react(self, input_data: Any, max_steps: int = 10, stop_on_success: bool = True):
        """重写 run_react 以支持写作任务"""
        from app.agents.base_agent import ReasoningStep, Action, Observation, ActionResultStatus
        
        self._reasoning_history = []
        
        context = {
            "input": input_data.get("text", "") if isinstance(input_data, dict) else str(input_data),
            "style": input_data.get("style", "standard") if isinstance(input_data, dict) else "standard",
            "_react_complete": False,
            "_observations": [],
            "current_draft": ""
        }
        
        step_id = 0
        
        while step_id < max_steps:
            # Think - 分析当前进度
            thought = self._writing_think(context, step_id)
            
            # Act - 决定行动
            action = self._writing_act(thought, context, step_id)
            
            step = ReasoningStep(
                step_id=step_id,
                thought=thought,
                action=action
            )
            
            # Observe - 执行并观察
            if action:
                observation = self._writing_observe(action, context)
                step.observation = observation
                
                # 更新上下文
                context = self._update_writing_context(context, observation)
                
                if stop_on_success and observation.status == ActionResultStatus.SUCCESS:
                    step.is_final = True
                    self._reasoning_history.append(step)
                    break
            
            self._reasoning_history.append(step)
            
            if step.is_final:
                break
                
            step_id += 1
        
        return {
            "result": {"draft_text": context.get("current_draft", "")},
            "reasoning_steps": [self._step_to_dict(s) for s in self._reasoning_history],
            "success": context.get("_react_complete", False),
            "steps_used": step_id + 1
        }

    def _writing_think(self, context: Dict[str, Any], step_id: int) -> str:
        """写作任务思考"""
        prompt = f"""作为写作 Agent，你正在创作小说章节。

当前进度: 第 {step_id + 1} 步
已写内容: {context.get('current_draft', '')[:200]}...
待写内容: {context.get('input', '')[:300]}

请思考：
1. 接下来应该写什么？
2. 需要调用哪个工具？
3. 当前的写作方向是否正确？"""

        return self._call_llm(prompt, system_prompt="你是一个创意写作助手，帮助分析写作进度和决定下一步行动。")

    def _writing_act(self, thought: str, context: Dict[str, Any], step_id: int):
        """写作行动选择"""
        from app.agents.base_agent import Action
        
        if step_id == 0:
            # 第一步，生成草稿
            return Action(
                tool_name="generate_draft",
                input_data={
                    "outline": context.get("input", ""),
                    "style": context.get("style", "standard")
                },
                reasoning="初始生成草稿"
            )
        
        # 后续步骤可以选择改进
        return None

    def _writing_observe(self, action, context):
        """写作观察"""
        from app.agents.base_agent import Observation, ActionResultStatus
        
        tool = self._tool_map.get(action.tool_name)
        if not tool:
            return Observation(
                action=action,
                result=None,
                status=ActionResultStatus.FAILURE,
                error_message=f"Tool {action.tool_name} not found"
            )
        
        try:
            result = tool.function(**action.input_data)
            return Observation(
                action=action,
                result=result,
                status=ActionResultStatus.SUCCESS
            )
        except Exception as e:
            return Observation(
                action=action,
                result=None,
                status=ActionResultStatus.FAILURE,
                error_message=str(e)
            )

    def _update_writing_context(self, context, observation):
        """更新写作上下文"""
        if observation.status.value == "success":
            context["current_draft"] = str(observation.result)
            context["_observations"].append(f"生成了内容，长度: {len(str(observation.result))}")
            
            # 如果内容足够长，完成
            if len(str(observation.result)) > 1500:
                context["_react_complete"] = True
        
        return context
