"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { Collaboration } from "@tiptap/extension-collaboration";
import { CollaborationCursor } from "@tiptap/extension-collaboration-cursor";
import * as Y from "yjs";
import { WebsocketProvider } from "y-websocket";

interface CollaborativeEditorProps {
  documentId: string;
  userName: string;
  userColor?: string;
  websocketUrl?: string;
  onContentChange?: (content: string) => void;
  className?: string;
}

interface AwarenessState {
  user: {
    name: string;
    color: string;
  };
}

/**
 * 协同编辑器组件
 * 基于 Tiptap + Yjs 实现多人实时协作编辑
 */
export const CollaborativeEditor: React.FC<CollaborativeEditorProps> = ({
  documentId,
  userName,
  userColor = "#ff0000",
  websocketUrl = "ws://localhost:1234",
  onContentChange,
  className = "",
}) => {
  const [ydoc] = useState(() => new Y.Doc());
  const [provider, setProvider] = useState<WebsocketProvider | null>(null);
  const [connected, setConnected] = useState(false);
  const [users, setUsers] = useState<AwarenessState[]>([]);

  // 初始化 WebSocket 连接
  useEffect(() => {
    const wsProvider = new WebsocketProvider(
      websocketUrl,
      documentId,
      ydoc
    );

    // 设置用户 awareness
    wsProvider.awareness.setLocalStateField("user", {
      name: userName,
      color: userColor,
    });

    // 监听连接状态
    wsProvider.on("status", (event: { status: string }) => {
      setConnected(event.status === "connected");
    });

    // 监听其他用户
    wsProvider.awareness.on("change", () => {
      const states = Array.from(wsProvider.awareness.getStates().values()) as AwarenessState[];
      setUsers(states.filter((state) => state.user));
    });

    setProvider(wsProvider);

    return () => {
      wsProvider.destroy();
    };
  }, [documentId, userName, userColor, websocketUrl, ydoc]);

  // 创建编辑器
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        // 历史记录由 Yjs 处理
      }),
      Collaboration.configure({
        document: ydoc,
      }),
      CollaborationCursor.configure({
        provider: provider || undefined,
        user: {
          name: userName,
          color: userColor,
        },
      }),
    ],
    editorProps: {
      attributes: {
        class:
          "prose dark:prose-invert max-w-none focus:outline-none min-h-[300px] p-4",
      },
    },
    onUpdate: ({ editor }) => {
      onContentChange?.(editor.getHTML());
    },
  });

  // 导出内容
  const exportContent = useCallback(() => {
    return editor?.getHTML() || "";
  }, [editor]);

  // 导入内容
  const importContent = useCallback(
    (content: string) => {
      editor?.commands.setContent(content);
    },
    [editor]
  );

  // 获取纯文本统计
  const getStats = useCallback(() => {
    const text = editor?.getText() || "";
    return {
      characters: text.length,
      words: text.trim().split(/\s+/).filter(Boolean).length,
    };
  }, [editor]);

  return (
    <div className={`border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden ${className}`}>
      {/* 工具栏 */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-4">
          {/* 连接状态 */}
          <div className="flex items-center space-x-2">
            <div
              className={`w-2 h-2 rounded-full ${
                connected ? "bg-green-500" : "bg-red-500"
              }`}
            />
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {connected ? "已连接" : "连接中..."}
            </span>
          </div>

          {/* 在线用户 */}
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-500 dark:text-gray-500">
              在线用户:
            </span>
            <div className="flex -space-x-2">
              {users.map((user, index) => (
                <div
                  key={index}
                  className="w-6 h-6 rounded-full flex items-center justify-center text-xs text-white font-medium border-2 border-white dark:border-gray-800"
                  style={{ backgroundColor: user.user.color }}
                  title={user.user.name}
                >
                  {user.user.name.charAt(0).toUpperCase()}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 编辑器工具 */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => editor?.chain().focus().toggleBold().run()}
            className={`p-2 rounded ${
              editor?.isActive("bold")
                ? "bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400"
                : "text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"
            }`}
            title="粗体"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M6 4h4a4 4 0 014 4 4 4 0 01-4 4H6V4zm0 8h5a4 4 0 014 4 4 4 0 01-4 4H6v-8z" />
            </svg>
          </button>
          <button
            onClick={() => editor?.chain().focus().toggleItalic().run()}
            className={`p-2 rounded ${
              editor?.isActive("italic")
                ? "bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400"
                : "text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"
            }`}
            title="斜体"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M8 4h2v12H8V4zm4 0h2v12h-2V4z" />
            </svg>
          </button>
          <button
            onClick={() => editor?.chain().focus().toggleHeading({ level: 2 }).run()}
            className={`p-2 rounded ${
              editor?.isActive("heading", { level: 2 })
                ? "bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400"
                : "text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"
            }`}
            title="标题"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4 4h2v5h8V4h2v12h-2v-5H6v5H4V4z" />
            </svg>
          </button>
          <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-2" />
          <button
            onClick={() => editor?.chain().focus().undo().run()}
            disabled={!editor?.can().undo()}
            className="p-2 rounded text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-50"
            title="撤销"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
            </svg>
          </button>
          <button
            onClick={() => editor?.chain().focus().redo().run()}
            disabled={!editor?.can().redo()}
            className="p-2 rounded text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-50"
            title="重做"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 10h-10a8 8 0 00-8 8v2M21 10l-6 6m6-6l-6-6" />
            </svg>
          </button>
        </div>
      </div>

      {/* 编辑器内容 */}
      <EditorContent editor={editor} />

      {/* 底部状态栏 */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
        <div className="flex items-center space-x-4">
          <span>{getStats().characters} 字符</span>
          <span>{getStats().words} 词</span>
        </div>
        <div>文档 ID: {documentId}</div>
      </div>
    </div>
  );
};

/**
 * 协同编辑钩子
 */
export function useCollaborativeEditor(
  documentId: string,
  userName: string,
  options?: {
    userColor?: string;
    websocketUrl?: string;
  }
) {
  const [ydoc] = useState(() => new Y.Doc());
  const [provider, setProvider] = useState<WebsocketProvider | null>(null);
  const [connected, setConnected] = useState(false);
  const [users, setUsers] = useState<string[]>([]);

  useEffect(() => {
    const wsProvider = new WebsocketProvider(
      options?.websocketUrl || "ws://localhost:1234",
      documentId,
      ydoc
    );

    wsProvider.awareness.setLocalStateField("user", {
      name: userName,
      color: options?.userColor || "#ff0000",
    });

    wsProvider.on("status", (event: { status: string }) => {
      setConnected(event.status === "connected");
    });

    wsProvider.awareness.on("change", () => {
      const states = Array.from(wsProvider.awareness.getStates().values()) as AwarenessState[];
      setUsers(states.filter((state) => state.user).map((state) => state.user.name));
    });

    setProvider(wsProvider);

    return () => {
      wsProvider.destroy();
    };
  }, [documentId, userName, options?.userColor, options?.websocketUrl, ydoc]);

  const getContent = useCallback(() => {
    return ydoc.getText("default").toString();
  }, [ydoc]);

  const setContent = useCallback(
    (content: string) => {
      const text = ydoc.getText("default");
      text.delete(0, text.length);
      text.insert(0, content);
    },
    [ydoc]
  );

  return {
    ydoc,
    provider,
    connected,
    users,
    getContent,
    setContent,
  };
}

export default CollaborativeEditor;
