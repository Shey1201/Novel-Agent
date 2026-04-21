# 代码审查与架构重梳理（迭代记录）

## 1. 审查问题清单

1. **编排初始化逻辑重复**
   - `/api/novel/generate` 与 `/generate_chapter` 重复手工构建初始状态。
2. **流程职责下沉不足**
   - API 层直接持有 graph 编译与执行逻辑，职责过重。
3. **模型声明不一致**
   - `ChapterDraftResponse` 早期未声明 `source`，与 service 实际返回不一致。
4. **可变默认值风险**
   - 部分 Pydantic 模型列表字段采用字面量默认值。
5. **文档覆盖不足**
   - 缺少可直接用于联调的后端 API 参考。
   - 前端文档存在历史路径与运行说明不一致问题。

---

## 2. 已完成改造

### 2.1 架构层

- 新增 `app/domain/pipeline_state.py`：统一 GraphState 与初始状态构造。
- 新增 `app/services/pipeline_service.py`：统一章节生成流程入口。
- API 层改为“请求/响应映射 + service 调用”，减少编排耦合。

### 2.2 模型层

- `StoryMemory` / `StoryBible` / `TraceText` 使用 `Field(default_factory=...)`。
- `ChapterDraftResponse` 增加 `source` 字段，统一契约。

### 2.3 文档层（本次补充）

- 重写 `architecture/agent-framework-design.md`，与当前代码一致。
- 重写 `development/frontend-next-tiptap-dev.md`，更新真实运行与交互链路。
- 新增 `development/backend-api-reference.md`，补齐接口示例与排查指引。
- 新增 `docs/README.md`，形成文档入口与维护约定。

---

## 3. 当前架构摘要

```text
Frontend (Next.js)
  -> API (FastAPI Router)
     -> NovelPipelineService
        -> LangGraph (planner -> conflict -> writing -> editor -> reader -> summary)
           -> StoryMemory persistence / Draft persistence
```

---

## 4. 剩余待办（建议优先级）

### P0

1. 合并 `agents/base.py` 与 `agents/base_agent.py`，统一同步/异步规范。
2. 将 `llm_config` 贯穿到 service 与 agent，提供 provider adapter。

### P1

3. 为 graph 节点与 API 增加自动化测试。
4. 为 `summary` 节点注入真实 `chapter_id`，移除硬编码。

### P2

5. 将 API 地址从前端组件中抽离为统一配置。
6. 增加端到端联调文档（含数据目录结构说明）。
