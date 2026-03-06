# 文档编写规范与版本管理

本文档定义 Novel Agent Studio 项目的文档编写标准和版本管理规则。

## 目录

- [文档体系结构](#文档体系结构)
- [文档命名规范](#文档命名规范)
- [文档格式规范](#文档格式规范)
- [版本管理规则](#版本管理规则)
- [文档维护流程](#文档维护流程)
- [文档审查清单](#文档审查清单)

## 文档体系结构

### 目录结构

```
docs/
├── README.md                          # 文档总览入口
├── VERSION.md                         # 文档版本记录
├── standards/                         # 规范标准
│   ├── documentation-standards.md    # 本文档
│   ├── api-standards.md              # API设计规范
│   └── code-standards.md             # 代码规范
├── api/                               # API文档
│   ├── openapi.yaml                  # OpenAPI规范
│   └── http/                         # HTTP接口示例
├── architecture/                      # 架构设计
│   ├── 00-index.md                   # 架构文档索引
│   ├── 01-overview.md                # 架构总览
│   ├── 02-agent-system.md            # Agent系统
│   └── CHANGELOG.md                  # 架构变更记录
├── development/                       # 开发文档
│   ├── 00-setup.md                   # 环境搭建
│   ├── 01-backend.md                 # 后端开发
│   ├── 02-frontend.md                # 前端开发
│   ├── 03-testing.md                 # 测试指南
│   ├── 04-deployment.md              # 部署指南
│   └── CHANGELOG.md                  # 开发文档变更
├── product/                           # 产品文档
│   ├── 00-overview.md                # 产品总览
│   ├── 01-user-guide.md              # 用户指南
│   ├── 02-features.md                # 功能说明
│   └── CHANGELOG.md                  # 产品变更
└── assets/                            # 文档资源
    ├── images/                       # 图片
    ├── diagrams/                     # 图表
    └── templates/                    # 模板
```

### 文档分类说明

| 分类 | 用途 | 目标读者 | 更新频率 |
|------|------|----------|----------|
| standards | 规范标准 | 开发者 | 低 |
| api | 接口文档 | 前后端开发者 | 高 |
| architecture | 架构设计 | 架构师/开发者 | 中 |
| development | 开发指南 | 开发者 | 中 |
| product | 产品文档 | 用户/产品经理 | 中 |

## 文档命名规范

### 文件命名

1. **使用小写字母和连字符**
   - ✅ `user-guide.md`
   - ❌ `UserGuide.md` / `user_guide.md`

2. **使用数字前缀排序（可选）**
   - `01-overview.md`
   - `02-setup.md`
   - `03-api-reference.md`

3. **版本号文件**
   - `README.v1.0.md` - 特定版本
   - `README.md` - 当前版本

### 文档标题

1. **一级标题使用文档文件名**
   ```markdown
   # 用户指南
   ```

2. **章节使用二级标题**
   ```markdown
   ## 快速入门
   ```

3. **子章节使用三级标题**
   ```markdown
   ### 创建小说
   ```

## 文档格式规范

### 头部元数据

每个文档必须包含头部元数据：

```markdown
---
title: 文档标题
description: 文档简短描述
category: 分类（architecture/development/product/api）
tags: [标签1, 标签2]
version: 1.0.0
author: 作者名
created: 2024-01-01
updated: 2024-01-15
status: draft | review | published | deprecated
---
```

### 目录结构

1. **必须包含目录**
   ```markdown
   ## 目录
   
   - [章节1](#章节1)
   - [章节2](#章节2)
     - [子章节](#子章节)
   ```

2. **使用相对链接**
   ```markdown
   [查看API文档](../api/openapi.yaml)
   ```

### 代码块

1. **必须标注语言**
   ```markdown
   ```python
   def hello():
       pass
   ```
   ```

2. **包含文件名（可选）**
   ```markdown
   ```python:title=app/main.py
   ```
   ```

### 表格

1. **表头使用管道符**
   ```markdown
   | 列1 | 列2 | 列3 |
   |-----|-----|-----|
   | 值1 | 值2 | 值3 |
   ```

2. **对齐方式**
   ```markdown
   | 左对齐 | 居中 | 右对齐 |
   |:-------|:----:|-------:|
   ```

### 图片

1. **使用相对路径**
   ```markdown
   ![描述](../assets/images/diagram.png)
   ```

2. **包含替代文本**
   ```markdown
   ![系统架构图](../assets/images/architecture.png)
   ```

## 版本管理规则

### 版本号格式

采用语义化版本控制（SemVer）：

```
主版本号.次版本号.修订号
```

- **主版本号**：重大架构变更，不兼容的修改
- **次版本号**：功能新增，向后兼容
- **修订号**：问题修复，向后兼容

### 文档版本记录

每个文档必须包含版本历史表格：

```markdown
## 版本历史

| 版本 | 日期 | 作者 | 说明 |
|------|------|------|------|
| 1.0.0 | 2024-01-01 | 张三 | 初始版本 |
| 1.1.0 | 2024-01-15 | 李四 | 新增部署章节 |
| 1.1.1 | 2024-01-20 | 王五 | 修正错误链接 |
```

### 变更日志（CHANGELOG）

每个分类目录必须包含 CHANGELOG.md：

```markdown
# 变更日志

## [Unreleased]

### Added
- 新增功能A
- 新增功能B

### Changed
- 优化了XXX

### Fixed
- 修复了YYY问题

### Deprecated
- 废弃了ZZZ接口

## [1.0.0] - 2024-01-01

### Added
- 初始版本发布
```

### 版本标签

使用标签标记文档状态：

```markdown
> **版本**: v1.2.3  
> **状态**: ✅ 已发布  
> **最后更新**: 2024-01-15
```

## 文档维护流程

### 创建新文档

1. **确定文档位置**
   - 根据内容选择合适的分类目录
   - 参考目录结构规范

2. **复制模板**
   ```bash
   cp docs/assets/templates/document-template.md docs/development/my-doc.md
   ```

3. **填写元数据**
   - 标题、描述、分类
   - 版本、作者、日期
   - 状态标记为 `draft`

4. **编写内容**
   - 遵循格式规范
   - 添加必要的代码示例
   - 包含目录和链接

5. **提交审查**
   - 创建PR
   - 指定审查人员
   - 通过后将状态改为 `published`

### 更新文档

1. **小修改（修订号+1）**
   - 错别字修正
   - 链接修复
   - 格式调整

2. **中修改（次版本号+1）**
   - 新增章节
   - 内容扩充
   - 示例更新

3. **大修改（主版本号+1）**
   - 架构重构
   - 重大功能变更
   - 不兼容修改

### 废弃文档

1. **标记废弃**
   ```markdown
   ---
   status: deprecated
   deprecated_date: 2024-01-01
   replacement: new-document.md
   ---
   ```

2. **添加废弃警告**
   ```markdown
   > ⚠️ **警告**: 本文档已废弃，请使用 [新文档](new-document.md)
   ```

3. **保留6个月后删除**

## 文档审查清单

### 内容审查

- [ ] 内容准确无误
- [ ] 示例代码可运行
- [ ] 链接有效
- [ ] 图片正常显示
- [ ] 术语使用一致

### 格式审查

- [ ] 包含头部元数据
- [ ] 包含目录
- [ ] 代码块标注语言
- [ ] 表格格式正确
- [ ] 标题层级正确

### 版本审查

- [ ] 版本号正确
- [ ] 版本历史已更新
- [ ] 变更日志已更新
- [ ] 状态标记正确

### 关联审查

- [ ] 相关文档已更新
- [ ] 反向链接已添加
- [ ] 文档索引已更新

## 文档模板

### 标准文档模板

```markdown
---
title: 文档标题
description: 文档描述
category: development
tags: []
version: 1.0.0
author: 作者
created: 2024-01-01
updated: 2024-01-01
status: draft
---

# 文档标题

## 目录

- [章节1](#章节1)
- [章节2](#章节2)

## 版本历史

| 版本 | 日期 | 作者 | 说明 |
|------|------|------|------|
| 1.0.0 | 2024-01-01 | 作者 | 初始版本 |

## 章节1

内容...

## 章节2

内容...

## 相关文档

- [相关文档1](../architecture/overview.md)
- [相关文档2](../development/setup.md)
```

### API文档模板

```markdown
---
title: API名称
description: API功能描述
category: api
version: 1.0.0
---

# API名称

## 基本信息

- **接口地址**: `/api/endpoint`
- **请求方式**: POST
- **Content-Type**: application/json

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.0 | 2024-01-01 | 初始版本 |

## 请求参数

### 请求体

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| param1 | string | 是 | 参数说明 |
| param2 | int | 否 | 参数说明 |

## 响应参数

| 参数 | 类型 | 说明 |
|------|------|------|
| code | int | 状态码 |
| message | string | 消息 |
| data | object | 数据 |

## 示例

### 请求示例

```json
{
  "param1": "value1"
}
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

## 错误码

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 400 | 请求参数错误 |
| 500 | 服务器内部错误 |
```

## 工具推荐

### 文档编写

- **VS Code**: 配合 Markdown 插件
- **Typora**: 所见即所得编辑器
- **Obsidian**: 知识管理工具

### 版本控制

- **Git**: 文档版本管理
- **GitHub**: PR审查流程
- **GitBook**: 文档发布平台

### 质量检查

- **markdownlint**: Markdown格式检查
- **vale**: 写作风格检查
- **lychee**: 链接检查

## 相关文档

- [API设计规范](api-standards.md)
- [代码规范](code-standards.md)
- [项目文档总览](../README.md)
