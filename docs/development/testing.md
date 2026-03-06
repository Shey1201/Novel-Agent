# 测试指南

本文档介绍 Novel Agent Studio 的测试策略和实践。

## 目录

- [测试策略](#测试策略)
- [后端测试](#后端测试)
- [前端测试](#前端测试)
- [集成测试](#集成测试)
- [性能测试](#性能测试)
- [测试覆盖率](#测试覆盖率)

## 测试策略

### 测试金字塔

```
       /\
      /  \     E2E测试 (少量)
     /----\
    /      \   集成测试 (中等)
   /--------\
  /          \ 单元测试 (大量)
 /------------\
```

### 测试类型

| 类型 | 范围 | 工具 | 优先级 |
|------|------|------|--------|
| 单元测试 | 函数/类 | pytest, jest | P0 |
| 集成测试 | 模块间 | pytest, supertest | P1 |
| E2E测试 | 完整流程 | playwright | P2 |
| 性能测试 | API性能 | locust | P2 |

## 后端测试

### 测试环境配置

```bash
cd backend

# 安装测试依赖
pip install pytest pytest-asyncio httpx

# 创建测试配置
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
```

### 目录结构

```
backend/
├── app/
└── tests/
    ├── __init__.py
    ├── conftest.py          # 测试配置和fixture
    ├── unit/                # 单元测试
    │   ├── test_agents.py
    │   ├── test_models.py
    │   └── test_services.py
    ├── integration/         # 集成测试
    │   ├── test_api.py
    │   └── test_pipeline.py
    └── e2e/                 # E2E测试
        └── test_workflow.py
```

### 单元测试示例

#### 测试Agent

```python
# tests/unit/test_agents.py
import pytest
from app.agents.writing_agent import WritingAgent
from app.memory.story_memory import StoryMemory

class TestWritingAgent:
    @pytest.fixture
    def agent(self):
        return WritingAgent()
    
    @pytest.fixture
    def story_memory(self):
        return StoryMemory(story_id="test-story")
    
    def test_agent_initialization(self, agent):
        assert agent.name == "WritingAgent"
        assert agent is not None
    
    def test_generate_draft(self, agent, story_memory):
        state = {
            "input_text": "测试大纲",
            "plan_text": "写作计划",
            "story_memory": story_memory,
            "agent_logs": [],
            "trace_data": []
        }
        
        result = agent.run(state)
        
        assert "draft_text" in result
        assert "trace_data" in result
        assert len(result["trace_data"]) > 0
```

#### 测试模型

```python
# tests/unit/test_models.py
import pytest
from app.models.novel import ChapterDraft, TraceText
from app.memory.story_memory import StoryMemory, Character

class TestModels:
    def test_chapter_draft_creation(self):
        draft = ChapterDraft(
            novel_id="novel-1",
            chapter_id="ch-1",
            content="测试内容"
        )
        
        assert draft.novel_id == "novel-1"
        assert draft.chapter_id == "ch-1"
        assert draft.content == "测试内容"
    
    def test_story_memory_default_values(self):
        memory = StoryMemory(story_id="test")
        
        assert memory.characters == []
        assert memory.timeline == []
        assert memory.chapter_summaries == []
        assert memory.world_locked is False
    
    def test_character_creation(self):
        char = Character(
            id="c1",
            name="主角",
            role="侦探"
        )
        
        assert char.name == "主角"
        assert char.role == "侦探"
```

#### 测试服务

```python
# tests/unit/test_services.py
import pytest
from unittest.mock import Mock, patch
from app.services.chapter_service import ChapterService

class TestChapterService:
    @pytest.fixture
    def service(self):
        return ChapterService(data_dir="/tmp/test-data")
    
    def test_save_draft(self, service):
        draft = {
            "novel_id": "n1",
            "chapter_id": "c1",
            "content": "测试内容"
        }
        
        with patch("builtins.open", mock_open()):
            result = service.save_draft(draft)
        
        assert result["novel_id"] == "n1"
        assert result["source"] == "file"
```

### 集成测试

#### 测试API端点

```python
# tests/integration/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestAPI:
    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_generate_chapter_endpoint(self):
        payload = {
            "outline": "测试大纲",
            "story_id": "test-story",
            "agent_configs": {},
            "constraints": []
        }
        
        response = client.post("/generate_chapter", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "final_text" in data
        assert "agent_logs" in data
    
    def test_draft_save_and_load(self):
        # 保存草稿
        save_payload = {
            "novel_id": "test-novel",
            "chapter_id": "ch-1",
            "content": "测试内容"
        }
        
        save_response = client.post("/api/novel/draft", json=save_payload)
        assert save_response.status_code == 200
        
        # 读取草稿
        load_response = client.get(
            "/api/novel/draft",
            params={"novel_id": "test-novel", "chapter_id": "ch-1"}
        )
        assert load_response.status_code == 200
        assert load_response.json()["content"] == "测试内容"
```

#### 测试Pipeline

```python
# tests/integration/test_pipeline.py
import pytest
from app.services.pipeline_service import NovelPipelineService
from app.memory.story_memory import StoryMemory

class TestPipeline:
    @pytest.fixture
    def service(self):
        return NovelPipelineService()
    
    @pytest.fixture
    def story_memory(self):
        return StoryMemory(story_id="pipeline-test")
    
    def test_full_pipeline_execution(self, service, story_memory):
        result = service.generate_chapter(
            outline="测试大纲",
            story_memory=story_memory,
            agent_configs={},
            constraints=[]
        )
        
        # 验证返回结构
        assert "final_text" in result
        assert "plan_text" in result
        assert "draft_text" in result
        assert "edited_text" in result
        assert "agent_logs" in result
        assert "trace_data" in result
        
        # 验证执行顺序
        logs = result["agent_logs"]
        agent_order = [log["agent"] for log in logs]
        assert "PlannerAgent" in agent_order
        assert "WritingAgent" in agent_order
```

### 测试Fixture

```python
# tests/conftest.py
import pytest
import tempfile
import shutil
from pathlib import Path

@pytest.fixture
def temp_data_dir():
    """创建临时数据目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_story_memory():
    """模拟StoryMemory"""
    from app.memory.story_memory import StoryMemory, StoryBible
    
    return StoryMemory(
        story_id="mock-story",
        bible=StoryBible(
            world_view="测试世界观",
            rules="测试规则"
        )
    )

@pytest.fixture
def sample_chapter_content():
    """示例章节内容"""
    return """
    第一章：雨夜
    
    雨下得很大。
    
    主角站在钟楼前，望着漆黑的夜空。
    """
```

## 前端测试

### 测试配置

```bash
cd frontend

# 安装测试依赖
npm install --save-dev jest @testing-library/react @testing-library/jest-dom

# jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
};
```

### 组件测试

```typescript
// src/components/__tests__/TiptapEditor.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { TiptapEditor } from '../editor/TiptapEditor';

describe('TiptapEditor', () => {
  it('renders editor with content', () => {
    render(<TiptapEditor content="测试内容" />);
    
    expect(screen.getByText('测试内容')).toBeInTheDocument();
  });
  
  it('calls onChange when content changes', () => {
    const onChange = jest.fn();
    render(<TiptapEditor content="" onChange={onChange} />);
    
    // 模拟编辑操作
    const editor = screen.getByRole('textbox');
    fireEvent.input(editor, { target: { innerHTML: '新内容' } });
    
    expect(onChange).toHaveBeenCalled();
  });
});
```

### Store测试

```typescript
// src/store/__tests__/novelStore.test.ts
import { useNovelStore } from '../novelStore';

describe('novelStore', () => {
  beforeEach(() => {
    // 重置store状态
    useNovelStore.setState({
      novels: [],
      currentNovelId: null,
      currentChapterId: null,
    });
  });
  
  it('adds a new novel', () => {
    const store = useNovelStore.getState();
    
    store.addNovel({
      id: 'novel-1',
      title: '测试小说',
      chapters: []
    });
    
    expect(useNovelStore.getState().novels).toHaveLength(1);
    expect(useNovelStore.getState().novels[0].title).toBe('测试小说');
  });
  
  it('sets current novel and chapter', () => {
    const store = useNovelStore.getState();
    
    store.setCurrentNovel('novel-1');
    store.setCurrentChapter('chapter-1');
    
    expect(useNovelStore.getState().currentNovelId).toBe('novel-1');
    expect(useNovelStore.getState().currentChapterId).toBe('chapter-1');
  });
});
```

### API测试

```typescript
// src/lib/__tests__/api.test.ts
import { fetchApi } from '../api';

// Mock fetch
global.fetch = jest.fn();

describe('API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  it('makes successful API call', async () => {
    const mockResponse = { data: 'test' };
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });
    
    const result = await fetchApi('/test');
    
    expect(result).toEqual(mockResponse);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/test'),
      expect.any(Object)
    );
  });
  
  it('handles API errors', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
    });
    
    await expect(fetchApi('/test')).rejects.toThrow();
  });
});
```

## 集成测试

### E2E测试

```python
# tests/e2e/test_workflow.py
import pytest
from playwright.sync_api import Page, expect

@pytest.mark.e2e
class TestNovelWorkflow:
    def test_create_and_edit_novel(self, page: Page):
        # 访问应用
        page.goto("http://localhost:3000")
        
        # 创建新小说
        page.click("text=新建小说")
        page.fill("[placeholder='小说标题']", "测试小说")
        page.click("text=确认")
        
        # 验证小说创建成功
        expect(page.locator("text=测试小说")).to_be_visible()
        
        # 添加章节
        page.click("text=新增章节")
        page.fill("[placeholder='章节标题']", "第一章")
        page.click("text=确认")
        
        # 编辑内容
        page.click("text=第一章")
        page.fill("[role='textbox']", "这是测试内容")
        
        # 运行Agent
        page.click("text=运行Agent")
        
        # 等待生成完成
        page.wait_for_selector("text=生成完成", timeout=60000)
        
        # 验证内容已更新
        content = page.locator("[role='textbox']").input_value()
        assert len(content) > 0
```

## 性能测试

### API性能测试

```python
# tests/performance/test_api_performance.py
import pytest
from locust import HttpUser, task, between

class NovelAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def health_check(self):
        self.client.get("/health")
    
    @task(1)
    def generate_chapter(self):
        payload = {
            "outline": "性能测试大纲",
            "story_id": "perf-test",
            "agent_configs": {},
            "constraints": []
        }
        self.client.post("/generate_chapter", json=payload)
    
    @task(2)
    def save_and_load_draft(self):
        # 保存草稿
        save_payload = {
            "novel_id": "perf-novel",
            "chapter_id": "ch-1",
            "content": "性能测试内容" * 100
        }
        self.client.post("/api/novel/draft", json=save_payload)
        
        # 读取草稿
        self.client.get("/api/novel/draft?novel_id=perf-novel&chapter_id=ch-1")

# 运行: locust -f tests/performance/test_api_performance.py
```

## 测试覆盖率

### 生成覆盖率报告

```bash
# 后端覆盖率
cd backend
pytest --cov=app --cov-report=html --cov-report=term

# 查看HTML报告
open htmlcov/index.html
```

### 覆盖率目标

| 模块 | 目标覆盖率 |
|------|-----------|
| models | 90%+ |
| services | 80%+ |
| api | 80%+ |
| agents | 70%+ |
| frontend | 70%+ |

### 覆盖率配置

```ini
# .coveragerc
[run]
source = app
omit = 
    */tests/*
    */venv/*
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
```

## CI/CD集成

### GitHub Actions配置

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run tests
        run: |
          cd frontend
          npm test -- --coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 测试最佳实践

1. **独立性**: 每个测试应该独立运行，不依赖其他测试
2. **可重复性**: 测试应该可以在任何环境下重复运行
3. **快速反馈**: 单元测试应该快速执行
4. **清晰命名**: 测试名称应该清楚描述测试内容
5. **单一职责**: 每个测试只验证一个概念
6. **使用Fixture**: 利用pytest fixture减少重复代码
7. **Mock外部依赖**: 测试时不应调用真实的LLM API

## 相关文档

- [开发环境搭建](setup-guide.md)
- [后端API参考](backend-api-reference.md)
- [贡献指南](contributing.md)
