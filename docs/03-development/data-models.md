# 数据模型文档

本文档详细说明 Novel Agent Studio 中的核心数据模型。

## 目录

- [概述](#概述)
- [Story Memory](#story-memory)
- [Pipeline State](#pipeline-state)
- [章节与草稿](#章节与草稿)
- [技能系统](#技能系统)
- [溯源数据](#溯源数据)

## 概述

项目使用 Pydantic 进行数据建模，确保类型安全和数据验证。所有模型定义位于 `backend/app/models/` 和 `backend/app/domain/`、`backend/app/memory/` 目录。

## Story Memory

Story Memory 用于维护长篇小说的长期一致性信息。

### StoryMemory

```python
class StoryMemory(BaseModel):
    story_id: str                          # 故事唯一标识
    bible: StoryBible                      # 世界观设定
    characters: List[Character]            # 角色列表
    timeline: List[TimelineEvent]          # 时间线事件
    chapter_summaries: List[ChapterSummary] # 章节摘要
    world_locked: bool = False             # 世界观是否已锁定
```

### StoryBible

```python
class StoryBible(BaseModel):
    world_view: Optional[str] = None       # 世界观描述
    rules: Optional[str] = None            # 世界规则
    themes: List[str] = Field(default_factory=list)  # 主题列表
```

### Character

```python
class Character(BaseModel):
    id: str
    name: str
    role: Optional[str] = None             # 角色定位
    description: Optional[str] = None      # 角色描述
```

### TimelineEvent

```python
class TimelineEvent(BaseModel):
    id: str
    chapter_id: Optional[str] = None       # 关联章节
    title: str
    summary: str
    order: int                             # 时间顺序
```

### ChapterSummary

```python
class ChapterSummary(BaseModel):
    chapter_id: str
    title: str
    summary: str                           # 内容摘要
    pov: Optional[str] = None              # 视角角色
```

## Pipeline State

Pipeline State 用于Agent工作流中的状态传递。

### GraphState

```python
class GraphState(TypedDict):
    input_text: str                        # 输入大纲/提示
    plan_text: str                         # Planner输出
    conflict_suggestions: List[str]        # Conflict建议
    draft_text: str                        # Writing初稿
    edited_text: str                       # Editor润色稿
    reader_feedback: List[str]             # Reader反馈
    summary_text: str                      # Summary总结
    final_text: str                        # 最终文本
    agent_logs: List[Dict[str, Any]]       # Agent执行日志
    trace_data: List[Dict[str, Any]]       # 溯源数据
    story_memory: StoryMemory              # 故事记忆
```

### 初始状态构建

```python
def build_initial_state(input_text: str, story_memory: StoryMemory) -> GraphState:
    return {
        "input_text": input_text,
        "agent_logs": [],
        "trace_data": [],
        "plan_text": "",
        "conflict_suggestions": [],
        "draft_text": "",
        "edited_text": "",
        "reader_feedback": [],
        "summary_text": "",
        "final_text": "",
        "story_memory": story_memory,
    }
```

## 章节与草稿

### ChapterDraft

用于保存章节草稿。

```python
class ChapterDraft(BaseModel):
    novel_id: str                          # 小说ID
    chapter_id: str                        # 章节ID
    content: str                           # 章节内容
```

### ChapterDraftResponse

保存响应，包含溯源信息。

```python
class ChapterDraftResponse(BaseModel):
    novel_id: str
    chapter_id: str
    content: str
    source: str                            # 数据来源(file/memory等)
    trace_data: Optional[List[TraceText]] = None  # 溯源数据
```

### TraceText

文本溯源条目。

```python
class TraceText(BaseModel):
    text: str                              # 文本片段
    source_agent: str                      # 来源Agent
    revisions: List[str] = Field(default_factory=list)  # 修改历史
```

## 技能系统

### Skill

```python
class Skill(BaseModel):
    id: str
    name: str
    description: str = ""
    category_id: str                       # 所属分类
    constraints: List[SkillConstraint] = Field(default_factory=list)  # 约束列表
    target_agents: List[str] = Field(default_factory=lambda: ["writer"])  # 目标Agent
    version: str = "1.0.0"
    is_active: bool = True
    is_system: bool = False                # 是否系统技能
    linked_assets: List[str] = Field(default_factory=list)  # 关联资源
    applicable_novels: List[str] = Field(default_factory=list)  # 适用小说
    created_at: str
    updated_at: str
    author: Optional[str] = None
    test_example: Optional[str] = None
```

### SkillConstraint

```python
class SkillConstraint(BaseModel):
    id: str
    content: str
    priority: Literal["high", "medium", "low"] = "medium"
    enabled: bool = True
```

### SkillCategory

```python
class SkillCategory(BaseModel):
    id: str
    name: str
    type: Literal["system", "writing", "domain", "auditing"]
    parent_id: Optional[str] = None        # 父分类
    color: str = "#6366f1"
    icon: Optional[str] = None
    is_system: bool = False
    description: Optional[str] = None
    default_agents: List[str] = Field(default_factory=list)
    order: int = 0
```

## 溯源数据

### TraceData结构

```json
{
  "trace_data": [
    {
      "text": "生成的文本片段",
      "source_agent": "WritingAgent",
      "revisions": [
        "EditorAgent: 润色修改说明"
      ]
    }
  ]
}
```

### AgentLog结构

```json
{
  "agent_logs": [
    {
      "agent": "PlannerAgent",
      "action": "generate_plan",
      "timestamp": "2024-01-01T12:00:00",
      "status": "success"
    }
  ]
}
```

## 数据持久化

### 存储位置

```
backend/data/
├── <story_id>/
│   ├── memory.json          # StoryMemory
│   ├── drafts/
│   │   └── <chapter_id>.json # 章节草稿
│   └── exports/
│       └── <chapter_id>.docx # Word导出
```

### 文件格式

- **memory.json**: StoryMemory的JSON序列化
- **drafts/*.json**: ChapterDraft的JSON序列化
- **exports/*.docx**: Word文档二进制文件

## 数据验证规则

### 必填字段验证

- `story_id`: 非空字符串
- `chapter_id`: 非空字符串
- `content`: 可为空字符串，但不能为null

### 列表字段默认值

所有列表字段使用 `Field(default_factory=list)` 避免可变默认值问题。

### 日期时间格式

- 创建/更新时间使用ISO 8601格式
- 示例: `2024-01-01T12:00:00`

## 模型使用示例

### 创建StoryMemory

```python
from app.memory.story_memory import StoryMemory, StoryBible, Character

memory = StoryMemory(
    story_id="demo-story",
    bible=StoryBible(
        world_view="赛博朋克世界",
        rules="高科技低生活",
        themes=["人性", "科技"]
    ),
    characters=[
        Character(id="c1", name="主角", role="侦探")
    ]
)
```

### 创建章节草稿

```python
from app.models.novel import ChapterDraft, TraceText

draft = ChapterDraft(
    novel_id="demo-novel",
    chapter_id="chapter-1",
    content="章节正文内容..."
)
```

### 构建Pipeline初始状态

```python
from app.domain.pipeline_state import build_initial_state

state = build_initial_state(
    input_text="本章大纲...",
    story_memory=memory
)
```

## 相关文档

- [架构设计文档](../architecture/agent-framework-design.md)
- [后端API参考](backend-api-reference.md)
