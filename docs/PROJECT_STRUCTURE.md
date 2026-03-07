# 项目结构详解

本文档详细说明 Novel Agent Studio 的完整项目结构和各模块职责。

## 目录结构概览

```
Novel-Agent-Studio/
├── backend/                    # 后端服务 (Python/FastAPI)
│   ├── app/                    # 应用代码
│   │   ├── agents/             # Agent系统 (15个Agent)
│   │   ├── api/                # API路由层 (15+模块)
│   │   ├── collaboration/      # 协作功能
│   │   ├── controller/         # 控制器层
│   │   ├── core/               # 核心功能 (25+模块)
│   │   ├── domain/             # 领域模型
│   │   ├── memory/             # 记忆系统 (10模块)
│   │   ├── models/             # 数据模型
│   │   ├── services/           # 业务服务层
│   │   └── workflow/           # 工作流编排
│   ├── tests/                  # 测试套件
│   │   ├── integration/        # 集成测试
│   │   └── unit/               # 单元测试
│   ├── data/                   # 数据存储目录
│   ├── pytest.ini              # Pytest配置
│   └── requirements.txt        # Python依赖
│
├── frontend/                   # 前端应用 (Next.js/React)
│   ├── src/
│   │   ├── app/                # Next.js页面路由
│   │   ├── components/         # React组件
│   │   │   ├── editor/         # 编辑器组件
│   │   │   ├── layout/         # 布局组件
│   │   │   ├── story-bible/    # 故事设定组件
│   │   │   ├── visualization/  # 可视化组件
│   │   │   ├── workspace/      # 工作区组件
│   │   │   └── writers-room/   # 写作室组件
│   │   └── store/              # Zustand状态管理
│   ├── public/                 # 静态资源
│   ├── jest.config.js          # Jest测试配置
│   └── package.json            # Node.js依赖
│
├── tests/                      # 端到端测试
│   └── e2e/                    # E2E测试
│
├── docs/                       # 项目文档
│   ├── architecture/           # 架构设计文档
│   ├── development/            # 开发文档
│   ├── product/                # 产品文档
│   └── standards/              # 规范文档
│
├── scripts/                    # 脚本工具
│   ├── start-services.ps1      # 启动脚本
│   └── test-api.ps1            # API测试脚本
├── docker-compose.yml          # Docker编排
└── README.md                   # 项目说明
```

## 后端详细结构

### 1. Agent系统 (`app/agents/`)

| 文件 | 职责 | 说明 |
|------|------|------|
| `base.py` | Agent基类 | 定义Agent接口和通用功能 |
| `base_agent.py` | 基础Agent实现 | 可复用的Agent基础功能 |
| `planner_agent.py` | 规划Agent | 规划章节结构和大纲 |
| `conflict_agent.py` | 冲突Agent | 设计冲突和悬念 |
| `writing_agent.py` | 写作Agent | 生成章节内容 |
| `editor_agent.py` | 编辑Agent | 润色和修改文本 |
| `reader_agent.py` | 读者Agent | 读者视角反馈 |
| `summary_agent.py` | 摘要Agent | 生成内容摘要 |
| `consistency_agent.py` | 一致性Agent | 检查设定一致性 |
| `critic_agent.py` | 批评Agent | 批判性分析 |
| `memory_agent.py` | 记忆Agent | 管理故事记忆 |
| `logic_agent.py` | 逻辑Agent | 逻辑推理和验证 |
| `strategist_agent.py` | 策略Agent | 策略规划 |
| `chapter_summary_agent.py` | 章节摘要Agent | 生成章节摘要 |
| `graph.py` | Agent图 | Agent编排和连接 |

### 2. API路由层 (`app/api/`)

| 文件 | 路由前缀 | 功能 |
|------|----------|------|
| `novel_routes.py` | `/api/novel` | 小说管理、草稿保存 |
| `download_api.py` | `/download` | 下载功能 (Word导出) |
| `agent_routes.py` | `/api/agent` | Agent交互 |
| `asset_routes.py` | `/api/assets` | 资源管理 |
| `skills.py` | `/api/skills` | 技能系统 |
| `world_routes.py` | `/api/world` | 世界观管理 |
| `stream_api.py` | `/api/stream` | 流式生成 |
| `writers_room_api.py` | `/api/writers-room` | 写作室 |
| `agent_room_api.py` | `/api/agent-room` | Agent房间 |
| `analysis_api.py` | `/api/analysis` | 文本分析 |
| `analytics_api.py` | `/api/analytics` | 数据统计 |
| `cache_api.py` | `/api/cache` | 缓存管理 |
| `collaboration_api.py` | `/api/collaboration` | 协作功能 |
| `system_settings_api.py` | `/api/system` | 系统设置 |
| `advanced_features_api.py` | `/api/advanced` | 高级功能 |
| `generate_chapter.py` | `/api/generate` | 章节生成 |

### 3. 核心功能 (`app/core/`)

| 文件 | 功能 |
|------|------|
| `llm.py` | LLM配置和管理 |
| `config.py` | 应用配置 |
| `agent_discussion_engine.py` | Agent讨论引擎 |
| `agent_reasoning_engine.py` | Agent推理引擎 |
| `narrative_intelligence_engine.py` | 叙事智能引擎 |
| `universal_logic_engine.py` | 通用逻辑引擎 |
| `symbolic_logic_engine.py` | 符号逻辑引擎 |
| `discussion_controller.py` | 讨论控制器 |
| `streaming_writer.py` | 流式写作 |
| `streaming_optimizer.py` | 流式优化 |
| `token_optimizer.py` | Token优化 |
| `token_budget_manager.py` | Token预算管理 |
| `token_compressor_enhanced.py` | Token压缩 |
| `cache_manager.py` | 缓存管理 |
| `cache_predictor.py` | 缓存预测 |
| `incremental_cache.py` | 增量缓存 |
| `context_compressor.py` | 上下文压缩 |
| `foreshadowing.py` | 伏笔管理 |
| `foreshadowing_enhanced.py` | 增强伏笔 |
| `reflexion.py` | 反思机制 |
| `author_decision_system.py` | 作者决策系统 |
| `conflict_analyzer.py` | 冲突分析 |
| `text_traceability.py` | 文本溯源 |
| `plagiarism_detector.py` | 抄袭检测 |
| `originality_tracker.py` | 原创性追踪 |
| `user_behavior_logger.py` | 用户行为日志 |
| `agent_analytics.py` | Agent分析 |
| `rag_optimizer.py` | RAG优化 |

### 4. 记忆系统 (`app/memory/`)

| 文件 | 层级 | 功能 |
|------|------|------|
| `story_memory.py` | L1 | 短期记忆，章节摘要 |
| `vector_store.py` | L2 | 语义记忆，向量检索 |
| `knowledge_graph.py` | L3 | 知识图谱，角色关系 |
| `memory_manager.py` | - | 记忆管理器，整合三层 |
| `enhanced_memory.py` | - | 增强记忆功能 |
| `rag_optimizer.py` | - | RAG优化器 |
| `global_asset_manager.py` | - | 全局资源管理 |
| `skill_memory.py` | - | 技能记忆 |
| `agent_skill_manager.py` | - | Agent技能管理 |
| `system_settings.py` | - | 系统设置存储 |

### 5. 工作流 (`app/workflow/`)

| 文件 | 功能 |
|------|------|
| `langgraph_flow_v3.py` | LangGraph工作流编排 |
| `writers_room.py` | 写作室工作流 |
| `facilitator.py` | 协调者 |
| `human_in_the_loop.py` | 人工介入机制 |

### 6. 服务层 (`app/services/`)

| 文件 | 功能 |
|------|------|
| `chapter_service.py` | 章节服务 (保存/加载/导出) |
| `pipeline_service.py` | 流水线服务 |
| `agent_chat_service.py` | Agent聊天服务 |
| `world_service.py` | 世界观服务 |

### 7. 数据模型 (`app/models/`)

| 文件 | 内容 |
|------|------|
| `novel.py` | 小说、章节、草稿模型 |
| `skill.py` | 技能模型 |

## 前端详细结构

### 1. 页面路由 (`src/app/`)

| 文件 | 路由 | 功能 |
|------|------|------|
| `page.tsx` | `/` | 主页面 |
| `layout.tsx` | - | 根布局 |
| `world/page.tsx` | `/world` | 世界观页面 |
| `globals.css` | - | 全局样式 |

### 2. 编辑器组件 (`src/components/editor/`)

| 文件 | 功能 |
|------|------|
| `TiptapEditor.tsx` | 主编辑器 |
| `DownloadDialog.tsx` | 下载对话框 |
| `StreamingEditor.tsx` | 流式写作编辑器 |
| `CollaborativeEditor.tsx` | 协作编辑器 |
| `EditorDiff.tsx` | 差异对比 |
| `OutlinePanel.tsx` | 大纲面板 |

### 3. 布局组件 (`src/components/layout/`)

| 文件 | 功能 |
|------|------|
| `MainSidebar.tsx` | 主导航侧边栏 |
| `SecondarySidebar.tsx` | 二级侧边栏 (小说结构) |
| `TopBar.tsx` | 顶部工具栏 |
| `AgentPanel.tsx` | Agent面板 |
| `ChatBar.tsx` | 聊天栏 |

### 4. 工作区组件 (`src/components/workspace/`)

| 目录/文件 | 功能 |
|-----------|------|
| `agent-management/index.tsx` | Agent管理 |
| `library/index.tsx` | 小说库 |
| `recycle-bin/index.tsx` | 回收站 |
| `settings/index.tsx` | 设置页面 |
| `skills/index.tsx` | 技能管理 |
| `skills/SkillMountPanel.tsx` | 技能挂载面板 |
| `story-assets/index.tsx` | 故事资源 |

### 5. 状态管理 (`src/store/`)

| 文件 | 功能 |
|------|------|
| `novelStore.ts` | 小说状态管理 |
| `assetStore.ts` | 资源状态管理 |
| `skillStore.ts` | 技能状态管理 |

## 测试结构

### 后端测试 (`backend/tests/`)

```
tests/
├── unit/                       # 单元测试
│   ├── test_download_api.py   # 下载API测试
│   ├── test_story_memory.py   # 记忆系统测试
│   ├── test_memory_manager.py # 记忆管理器测试
│   ├── test_writers_room.py   # 写作室测试
│   └── test_config.py         # 配置测试
├── integration/               # 集成测试
│   ├── test_api_basic.py      # API基础测试
│   ├── test_novel_workflow.py # 小说流程测试
│   └── test_writers_room_api.py # 写作室API测试
└── conftest.py                # Pytest配置
```

### 前端测试 (`frontend/src/`)

```
src/
├── store/__tests__/
│   └── novelStore.test.ts     # Store测试
└── components/editor/__tests__/
    └── DownloadDialog.test.tsx # 组件测试
```

### E2E测试 (`tests/e2e/`)

```
tests/e2e/
└── test_complete_user_journey.py  # 用户旅程测试
```

## 文档结构 (`docs/`)

```
docs/
├── architecture/               # 架构设计
│   ├── agent-framework-design.md
│   ├── agent-system.md
│   └── code-review-and-refactor-plan.md
├── development/               # 开发文档
│   ├── api-reference.md       # API参考
│   ├── backend-api-reference.md
│   ├── contributing.md
│   ├── data-models.md
│   ├── deployment.md
│   ├── developer-guide.md     # 开发指南
│   ├── frontend-next-tiptap-dev.md
│   ├── setup-guide.md
│   ├── testing.md
│   └── vector-database-setup.md
├── product/                   # 产品文档
│   ├── project-feature-overview.md
│   ├── user-guide.md
│   └── v3-upgrade-plan.md
├── standards/                 # 规范文档
│   ├── api-standards.md
│   └── documentation-standards.md
├── README.md                  # 文档首页
└── VERSION.md                 # 版本信息
```

## 数据存储结构

### 后端数据 (`backend/data/`)

```
data/
└── {novel_id}/
    ├── {chapter_id}.json      # 章节JSON数据
    ├── {chapter_id}.txt       # 章节纯文本
    ├── story_memory.json      # 故事记忆
    ├── world.json             # 世界设定
    ├── characters.json        # 角色信息
    └── timeline.json          # 时间线
```

### 前端存储

- **localStorage**: Zustand persist中间件自动存储
  - `novel-store`: 小说数据
  - `asset-store`: 资源数据

## 配置文件

### 后端配置

| 文件 | 用途 |
|------|------|
| `requirements.txt` | Python依赖 |
| `pytest.ini` | Pytest配置 |
| `.env` | 环境变量 (API Key等) |

### 前端配置

| 文件 | 用途 |
|------|------|
| `package.json` | Node.js依赖和脚本 |
| `tsconfig.json` | TypeScript配置 |
| `next.config.ts` | Next.js配置 |
| `tailwind.config.ts` | Tailwind CSS配置 |
| `jest.config.js` | Jest测试配置 |
| `eslint.config.mjs` | ESLint配置 |

### 项目配置

| 文件/目录 | 用途 |
|------|------|
| `docker-compose.yml` | Docker服务编排 |
| `scripts/start-services.ps1` | PowerShell启动脚本 |
| `scripts/test-api.ps1` | API测试脚本 |
| `.gitignore` | Git忽略规则 |

## 模块依赖关系

### 后端依赖图

```
API Layer (api/)
    ↓
Service Layer (services/)
    ↓
Agent Layer (agents/) ←→ Core Layer (core/)
    ↓                       ↓
Memory Layer (memory/) ←→ Workflow (workflow/)
    ↓
Models (models/)
```

### 前端依赖图

```
Pages (app/)
    ↓
Components (components/)
    ↓
Store (store/)
```

## 代码统计

| 模块 | 文件数 | 主要功能 |
|------|--------|----------|
| Agents | 15 | 智能体系统 |
| API | 16 | REST API |
| Core | 28 | 核心功能 |
| Memory | 10 | 记忆管理 |
| Frontend Components | 20+ | UI组件 |
| Tests | 24 | 测试用例 |
| Docs | 15+ | 文档 |

总计: 约150+个文件，涵盖完整的AI小说创作系统。
