# API 设计规范

本文档定义 Novel Agent Studio 项目的 API 设计标准和最佳实践。

## 目录

- [设计原则](#设计原则)
- [URL 规范](#url-规范)
- [请求规范](#请求规范)
- [响应规范](#响应规范)
- [错误处理](#错误处理)
- [版本控制](#版本控制)
- [安全规范](#安全规范)

## 设计原则

### RESTful 设计

1. **资源导向**
   - 使用名词表示资源
   - ✅ `GET /api/novels`
   - ❌ `GET /api/getNovels`

2. **HTTP 方法语义**
   - `GET`: 获取资源
   - `POST`: 创建资源
   - `PUT`: 完整更新
   - `PATCH`: 部分更新
   - `DELETE`: 删除资源

3. **状态码使用**
   - `200`: 成功
   - `201`: 创建成功
   - `400`: 请求参数错误
   - `401`: 未认证
   - `403`: 无权限
   - `404`: 资源不存在
   - `422`: 验证错误
   - `500`: 服务器错误

## URL 规范

### 基本格式

```
/api/{资源名}/{资源ID}/{子资源}
```

### 命名规则

1. **使用小写和连字符**
   ```
   /api/chapter-drafts
   /api/story-memories
   ```

2. **复数形式**
   ```
   /api/novels          # 小说列表
   /api/novels/{id}     # 单本小说
   /api/novels/{id}/chapters  # 子资源
   ```

3. **避免动词**
   ```
   # ❌ 不推荐
   POST /api/novels/create
   
   # ✅ 推荐
   POST /api/novels
   ```

### 查询参数

1. **过滤**
   ```
   GET /api/novels?status=published&author=zhangsan
   ```

2. **分页**
   ```
   GET /api/novels?page=1&size=20
   ```

3. **排序**
   ```
   GET /api/novels?sort=-created_at
   ```

4. **字段选择**
   ```
   GET /api/novels?fields=id,title,author
   ```

## 请求规范

### Content-Type

- `application/json`: JSON 数据
- `multipart/form-data`: 文件上传
- `application/x-www-form-urlencoded`: 表单数据

### 请求体格式

```json
{
  "title": "小说标题",
  "content": "章节内容",
  "metadata": {
    "word_count": 5000,
    "genre": "科幻"
  }
}
```

### 字段命名

使用 snake_case（下划线命名）

```json
{
  "novel_id": "novel-123",
  "chapter_title": "第一章",
  "created_at": "2024-01-01T00:00:00Z"
}
```

## 响应规范

### 标准响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

### 成功响应

#### 单资源

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "novel-123",
    "title": "小说标题",
    "author": "作者名",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### 列表资源

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {"id": "1", "title": "小说1"},
      {"id": "2", "title": "小说2"}
    ],
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 100,
      "total_pages": 5
    }
  }
}
```

### 空数据响应

```json
{
  "code": 0,
  "message": "success",
  "data": null
}
```

或

```json
{
  "code": 0,
  "message": "success",
  "data": []
}
```

## 错误处理

### 错误响应格式

```json
{
  "code": 400,
  "message": "请求参数错误",
  "errors": [
    {
      "field": "title",
      "message": "标题不能为空"
    }
  ]
}
```

### 常见错误码

| 错误码 | 说明 | HTTP 状态码 |
|--------|------|-------------|
| 0 | 成功 | 200 |
| 400 | 请求参数错误 | 400 |
| 401 | 未认证 | 401 |
| 403 | 无权限 | 403 |
| 404 | 资源不存在 | 404 |
| 409 | 资源冲突 | 409 |
| 422 | 验证错误 | 422 |
| 429 | 请求过于频繁 | 429 |
| 500 | 服务器内部错误 | 500 |
| 503 | 服务不可用 | 503 |

### 业务错误码

| 错误码 | 说明 |
|--------|------|
| 1001 | 小说不存在 |
| 1002 | 章节不存在 |
| 2001 | Agent 执行失败 |
| 2002 | LLM API 调用失败 |
| 3001 | 文件上传失败 |
| 3002 | 导出失败 |

## 版本控制

### URL 版本控制

```
/api/v1/novels
/api/v2/novels
```

### Header 版本控制

```
Accept: application/vnd.api+json;version=1
```

### 版本兼容性

- 主版本号变更：不兼容的修改
- 次版本号变更：向后兼容的功能新增
- 修订号变更：向后兼容的问题修复

## 安全规范

### 认证

使用 Bearer Token

```
Authorization: Bearer <token>
```

### 限流

响应头包含限流信息

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1640995200
```

### CORS

允许的源：

```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

### 敏感信息

- 不在 URL 中传递敏感信息
- 使用 HTTPS
- 密码等敏感字段加密存储

## 文档规范

### OpenAPI 规范

所有 API 必须提供 OpenAPI 文档：

```yaml
openapi: 3.0.3
info:
  title: API Title
  version: 1.0.0
paths:
  /api/novels:
    get:
      summary: 获取小说列表
      parameters:
        - name: page
          in: query
          schema:
            type: integer
      responses:
        '200':
          description: 成功
```

### 文档注释

代码中必须包含文档注释：

```python
@router.get("/api/novels")
async def get_novels(
    page: int = Query(1, description="页码"),
    size: int = Query(20, description="每页数量")
) -> NovelListResponse:
    """
    获取小说列表
    
    Args:
        page: 页码，从1开始
        size: 每页数量，默认20
        
    Returns:
        小说列表和分页信息
        
    Raises:
        400: 参数错误
        500: 服务器错误
    """
    pass
```

## 示例

### 完整示例

#### 创建小说

**请求**

```http
POST /api/novels HTTP/1.1
Content-Type: application/json
Authorization: Bearer <token>

{
  "title": "新小说",
  "description": "小说简介",
  "genre": "科幻"
}
```

**成功响应**

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "code": 0,
  "message": "创建成功",
  "data": {
    "id": "novel-123",
    "title": "新小说",
    "description": "小说简介",
    "genre": "科幻",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**错误响应**

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "code": 400,
  "message": "请求参数错误",
  "errors": [
    {
      "field": "title",
      "message": "标题长度不能超过100字符"
    }
  ]
}
```

## 相关文档

- [OpenAPI 规范](../api/openapi.yaml)
- [后端 API 参考](../development/backend-api-reference.md)
- [文档编写规范](documentation-standards.md)
