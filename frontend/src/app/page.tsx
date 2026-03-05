"use client";

import React, { useRef, useState } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { AgentPanel } from "@/components/layout/AgentPanel";
import { TopBar } from "@/components/layout/TopBar";
import { TiptapEditor, type TiptapEditorHandle } from "@/components/editor/TiptapEditor";
import { useNovelStore } from "@/store/novelStore";

export default function Home() {
  const editorRef = useRef<TiptapEditorHandle>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const {
    workspaceModule,
    currentSidebarView,
    selectedAssetCategory,
    storyAssets,
    currentNovelId,
    novels,
    currentChapterId,
    updateChapterTitle,
    agents,
    updateAgent,
  } = useNovelStore();

  const currentNovel = novels.find((n) => n.id === currentNovelId);
  const currentChapter = currentNovel?.chapters.find((c) => c.id === currentChapterId);

  const handleRunAgents = async () => {
    if (editorRef.current) {
      setIsProcessing(true);
      await editorRef.current.handleRunAgents();
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-zinc-50 font-sans text-zinc-900">
      <TopBar onRunAgents={handleRunAgents} isProcessing={isProcessing} />

      <div className="flex flex-1 min-h-0 overflow-hidden">
        <Sidebar />

        <main className="flex flex-1 flex-col min-w-0 bg-white relative shadow-2xl z-10 border-x border-zinc-200">
          <div className="flex-1 overflow-y-auto p-8 bg-white">
            {workspaceModule === 'novels' && currentSidebarView === 'chapter' && (
              <div className="w-full max-w-3xl mx-auto space-y-4">
                <input
                  value={currentChapter?.title || ''}
                  onChange={(e) => currentNovel && currentChapter && updateChapterTitle(currentNovel.id, currentChapter.id, e.target.value)}
                  className="w-full text-2xl font-bold border-b border-zinc-200 pb-2 outline-none"
                />
                <div className="text-xs text-zinc-500">Outline：建议在右侧 Agent Room 使用 /outline 生成。</div>
                <TiptapEditor ref={editorRef} />
              </div>
            )}

            {workspaceModule === 'novels' && currentSidebarView === 'outline' && (
              <Panel title="Global Outline" content="在右侧 Room 使用 /generate outline 或 /outline 进行讨论并生成全局大纲。" />
            )}

            {workspaceModule === 'agent-management' && (
              <div className="max-w-3xl mx-auto border border-zinc-200 rounded-xl bg-zinc-50 p-6 space-y-3">
                <h2 className="text-lg font-bold">Agent Management</h2>
                {agents.map((agent) => (
                  <div key={agent.id} className="bg-white border border-zinc-200 rounded-lg p-3 space-y-2">
                    <div className="font-semibold">{agent.name}</div>
                    <input value={agent.role} onChange={(e) => updateAgent(agent.id, { role: e.target.value })} className="w-full text-sm border rounded px-2 py-1" />
                    <input value={agent.prompt} onChange={(e) => updateAgent(agent.id, { prompt: e.target.value })} className="w-full text-xs border rounded px-2 py-1" />
                  </div>
                ))}
              </div>
            )}

            {workspaceModule === 'story-assets' && (
              <div className="max-w-3xl mx-auto border border-zinc-200 rounded-xl bg-zinc-50 p-6 space-y-3">
                <h2 className="text-lg font-bold">Story Assets / {selectedAssetCategory}</h2>
                {(storyAssets[selectedAssetCategory] || []).map((asset) => (
                  <div key={asset.id} className="bg-white border border-zinc-200 rounded-lg p-3 text-sm flex items-center justify-between">
                    <span>{asset.name}</span>
                    <span className="text-xs text-zinc-400">source: {asset.novelId}</span>
                  </div>
                ))}
                <p className="text-xs text-zinc-500">每部小说可按需引用其它小说的资产（角色/世界观/时间线）。</p>
              </div>
            )}

            {workspaceModule === 'settings' && (
              <div className="max-w-3xl mx-auto border border-zinc-200 rounded-xl bg-zinc-50 p-6 space-y-3">
                <h2 className="text-lg font-bold">Settings</h2>
                {['API Keys', 'Appearance', 'Model Defaults', 'System'].map((x) => (
                  <div key={x} className="bg-white border border-zinc-200 rounded-lg p-3 text-sm">{x}</div>
                ))}
              </div>
            )}
          </div>
        </main>

        <AgentPanel />
      </div>
    </div>
  );
}

function Panel({ title, content }: { title: string; content: string }) {
  return (
    <div className="max-w-3xl mx-auto border border-zinc-200 rounded-xl bg-zinc-50 p-6">
      <h2 className="text-lg font-bold mb-3">{title}</h2>
      <p className="text-sm whitespace-pre-wrap text-zinc-700">{content}</p>
    </div>
  );
}
