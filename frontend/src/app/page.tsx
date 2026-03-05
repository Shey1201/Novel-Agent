"use client";

import React, { useRef, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { AgentPanel } from "@/components/layout/AgentPanel";
import { TopBar } from "@/components/layout/TopBar";
import { ChatBar } from "@/components/layout/ChatBar";
import { TiptapEditor } from "@/components/editor/TiptapEditor";

export default function Home() {
  const editorRef = useRef<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const handleRunAgents = async () => {
    if (editorRef.current) {
      setIsProcessing(true);
      await editorRef.current.handleRunAgents();
      setIsProcessing(false);
    }
  };

  const handleSaveChapter = async () => {
    if (!editorRef.current?.handleSaveChapter) return;
    setIsSaving(true);
    await editorRef.current.handleSaveChapter();
    setTimeout(() => setIsSaving(false), 500);
  };

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-zinc-50 font-sans text-zinc-900">
      {/* Top Bar */}
      <TopBar onRunAgents={handleRunAgents} isProcessing={isProcessing} />

      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Left Sidebar */}
        <Sidebar />

        {/* Main Content Area */}
        <main className="flex flex-1 flex-col min-w-0 bg-white relative shadow-2xl z-10 border-x border-zinc-200">
          <div className="flex items-center justify-end border-b border-zinc-100 px-6 py-3">
            <button
              onClick={handleSaveChapter}
              className="flex items-center gap-2 rounded-lg border border-indigo-200 bg-indigo-50 px-4 py-1.5 text-xs font-bold text-indigo-700 hover:bg-indigo-100 transition-colors"
            >
              <span>{isSaving ? "保存中..." : "保存章节"}</span>
            </button>
          </div>
          {/* Editor Area */}
          <div className="flex-1 overflow-y-auto p-12 flex justify-center scrollbar-hide bg-white">
            <div className="w-full max-w-2xl">
              <TiptapEditor ref={editorRef} />
            </div>
          </div>
        </main>

        {/* Right Sidebar - Agent Panel */}
        <AgentPanel />
      </div>
    </div>
  );
}
