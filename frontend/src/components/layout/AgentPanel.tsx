"use client";

import React, { useState, useRef, useEffect } from "react";
import { useNovelStore } from "@/store/novelStore";

export const AgentPanel: React.FC = () => {
  const { messages, addMessage, agents, currentNovelId, currentChapterId, updateChapterContent } = useNovelStore();
  const [inputValue, setEditValue] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  const commands = [
    { cmd: "/discuss", desc: "讨论剧情" },
    { cmd: "/generate", desc: "生成章节" },
    { cmd: "/rewrite", desc: "重写章节" },
    { cmd: "/outline", desc: "生成大纲" },
  ];

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMsg = {
      id: Date.now().toString(),
      sender: "User",
      role: "user" as const,
      content: inputValue,
      timestamp: Date.now(),
    };
    addMessage(userMsg);
    setEditValue("");

    // 模拟 Agent 讨论流程
    if (inputValue.startsWith("/")) {
      await simulateAgentFlow(inputValue);
    }
  };

  const simulateAgentFlow = async (cmd: string) => {
    const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

    // 1. Agent 讨论阶段
    const activeAgents = agents.filter(a => a.enabled && a.id !== 'writer');
    for (const agent of activeAgents) {
      await delay(1000 + Math.random() * 1000);
      addMessage({
        id: Date.now().toString(),
        sender: agent.name,
        role: "agent",
        content: getAgentResponse(agent.id, cmd),
        timestamp: Date.now(),
        agentId: agent.id
      });
    }

    // 2. Writer 生成阶段
    await delay(1500);
    const writer = agents.find(a => a.id === 'writer');
    const generatedContent = `<p>这是由 ${writer?.name} 根据指令 "${cmd}" 生成的内容...</p><p>在漆黑的夜里，刺客潜入了宫殿...</p>`;
    
    addMessage({
      id: Date.now().toString(),
      sender: writer?.name || "Writer Agent",
      role: "agent",
      content: "我已经根据大家的建议完成了内容生成，正在写入章节...",
      timestamp: Date.now(),
      agentId: writer?.id
    });

    // 3. 写入章节
    if (currentNovelId && currentChapterId) {
      updateChapterContent(currentNovelId, currentChapterId, generatedContent);
    }
  };

  const getAgentResponse = (id: string, cmd: string) => {
    const responses: Record<string, string[]> = {
      conflict: ["建议增加一个刺客角色", "冲突不够，可以让刺客刺杀主角", "这里可以增加一些环境压力"],
      editor: ["建议保留悬念", "节奏可以再紧凑一点", "注意词汇的多样性"],
      reader: ["这章节节奏太慢，需要增加冲突", "主角的动机稍微有点模糊", "这段对话很有趣！"],
      world: ["注意保持魔法体系的逻辑一致性", "这个地名在设定集中已经提到过了", "这种科技水平不符合当前世界观"],
      outline: ["章节承接很自然，但需要为下一章埋下伏笔", "建议在这里加入一个反转", "整体结构符合三幕式结构"],
    };
    const pool = responses[id] || ["我正在思考中..."];
    return pool[Math.floor(Math.random() * pool.length)];
  };

  return (
    <aside className="w-96 border-l border-zinc-200 bg-zinc-50 flex flex-col h-full shrink-0 shadow-sm">
      <div className="p-4 border-b border-zinc-200 bg-white flex items-center gap-2 shrink-0">
        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
        <h2 className="text-sm font-bold text-zinc-800">Agent Room</h2>
      </div>

      {/* 消息区域 */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
            <div className="flex items-center gap-2 mb-1 px-1">
              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">{msg.sender}</span>
              <span className="text-[9px] text-zinc-300">{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
            <div className={`max-w-[90%] p-3 rounded-2xl text-sm shadow-sm ${
              msg.role === 'user' 
                ? 'bg-indigo-600 text-white rounded-tr-none' 
                : 'bg-white text-zinc-700 border border-zinc-100 rounded-tl-none'
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
      </div>

      {/* 输入区域 */}
      <div className="p-4 bg-white border-t border-zinc-200 space-y-3 shrink-0">
        <div className="flex flex-wrap gap-1.5">
          {commands.map((c) => (
            <button
              key={c.cmd}
              onClick={() => setEditValue(c.cmd + " ")}
              className="px-2 py-1 bg-zinc-100 hover:bg-indigo-50 hover:text-indigo-600 text-[10px] font-bold text-zinc-500 rounded-md transition-all border border-zinc-200/50"
            >
              {c.cmd}
            </button>
          ))}
        </div>
        <div className="relative">
          <textarea
            value={inputValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
            placeholder="输入命令 (如 /generate) 或与 Agent 讨论..."
            className="w-full pl-3 pr-10 py-2.5 bg-zinc-50 border border-zinc-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all resize-none h-20"
          />
          <button
            onClick={handleSend}
            className="absolute right-2 bottom-2 w-7 h-7 flex items-center justify-center bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors shadow-sm"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
          </button>
        </div>
      </div>
    </aside>
  );
};
