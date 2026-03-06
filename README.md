# Novel Agent Studio

一个基于多Agent协作的智能小说创作工作台。

## 项目简介

Novel Agent Studio 是一个创新的AI驱动小说创作平台，通过多个专业Agent的协作，帮助作者从构思到成稿的全流程创作。系统采用模块化设计，支持可扩展的Agent架构，提供丰富的写作辅助功能。

## 核心特性

- **多Agent协作写作**：Planner、Conflict、Writing、Editor、Reader、Summary等多个Agent协同工作
- **智能章节生成**：基于大纲自动生成完整章节内容
- **文本溯源追踪**：记录文本生成和修改历史，支持溯源展示
- **世界观管理**：统一的故事设定管理，确保长篇小说一致性
- **Agent Room**：支持命令式交互的AI策划室
- **富文本编辑**：基于Tiptap的专业写作编辑器
- **草稿持久化**：自动保存和版本管理
- **Word导出**：一键导出为Word文档

## 技术架构

### 后端技术栈
- **框架**: FastAPI + Python 3.x
- **Agent编排**: LangGraph
- **LLM集成**: LangChain + OpenAI
- **数据模型**: Pydantic
- **持久化**: 文件系统存储

### 前端技术栈
- **框架**: Next.js 16 + React 19
- **语言**: TypeScript 5
- **样式**: Tailwind CSS 4
- **编辑器**: Tiptap
- **状态管理**: Zustand

## 快速开始

### 环境要求
- Python 3.9+
- Node.js 20+
- npm 或 yarn

### 安装与运行

1. 克隆项目
```bash
git clone <repository-url>
cd Novel-Agent-Studio
```

2. 启动后端服务
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. 启动前端服务
```bash
cd frontend
npm install
npm run dev
```

4. 访问应用
打开浏览器访问 `http://localhost:3000`

## 项目结构

```
Novel-Agent-Studio/
├── backend/              # 后端服务
│   ├── app/
│   │   ├── agents/       # Agent实现
│   │   ├── api/          # API路由
│   │   ├── core/         # 核心配置
│   │   ├── domain/       # 领域模型
│   │   ├── memory/       # 记忆管理
│   │   ├── models/       # 数据模型
│   │   └── services/     # 业务服务
│   └── requirements.txt
├── frontend/             # 前端应用
│   ├── src/
│   │   ├── app/          # 页面路由
│   │   ├── components/   # 组件
│   │   └── store/        # 状态管理
│   └── package.json
└── docs/                 # 项目文档
    ├── architecture/     # 架构设计
    ├── development/      # 开发文档
    └── product/          # 产品文档
```

## 文档导航

- [架构设计文档](docs/architecture/agent-framework-design.md) - 了解系统架构和Agent编排
- [后端API参考](docs/development/backend-api-reference.md) - API接口详细说明
- [前端开发指南](docs/development/frontend-next-tiptap-dev.md) - 前端开发规范
- [功能总览](docs/product/project-feature-overview.md) - 功能特性说明

## Agent工作流程

```
Planner -> Conflict -> Writing -> Editor -> Reader -> Summary
```

1. **Planner**: 将大纲扩展为详细写作计划
2. **Conflict**: 生成冲突建议
3. **Writing**: 生成初稿并创建溯源数据
4. **Editor**: 润色文本并更新修改历史
5. **Reader**: 提供读者视角反馈
6. **Summary**: 生成章节总结并更新故事记忆

## 开发规范

- 后端代码遵循PEP 8规范
- 前端代码使用ESLint进行代码检查
- 提交前请运行相关测试
- 新增功能需同步更新文档

## 贡献指南

欢迎提交Issue和Pull Request。在贡献代码前，请阅读[贡献指南](docs/development/contributing.md)。

## 许可证

MIT License

## 联系方式

如有问题或建议，欢迎通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至项目维护者

---

> **注意**: 本项目处于持续开发中，API和功能可能会发生变化。请关注文档更新。
