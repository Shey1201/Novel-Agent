"use client";

import React, { useState, useRef, useCallback } from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";

interface StreamWriteProps {
  novelId: string;
  chapterId: string;
  planText: string;
  onComplete?: (text: string) => void;
  onSave?: (text: string) => void;
}

export const StreamingEditor: React.FC<StreamWriteProps> = ({
  novelId,
  chapterId,
  planText,
  onComplete,
  onSave,
}) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<string>("");
  const [generatedText, setGeneratedText] = useState("");
  const abortControllerRef = useRef<AbortController | null>(null);

  const editor = useEditor({
    extensions: [StarterKit],
    content: "",
    editable: !isGenerating,
  });

  const startStreaming = useCallback(async () => {
    if (isGenerating) return;

    setIsGenerating(true);
    setProgress(0);
    setGeneratedText("");
    editor?.commands.setContent("");

    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch("http://localhost:8000/api/stream/write", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          novel_id: novelId,
          chapter_id: chapterId,
          plan_text: planText,
          writing_mode: "ai-assisted",
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error("Failed to start streaming");
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("No reader available");
      }

      const decoder = new TextDecoder();
      let accumulatedText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));

              switch (data.type) {
                case "start":
                  setStatus("准备生成...");
                  break;

                case "progress":
                  setStatus(
                    data.data.step === "context_ready"
                      ? `上下文准备完成 (${data.data.tokens} tokens)`
                      : "正在生成..."
                  );
                  break;

                case "token":
                  accumulatedText += data.content;
                  setGeneratedText(accumulatedText);
                  editor?.commands.setContent(accumulatedText);
                  setProgress((prev) => Math.min(prev + 1, 95));
                  break;

                case "complete":
                  setStatus("生成完成");
                  setProgress(100);
                  setIsGenerating(false);
                  onComplete?.(accumulatedText);
                  break;

                case "error":
                  setStatus(`错误: ${data.data.message}`);
                  setIsGenerating(false);
                  break;
              }
            } catch (e) {
              console.error("Failed to parse SSE data:", e);
            }
          }
        }
      }
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        setStatus("已取消");
      } else {
        setStatus(`错误: ${error instanceof Error ? error.message : "未知错误"}`);
      }
      setIsGenerating(false);
    }
  }, [novelId, chapterId, planText, editor, onComplete, isGenerating]);

  const stopStreaming = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsGenerating(false);
    setStatus("已停止");
  }, []);

  const handleSave = useCallback(() => {
    const content = editor?.getText() || "";
    onSave?.(content);
  }, [editor, onSave]);

  return (
    <div className="flex flex-col h-full bg-white rounded-xl border border-zinc-200 overflow-hidden">
      {/* 工具栏 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-200 bg-zinc-50">
        <div className="flex items-center gap-4">
          <h3 className="font-bold text-zinc-800">✍️ AI 流式写作</h3>
          
          {isGenerating && (
            <div className="flex items-center gap-2 text-sm text-zinc-600">
              <span className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse" />
              {status}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {!isGenerating ? (
            <button
              onClick={startStreaming}
              disabled={!planText}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:bg-zinc-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
              开始生成
            </button>
          ) : (
            <button
              onClick={stopStreaming}
              className="px-4 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors flex items-center gap-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="6" y="4" width="4" height="16" />
                <rect x="14" y="4" width="4" height="16" />
              </svg>
              停止
            </button>
          )}

          <button
            onClick={handleSave}
            disabled={!generatedText}
            className="px-4 py-2 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 disabled:bg-zinc-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
              <polyline points="17 21 17 13 7 13 7 21" />
              <polyline points="7 3 7 8 15 8" />
            </svg>
            保存
          </button>
        </div>
      </div>

      {/* 进度条 */}
      {isGenerating && (
        <div className="h-1 bg-zinc-100">
          <div
            className="h-full bg-indigo-600 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {/* 编辑器 */}
      <div className="flex-1 overflow-y-auto">
        <EditorContent
          editor={editor}
          className="prose prose-zinc max-w-none p-6 focus:outline-none"
        />
      </div>

      {/* 底部状态 */}
      <div className="px-4 py-2 border-t border-zinc-200 bg-zinc-50 text-xs text-zinc-500 flex items-center justify-between">
        <span>
          {generatedText.length > 0 && `${generatedText.length} 字符`}
        </span>
        <span>{status}</span>
      </div>
    </div>
  );
};
