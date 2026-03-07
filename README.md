# Novel Agent Studio

一个基于多Agent协作的智能小说创作工作台。

## 项目简介

Novel Agent Studio 是一个创新的AI驱动小说创作平台，通过多个专业Agent的协作，帮助作者从构思到成稿的全流程创作。系统采用模块化设计，支持可扩展的Agent架构，提供丰富的写作辅助功能。

## 核心特性

### 写作功能
- **多Agent协作写作**：Planner、Conflict、Writing、Editor、Reader、Summary等多个Agent协同工作
- **智能章节生成**：基于大纲自动生成完整章节内容
- **文本溯源追踪**：记录文本生成和修改历史，支持溯源展示
- **富文本编辑**：基于Tiptap的专业写作编辑器，支持协作编辑
- **草稿持久化**：自动保存和版本管理
- **Word导出**：一键导出为Word文档(.docx)，支持中文

### 管理功能
- **世界观管理**：统一的故事设定管理，确保长篇小说一致性
- **角色管理**：完整的角色档案和关系网络
- **故事资源**：角色、世界设定、势力、地点、时间线管理
- **小说分类**：支持自定义分类和颜色标记
- **回收站**：删除的小说可恢复，防止误删

### 交互功能
- **Agent Room**：支持命令式交互的AI策划室
- **实时协作**：基于Yjs的多人协作编辑
- **流式写作**：AI实时生成内容，边写边看
- **讨论面板**：Agent之间的讨论和决策过程可视化

## 技术架构

### 后端技术栈
- **框架**: FastAPI + Python 3.9+
- **Agent编排**: LangGraph
- **LLM集成**: LangChain + OpenAI
- **数据模型**: Pydantic
- **文档生成**: python-docx
- **向量存储**: Qdrant (可选，支持内存回退)
- **图数据库**: Neo4j (可选，支持内存回退)

### 前端技术栈
- **框架**: Next.js 16 + React 19
- **语言**: TypeScript 5
- **样式**: Tailwind CSS 4
- **编辑器**: Tiptap + TipTap Collaboration
- **状态管理**: Zustand + persist中间件
- **协作**: Yjs + y-websocket

## 快速开始

### 环境要求
- Python 3.9+
- Node.js 20+
- npm 或 yarn

### 安装与运行

#### 方式一：手动启动

1. 克隆项目
```bash
git clone <repository-url>
cd Novel-Agent-Studio
```

2. 配置环境变量
```bash
# 在 backend 目录创建 .env 文件
cd backend
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

3. 启动后端服务
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. 启动前端服务
```bash
cd frontend
npm install
npm run dev
```

5. 访问应用
打开浏览器访问 `http://localhost:3000`

#### 方式二：使用PowerShell脚本

```powershell
# 在项目根目录运行
.\start-services.ps1
```

## 项目结构

```
Novel-Agent-Studio/
├── backend/              # 后端服务
│   ├── app/
│   │   ├── agents/       # Agent实现 
│   │   ├── api/          # API路由 
│   │   ├── collaboration/# 协作功能
│   │   ├── controller/   # 控制器
│   │   ├── core/         # 核心功能
│   │   ├── domain/       # 领域模型
│   │   ├── memory/       # 记忆管理
│   │   ├── models/       # 数据模型
│   │   ├── services/     # 业务服务
│   │   └── workflow/     # 工作流编排
│   ├── tests/            # 测试套件
│   │   ├── unit/         # 单元测试
│   │   └── integration/  # 集成测试
│   ├── data/             # 数据存储目录
│   └── requirements.txt  # Python依赖
├── frontend/             # 前端应用
│   ├── src/
│   │   ├── app/          # Next.js页面路由
│   │   ├── components/   # React组件
│   │   │   ├── editor/   # 编辑器组件
│   │   │   ├── layout/   # 布局组件
│   │   │   ├── visualization/ # 可视化组件
│   │   │   ├── workspace/# 工作区组件
│   │   │   └── writers-room/  # 写作室组件
│   │   └── store/        # Zustand状态管理
│   ├── public/           # 静态资源
│   └── package.json      # Node.js依赖
├── tests/                # 端到端测试
│   └── e2e/              # E2E测试
├── docs/                 # 项目文档
│   ├── architecture/     # 架构设计文档
│   ├── development/      # 开发文档
│   ├── product/          # 产品文档
│   └── standards/        # 规范文档
└── docker-compose.yml    # Docker编排配置
```

## 功能模块详解

### 1. Agent系统
- **PlannerAgent**: 规划章节结构
- **WritingAgent**: 生成章节内容
- **EditorAgent**: 润色和修改
- **ReaderAgent**: 读者视角反馈
- 以及更多...

### 2. API模块
- `/api/novel/*` - 小说管理
- `/api/agent/*` - Agent交互
- `/api/assets/*` - 资源管理
- `/api/download/*` - 下载功能
- 以及更多...

### 3. 记忆系统 (三层架构)
- **L1 Short Memory**: 短期记忆，最近章节
- **L2 Semantic Memory**: 语义记忆，向量检索
- **L3 Knowledge Graph**: 知识图谱，角色关系

## 文档导航

### 架构文档
- [架构设计](docs/architecture/agent-framework-design.md) - 系统架构和Agent编排
- [Agent系统](docs/architecture/agent-system.md) - Agent详细设计

### 开发文档
- [后端API参考](docs/development/backend-api-reference.md) - API接口详细说明
- [前端开发指南](docs/development/frontend-next-tiptap-dev.md) - 前端开发规范
- [数据模型](docs/development/data-models.md) - 数据结构设计
- [测试指南](docs/development/testing.md) - 测试编写规范
- [部署指南](docs/development/deployment.md) - 部署流程

## 许可证

[MIT](LICENSE)

**Novel Agent Studio** - 让AI成为您的创作伙伴
