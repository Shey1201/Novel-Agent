# Agent 框架设计文档（v0.2）

## 1. 目标与原则

- **流程统一**：通过 `NovelPipelineService` 统一触发章节生成，避免 API 层重复编排。
- **分层清晰**：按 `API -> Service -> Agent Graph -> Agent` 分层，降低耦合。
- **可扩展性**：Agent 节点职责单一，便于替换真实 LLM 或新增节点。
- **可观测性**：输出 `agent_logs` 与 `trace_data`，便于前端展示和调试。

---

## 2. 当前后端分层

- `backend/app/api/`
  - 接口定义与请求/响应映射。
  - 不承担流程编排细节。
- `backend/app/services/`
  - `pipeline_service.py`：章节生成流程入口。
  - `chapter_service.py`：草稿与 memory 持久化、导出 Word。
- `backend/app/domain/`
  - `pipeline_state.py`：GraphState 与初始状态构造。
- `backend/app/agents/`
  - 各节点 Agent 实现。
  - `graph.py` 负责将 Agent 组装成 LangGraph 工作流。
- `backend/app/memory/`
  - Story Memory 结构定义（角色、时间线、章节摘要等）。

---

## 3. 流程编排（LangGraph）

当前顺序：

1. `planner`：将输入思路扩展为计划
2. `conflict`：生成冲突建议
3. `writing`：生成草稿并写入 trace
4. `editor`：润色文本并更新 trace
5. `reader`：给出读者视角反馈
6. `summary`：生成章节总结并回写 Story Memory

返回字段核心包括：
- 文本链路：`plan_text`、`draft_text`、`edited_text`、`final_text`
- 过程信息：`conflict_suggestions`、`reader_feedback`、`agent_logs`、`trace_data`
- 记忆信息：`story_memory`（含章节 summary 更新）

---

## 4. 关键数据结构

### 4.1 GraphState（domain）
- 统一定义流程上下文，避免多处重复初始化。
- 通过 `build_initial_state(input_text, story_memory)` 构造完整初始状态。

### 4.2 StoryMemory（memory）
- `story_id`
- `bible`（world_view/rules/themes）
- `characters`
- `timeline`
- `chapter_summaries`

说明：列表字段使用 `Field(default_factory=list)`，避免共享可变默认值。

---

## 5. 典型调用链

- 前端点击 “Run Agents”
- 调用 `POST /generate_chapter`
- API 层将 `outline/story_id` 传给 `NovelPipelineService`
- service 组装初始状态，执行 graph
- 返回 `final_text + trace_data + agent_logs` 给前端
- 前端更新编辑器内容并展示 Agent 消息

---

## 6. 已知问题与下一步

1. `agents/base.py` 与 `agents/base_agent.py` 契约并存，建议收敛为一种。
2. `llm_config` 尚未真正注入 service/agent。
3. `summary` 节点 `chapter_id` 仍为占位值，需接入真实章节上下文。
4. 缺少系统化自动化测试（流程级 + 节点级）。

---

## 7. 重构建议（短期）

- 引入 `PipelineContext`（story_id/chapter_id/llm_config）统一上下文。
- 在 service 层引入 provider adapter，隔离不同模型 SDK。
- 增加最小回归测试：
  - API 响应字段完整性
  - graph 执行链路完整性
  - trace_data 非空约束
