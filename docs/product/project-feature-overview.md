# 项目功能点总览（当前实现）

> 本文基于当前仓库代码梳理“已实现能力（含占位能力）”。

## 1. 产品定位

Novel-Agent 是一个“多 Agent 协作写作工作台”：
- 前端提供章节编辑、约束配置、Agent 消息面板与溯源展示。
- 后端提供多 Agent 流程编排、草稿持久化与 Word 导出。

---

## 2. 已有功能点（按用户可感知维度）

## 2.1 小说与章节管理（前端）

- 小说列表展示与切换。
- 小说标题可行内编辑。
- 小说可删除。
- 支持新增章节并自动切换到新章节。
- 章节列表可切换当前编辑章节。

对应位置：`frontend/src/components/layout/Sidebar.tsx` + `frontend/src/store/novelStore.ts`。

## 2.2 富文本编辑与保存（前端）

- 使用 Tiptap 提供正文编辑能力。
- 编辑内容会回写到本地状态（Zustand 持久化）。
- 章节切换时会自动加载对应章节内容。

对应位置：`frontend/src/components/editor/TiptapEditor.tsx`。

## 2.3 一键运行多 Agent（前后端联动）

- 顶栏触发“Run Agents”。
- 前端将当前章节文本作为 `outline` 调用后端 `POST /generate_chapter`。
- 后端按固定链路执行：`Planner -> Conflict -> Writing -> Editor -> Reader -> Summary`。
- 返回 `final_text/trace_data/agent_logs`，前端更新正文与消息。

对应位置：`TopBar.tsx`、`TiptapEditor.tsx`、`backend/app/agents/graph.py`、`backend/app/api/generate_chapter.py`。

## 2.4 Agent Room（AI 策划室）

- 支持在 Room 中通过命令与后端 Agent 编排服务对话：
  - `/start chapter N`（自动注入最近章节上下文）
  - `/generate outline`、`/plan`、`/outline`
  - `/world`、`/world approve`
  - `/write`、`/continue`、`/rewrite`、`/review`
- 已接入后端 `POST /api/agent/chat`，不再是前端本地模拟。
- 对于写作类命令会将结果直接回写当前章节编辑区。

对应位置：`frontend/src/components/layout/AgentPanel.tsx`、`backend/app/api/agent_routes.py`、`backend/app/services/agent_chat_service.py`。

## 2.5 文本溯源显示（Trace）

- 后端 `WritingAgent` 生成初始 `trace_data`。
- 后端 `EditorAgent` 更新 `revisions` 形成修改历史。
- 前端选中文本后展示 `source_agent` 与修订记录气泡。

对应位置：`backend/app/agents/writing_agent.py`、`editor_agent.py`、`frontend/src/components/editor/TiptapEditor.tsx`。

## 2.6 写作模式、约束与 Agent 参数（前端配置）

- 写作模式：`manual / ai-assisted / ai-writer`。
- 全局约束列表：增删能力。
- Agent 配置参数（如节奏、冲突强度、文风等）可在状态中维护。

说明：这些配置目前已能在前端维护并随请求发送，但后端尚未完整消费全部字段。

对应位置：`frontend/src/store/novelStore.ts`、`TopBar.tsx`、`TiptapEditor.tsx`。

## 2.7 草稿持久化与导出（后端）

- 保存草稿：`POST /api/novel/draft`。
- 读取草稿：`GET /api/novel/draft`。
- 导出 Word：`GET /api/novel/export/word`。
- 数据保存于 `backend/data/<novel_or_story_id>/`。

对应位置：`backend/app/api/novel_routes.py`、`backend/app/services/chapter_service.py`。

## 2.8 Story Memory（后端）

- 维护故事层长期信息结构：设定、角色、时间线、章节摘要。
- 在 `summary` 节点会将章节总结写入 memory 文件。

对应位置：`backend/app/memory/story_memory.py`、`backend/app/agents/graph.py`。

---

## 3. 已实现 API 能力清单

- `GET /health`：健康检查。
- `POST /api/novel/generate`：简版完整流程生成（返回 `final_text`）。
- `POST /generate_chapter`：完整版流程生成（返回过程字段与日志）。
- `POST /api/novel/pipeline`：简化流水线（Writing->Editor->Conflict）。
- `POST /api/novel/draft`：保存草稿。
- `GET /api/novel/draft`：读取草稿。
- `GET /api/novel/export/word`：导出 Word。

---

## 4. 当前“真能力 vs 占位能力”

### 真能力（已可直接使用）

- 前端多章节编辑与本地持久化。
- 后端流程编排与接口联调。
- 草稿读写与 Word 导出。
- 基础 trace 展示。

### 占位能力（有框架，待增强）

- Agent 的智能生成逻辑仍以 mock/prompt 占位为主。
- `llm_config` / `agent_configs` / `constraints` 未在后端深度生效。
- Agent Room 命令流主要是前端模拟，不是后端多 Agent 会话系统。

---

## 5. 建议优先级（功能演进）

1. **P0：打通真实 LLM 注入**
   - 在 `NovelPipelineService` 中消费 `llm_config` 并分发给各 Agent。
2. **P0：统一命令入口**
   - 让 Agent Room 的 `/generate` 等命令走后端统一编排，而非前端模拟。
3. **P1：上下文补全**
   - 在流程中接入 `chapter_id`、`agent_configs`、`constraints` 作为实际输入。
4. **P1：测试补齐**
   - 增加 API 与 graph 节点回归测试，保障重构稳定。

---

## 6. 快速结论

项目已经具备“可跑通”的多 Agent 写作产品雏形：
- UI、状态管理、编排服务、接口、导出链路都已就位；
- 但“智能程度”和“配置生效程度”仍处于可扩展阶段，下一步重点是把占位逻辑替换为真实模型能力。


## 7. Agent Room 新定位（已实现）

- Agent Room 作为 **AI 策划室**，不再只是前端本地模拟。
- 当前已接入后端 `POST /api/agent/chat`，支持命令：
  - `/plan` `/outline` `/world`
  - `/write` `/continue`
  - `/rewrite` `/style`
  - `/review`
  - `/world approve`
- 世界观确认后会写入 Story Bible 并锁定（`world_locked=true`）。
