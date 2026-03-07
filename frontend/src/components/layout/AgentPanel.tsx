"use client";

import React, { useState, useRef, useEffect } from "react";
import { useNovelStore } from "@/store/novelStore";

interface ChatResponse {
  final_text?: string;
  world_bible?: { world_view?: string; rules?: string; themes?: string[] };
  approved?: boolean;
  context?: { recent_summaries?: string[] };
  agent_logs?: Array<{ agent?: string; message?: string; content?: string }>;
}

// 字数范围选项
const WORD_COUNT_OPTIONS = [
  { label: "短篇 (1000-2000字)", min: 1000, max: 2000 },
  { label: "中篇 (2000-3000字)", min: 2000, max: 3000 },
  { label: "标准 (3000-4000字)", min: 3000, max: 4000 },
  { label: "长篇 (4000-6000字)", min: 4000, max: 6000 },
  { label: "超长 (6000-10000字)", min: 6000, max: 10000 },
];

export const AgentPanel: React.FC = () => {
  const { messages, addMessage, currentNovelId, currentChapterId, updateChapterContent, setWorldBible, setWorldApproved } =
    useNovelStore();
  const [inputValue, setEditValue] = useState("");
  const [selectedWordCount, setSelectedWordCount] = useState(WORD_COUNT_OPTIONS[2]); // 默认标准
  const [showSettings, setShowSettings] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const seqRef = useRef(100);



  const nextMeta = () => {
    seqRef.current += 1;
    return { id: `msg-${seqRef.current}`, timestamp: seqRef.current };
  };

  const push = (sender: string, role: "user" | "agent", content: string) => {
    const meta = nextMeta();
    addMessage({ ...meta, sender, role, content });
  };

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim()) return;
    const message = inputValue.trim();
    
    // 添加字数范围信息到消息中
    const messageWithWordCount = message.startsWith('/write') || message.startsWith('/continue') || message.startsWith('/generate')
      ? `${message} [字数范围: ${selectedWordCount.min}-${selectedWordCount.max}字]`
      : message;
    
    push("User", "user", messageWithWordCount);
    setEditValue("");

    try {
      const res = await fetch("http://127.0.0.1:8000/api/agent/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message, 
          story_id: "demo-story",
          word_count_range: {
            min: selectedWordCount.min,
            max: selectedWordCount.max
          }
        }),
      });
      const data = (await res.json()) as ChatResponse;

      data.agent_logs?.forEach((log) => {
        const text = log.content ? `${log.message || ""}\n${String(log.content)}` : log.message || "";
        push(log.agent || "agent", "agent", text);
      });

      if (data.context?.recent_summaries?.length) {
        push("system", "agent", `Recent Chapters:\n${data.context.recent_summaries.join("\n")}`);
      }

      if (data.world_bible) {
        setWorldBible({
          world_view: data.world_bible.world_view,
          rules: data.world_bible.rules,
          themes: data.world_bible.themes || [],
        });
      }
      if (typeof data.approved === "boolean") {
        setWorldApproved(data.approved);
      }

      if (
        data.final_text &&
        currentNovelId &&
        currentChapterId &&
        (message.startsWith("/write") || message.startsWith("/continue") || message.startsWith("/rewrite") || message.startsWith("/generate"))
      ) {
        updateChapterContent(currentNovelId, currentChapterId, data.final_text);
      }
    } catch (error) {
      push("system", "agent", `Agent Room 请求失败: ${String(error)}`);
    }
  };

  return (
    <aside className="w-96 border-l border-zinc-200 bg-zinc-50 flex flex-col h-full shrink-0 shadow-sm">
      <div className="p-4 border-b border-zinc-200 bg-white shrink-0">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-zinc-800">Agent Room</h2>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-1.5 text-zinc-400 hover:text-indigo-600 hover:bg-zinc-100 rounded-lg transition-colors"
            title="生成设置"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
          </button>
        </div>
        <p className="mt-1.5 text-[10px] text-zinc-400">找找灵感来 battle 一下吧</p>
        
        {/* 生成设置面板 */}
        {showSettings && (
          <div className="mt-3 pt-3 border-t border-zinc-200">
            <label className="block text-xs font-medium text-zinc-600 mb-2">
              每章生成字数范围
            </label>
            <select
              value={selectedWordCount.label}
              onChange={(e) => {
                const option = WORD_COUNT_OPTIONS.find(o => o.label === e.target.value);
                if (option) setSelectedWordCount(option);
              }}
              className="w-full px-3 py-2 text-sm bg-zinc-50 border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
            >
              {WORD_COUNT_OPTIONS.map((option) => (
                <option key={option.label} value={option.label}>
                  {option.label}
                </option>
              ))}
            </select>
            <p className="mt-1.5 text-[10px] text-zinc-400">
              当前选择: {selectedWordCount.min.toLocaleString()}-{selectedWordCount.max.toLocaleString()} 字
            </p>
          </div>
        )}
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}>
            <div className="flex items-center gap-2 mb-1 px-1">
              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">{msg.sender}</span>
            </div>
            <div className={`max-w-[90%] whitespace-pre-wrap p-3 rounded-2xl text-sm shadow-sm ${msg.role === "user" ? "bg-indigo-600 text-white rounded-tr-none" : "bg-white text-zinc-700 border border-zinc-100 rounded-tl-none"}`}>
              {msg.content}
            </div>
          </div>
        ))}
      </div>

      <div className="p-4 bg-white border-t border-zinc-200 shrink-0">
        <div className="relative">
          <textarea
            value={inputValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), handleSend())}
            placeholder="在 Room 中与 Agent 聊天，例如：/start chapter 8"
            className="w-full pl-3 pr-10 py-2.5 bg-zinc-50 border border-zinc-200 rounded-xl text-sm resize-none h-20"
          />
          <button onClick={handleSend} className="absolute right-2 bottom-2 w-7 h-7 bg-indigo-600 text-white rounded-lg">↗</button>
        </div>
      </div>
    </aside>
  );
};
