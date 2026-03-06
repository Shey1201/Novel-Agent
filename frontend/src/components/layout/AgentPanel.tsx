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



export const AgentPanel: React.FC = () => {
  const { messages, addMessage, currentNovelId, currentChapterId, updateChapterContent, setWorldBible, setWorldApproved } =
    useNovelStore();
  const [inputValue, setEditValue] = useState("");
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
    push("User", "user", message);
    setEditValue("");

    try {
      const res = await fetch("http://127.0.0.1:8000/api/agent/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, story_id: "demo-story" }),
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
        <h2 className="text-sm font-bold text-zinc-800">Agent Room（讨论 / 命令）</h2>
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
