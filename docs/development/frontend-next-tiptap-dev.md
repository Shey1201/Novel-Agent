# 前端开发文档（Next.js + Tiptap）

## 1. 技术栈

- Next.js（App Router）
- TypeScript
- Tailwind CSS
- Zustand（状态管理）
- Tiptap（富文本编辑）

---

## 2. 本地运行

```bash
cd frontend
npm install
npm run dev
```

默认访问：`http://localhost:3000`

> 后端默认地址为 `http://127.0.0.1:8000`，需要先启动后端服务。

---

## 3. 页面结构

首页由三栏布局组成：

- 左栏：`Sidebar`
  - 小说/章节导航
- 中栏：`TiptapEditor`
  - 编辑器主体与选区溯源气泡
- 右栏：`AgentPanel`
  - Agent 状态与信息
- 顶栏：`TopBar`
  - 写作模式切换、运行 Agent、导出等操作

入口文件：`frontend/src/app/page.tsx`

---

## 4. 核心交互链路

### 4.1 运行多 Agent

1. 用户点击 TopBar 的运行按钮
2. `page.tsx` 调用 `editorRef.current.handleRunAgents()`
3. `TiptapEditor` 发起 `POST /generate_chapter`
4. 接收 `final_text / trace_data / agent_logs`
5. 更新编辑器内容、chapter 状态和消息流

### 4.2 文本溯源（Trace）

- `trace_data` 保存在章节结构中。
- 在编辑器选中文本时，从 `trace_data` 匹配来源片段。
- 匹配到后在 BubbleMenu 展示：
  - `source_agent`
  - `revisions`

---

## 5. 状态管理建议

当前 `novelStore` 已承载：
- 当前小说/章节
- 消息列表
- Agent 配置
- 约束（constraints）

建议后续拆分：
- `editorSlice`：编辑器与 trace
- `workflowSlice`：agent 运行状态与日志
- `projectSlice`：novel/chapter 元数据

---

## 6. 常见问题

### 6.1 点击运行无反应

- 检查后端是否启动（`/health`）
- 检查浏览器控制台是否有跨域或网络错误

### 6.2 导出 Word 失败

- 检查 `currentNovelId/currentChapterId` 是否为空
- 检查后端 `/api/novel/export/word` 是否可访问

### 6.3 溯源信息不显示

- 确认后端返回 `trace_data`
- 确认选中文本与 trace 文本有交集

---

## 7. 前端开发规范（建议）

- UI 组件放 `components/`，业务逻辑尽量放 store/hooks。
- API 地址建议抽离到 `src/lib/api.ts`，避免硬编码。
- 新增页面/组件时同步更新本文件的“页面结构”与“交互链路”。
