"use client";

import React, { useState } from "react";

export const ChatBar: React.FC = () => {
  const [message, setMessage] = useState("");

  const handleSendMessage = () => {
    if (message.trim()) {
      // 这里的逻辑后续可以与后端对话接口对接
      setMessage("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="border-t border-zinc-200 p-4 bg-zinc-50/50">
      <div className="max-w-4xl mx-auto space-y-4">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-full bg-zinc-200 flex-shrink-0 flex items-center justify-center text-xs text-zinc-500 font-bold">SYS</div>
          <div className="space-y-1">
            <span className="text-xs font-bold text-zinc-500">系统</span>
            <p className="text-sm text-zinc-600 italic">欢迎来到 AI 写作室。请告诉我您想写什么样的故事（例如，“一个发生在‘新东京’的赛博朋克侦探故事”），我将帮助您完成设定。</p>
          </div>
        </div>
        
        <div className="flex gap-2">
          <button className="px-3 py-1 bg-purple-50 text-purple-600 text-[10px] font-bold rounded-full border border-purple-100 flex items-center gap-1 hover:bg-purple-100 transition-colors">✨ 生成章节</button>
          <button className="px-3 py-1 bg-blue-50 text-blue-600 text-[10px] font-bold rounded-full border border-blue-100 flex items-center gap-1 hover:bg-blue-100 transition-colors">🔄 重写</button>
          <button className="px-3 py-1 bg-green-50 text-green-600 text-[10px] font-bold rounded-full border border-green-100 flex items-center gap-1 hover:bg-green-100 transition-colors">⏩ 继续</button>
        </div>

        <div className="relative">
          <textarea 
            rows={1}
            placeholder="输入指令 (/generate) 或与 Agent 讨论..." 
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full pl-4 pr-12 py-3 bg-white border border-zinc-200 rounded-xl shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all resize-none"
          />
          <button 
            onClick={handleSendMessage}
            className="absolute right-3 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
          >
            <span className="text-xs font-bold">✈️</span>
          </button>
        </div>
      </div>
    </div>
  );
};
