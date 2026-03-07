# Novel Agent Studio 快速启动指南

## 系统要求

- **Node.js** >= 18.0.0
- **Python** >= 3.9
- **Docker Desktop** (用于运行 Qdrant 和 Neo4j)

## 1. 安装依赖

### 后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 前端依赖

```bash
cd frontend
npm install
```

## 2. 配置环境变量

1. 复制 `.env.example` 为 `.env`
2. 填写你的 OpenAI API Key:

```env
OPENAI_API_KEY=your-openai-api-key-here
```

## 3. 启动依赖服务

使用 PowerShell 脚本启动 Qdrant、Neo4j 和 Redis:

```powershell
.\start-services.ps1
```

或者使用 Docker Compose:

```bash
docker-compose up -d
```

服务启动后:
- Qdrant Dashboard: http://localhost:6333/dashboard
- Neo4j Browser: http://localhost:7474 (用户名: neo4j, 密码: novelagent123)

## 4. 启动应用

### 启动后端

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 启动前端

```bash
cd frontend
npm run dev
```

## 5. 访问应用

打开浏览器访问: http://localhost:3000

## 常用命令

### 查看服务状态

```powershell
.\start-services.ps1 -Status
```

### 停止服务

```powershell
.\start-services.ps1 -Stop
```

### 重启服务

```powershell
.\start-services.ps1 -Restart
```

## 功能模块

### Writers Room 💬
- 多 Agent 协作讨论
- 实时 WebSocket 通信
- 人工干预和共识判定

### Story Bible 📚
- 世界观管理
- 角色档案
- 情节结构

### Agent 可视化 ⭐
- 执行时间线
- 思考过程展示
- 质量评分

### 流式写作 ✍️
- AI 实时生成
- Token 级流式输出
- 进度可视化

## 故障排除

### 后端启动失败

1. 检查 Python 版本: `python --version`
2. 检查依赖安装: `pip list | grep -E "fastapi|uvicorn|langchain"`
3. 检查端口占用: `netstat -an | grep 8000`

### 前端启动失败

1. 检查 Node.js 版本: `node --version`
2. 删除 node_modules 重新安装:
   ```bash
   cd frontend
   rm -rf node_modules
   npm install
   ```

### 数据库连接失败

1. 检查 Docker 是否运行
2. 检查服务状态: `.\start-services.ps1 -Status`
3. 查看日志: `docker-compose logs`

## 开发指南

### 项目结构

```
novel-agent-studio/
├── backend/           # FastAPI 后端
│   ├── app/
│   │   ├── agents/    # Agent 实现
│   │   ├── api/       # API 路由
│   │   ├── memory/    # 记忆系统
│   │   └── workflow/  # 工作流
│   └── requirements.txt
├── frontend/          # Next.js 前端
│   ├── src/
│   │   ├── components/# 组件
│   │   ├── app/       # 页面
│   │   └── store/     # 状态管理
│   └── package.json
├── docker-compose.yml # 服务配置
└── .env              # 环境变量
```

### API 文档

启动后端后访问: http://localhost:8000/docs

## 更新日志

### v3.0.0 (最新)

- ✅ Writers Room 多 Agent 协作
- ✅ 三层记忆系统 (L1/L2/L3)
- ✅ 流式写作
- ✅ Agent 可视化
- ✅ Story Bible 实体化

## 支持

如有问题，请查看:
1. [完整文档](./docs/)
2. [API 文档](http://localhost:8000/docs)
3. [GitHub Issues](https://github.com/Shey1201/Novel-Agent/issues)
