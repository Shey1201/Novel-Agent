# 后端 API 参考（FastAPI）

## 1. 服务启动

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

健康检查：`GET /health`

---

## 2. 接口总览

### 2.1 生成（简版）

- **POST** `/api/novel/generate`
- 请求体：

```json
{ "text": "本章大纲" }
```

- 响应（示例）：

```json
{ "input": "本章大纲", "result": "最终文本" }
```

### 2.2 章节完整流程生成

- **POST** `/generate_chapter`
- 请求体：

```json
{
  "outline": "主角在雨夜潜入钟楼",
  "story_id": "demo-story",
  "agent_configs": {},
  "constraints": ["第一人称", "节奏偏快"],
  "llm_config": null
}
```

- 响应关键字段：
  - `plan_text`
  - `conflict_suggestions`
  - `draft_text`
  - `edited_text`
  - `reader_feedback`
  - `summary_text`
  - `final_text`
  - `agent_logs`
  - `trace_data`

### 2.3 简化三段流水线

- **POST** `/api/novel/pipeline`
- 请求体：

```json
{ "text": "输入文本" }
```

- 说明：按 `Writing -> Editor -> Conflict` 顺序执行。

### 2.4 草稿保存

- **POST** `/api/novel/draft`
- 请求体：

```json
{
  "novel_id": "demo-novel",
  "chapter_id": "chapter-1",
  "content": "章节正文"
}
```

- 响应字段：
  - `novel_id`
  - `chapter_id`
  - `content`
  - `source`（`file`）

### 2.5 草稿读取

- **GET** `/api/novel/draft?novel_id=demo-novel&chapter_id=chapter-1`

### 2.6 导出 Word

- **GET** `/api/novel/export/word?novel_id=demo-novel&chapter_id=chapter-1`
- 返回：`.docx` 文件流


### 2.7 世界观 Debate

- **POST** `/api/world/debate`
- 请求体：

```json
{
  "prompt": "赛博朋克侦探 + 宗教阴谋",
  "story_id": "demo-story",
  "max_rounds": 2
}
```

- 说明：执行 `Planner -> Conflict -> Logic -> Reader -> Planner revise -> Editor` 的 debate loop（最多 2 轮）。

### 2.8 世界观确认（锁定）

- **POST** `/api/world/approve`
- 请求体包含 `story_id + world_bible`。
- 说明：写入 Story Bible 并将 `world_locked=true`，后续写作应读取该设定。

### 2.9 世界观读取

- **GET** `/api/world/{story_id}`


### 2.10 Agent Room 聊天入口

- **POST** `/api/agent/chat`
- 请求体：

```json
{
  "message": "/start chapter 8",
  "story_id": "demo-story"
}
```

- 说明：按命令路由到 Strategist/Writer/Editor/Critic/Memory 对应能力。
- 推荐命令：`/start chapter N` 会自动返回 Story Bible + 最近 3 章摘要上下文。

---

## 3. 前后端联调要点

- CORS 已允许：
  - `http://localhost:3000`
  - `http://127.0.0.1:3000`
- 前端默认调用 `http://127.0.0.1:8000`
- 若端口变更，需同步调整前端 fetch 地址

---

## 4. 返回数据约定建议

建议统一响应结构（后续可演进）：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

当前版本仍以“直接业务对象”返回，保持开发效率优先。

---

## 5. 常见错误排查

- 422：请求字段缺失或类型不匹配
- 500：通常为流程节点异常或持久化失败
- 导出失败：检查 `python-docx` 是否安装、`backend/data` 是否可写
