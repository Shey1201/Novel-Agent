---
title: Novel Agent Studio 文档中心
description: 项目文档总览和导航入口
category: documentation
version: 3.0.0
status: published
---

# Novel Agent Studio 文档中心

文档目录按阅读意图重新收口：先看产品，再看架构，然后进入开发与部署资料。旧的审计、版本和迁移记录保留在 `archive/` 或部署文档中。

## 推荐阅读路径

| 如果你是... | 推荐阅读 |
|------------|----------|
| 新用户 | [产品功能总览](01-product/project-feature-overview.md) -> [用户指南](01-product/user-guide.md) |
| 开发者 | [环境搭建](03-development/setup-guide.md) -> [Agent 框架设计](02-architecture/agent-framework-design.md) |
| 前端开发 | [前端开发指南](03-development/frontend-next-tiptap-dev.md) -> [项目结构](03-development/project-structure.md) |
| 后端开发 | [后端 API 参考](03-development/backend-api-reference.md) -> [数据模型](03-development/data-models.md) |
| 运维部署 | [部署指南](04-deployment/deployment.md) -> [Railway 环境配置](04-deployment/railway-env-setup.md) |

## 目录说明

### 01-product

面向产品理解和使用说明。

- [项目功能总览](01-product/project-feature-overview.md)
- [用户指南](01-product/user-guide.md)
- [v3 升级计划](01-product/v3-upgrade-plan.md)
- [FEATURES v3](01-product/FEATURES-v3.md)

### 02-architecture

面向系统设计、Agent 编排和核心边界。

- [Agent 框架设计](02-architecture/agent-framework-design.md)
- [Agent 系统详细设计](02-architecture/agent-system.md)
- [代码审查与重构记录](02-architecture/code-review-and-refactor-plan.md)

### 03-development

面向开发、测试、接口、规范和项目结构。

- [快速开始](03-development/quickstart.md)
- [环境搭建](03-development/setup-guide.md)
- [开发者指南](03-development/developer-guide.md)
- [项目结构](03-development/project-structure.md)
- [后端 API 参考](03-development/backend-api-reference.md)
- [前端开发指南](03-development/frontend-next-tiptap-dev.md)
- [数据模型](03-development/data-models.md)
- [测试指南](03-development/testing.md)
- [贡献指南](03-development/contributing.md)
- [OpenAPI 规范](03-development/api/openapi.yaml)
- [API 设计规范](03-development/standards/api-standards.md)
- [文档编写规范](03-development/standards/documentation-standards.md)

### 04-deployment

面向数据库迁移、部署环境和上线配置。

- [数据库迁移指南](04-deployment/database-migration-guide.md)
- [迁移快速开始](04-deployment/migration-quickstart.md)
- [Railway 环境配置](04-deployment/railway-env-setup.md)

### archive

保留审计、历史版本和不适合放在主阅读路径里的资料。

- [功能审计报告](archive/audit/FUNCTIONALITY_AUDIT_REPORT.md)
- [版本记录](archive/version.md)

## 维护约定

- 新增或调整 Agent 编排时，更新 `02-architecture/` 中的 Agent 设计文档。
- 修改 API 请求或响应字段时，同步更新 OpenAPI、后端 API 参考和数据模型文档。
- 修改部署配置或数据库迁移时，更新 `04-deployment/`。
- 新增用户可见能力时，更新 `01-product/` 的功能总览和用户指南。



