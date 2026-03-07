# 开发指南

本文档为 Novel Agent Studio 的开发者提供详细的开发规范和指南。

## 目录

1. [开发环境搭建](#开发环境搭建)
2. [项目结构规范](#项目结构规范)
3. [代码规范](#代码规范)
4. [测试规范](#测试规范)
5. [Git工作流](#git工作流)
6. [调试技巧](#调试技巧)

## 开发环境搭建

### 必需软件

- **Python 3.9+**: 后端开发
- **Node.js 20+**: 前端开发
- **Git**: 版本控制
- **VS Code**: 推荐IDE

### 推荐VS Code插件

- **前端**:
  - ESLint
  - Prettier
  - Tailwind CSS IntelliSense
  - TypeScript Importer
  - Auto Rename Tag

- **后端**:
  - Python
  - Pylance
  - autoDocstring
  - Python Test Explorer

### 环境配置

#### 1. 克隆项目

```bash
git clone <repository-url>
cd Novel-Agent-Studio
```

#### 2. 后端环境

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 创建.env文件
echo "OPENAI_API_KEY=your_key" > .env
```

#### 3. 前端环境

```bash
cd frontend

# 安装依赖
npm install

# 开发模式运行
npm run dev
```

## 项目结构规范

### 后端目录结构

```
backend/
├── app/
│   ├── agents/           # Agent实现
│   │   ├── base.py       # Agent基类
│   │   ├── planner_agent.py
│   │   └── ...
│   ├── api/              # API路由
│   │   ├── novel_routes.py
│   │   └── ...
│   ├── core/             # 核心功能
│   │   ├── llm.py        # LLM配置
│   │   └── ...
│   ├── memory/           # 记忆管理
│   │   ├── story_memory.py
│   │   └── ...
│   ├── models/           # Pydantic模型
│   │   └── novel.py
│   └── services/         # 业务服务
│       └── chapter_service.py
├── tests/
│   ├── unit/             # 单元测试
│   └── integration/      # 集成测试
└── data/                 # 数据存储
```

### 前端目录结构

```
frontend/
├── src/
│   ├── app/              # Next.js页面
│   │   ├── page.tsx      # 主页面
│   │   └── layout.tsx    # 根布局
│   ├── components/       # React组件
│   │   ├── editor/       # 编辑器组件
│   │   ├── layout/       # 布局组件
│   │   └── workspace/    # 工作区组件
│   ├── store/            # Zustand状态管理
│   │   ├── novelStore.ts
│   │   └── assetStore.ts
│   └── lib/              # 工具函数
│       └── utils.ts
├── public/               # 静态资源
└── __tests__/            # 测试文件
```

## 代码规范

### Python代码规范

#### 1. 命名规范

```python
# 类名: PascalCase
class NovelGenerator:
    pass

# 函数名: snake_case
def generate_chapter(novel_id: str) -> str:
    pass

# 常量: UPPER_SNAKE_CASE
MAX_CHAPTER_LENGTH = 10000

# 私有变量: _leading_underscore
_private_var = "private"
```

#### 2. 类型注解

```python
from typing import Optional, List, Dict, Any

def process_chapters(
    chapters: List[Chapter],
    config: Optional[Dict[str, Any]] = None
) -> List[ProcessedChapter]:
    """处理章节列表
    
    Args:
        chapters: 章节列表
        config: 可选配置
        
    Returns:
        处理后的章节列表
    """
    pass
```

#### 3. 文档字符串

```python
def create_word_document(
    novel_title: str,
    chapters: List[ChapterData]
) -> BytesIO:
    """创建Word文档
    
    将小说章节转换为Word文档格式，支持中文字体。
    
    Args:
        novel_title: 小说标题
        chapters: 章节数据列表
        
    Returns:
        包含Word文档的BytesIO对象
        
    Raises:
        ValueError: 当章节列表为空时
        
    Example:
        >>> chapters = [ChapterData(id="1", title="第一章", content="内容")]
        >>> doc = create_word_document("小说", chapters)
    """
    pass
```

#### 4. 错误处理

```python
try:
    result = process_data(data)
except ValueError as e:
    logger.error(f"数据验证失败: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.exception("处理数据时发生错误")
    raise HTTPException(status_code=500, detail="内部服务器错误")
```

### TypeScript代码规范

#### 1. 命名规范

```typescript
// 接口: PascalCase
interface NovelData {
  id: string;
  title: string;
}

// 类型: PascalCase
type SidebarView = 'chapter' | 'outline';

// 函数: camelCase
function updateChapterTitle(novelId: string, title: string): void {
  // ...
}

// 组件: PascalCase
function DownloadDialog({ isOpen, onClose }: DownloadDialogProps) {
  // ...
}

// 常量: UPPER_SNAKE_CASE
const MAX_CHAPTERS = 1000;
```

#### 2. 类型定义

```typescript
// 明确返回类型
interface Chapter {
  id: string;
  title: string;
  content: string;
  trace_data: TraceItem[];
}

// 使用类型别名
type NovelAction = 
  | { type: 'ADD_CHAPTER'; payload: Chapter }
  | { type: 'UPDATE_TITLE'; payload: string };

// 泛型使用
function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T) => void] {
  // ...
}
```

#### 3. 组件规范

```typescript
// Props接口
interface DownloadDialogProps {
  isOpen: boolean;
  onClose: () => void;
  novelId: string;
}

// 函数组件
export function DownloadDialog({ 
  isOpen, 
  onClose, 
  novelId 
}: DownloadDialogProps) {
  // 状态定义
  const [downloadType, setDownloadType] = useState<'full' | 'single' | 'range'>('full');
  
  // 副作用
  useEffect(() => {
    if (isOpen) {
      loadNovelData();
    }
  }, [isOpen, novelId]);
  
  // 事件处理
  const handleDownload = async () => {
    // ...
  };
  
  // 渲染
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 z-50">
      {/* ... */}
    </div>
  );
}
```

## 测试规范

### Python测试

#### 1. 测试文件命名

```
test_<module_name>.py
```

#### 2. 测试类命名

```python
class TestNovelService:
    """测试小说服务"""
    
    def test_create_novel(self):
        """测试创建小说"""
        pass
    
    def test_update_novel_raises_error_when_not_found(self):
        """测试更新不存在的小说时抛出错误"""
        pass
```

#### 3. 测试用例编写

```python
import pytest
from fastapi.testclient import TestClient

class TestDownloadAPI:
    """测试下载API"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_download_full_novel(self, client):
        """测试下载完整小说"""
        # Arrange
        request_data = {
            "novel_title": "测试小说",
            "download_type": "full",
            "chapters": [...]
        }
        
        # Act
        response = client.post("/download/novel", json=request_data)
        
        # Assert
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    @pytest.mark.parametrize("download_type", ["full", "single", "range"])
    def test_download_with_different_types(self, client, download_type):
        """测试不同下载类型"""
        pass
```

### TypeScript测试

#### 1. 测试文件位置

```
<component_path>/__tests__/<ComponentName>.test.tsx
```

#### 2. 测试编写

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { DownloadDialog } from '../DownloadDialog';

describe('DownloadDialog', () => {
  const mockOnClose = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  it('应该正确渲染对话框', () => {
    render(
      <DownloadDialog
        isOpen={true}
        onClose={mockOnClose}
        novelId="test-1"
      />
    );
    
    expect(screen.getByText('下载小说')).toBeInTheDocument();
  });
  
  it('关闭按钮应该能关闭对话框', () => {
    render(
      <DownloadDialog
        isOpen={true}
        onClose={mockOnClose}
        novelId="test-1"
      />
    );
    
    fireEvent.click(screen.getByText('取消'));
    
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });
});
```

## Git工作流

### 分支命名规范

```
feature/<feature-name>      # 新功能
bugfix/<bug-description>    # Bug修复
hotfix/<hotfix-description> # 紧急修复
refactor/<refactor-name>    # 重构
docs/<doc-name>             # 文档更新
test/<test-name>            # 测试相关
```

### 提交信息规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**:
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

**示例**:

```
feat(download): 添加Word文档导出功能

- 实现create_word_document函数
- 添加中文字体支持
- 添加下载API端点

Closes #123
```

### 提交检查清单

- [ ] 代码通过所有测试
- [ ] 添加/更新了测试用例
- [ ] 更新了相关文档
- [ ] 代码符合规范
- [ ] 提交信息清晰明了

## 调试技巧

### 后端调试

#### 1. 使用日志

```python
import logging

logger = logging.getLogger(__name__)

# 不同级别的日志
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.exception("异常信息")  # 自动包含堆栈
```

#### 2. 使用pdb

```python
def complex_function(data):
    import pdb; pdb.set_trace()  # 设置断点
    result = process(data)
    return result
```

#### 3. 使用VS Code调试

创建 `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

### 前端调试

#### 1. React DevTools

安装React Developer Tools浏览器扩展。

#### 2. 使用console

```typescript
// 格式化输出
console.log('%c重要信息', 'color: red; font-size: 20px');

// 分组输出
console.group('数据处理');
console.log('步骤1');
console.log('步骤2');
console.groupEnd();

// 表格输出
console.table(data);
```

#### 3. 使用VS Code调试

创建 `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Next.js: debug",
      "type": "node-terminal",
      "request": "launch",
      "command": "npm run dev",
      "cwd": "${workspaceFolder}/frontend"
    }
  ]
}
```

## 性能优化

### 后端优化

1. **使用缓存**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_operation(param: str) -> str:
    pass
```

2. **异步处理**
```python
async def process_chapters(chapters: List[Chapter]):
    tasks = [process_chapter(ch) for ch in chapters]
    return await asyncio.gather(*tasks)
```

### 前端优化

1. **组件懒加载**
```typescript
const HeavyComponent = lazy(() => import('./HeavyComponent'));
```

2. **使用useMemo和useCallback**
```typescript
const memoizedValue = useMemo(() => computeExpensiveValue(a, b), [a, b]);
const memoizedCallback = useCallback(() => doSomething(a, b), [a, b]);
```

3. **虚拟列表**
对于长列表使用虚拟滚动。

## 常见问题

### Q: 如何处理跨域问题？

A: 后端已配置CORS，前端开发服务器会自动代理API请求。

### Q: 如何添加新的Agent？

A: 
1. 在 `backend/app/agents/` 创建新文件
2. 继承 `BaseAgent` 类
3. 实现 `run` 方法
4. 在 `backend/app/api/` 添加API端点

### Q: 如何添加新的API端点？

A:
1. 在 `backend/app/api/` 创建或修改路由文件
2. 定义Pydantic模型
3. 实现处理函数
4. 在 `main.py` 注册路由

### Q: 如何调试Agent行为？

A:
1. 启用详细日志: `LOG_LEVEL=DEBUG`
2. 使用Agent Room查看Agent讨论
3. 检查记忆系统状态

## 相关文档

- [API参考](api-reference.md)
- [架构设计](../architecture/agent-framework-design.md)
- [测试指南](testing.md)
- [部署指南](deployment.md)
