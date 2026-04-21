"""
BaseAgent - 基础 Agent 框架
基于 hello-agents 最佳实践增强：
- ReAct 模式支持
- Tool/Action 调用能力
- 反思机制 (Reflection)
- 状态管理
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import re


class AgentMode(Enum):
    """Agent 运行模式"""
    CHAIN = "chain"           # 链式调用（默认）
    REACT = "react"           # ReAct 推理模式
    REFLECTION = "reflection"  # 反思模式
    PLAN_EXECUTE = "plan_execute"  # 计划执行模式


class ActionResultStatus(Enum):
    """行动结果状态"""
    SUCCESS = "success"
    FAILURE = "failure"
    NEED_MORE_CONTEXT = "need_more_context"
    REQUIRES_HUMAN = "requires_human"


@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    function: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Action:
    """Action - Agent 的行动单元"""
    tool_name: str
    input_data: Dict[str, Any]
    reasoning: str  # 思考过程
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Observation:
    """Observation - 行动观察结果"""
    action: Action
    result: Any
    status: ActionResultStatus
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ReasoningStep:
    """推理步骤"""
    step_id: int
    thought: str           # 思考
    action: Optional[Action] = None  # 行动
    observation: Optional[Observation] = None  # 观察结果
    is_final: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ReflectionResult:
    """反思结果"""
    original_output: Any
    critique: str          # 批评/评估
    improvements: List[str]  # 改进建议
    should_retry: bool
    confidence: float      # 0-1 置信度
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class BaseAgent:
    """
    所有具体 Agent 的基础父类。
    
    基于 hello-agents 项目最佳实践增强：
    - name: Agent 名称（用于日志、调试、前端显示）
    - llm: 底层大模型客户端或可调用对象
    - mode: 运行模式 (CHAIN/REACT/REFLECTION/PLAN_EXECUTE)
    - tools: 可用工具列表
    - run(input_data): 统一入口，返回处理结果
    - run_with_reflection(): 带反思的执行
    - run_react(): ReAct 模式执行
    """

    def __init__(
        self,
        name: str,
        llm: Any = None,
        mode: AgentMode = AgentMode.CHAIN,
        tools: Optional[List[Tool]] = None
    ):
        self.name = name
        self.llm = llm
        self.mode = mode
        self.tools = tools or []
        
        # 运行时状态
        self._reasoning_history: List[ReasoningStep] = []
        self._current_context: Dict[str, Any] = {}
        
        # 工具映射
        self._tool_map: Dict[str, Tool] = {t.name: t for t in self.tools}

    def register_tool(self, tool: Tool):
        """注册工具"""
        self._tool_map[tool.name] = tool
        self.tools.append(tool)

    def run(self, input_data: Any) -> Any:
        """
        统一的执行入口，子类必须重写。
        """
        raise NotImplementedError("Subclasses must implement run()")

    def _call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        调用 LLM 生成内容
        """
        if self.llm is None:
            return f"[{self.name} - LLM 未配置]"

        try:
            # 兼容不同版本的 langchain
            try:
                from langchain_core.messages import HumanMessage, SystemMessage
                messages = []
                if system_prompt:
                    messages.append(SystemMessage(content=system_prompt))
                messages.append(HumanMessage(content=prompt))
            except ImportError:
                from langchain.schema import HumanMessage, SystemMessage
                messages = []
                if system_prompt:
                    messages.append(SystemMessage(content=system_prompt))
                messages.append(HumanMessage(content=prompt))

            response = self.llm.invoke(messages)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            return f"[{self.name} - LLM 调用错误: {str(e)}]"

    # ==================== ReAct 模式 ====================
    
    def run_react(
        self,
        input_data: Any,
        max_steps: int = 10,
        stop_on_success: bool = True
    ) -> Dict[str, Any]:
        """
        ReAct (Reason + Act) 模式执行
        
        1. Think: 思考当前情况
        2. Act: 选择并执行行动
        3. Observe: 观察行动结果
        4. 重复直到完成
        
        Args:
            input_data: 输入数据
            max_steps: 最大迭代次数
            stop_on_success: 成功后是否停止
            
        Returns:
            包含最终结果和推理历史
        """
        self._reasoning_history = []
        
        context = self._prepare_react_context(input_data)
        step_id = 0
        
        while step_id < max_steps:
            # 1. Think - 分析当前情况
            thought = self._react_think(context, step_id)
            
            # 2. Act - 决定行动
            action = self._react_act(thought, context, step_id)
            
            step = ReasoningStep(
                step_id=step_id,
                thought=thought,
                action=action
            )
            
            # 3. Observe - 执行行动并观察结果
            if action:
                observation = self._react_observe(action, context)
                step.observation = observation
                
                # 更新上下文
                context = self._update_context_after_observation(
                    context, observation
                )
                
                # 检查是否成功
                if stop_on_success and observation.status == ActionResultStatus.SUCCESS:
                    step.is_final = True
                    self._reasoning_history.append(step)
                    break
                    
                # 检查是否需要人工介入
                if observation.status == ActionResultStatus.REQUIRES_HUMAN:
                    step.is_final = True
                    self._reasoning_history.append(step)
                    break
            else:
                # 没有行动，可能是最终答案
                step.is_final = True
            
            self._reasoning_history.append(step)
            step_id += 1
        
        # 生成最终结果
        final_result = self._extract_react_result(context)
        
        return {
            "result": final_result,
            "reasoning_steps": [self._step_to_dict(s) for s in self._reasoning_history],
            "success": context.get("_react_complete", False),
            "steps_used": step_id + 1
        }

    def _prepare_react_context(self, input_data: Any) -> Dict[str, Any]:
        """准备 ReAct 上下文"""
        return {
            "input": input_data,
            "_react_complete": False,
            "_observations": []
        }

    def _react_think(self, context: Dict[str, Any], step_id: int) -> str:
        """ReAct Think 步骤 - 分析当前情况"""
        prompt = f"""你正在执行任务：{self.name}

当前步骤: {step_id}

输入数据: {context.get('input', {})}

已有观察:
{chr(10).join(context.get('_observations', []))}

可用工具: {', '.join(t.name for t in self.tools) if self.tools else '无'}

请分析当前情况，决定下一步应该做什么。保持简洁思考过程。"""

        return self._call_llm(prompt, system_prompt="你是一个推理助手，帮助分析情况并决定行动。")

    def _react_act(
        self,
        thought: str,
        context: Dict[str, Any],
        step_id: int
    ) -> Optional[Action]:
        """ReAct Act 步骤 - 决定并执行行动"""
        if not self.tools:
            return None
            
        # 让 LLM 选择工具
        tool_selection_prompt = f"""当前思考: {thought}

可用工具:
{chr(10).join(f"- {t.name}: {t.description}" for t in self.tools)}

请决定使用哪个工具（如果需要）。输出格式：
TOOL_NAME: tool_name
INPUT: {{"key": "value"}}
REASONING: 为什么选择这个工具

如果不需要工具，输出：
NO_ACTION"""

        response = self._call_llm(tool_selection_prompt)
        
        try:
            # 解析工具调用
            lines = response.split('\n')
            tool_name = None
            tool_input = {}
            reasoning = ""
            
            for line in lines:
                if line.startswith("TOOL_NAME:"):
                    tool_name = line.split(":", 1)[1].strip()
                elif line.startswith("INPUT:"):
                    try:
                        tool_input = json.loads(line.split(":", 1)[1].strip())
                    except:
                        tool_input = {}
                elif line.startswith("REASONING:"):
                    reasoning = line.split(":", 1)[1].strip()
            
            if tool_name and tool_name != "NO_ACTION" and tool_name in self._tool_map:
                return Action(
                    tool_name=tool_name,
                    input_data=tool_input,
                    reasoning=reasoning
                )
        except:
            pass
        
        return None

    def _react_observe(self, action: Action, context: Dict[str, Any]) -> Observation:
        """ReAct Observe 步骤 - 执行行动并观察结果"""
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

    def _update_context_after_observation(
        self,
        context: Dict[str, Any],
        observation: Observation
    ) -> Dict[str, Any]:
        """更新上下文"""
        context["_observations"].append(
            f"Step {len(context.get('_observations', []))}: "
            f"{observation.action.tool_name} -> {observation.status.value}"
        )
        
        # 如果失败，标记需要更多上下文
        if observation.status == ActionResultStatus.FAILURE:
            context["_needs_retry"] = True
            
        return context

    def _extract_react_result(self, context: Dict[str, Any]) -> Any:
        """从上下文中提取最终结果"""
        # 默认返回输入的某种处理结果
        return context.get("input", {})

    def _step_to_dict(self, step: ReasoningStep) -> Dict[str, Any]:
        """转换推理步骤为字典"""
        return {
            "step_id": step.step_id,
            "thought": step.thought,
            "action": {
                "tool": step.action.tool_name if step.action else None,
                "input": step.action.input_data if step.action else None,
                "reasoning": step.action.reasoning if step.action else None
            } if step.action else None,
            "observation": {
                "status": step.observation.status.value if step.observation else None,
                "result": str(step.observation.result)[:200] if step.observation else None,
                "error": step.observation.error_message if step.observation else None
            } if step.observation else None,
            "is_final": step.is_final
        }

    # ==================== 反思模式 ====================
    
    def run_with_reflection(
        self,
        input_data: Any,
        max_retries: int = 2,
        execute_func: callable = None
    ) -> Dict[str, Any]:
        """
        带反思的执行模式
        
        1. 先执行任务
        2. 对结果进行反思
        3. 如果需要改进，重试
        4. 返回最终结果和反思历史
        
        Args:
            input_data: 输入数据
            max_retries: 最大重试次数
            execute_func: 可选的执行函数，避免递归调用
        """
        # 如果没有提供执行函数，使用自身的 run 方法
        if execute_func is None:
            execute_func = self.run
        
        # 第一次尝试
        result = execute_func(input_data)
        
        reflection_history = []
        
        for attempt in range(max_retries):
            # 反思当前结果
            reflection = self._reflect(result, input_data, attempt)
            reflection_history.append(reflection)
            
            if not reflection.should_retry or attempt >= max_retries - 1:
                break
                
            # 根据反思改进
            result = self._improve_from_reflection(result, reflection, input_data)
        
        return {
            "final_result": result,
            "reflection_history": [self._reflection_to_dict(r) for r in reflection_history],
            "attempts": len(reflection_history),
            "success": reflection_history[-1].confidence > 0.5 if reflection_history else True
        }

    def _reflect(
        self,
        result: Any,
        input_data: Any,
        attempt: int
    ) -> ReflectionResult:
        """对结果进行反思"""
        prompt = f"""作为 {self.name}，请反思你刚刚生成的结果。

输入: {str(input_data)[:500]}
输出: {str(result)[:1000]}

请评估这个输出：
1. 是否完成了任务？
2. 有什么明显的问题？
3. 需要改进的地方？

请以 JSON 格式输出：
{{
    "critique": "批评内容",
    "improvements": ["改进建议1", "改进建议2"],
    "should_retry": true/false,
    "confidence": 0.0-1.0
}}"""

        try:
            response = self._call_llm(prompt)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return ReflectionResult(
                    original_output=result,
                    critique=data.get("critique", ""),
                    improvements=data.get("improvements", []),
                    should_retry=data.get("should_retry", False),
                    confidence=data.get("confidence", 0.5)
                )
        except Exception as e:
            print(f"Reflection error: {e}")
        
        # 默认返回
        return ReflectionResult(
            original_output=result,
            critique="反思调用失败",
            improvements=[],
            should_retry=False,
            confidence=0.5
        )

    def _improve_from_reflection(
        self,
        result: Any,
        reflection: ReflectionResult,
        input_data: Any
    ) -> Any:
        """根据反思改进结果"""
        improvement_prompt = f"""请根据以下反思建议改进之前的结果。

原始输入: {str(input_data)[:500]}
原结果: {str(result)[:1000]}

反思批评: {reflection.critique}
改进建议: {', '.join(reflection.improvements)}

请生成改进后的版本。"""

        return self._call_llm(improvement_prompt)

    def _reflection_to_dict(self, reflection: ReflectionResult) -> Dict[str, Any]:
        """转换反思结果为字典"""
        return {
            "critique": reflection.critique,
            "improvements": reflection.improvements,
            "should_retry": reflection.should_retry,
            "confidence": reflection.confidence,
            "timestamp": reflection.timestamp
        }

    # ==================== 工具方法 ====================
    
    def get_reasoning_history(self) -> List[Dict[str, Any]]:
        """获取推理历史"""
        return [self._step_to_dict(s) for s in self._reasoning_history]

    def clear_history(self):
        """清空历史"""
        self._reasoning_history = []
        self._current_context = {}

