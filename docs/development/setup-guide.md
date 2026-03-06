# 开发环境搭建指南

本文档详细介绍 Novel Agent Studio 的开发环境搭建步骤。

## 目录

- [环境要求](#环境要求)
- [后端环境搭建](#后端环境搭建)
- [前端环境搭建](#前端环境搭建)
- [IDE配置](#ide配置)
- [常见问题](#常见问题)

## 环境要求

### 必需软件

| 软件 | 版本要求 | 用途 |
|------|----------|------|
| Python | 3.9+ | 后端运行环境 |
| Node.js | 20+ | 前端运行环境 |
| Git | 任意版本 | 版本控制 |

### 推荐IDE

- **VS Code** (推荐): 配合Python、TypeScript插件
- **PyCharm**: Python开发专用
- **WebStorm**: 前端开发专用

## 后端环境搭建

### 1. 创建虚拟环境

```bash
cd backend

# 使用venv创建虚拟环境
python -m venv venv

# Windows激活虚拟环境
venv\Scripts\activate

# macOS/Linux激活虚拟环境
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
# OpenAI API配置
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# 可选：其他LLM提供商配置
# ANTHROPIC_API_KEY=your_key
```

### 4. 验证安装

```bash
python -c "import fastapi; import langgraph; print('依赖安装成功')"
```

### 5. 启动服务

```bash
# 开发模式（热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

访问 `http://localhost:8000/health` 验证服务是否正常运行。

## 前端环境搭建

### 1. 安装Node.js依赖

```bash
cd frontend
npm install
```

### 2. 配置环境变量

在项目根目录创建 `.env.local` 文件：

```env
# API基础地址
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

### 3. 启动开发服务器

```bash
npm run dev
```

访问 `http://localhost:3000` 查看应用。

### 4. 构建生产版本

```bash
npm run build
npm start
```

## IDE配置

### VS Code推荐配置

安装以下扩展：

- **Python** (ms-python.python)
- **Pylance** (ms-python.vscode-pylance)
- **ESLint** (dbaeumer.vscode-eslint)
- **Prettier** (esbenp.prettier-vscode)
- **Tailwind CSS IntelliSense** (bradlc.vscode-tailwindcss)
- **TypeScript Importer** (pmneo.tsimporter)

#### 推荐settings.json配置

```json
{
  "python.defaultInterpreterPath": "./backend/venv/Scripts/python.exe",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "typescript.preferences.importModuleSpecifier": "relative"
}
```

## 常见问题

### 后端问题

#### 1. 端口被占用

```bash
# Windows查找并结束占用8000端口的进程
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:8000 | xargs kill -9
```

#### 2. 依赖安装失败

```bash
# 更新pip
python -m pip install --upgrade pip

# 使用镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 3. 导入错误

确保在backend目录下运行，且虚拟环境已激活：

```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

### 前端问题

#### 1. npm install 失败

```bash
# 清除缓存
npm cache clean --force

# 删除node_modules重新安装
rm -rf node_modules package-lock.json
npm install
```

#### 2. 热重载不生效

检查 `next.config.ts` 中的配置，确保没有禁用热重载。

#### 3. 跨域错误

确保后端服务已启动，且CORS配置正确。检查浏览器控制台的具体错误信息。

### 联调问题

#### 1. 前端无法连接后端

- 确认后端服务运行在 `http://127.0.0.1:8000`
- 检查前端 `.env.local` 中的 `NEXT_PUBLIC_API_URL` 配置
- 确认防火墙没有阻止端口访问

#### 2. API返回404

- 确认后端路由已正确注册
- 检查请求URL是否正确
- 查看后端日志确认路由匹配情况

## 开发工作流

### 日常开发步骤

1. **启动后端**
   ```bash
   cd backend
   venv\Scripts\activate
   uvicorn app.main:app --reload
   ```

2. **启动前端**（新终端）
   ```bash
   cd frontend
   npm run dev
   ```

3. **开始开发**
   - 后端代码修改会自动重载
   - 前端代码修改会自动刷新

### 代码检查

```bash
# 后端代码检查（如有配置）
cd backend
python -m pylint app/

# 前端代码检查
cd frontend
npm run lint
```

## 下一步

环境搭建完成后，建议阅读：
- [架构设计文档](../architecture/agent-framework-design.md)
- [后端API参考](backend-api-reference.md)
- [前端开发指南](frontend-next-tiptap-dev.md)
