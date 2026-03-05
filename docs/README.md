# Novel-Agent 文档总览

本目录用于沉淀项目的架构设计、开发流程、接口规范与重构记录。

## 文档导航

- 架构设计
  - `architecture/agent-framework-design.md`：多 Agent 框架、流程编排与分层边界。
  - `architecture/code-review-and-refactor-plan.md`：最近一次代码审查结论与落地改造记录。
- 开发文档
  - `development/frontend-next-tiptap-dev.md`：前端（Next.js + Tiptap）开发指南。
  - `development/backend-api-reference.md`：后端 API 参考与调用示例。
- 产品梳理
  - `product/project-feature-overview.md`：项目现阶段功能点总览（真能力/占位能力）。

## 推荐阅读顺序

1. 先看 `architecture/agent-framework-design.md`，了解项目当前的运行链路。
2. 再看 `development/backend-api-reference.md`，理解前后端接口契约。
3. 前端开发时配合 `development/frontend-next-tiptap-dev.md`。
4. 追踪演进时阅读 `architecture/code-review-and-refactor-plan.md`。
5. 需要快速了解能力边界时阅读 `product/project-feature-overview.md`。

## 文档维护约定

- 每次新增 Agent 或调整编排顺序时：
  - 同步更新 `architecture/agent-framework-design.md` 的“流程图/节点职责”。
- 每次修改 API 请求或响应字段时：
  - 同步更新 `development/backend-api-reference.md`。
- 每次重构（分层、模块迁移）时：
  - 追加/更新 `architecture/code-review-and-refactor-plan.md`。
- 每次新增用户可见能力时：
  - 同步更新 `product/project-feature-overview.md`。
