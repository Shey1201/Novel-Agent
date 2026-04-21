# 贡献指南

感谢您对 Novel Agent Studio 项目的关注！本文档将指导您如何参与项目贡献。

## 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发流程](#开发流程)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [审查流程](#审查流程)

## 行为准则

- 尊重所有参与者
- 接受建设性的批评
- 关注对项目最有利的事情
- 对其他社区成员表示同理心

## 如何贡献

### 报告问题

如果您发现了bug或有功能建议：

1. 先搜索现有Issue，避免重复
2. 使用Issue模板创建新Issue
3. 提供详细的复现步骤
4. 附上相关的日志和截图

### 提交代码

1. Fork 项目仓库
2. 创建您的功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 文档贡献

文档改进同样重要：

- 修正拼写和语法错误
- 改进现有文档的清晰度
- 添加缺失的文档
- 翻译文档

## 开发流程

### 1. 环境准备

```bash
# 克隆您的fork
git clone https://github.com/your-username/Novel-Agent-Studio.git
cd Novel-Agent-Studio

# 添加上游仓库
git remote add upstream https://github.com/original/Novel-Agent-Studio.git

# 创建开发分支
git checkout -b dev/my-feature
```

### 2. 开发工作流

```bash
# 同步上游代码
git fetch upstream
git rebase upstream/main

# 进行开发
# ... coding ...

# 提交更改
git add .
git commit -m "feat: add new feature"

# 推送到您的fork
git push origin dev/my-feature
```

### 3. 创建Pull Request

- 使用清晰的标题描述更改
- 详细说明更改的内容和原因
- 关联相关的Issue
- 确保CI检查通过

## 代码规范

### Python代码规范

遵循 PEP 8 规范：

```python
# 正确的命名
class NovelAgent:           # 类名: 大驼峰
    def generate_text(self): # 方法名: 小写下划线
        pass

MAX_RETRY = 3               # 常量: 大写下划线

# 正确的导入顺序
import os                   # 标准库
from typing import List

from fastapi import FastAPI # 第三方库
from pydantic import BaseModel

from app.models import Novel # 本地模块
```

#### 代码风格检查

```bash
cd backend

# 使用black格式化代码
black app/

# 使用isort排序导入
isort app/

# 使用flake8检查代码
flake8 app/

# 使用mypy进行类型检查
mypy app/
```

### TypeScript代码规范

```typescript
// 接口命名: 大驼峰
interface NovelConfig {
  title: string;
  chapters: Chapter[];
}

// 类型别名: 大驼峰
type AgentType = 'planner' | 'writer' | 'editor';

// 函数命名: 小驼峰
function generateChapter(config: NovelConfig): Promise<string> {
  // ...
}

// 常量: 大写下划线
const MAX_RETRY_COUNT = 3;

// 组件: 大驼峰 + 函数组件
const ChapterEditor: React.FC<EditorProps> = ({ content }) => {
  return <div>{content}</div>;
};
```

#### 前端代码检查

```bash
cd frontend

# ESLint检查
npm run lint

# TypeScript类型检查
npx tsc --noEmit
```

### 文档规范

- 使用清晰的标题层级
- 代码块标注语言类型
- 添加必要的注释说明
- 保持中英文标点一致

## 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

### 提交类型

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug修复 |
| `docs` | 文档更新 |
| `style` | 代码格式调整（不影响功能） |
| `refactor` | 代码重构 |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建/工具相关 |

### 提交格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 示例

```bash
# 新功能
feat(agent): add summary agent for chapter conclusion

# Bug修复
fix(api): resolve cors issue in production

# 文档更新
docs(readme): update installation guide

# 代码重构
refactor(pipeline): extract common logic to base class
```

## 审查流程

### 审查清单

- [ ] 代码符合项目规范
- [ ] 功能实现正确
- [ ] 有适当的测试覆盖
- [ ] 文档已更新
- [ ] 没有引入安全问题
- [ ] 性能影响已评估

### 审查原则

1. **及时性**: 尽快响应审查请求
2. **建设性**: 提供改进建议而非批评
3. **尊重**: 尊重作者的工作
4. **清晰**: 说明为什么需要修改

### 合并标准

- 至少1个维护者批准
- 所有CI检查通过
- 无冲突需要解决
- 符合项目架构设计

## 项目结构

贡献代码前请了解项目结构：

```
backend/
├── app/
│   ├── agents/      # Agent实现
│   ├── api/         # API路由
│   ├── core/        # 核心配置
│   ├── domain/      # 领域模型
│   ├── memory/      # 记忆管理
│   ├── models/      # 数据模型
│   └── services/    # 业务服务

docs/
├── architecture/    # 架构设计
├── development/     # 开发文档
└── product/         # 产品文档

frontend/
├── src/
│   ├── app/         # 页面路由
│   ├── components/  # 组件
│   └── store/       # 状态管理
```

## 测试要求

### 后端测试

```python
# 测试示例
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

运行测试：

```bash
cd backend
pytest
```

### 前端测试

```bash
cd frontend
npm test
```

## 发布流程

1. 更新版本号
2. 更新CHANGELOG
3. 创建Release PR
4. 合并到main分支
5. 打标签并创建Release

## 获取帮助

如果您在贡献过程中遇到问题：

- 查看[开发环境搭建](setup-guide.md)文档
- 在Issue中提问
- 联系项目维护者

## 许可证

通过贡献代码，您同意您的贡献将在MIT许可证下发布。

---

感谢您的贡献！🎉
