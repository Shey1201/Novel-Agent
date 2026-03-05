## Agent 框架设计文档（版本 0.1）

### 1. 设计目标

- **统一接口**：所有 Agent 通过统一的 `BaseAgent` 接口对外暴露 `run(input_data)` 能力，便于 Controller 与 LangGraph 集成。
- **可插拔 LLM**：`llm` 作为构造参数传入，支持 OpenAI / DeepSeek / Claude / 本地模型等任意实现。
- **易扩展**：新增 Agent（如 Planner / Reader / Summary）只需继承基类并实现 `run`。

### 2. 目录结构

- `app/agents/`
  - `base_agent.py`：统一的 Agent 基类。
  - `writing_agent.py`：写作 Agent。
  - `editor_agent.py`：编辑 Agent。
  - `conflict_agent.py`：冲突 Agent。
  - `graph.py`：当前 LangGraph 简易 Flow（后续会接入具体 Agent）。

### 3. BaseAgent 设计

文件：`app/agents/base_agent.py`

```python
class BaseAgent:
    def __init__(self, name: str, llm: Any):
        self.name = name
        self.llm = llm

    def run(self, input_data: Any) -> Any:
        raise NotImplementedError("Subclasses must implement run()")
```

- **`name`**：Agent 标识，用于日志与前端显示。
- **`llm`**：任意可调用的大模型客户端（约定为 `llm(prompt) -> str` 或更复杂的接口）。
- **`run(input_data)`**：
  - 统一入口，输入/输出由具体 Agent 自行定义清晰的字段约定。
  - 在 LangGraph 中会以 `state` 的一部分传入传出。

### 4. 三个核心 Agent 约定

#### 4.1 WritingAgent（写作 Agent）

文件：`app/agents/writing_agent.py`

- **输入**：`{"text": str, ...}`，其中 `text` 通常为剧情大纲/指令。
- **输出**：
  - `draft_text: str`：章节草稿文本。
  - `agent: str`：固定为 `"writing-agent"`。
- 占位逻辑：
  - 若 `llm` 可调用：`llm(text)`。
  - 否则：简单加前缀 `"[WritingAgent draft]\n"`。

#### 4.2 EditorAgent（编辑 Agent）

文件：`app/agents/editor_agent.py`

- **输入**：`{"draft_text": str, ...}`。
- **输出**：
  - `edited_text: str`：润色后的文本。
  - `agent: str`：`"editor-agent"`。
- 占位逻辑：
  - 若 `llm` 可调用：对 `draft_text` 做一次调用。
  - 否则：加前缀 `"[EditorAgent polished]\n"`。

#### 4.3 ConflictAgent（冲突 Agent）

文件：`app/agents/conflict_agent.py`

- **输入**：优先使用 `edited_text`，否则回退到 `draft_text`。
- **输出**：
  - `conflict_suggestions: List[str]`：冲突/反转建议列表。
  - `agent: str`：`"conflict-agent"`。
- 占位逻辑：
  - 若 `llm` 可调用：以文本为输入，返回的结果包在列表中。
  - 否则：返回两条固定的示例建议。

### 5. 与 LangGraph / Controller 的关系（当前阶段）

- 当前 `graph.py` 中使用的是简单的 `echo_node`，仅用于验证 LangGraph 流程。
- 后续演进方向：
  1. 将 `echo_node` 替换为调用 `WritingAgent`。
  2. 在 Flow 中追加 `EditorAgent`、`ConflictAgent` 节点，形成线性或并行链路。
  3. 由 Controller 汇总各 Agent 的输出并写回统一的 `GraphState`。

### 6. 扩展新 Agent 的规范

新增 Agent 时，应遵循以下步骤：

1. 在 `app/agents/` 下新增文件，例如 `planner_agent.py`。
2. 继承 `BaseAgent`：

   ```python
   class PlannerAgent(BaseAgent):
       def __init__(self, llm: Any = None):
           super().__init__(name="planner-agent", llm=llm)

       def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
           ...
   ```

3. 明确文档中定义：
   - 输入字段约定（从 `GraphState` 读取哪些 key）。
   - 输出字段约定（写回哪些 key）。
4. 在 LangGraph Flow 中注册为节点，并在 Controller 中组合调用顺序。

