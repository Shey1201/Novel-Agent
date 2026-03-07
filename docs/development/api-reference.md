# API 参考文档

本文档详细说明 Novel Agent Studio 的所有 API 接口。

## 基础信息

- **基础URL**: `http://localhost:8000`
- **API版本**: v1
- **内容类型**: `application/json`

## 小说管理 API

### 保存章节草稿

```http
POST /api/novel/draft
```

**请求体**:
```json
{
  "novel_id": "string",
  "chapter_id": "string",
  "content": "string (HTML格式)"
}
```

**响应**:
```json
{
  "novel_id": "string",
  "chapter_id": "string",
  "content": "string",
  "source": "file"
}
```

**说明**: 保存章节内容到本地文件系统，同时生成.txt纯文本版本。

---

### 获取章节草稿

```http
GET /api/novel/draft
```

**查询参数**:
- `novel_id` (required): 小说ID
- `chapter_id` (required): 章节ID

**响应**:
```json
{
  "novel_id": "string",
  "chapter_id": "string",
  "content": "string",
  "source": "file | empty"
}
```

---

### 导出为Word文档

```http
GET /api/novel/export/word
```

**查询参数**:
- `novel_id` (required): 小说ID
- `chapter_id` (required): 章节ID

**响应**: Word文档文件 (.docx)

---

### 生成章节内容

```http
POST /api/novel/generate
```

**请求体**:
```json
{
  "text": "string (大纲内容)"
}
```

**响应**:
```json
{
  "input": "string",
  "result": "string (生成的内容)"
}
```

---

## 下载 API

### 下载小说

```http
POST /download/novel
```

**请求体**:
```json
{
  "novel_title": "string",
  "download_type": "full | single | range",
  "chapters": [
    {
      "id": "string",
      "title": "string",
      "content": "string (HTML)"
    }
  ],
  "single_chapter_id": "string (可选，单章下载时)",
  "start_chapter": "number (可选，范围下载时)",
  "end_chapter": "number (可选，范围下载时)"
}
```

**响应**: Word文档文件 (.docx)

**错误码**:
- `400`: 参数错误（缺少章节ID、无效范围、无章节等）
- `404`: 章节不存在
- `500`: 生成文档失败

**示例**:

下载完整小说:
```bash
curl -X POST http://localhost:8000/download/novel \
  -H "Content-Type: application/json" \
  -d '{
    "novel_title": "我的小说",
    "download_type": "full",
    "chapters": [
      {"id": "ch1", "title": "第一章", "content": "<p>内容</p>"}
    ]
  }' \
  --output "我的小说.docx"
```

下载单章:
```bash
curl -X POST http://localhost:8000/download/novel \
  -H "Content-Type: application/json" \
  -d '{
    "novel_title": "我的小说",
    "download_type": "single",
    "single_chapter_id": "ch1",
    "chapters": [...]
  }'
```

下载章节范围:
```bash
curl -X POST http://localhost:8000/download/novel \
  -H "Content-Type: application/json" \
  -d '{
    "novel_title": "我的小说",
    "download_type": "range",
    "start_chapter": 1,
    "end_chapter": 5,
    "chapters": [...]
  }'
```

---

## Agent API

### Agent房间交互

```http
POST /api/agent/room/chat
```

**请求体**:
```json
{
  "message": "string",
  "context": {
    "novel_id": "string",
    "chapter_id": "string"
  }
}
```

---

### 流式写作

```http
POST /api/agent/stream/write
```

**请求体**:
```json
{
  "novel_id": "string",
  "chapter_id": "string",
  "outline": "string",
  "context": "string"
}
```

**响应**: SSE流 (Server-Sent Events)

---

## 资源管理 API

### 获取所有资源

```http
GET /api/assets/all
```

**响应**:
```json
{
  "characters": [...],
  "worldbuilding": [...],
  "factions": [...],
  "locations": [...],
  "timeline": [...]
}
```

---

### 创建资源

```http
POST /api/assets/{category}
```

**路径参数**:
- `category`: characters | worldbuilding | factions | locations | timeline

**请求体**:
```json
{
  "name": "string",
  "description": "string",
  "content": "object"
}
```

---

## 世界观 API

### 获取世界设定

```http
GET /api/world/{novel_id}
```

**响应**:
```json
{
  "world_view": "string",
  "rules": "string",
  "themes": ["string"]
}
```

---

### 更新世界设定

```http
POST /api/world/{novel_id}
```

**请求体**:
```json
{
  "world_view": "string",
  "rules": "string",
  "themes": ["string"]
}
```

---

## 写作室 API

### 创建讨论

```http
POST /api/writers-room/discuss
```

**请求体**:
```json
{
  "topic": "string",
  "agents": ["string"],
  "context": "string"
}
```

**响应**: 流式SSE响应

---

## 系统设置 API

### 获取系统设置

```http
GET /api/system/settings
```

### 更新系统设置

```http
POST /api/system/settings
```

---

## 数据分析 API

### 获取小说统计

```http
GET /api/analytics/novel/{novel_id}
```

**响应**:
```json
{
  "total_chapters": 10,
  "total_words": 50000,
  "avg_chapter_length": 5000,
  "writing_time": "2h 30m"
}
```

---

## 错误处理

所有API错误都遵循以下格式:

```json
{
  "detail": "错误描述信息"
}
```

**HTTP状态码**:
- `200`: 成功
- `400`: 请求参数错误
- `404`: 资源不存在
- `422`: 验证错误
- `500`: 服务器内部错误

---

## 数据模型

### ChapterData

```typescript
interface ChapterData {
  id: string;
  title: string;
  content: string;  // HTML格式
}
```

### NovelDownloadRequest

```typescript
interface NovelDownloadRequest {
  novel_title: string;
  download_type: 'full' | 'single' | 'range';
  chapters: ChapterData[];
  single_chapter_id?: string;
  start_chapter?: number;
  end_chapter?: number;
}
```

### AgentConfig

```typescript
interface AgentConfig {
  excitement_level: number;  // 1-10
  strictness: number;        // 1-10
  pacing: number;            // 1-10
  character_depth: number;   // 1-10
  conflict_intensity: number;// 1-10
  description_density: number;// 1-10
  style: string;
}
```

---

## 限流说明

目前API没有严格的限流策略，但建议:
- 生成类API间隔至少1秒
- 批量操作单次不超过100条数据
- 流式API保持连接活跃

---

## 认证

当前版本API不需要认证。生产环境建议添加:
- API Key认证
- JWT Token认证
- OAuth2认证
