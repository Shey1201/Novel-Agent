# Agent系统设计文档

本文档详细描述 Novel Agent Studio 中的Agent系统设计。

## 目录

- [系统概述](#系统概述)
- [Agent架构](#agent架构)
- [核心Agent](#核心agent)
- [Agent编排](#agent编排)
- [状态管理](#状态管理)
- [扩展机制](#扩展机制)

## 系统概述

### 设计目标

1. **模块化**: 每个Agent职责单一，便于独立开发和测试
2. **可组合**: Agent可以灵活组合成不同的工作流
3. **可观测**: 完整的执行日志和溯源信息
4. **可扩展**: 易于添加新的Agent类型

### 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Pipeline Service                      │
│                   (流程编排入口)                          │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    LangGraph Workflow                    │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│  │ Planner │─▶│ Conflict│─▶│ Writing │─▶│ Editor  │    │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │
│                                               │         │
│                                               ▼         │
│  ┌─────────┐  ┌─────────┐              ┌─────────┐     │
│  │ Summary │◀─│  Reader │◀─────────────│  (loop) │     │
│  └─────────┘  └─────────┘              └─────────┘     │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    Story Memory                          │
│              (长期记忆持久化)                             │
└─────────────────────────────────────────────────────────┘
```

## Agent架构

### 基础Agent类

```python
# app/agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseAgent(ABC):
    """Agent基类"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
    
    @abstractmethod
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行Agent逻辑
        
        Args:
            state: 当前流程状态
            
        Returns:
            更新后的状态
        """
        pass
    
    def log(self, action: str, details: Dict[str, Any] = None):
        """记录执行日志"""
        return {
            "agent": self.name,
            "action": action,
            "details": details or {}
        }
```

### Agent配置

```python
# Agent配置结构
agent_config = {
    "planner": {
        "temperature": 0.7,
        "max_tokens": 2000,
        "style": "detailed"
    },
    "writing": {
        "temperature": 0.8,
        "max_tokens": 4000,
        "style": "creative"
    },
    "editor": {
        "temperature": 0.3,
        "max_tokens": 4000,
        "focus": ["grammar", "style", "consistency"]
    }
}
```

## 核心Agent

### 1. Planner Agent

**职责**: 将大纲扩展为详细的写作计划

**输入**:
- input_text: 用户输入的大纲
- story_memory: 故事记忆

**输出**:
- plan_text: 详细的写作计划

**实现**:

```python
class PlannerAgent(BaseAgent):
    """规划Agent"""
    
    def __init__(self, llm_config: Dict = None):
        super().__init__("PlannerAgent", llm_config)
    
    def run(self, state: GraphState) -> GraphState:
        input_text = state["input_text"]
        story_memory = state["story_memory"]
        
        # 构建提示
        prompt = self._build_prompt(input_text, story_memory)
        
        # 调用LLM生成计划
        plan_text = self._call_llm(prompt)
        
        # 更新状态
        state["plan_text"] = plan_text
        state["agent_logs"].append(
            self.log("generate_plan", {"input_length": len(input_text)})
        )
        
        return state
    
    def _build_prompt(self, input_text: str, memory: StoryMemory) -> str:
        return f"""基于以下大纲和故事背景，生成详细的写作计划：

大纲：
{input_text}

世界观：
{memory.bible.world_view}

角色：
{[c.name for c in memory.characters]}

请生成包含以下内容的写作计划：
1. 章节结构
2. 场景安排
3. 角色出场顺序
4. 关键情节点
"""
```

### 2. Conflict Agent

**职责**: 分析并生成冲突建议

**输入**:
- plan_text: 写作计划

**输出**:
- conflict_suggestions: 冲突建议列表

**实现**:

```python
class ConflictAgent(BaseAgent):
    """冲突分析Agent"""
    
    def __init__(self, llm_config: Dict = None):
        super().__init__("ConflictAgent", llm_config)
    
    def run(self, state: GraphState) -> GraphState:
        plan_text = state["plan_text"]
        
        # 分析计划中的冲突点
        prompt = f"""分析以下写作计划，识别潜在的冲突机会：

{plan_text}

请提供：
1. 主要冲突点
2. 次要冲突建议
3. 冲突升级路径
"""
        
        suggestions = self._call_llm(prompt)
        
        state["conflict_suggestions"] = suggestions.split("\n")
        state["agent_logs"].append(
            self.log("analyze_conflict", {"suggestions_count": len(suggestions)})
        )
        
        return state
```

### 3. Writing Agent

**职责**: 根据计划生成初稿

**输入**:
- plan_text: 写作计划
- conflict_suggestions: 冲突建议
- story_memory: 故事记忆

**输出**:
- draft_text: 初稿文本
- trace_data: 溯源数据

**实现**:

```python
class WritingAgent(BaseAgent):
    """写作Agent"""
    
    def __init__(self, llm_config: Dict = None):
        super().__init__("WritingAgent", llm_config)
    
    def run(self, state: GraphState) -> GraphState:
        plan_text = state["plan_text"]
        conflict_suggestions = state["conflict_suggestions"]
        memory = state["story_memory"]
        
        # 构建写作提示
        prompt = self._build_writing_prompt(
            plan_text, conflict_suggestions, memory
        )
        
        # 生成初稿
        draft_text = self._call_llm(prompt)
        
        # 创建溯源数据
        trace_entry = TraceText(
            text=draft_text[:500],  # 前500字符
            source_agent=self.name,
            revisions=[]
        )
        
        # 更新状态
        state["draft_text"] = draft_text
        state["trace_data"].append(trace_entry.dict())
        state["agent_logs"].append(
            self.log("generate_draft", {"length": len(draft_text)})
        )
        
        return state
```

### 4. Editor Agent

**职责**: 润色文本，提升质量

**输入**:
- draft_text: 初稿
- constraints: 约束条件

**输出**:
- edited_text: 润色后的文本
- trace_data: 更新溯源数据

**实现**:

```python
class EditorAgent(BaseAgent):
    """编辑Agent"""
    
    def __init__(self, llm_config: Dict = None):
        super().__init__("EditorAgent", llm_config)
        self.focus_areas = ["grammar", "style", "flow", "consistency"]
    
    def run(self, state: GraphState) -> GraphState:
        draft_text = state["draft_text"]
        
        # 逐段润色
        edited_text = self._edit_text(draft_text)
        
        # 记录修改
        revision_note = f"{self.name}: 润色文本，改进表达流畅度"
        
        # 更新溯源数据
        if state["trace_data"]:
            state["trace_data"][-1]["revisions"].append(revision_note)
        
        state["edited_text"] = edited_text
        state["agent_logs"].append(
            self.log("edit_draft", {"changes": "style_improvements"})
        )
        
        return state
    
    def _edit_text(self, text: str) -> str:
        prompt = f"""请润色以下文本，重点关注：
1. 语法正确性
2. 表达流畅度
3. 段落衔接
4. 风格一致性

原文：
{text}

请输出润色后的文本："""
        
        return self._call_llm(prompt)
```

### 5. Reader Agent

**职责**: 从读者视角提供反馈

**输入**:
- edited_text: 编辑后的文本

**输出**:
- reader_feedback: 读者反馈列表

**实现**:

```python
class ReaderAgent(BaseAgent):
    """读者Agent"""
    
    def __init__(self, llm_config: Dict = None):
        super().__init__("ReaderAgent", llm_config)
    
    def run(self, state: GraphState) -> GraphState:
        edited_text = state["edited_text"]
        
        prompt = f"""请以读者视角阅读以下章节，提供反馈：

{edited_text}

请从以下维度评价：
1. 吸引力：开头是否吸引人？
2. 节奏：叙事节奏是否合适？
3. 角色：角色是否立体？
4. 冲突：冲突是否充分？
5. 改进建议
"""
        
        feedback = self._call_llm(prompt)
        
        state["reader_feedback"] = feedback.split("\n")
        state["agent_logs"].append(
            self.log("reader_feedback", {"feedback_length": len(feedback)})
        )
        
        return state
```

### 6. Summary Agent

**职责**: 生成章节总结，更新故事记忆

**输入**:
- final_text: 最终文本
- story_memory: 故事记忆

**输出**:
- summary_text: 章节总结
- story_memory: 更新后的故事记忆

**实现**:

```python
class SummaryAgent(BaseAgent):
    """总结Agent"""
    
    def __init__(self, llm_config: Dict = None):
        super().__init__("SummaryAgent", llm_config)
    
    def run(self, state: GraphState) -> GraphState:
        final_text = state["final_text"]
        memory = state["story_memory"]
        
        # 生成章节总结
        summary = self._generate_summary(final_text)
        
        # 提取角色信息
        characters = self._extract_characters(final_text)
        
        # 提取时间线事件
        events = self._extract_events(final_text)
        
        # 更新StoryMemory
        memory.chapter_summaries.append(
            ChapterSummary(
                chapter_id="current",  # 需要传入真实ID
                title="章节标题",
                summary=summary
            )
        )
        
        # 合并新角色
        existing_ids = {c.id for c in memory.characters}
        for char in characters:
            if char.id not in existing_ids:
                memory.characters.append(char)
        
        state["summary_text"] = summary
        state["agent_logs"].append(
            self.log("summarize_chapter", {"summary_length": len(summary)})
        )
        
        return state
```

## Agent编排

### LangGraph工作流

```python
# app/agents/graph.py
from langgraph.graph import StateGraph, END
from app.domain.pipeline_state import GraphState

class NovelWorkflow:
    """小说生成工作流"""
    
    def __init__(self, agents: Dict[str, BaseAgent]):
        self.agents = agents
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        # 创建工作流
        workflow = StateGraph(GraphState)
        
        # 添加节点
        workflow.add_node("planner", self.agents["planner"].run)
        workflow.add_node("conflict", self.agents["conflict"].run)
        workflow.add_node("writing", self.agents["writing"].run)
        workflow.add_node("editor", self.agents["editor"].run)
        workflow.add_node("reader", self.agents["reader"].run)
        workflow.add_node("summary", self.agents["summary"].run)
        
        # 定义边
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "conflict")
        workflow.add_edge("conflict", "writing")
        workflow.add_edge("writing", "editor")
        workflow.add_edge("editor", "reader")
        workflow.add_edge("reader", "summary")
        workflow.add_edge("summary", END)
        
        return workflow.compile()
    
    def run(self, initial_state: GraphState) -> GraphState:
        return self.workflow.invoke(initial_state)
```

### 条件分支

```python
def should_continue_editing(state: GraphState) -> str:
    """判断是否继续编辑"""
    feedback = state.get("reader_feedback", [])
    
    # 如果反馈中有重大问题，返回编辑
    for item in feedback:
        if "严重" in item or "问题" in item:
            return "editor"
    
    return "summary"

# 在工作流中使用条件边
workflow.add_conditional_edges(
    "reader",
    should_continue_editing,
    {
        "editor": "editor",
        "summary": "summary"
    }
)
```

## 状态管理

### 状态流转

```
初始状态
    │
    ▼
┌─────────────┐
│  input_text │ 用户输入的大纲
│ story_memory│ 故事记忆
└─────────────┘
    │
    ▼
Planner ──────▶ plan_text
    │
    ▼
Conflict ─────▶ conflict_suggestions
    │
    ▼
Writing ──────▶ draft_text + trace_data
    │
    ▼
Editor ───────▶ edited_text (更新trace_data)
    │
    ▼
Reader ───────▶ reader_feedback
    │
    ▼
Summary ──────▶ summary_text + 更新story_memory
    │
    ▼
最终状态 (final_text = edited_text)
```

### 状态持久化

```python
class StatePersistence:
    """状态持久化管理"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
    
    def save_checkpoint(self, state: GraphState, checkpoint_id: str):
        """保存检查点"""
        filepath = f"{self.data_dir}/checkpoints/{checkpoint_id}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    
    def load_checkpoint(self, checkpoint_id: str) -> GraphState:
        """加载检查点"""
        filepath = f"{self.data_dir}/checkpoints/{checkpoint_id}.json"
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
```

## 扩展机制

### 添加新Agent

1. 继承BaseAgent
2. 实现run方法
3. 注册到工作流

```python
# 1. 创建新Agent
class CustomAgent(BaseAgent):
    def __init__(self, config: Dict = None):
        super().__init__("CustomAgent", config)
    
    def run(self, state: GraphState) -> GraphState:
        # 实现逻辑
        state["custom_output"] = "结果"
        return state

# 2. 注册到工作流
agents = {
    "planner": PlannerAgent(),
    "custom": CustomAgent(),  # 新Agent
    "writing": WritingAgent(),
}

workflow = NovelWorkflow(agents)
```

### Agent配置化

```python
# config/agents.yaml
agents:
  planner:
    class: app.agents.planner.PlannerAgent
    config:
      temperature: 0.7
      max_tokens: 2000
  
  writing:
    class: app.agents.writing.WritingAgent
    config:
      temperature: 0.8
      style: creative
```

## 性能优化

### 并行执行

```python
# 可以并行的节点
from langgraph.graph import StateGraph

workflow = StateGraph(GraphState)

# 添加并行节点
workflow.add_node("character_analysis", character_agent)
workflow.add_node("plot_analysis", plot_agent)

# 从同一节点分支
workflow.add_edge("planner", "character_analysis")
workflow.add_edge("planner", "plot_analysis")

# 合并结果
workflow.add_edge(["character_analysis", "plot_analysis"], "writing")
```

### 缓存机制

```python
from functools import lru_cache

class CachedAgent(BaseAgent):
    """带缓存的Agent"""
    
    @lru_cache(maxsize=100)
    def _call_llm_cached(self, prompt_hash: str) -> str:
        # 实际调用LLM
        pass
```

## 相关文档

- [Agent框架设计](agent-framework-design.md)
- [数据模型](../development/data-models.md)
- [后端API参考](../development/backend-api-reference.md)
