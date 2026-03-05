# 前端模块开发文档（模块2：Next.js + Tailwind + Tiptap 基础）

## 目标

- 使用 Next.js App Router + TypeScript 初始化前端项目。
- 集成 Tailwind CSS 作为样式方案。
- 引入 Tiptap 作为基础富文本编辑器，构建一个最简单可用的小说编辑器页面。

## 目录结构（与本模块相关部分）

- `frontend/`
  - `src/app/page.tsx`：首页，渲染小说编辑器原型。
  - `src/app/layout.tsx`：全局布局与字体配置。
  - `src/app/globals.css`：全局样式（包含 Tailwind 引导）。
  - `src/components/editor/TiptapEditor.tsx`：Tiptap 编辑器组件。

## 初始化命令（已执行）

```bash
cd "D:\Project\Novel Agent Studio\frontend"
npx create-next-app@latest . --ts --tailwind --eslint --app --src-dir --use-npm --import-alias "@/ *" --yes
npm install @tiptap/react @tiptap/starter-kit
```

## 运行方式

```bash
cd "D:\Project\Novel Agent Studio\frontend"
npm run dev
```

访问 `http://localhost:3000` 即可看到 Tiptap 编辑器页面。

## 关键点说明

- 使用 `"use client"` 声明 `TiptapEditor` 为客户端组件（依赖浏览器事件）。
- 通过 `useEditor` 创建编辑器实例，将 `EditorContent` 渲染到页面。
- 当前模块仅实现前端编辑器，不与后端通信，后续会在此基础上接入多 Agent 与溯源信息。

