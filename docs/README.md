---
title: Novel Agent Studio 文档中心
description: 项目文档总览和导航入口
category: documentation
version: 2.0.0
author: Novel Agent Studio Team
created: 2023-12-01
updated: 2024-01-15
status: published
---

# Novel Agent Studio 文档中心

> **版本**: v2.0.0 | **最后更新**: 2024-01-15 | **状态**: ✅ 已发布

欢迎来到 Novel Agent Studio 文档中心！本文档中心提供项目的完整技术文档、开发指南和使用说明。

## 📚 文档导航

### 🎯 快速开始

| 如果你是... | 推荐阅读 |
|------------|----------|
| **新用户** | [产品总览](product/project-feature-overview.md) → [用户指南](product/user-guide.md) |
| **开发者** | [环境搭建](development/setup-guide.md) → [架构总览](architecture/agent-framework-design.md) |
| **运维人员** | [部署指南](development/deployment.md) → [API 文档](api/openapi.yaml) |
| **贡献者** | [贡献指南](development/contributing.md) → [文档规范](standards/documentation-standards.md) |

---

### 📋 规范标准 (Standards)

定义项目的文档规范、API 规范和代码规范。

| 文档 | 说明 | 版本 |
|------|------|------|
| [文档编写规范](standards/documentation-standards.md) | 文档格式、版本管理、维护流程 | v1.0.0 |
| [API 设计规范](standards/api-standards.md) | RESTful API 设计标准和最佳实践 | v1.0.0 |

---

### 🔌 接口文档 (API)

完整的 API 接口规范和调用示例。

| 文档 | 说明 | 格式 |
|------|------|------|
| [OpenAPI 规范](api/openapi.yaml) | 完整的 OpenAPI 3.0 规范文档 | YAML |

**主要接口分类**:

- **系统接口**: `/health` - 健康检查
- **生成接口**: `/generate_chapter`, `/api/novel/generate` - 章节生成
- **小说管理**: `/api/novel/draft`, `/api/novel/export/word` - 草稿和导出
- **世界观管理**: `/api/world/debate`, `/api/world/approve` - 世界观设定
- **Agent Room**: `/api/agent/chat` - 实时对话
- **技能管理**: `/api/skills` - 技能系统

---

### 🏗️ 架构设计 (Architecture)

系统架构设计文档和决策记录。

| 文档 | 说明 | 版本 | 状态 |
|------|------|------|------|
| [Agent 框架设计](architecture/agent-framework-design.md) | 多 Agent 框架、流程编排与分层边界 | v0.2 | ✅ |
| [Agent 系统详细设计](architecture/agent-system.md) | Agent 实现细节、状态管理、扩展机制 | v1.0 | ✅ |
| [代码审查与重构记录](architecture/code-review-and-refactor-plan.md) | 代码审查结论与改造记录 | v1.0 | ✅ |

**架构概览**:

```
Frontend (Next.js)
  │
  ▼
API Layer (FastAPI)
  │
  ▼
Service Layer
  │
  ├── NovelPipelineService
  │   └── LangGraph Workflow
  │       ├── Planner Agent
  │       ├── Conflict Agent
  │       ├── Writing Agent
  │       ├── Editor Agent
  │       ├── Reader Agent
  │       └── Summary Agent
  │
  ├── ChapterService
  └── WorldService
  │
  ▼
Memory Layer
  ├── StoryMemory
  ├── SkillMemory
  └── Draft Storage
```

---

### 💻 开发文档 (Development)

开发环境搭建、编码规范和部署指南。

#### 环境搭建

| 文档 | 说明 | 版本 |
|------|------|------|
| [开发环境搭建指南](development/setup-guide.md) | 完整的开发环境配置步骤 | v1.0.0 |
| [后端 API 参考](development/backend-api-reference.md) | 后端接口详细说明和调用示例 | v1.0.0 |
| [前端开发指南](development/frontend-next-tiptap-dev.md) | Next.js + Tiptap 开发指南 | v1.0.0 |

#### 数据与模型

| 文档 | 说明 | 版本 |
|------|------|------|
| [数据模型文档](development/data-models.md) | StoryMemory、Pipeline State、技能系统 | v1.0.0 |

#### 质量保障

| 文档 | 说明 | 版本 |
|------|------|------|
| [测试指南](development/testing.md) | 测试策略、单元测试、集成测试、E2E 测试 | v1.0.0 |
| [贡献指南](development/contributing.md) | 贡献流程、代码规范、提交规范 | v1.0.0 |

#### 部署运维

| 文档 | 说明 | 版本 |
|------|------|------|
| [部署指南](development/deployment.md) | 生产环境部署、Docker、监控、备份 | v1.0.0 |

---

### 📖 产品文档 (Product)

产品功能说明和用户使用指南。

| 文档 | 说明 | 版本 | 目标读者 |
|------|------|------|----------|
| [项目功能总览](product/project-feature-overview.md) | 现阶段功能点总览 | v1.0 | 所有人 |
| [用户指南](product/user-guide.md) | 详细的使用教程和常见问题 | v1.0 | 用户 |

---

## 📊 文档统计

### 当前版本 (v2.0.0)

| 分类 | 文档数 | 状态 |
|------|--------|------|
| Standards | 2 | ✅ 完整 |
| API | 1 | ✅ 完整 |
| Architecture | 3 | ✅ 完整 |
| Development | 7 | ✅ 完整 |
| Product | 2 | ✅ 完整 |
| **总计** | **15** | **✅ 已发布** |

---

## 🔄 版本历史

查看完整的 [版本记录](VERSION.md)。

### 最新变更 (v2.0.0)

#### 🆕 新增
- 创建完整的 OpenAPI 规范文档
- 新增文档编写规范标准
- 新增项目根目录 README
- 新增开发环境搭建、数据模型、部署、测试、贡献指南
- 新增 Agent 系统详细设计文档
- 新增用户指南

#### 🔄 改进
- 重构 docs 目录结构
- 统一文档格式和版本管理
- 完善 API 接口说明

---

## 📝 文档维护

### 文档状态标记

- ✅ **已发布** - 文档已完成，可供使用
- 📝 **草稿** - 文档正在编写中
- 🔄 **更新中** - 文档正在更新
- 🗑️ **已废弃** - 文档已废弃，请查看最新版本

### 维护约定

1. **每次新增 Agent 或调整编排顺序时**:
   - 更新 [Agent 框架设计](architecture/agent-framework-design.md)
   - 更新 [Agent 系统详细设计](architecture/agent-system.md)
   - 更新 [OpenAPI 规范](api/openapi.yaml)

2. **每次修改 API 请求或响应字段时**:
   - 更新 [OpenAPI 规范](api/openapi.yaml)
   - 更新 [后端 API 参考](development/backend-api-reference.md)
   - 更新 [数据模型文档](development/data-models.md)

3. **每次重构（分层、模块迁移）时**:
   - 追加/更新 [代码审查与重构记录](architecture/code-review-and-refactor-plan.md)
   - 更新相关架构文档

4. **每次新增用户可见能力时**:
   - 更新 [项目功能总览](product/project-feature-overview.md)
   - 更新 [用户指南](product/user-guide.md)

5. **每次修改部署相关配置时**:
   - 更新 [部署指南](development/deployment.md)

### 编写新文档

1. 复制 [文档模板](assets/templates/document-template.md)
2. 参考 [文档编写规范](standards/documentation-standards.md)
3. 在本文档中添加导航链接
4. 更新 [版本记录](VERSION.md)

---

## 🤝 参与贡献

我们欢迎社区成员参与文档贡献！

### 贡献方式

- 🐛 **报告问题**: 发现文档错误或过时
- 📝 **提交改进**: 完善现有文档内容
- 🆕 **新增文档**: 补充缺失的文档
- 🌐 **多语言支持**: 翻译文档

### 贡献流程

1. 阅读 [贡献指南](development/contributing.md)
2. 遵循 [文档编写规范](standards/documentation-standards.md)
3. 提交 Pull Request

---

## 📞 获取帮助

- 📧 **问题反馈**: 提交 GitHub Issue
- 💬 **技术讨论**: 参与 GitHub Discussions
- 📚 **更多资源**: 查看 [项目 Wiki](https://github.com/your-repo/wiki)

---

> **维护者**: Novel Agent Studio Team  
> **许可证**: MIT License  
> **最后更新**: 2024-01-15
