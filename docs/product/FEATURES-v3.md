# Novel Agent Studio v3.0 功能清单

## 🚀 新功能概览

### 1. Writers Room 💬
**多 Agent 协作讨论系统**

- **功能特点**:
  - 多 Agent 实时讨论（Planner、Conflict、Writing、Consistency）
  - WebSocket 实时通信
  - 共识度评估和自动判定
  - 人工干预（接受/拒绝/评论）
  - Facilitator 动态发言调度
  - Consistency Agent 高优先级插话

- **使用方式**:
  1. 点击左侧边栏 "Writers Room" 图标
  2. 创建讨论议案（输入标题和描述）
  3. 点击"开始讨论"
  4. 观察 Agent 们的讨论过程
  5. 可随时人工干预

- **API 端点**:
  - `POST /api/writers-room/discussions` - 创建讨论
  - `GET /api/writers-room/discussions/{id}` - 获取讨论状态
  - `POST /api/writers-room/discussions/{id}/round` - 运行一轮
  - `POST /api/writers-room/discussions/{id}/intervene` - 人工干预
  - `WebSocket /api/writers-room/ws/{id}` - 实时通信

### 2. Story Bible 📚
**故事设定管理中心**

- **功能特点**:
  - 完整的角色档案管理
  - 世界规则设定
  - 情节结构规划
  - 主题和基调设定
  - 自动保存功能

- **使用方式**:
  1. 点击左侧边栏 "Story Bible" 图标
  2. 在"概览"标签填写基本信息
  3. 在"角色"标签管理角色
  4. 在"世界"标签设定规则
  5. 在"情节"标签规划情节点

- **数据模型**:
  - Character: 完整角色档案（性格、能力、关系、弧线）
  - WorldRule: 世界规则（魔法、物理、社会等）
  - WorldLocation: 地点设定
  - WorldFaction: 势力/组织
  - StoryTheme: 主题定义

### 3. Agent 可视化 ⭐
**Agent 执行过程可视化**

- **功能特点**:
  - 实时执行时间线
  - Agent 思考过程展示
  - 质量评分雷达图
  - 执行状态追踪

- **组件位置**:
  - Writers Room 页面右侧
  - 独立弹窗（点击"AI写作"按钮时显示）

- **事件类型**:
  - `agent_start` - Agent 开始执行
  - `agent_thinking` - 思考过程
  - `agent_complete` - 执行完成
  - `quality_check` - 质量评分
  - `rewrite` - 触发重写

### 4. 流式写作 ✍️
**AI 实时写作体验**

- **功能特点**:
  - Token 级流式输出
  - 实时打字效果
  - 上下文自动构建
  - 进度可视化

- **使用方式**:
  1. 进入小说编辑页面
  2. 点击"AI写作"按钮
  3. 等待 AI 生成内容
  4. 可实时看到生成过程
  5. 点击"保存"保存内容

- **API 端点**:
  - `POST /api/stream/write` - SSE 流式写作
  - `GET /api/stream/execution/{id}` - 执行过程流
  - `GET /api/stream/progress/{id}` - 进度查询

### 5. 三层记忆系统 🧠

#### L1 - Short Memory
- StoryMemory 内存存储
- 近期章节摘要
- 角色状态追踪

#### L2 - Semantic Memory
- Qdrant 向量数据库
- 语义检索
- 相似度搜索

#### L6 - Knowledge Graph
- Neo4j 图数据库
- 角色关系网络
- 世界实体关联

## 📁 新增文件结构

```
backend/
├── app/
│   ├── api/
│   │   ├── writers_room_api.py    # Writers Room API
│   │   └── stream_api.py          # 流式 API
│   ├── agents/
│   │   ├── critic_agent.py        # Critic Agent
│   │   └── consistency_agent.py   # Consistency Agent
│   ├── memory/
│   │   ├── vector_store.py        # L2 向量存储
│   │   ├── knowledge_graph.py     # L3 知识图谱
│   │   └── memory_manager.py      # 记忆管理器
│   └── workflow/
│       ├── writers_room.py        # Writers Room 实现
│       └── langgraph_flow_v3.py   # v3 工作流

frontend/
├── src/
│   ├── components/
│   │   ├── writers-room/
│   │   │   └── DiscussionPanel.tsx    # Writers Room UI
│   │   ├── visualization/
│   │   │   └── AgentTimeline.tsx      # Agent 可视化
│   │   ├── editor/
│   │   │   └── StreamingEditor.tsx    # 流式写作编辑器
│   │   └── story-bible/
│   │       └── StoryBibleManager.tsx  # Story Bible UI

├── docker-compose.yml         # 服务编排
├── .env                       # 环境变量
├── QUICKSTART.md             # 快速启动指南
└── FEATURES-v3.md            # 本文件
```

## 🔧 配置说明

### 环境变量

```env
# LLM 配置（必需）
OPENAI_API_KEY=your-api-key

# 向量数据库（可选，默认内存模式）
QDRANT_URL=http://localhost:6333

# 知识图谱（可选，默认内存模式）
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=novelagent123
```

### 启动服务

```powershell
# 方式1: 使用脚本（推荐）
.\start-services.ps1

# 方式2: 使用 Docker
docker compose up -d

# 方式3: 手动启动
docker run -p 6333:6333 qdrant/qdrant
docker run -p 7474:7474 -p 7687:7687 neo4j:5.15.0
```

## 🎯 使用流程

### 完整创作流程

1. **创建小说**
   - 进入 Library
   - 点击"新建小说"
   - 填写基本信息

2. **设定 Story Bible**
   - 进入 Story Bible
   - 创建角色档案
   - 设定世界规则
   - 规划情节结构

3. **Writers Room 讨论**
   - 进入 Writers Room
   - 创建讨论议案
   - 让 Agents 讨论剧情
   - 人工干预指导方向

4. **流式写作**
   - 进入章节编辑
   - 点击"AI写作"
   - 观察实时生成
   - 保存生成内容

5. **迭代优化**
   - 使用 Agent Panel 聊天
   - 获取修改建议
   - 反复打磨内容

## 📊 性能指标

- **流式生成速度**: ~50 tokens/秒
- **Agent 响应时间**: < 2秒
- **WebSocket 延迟**: < 100ms
- **内存使用**: ~500MB（内存模式）

## 🔮 未来计划

- [ ] 支持更多 LLM 提供商（DeepSeek、Claude）
- [ ] 团队协作功能
- [ ] 版本控制和对比
- [ ] AI 辅助编辑（续写、改写、扩写）
- [ ] 导出功能（PDF、EPUB、Word）
- [ ] 移动端适配

## 🐛 已知问题

1. **Docker 未安装时**: 自动使用内存模式（功能正常，数据不持久化）
2. **WebSocket 重连**: 断线后需要手动刷新页面
3. **流式生成**: 长文本生成可能需要较长时间

## 📞 支持

- API 文档: http://localhost:8000/docs
- GitHub Issues: https://github.com/Shey1201/Novel-Agent/issues
