"use client";

import React, { useRef, useState } from "react";
import { MainSidebar } from "@/components/layout/MainSidebar";
import { SecondarySidebar } from "@/components/layout/SecondarySidebar";
import { AgentPanel } from "@/components/layout/AgentPanel";
import { TopBar } from "@/components/layout/TopBar";
import { TiptapEditor, type TiptapEditorHandle } from "@/components/editor/TiptapEditor";
import { useNovelStore } from "@/store/novelStore";
import AgentManagement from "@/components/workspace/agent-management";
import StoryAssets from "@/components/workspace/story-assets";
import SkillsManagement from "@/components/workspace/skills";
import Settings, { SettingsModal } from "@/components/workspace/settings";
import Library from "@/components/workspace/library";
import RecycleBin from "@/components/workspace/recycle-bin";

export default function Home() {
  const editorRef = useRef<TiptapEditorHandle>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
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

  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  const handleSave = async () => {
    if (!currentNovelId || !currentChapterId || !currentChapter) return;
    
    setSaveStatus('saving');
    try {
      const response = await fetch("http://127.0.0.1:8000/api/novel/draft", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          novel_id: currentNovelId,
          chapter_id: currentChapterId,
          content: currentChapter.content,
        }),
      });
      
      if (response.ok) {
        setSaveStatus('saved');
        setTimeout(() => setSaveStatus('idle'), 2000);
      } else {
        setSaveStatus('error');
      }
    } catch (error) {
      console.error("Save failed:", error);
      setSaveStatus('error');
    }
  };

  // 判断是否处于小说编辑模式
  const isNovelEditingMode = workspaceModule === 'novels' && currentNovelId;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-zinc-50 font-sans text-zinc-900">
      <MainSidebar />

      <div className="flex flex-1 flex-col min-w-0 overflow-hidden">
        <TopBar />

        <div className="flex flex-1 min-h-0 overflow-hidden">
          {/* 只在小说编辑模式显示二级侧边栏 */}
          {isNovelEditingMode && <SecondarySidebar />}

          <main className="flex flex-1 flex-col min-w-0 bg-white relative shadow-2xl z-10 border-x border-zinc-200">
            <div className="flex-1 overflow-y-auto bg-white">
              {workspaceModule === 'novels' && !currentNovelId && <Library />}

              {workspaceModule === 'novels' && currentNovelId && currentSidebarView === 'chapter' && (
                <div className="w-full max-w-3xl mx-auto p-8 space-y-4">
                  <div className="flex items-center justify-between border-b border-zinc-200 pb-2">
                    <input
                      value={currentChapter?.title || ''}
                      onChange={(e) => currentNovel && currentChapter && updateChapterTitle(currentNovel.id, currentChapter.id, e.target.value)}
                      className="flex-1 text-2xl font-bold outline-none bg-transparent"
                      placeholder="请输入章节标题..."
                    />
                    <div className="flex items-center gap-2">
                      {saveStatus === 'saved' && <span className="text-[10px] text-emerald-600 font-bold animate-pulse">已保存</span>}
                      {saveStatus === 'error' && <span className="text-[10px] text-red-500 font-bold">保存失败</span>}
                      <button
                        onClick={handleSave}
                        disabled={saveStatus === 'saving'}
                        className={`flex items-center gap-2 rounded-lg px-4 py-1.5 text-xs font-bold text-white shadow-sm transition-all ${
                          saveStatus === 'saving' ? 'bg-zinc-400' : 'bg-indigo-600 hover:bg-indigo-700'
                        }`}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
                        <span>{saveStatus === 'saving' ? '保存中...' : '保存'}</span>
                      </button>
                    </div>
                  </div>
                  <div className="text-xs text-zinc-500">Outline：建议在右侧 Agent Room 使用 /outline 生成。</div>
                  <TiptapEditor ref={editorRef} />
                </div>
              )}

              {workspaceModule === 'novels' && currentNovelId && currentSidebarView === 'outline' && (
                <div className="p-8">
                  <Panel title="Global Outline" content="在右侧 Room 使用 /generate outline 或 /outline 进行讨论并生成全局大纲。" />
                </div>
              )}

              {workspaceModule === 'agent-management' && (
                <div className="p-4">
                  <AgentManagement />
                </div>
              )}

              {workspaceModule === 'story-assets' && (
                <div className="h-full">
                  <StoryAssets />
                </div>
              )}

              {workspaceModule === 'skills' && (
                <div className="h-full">
                  <SkillsManagement />
                </div>
              )}

              {workspaceModule === 'settings' && (
                <div className="p-8">
                  <Settings />
                </div>
              )}

              {/* Settings Modal */}
              <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />

              {workspaceModule === 'recycle-bin' && (
                <div className="p-8">
                  <RecycleBin />
                </div>
              )}
            </div>
          </main>

          {/* 只在小说编辑模式显示 Agent Panel */}
          {isNovelEditingMode && <AgentPanel />}
        </div>
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
