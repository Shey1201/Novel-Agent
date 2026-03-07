"use client";

import React, { useRef, useState, useEffect } from "react";
import { MainSidebar } from "@/components/layout/MainSidebar";
import { SecondarySidebar } from "@/components/layout/SecondarySidebar";
import { AgentPanel } from "@/components/layout/AgentPanel";
import { TopBar } from "@/components/layout/TopBar";
import { TiptapEditor, type TiptapEditorHandle } from "@/components/editor/TiptapEditor";
import { StreamingEditor } from "@/components/editor/StreamingEditor";
import { AgentTimeline } from "@/components/visualization/AgentTimeline";
import { DownloadDialog } from "@/components/editor/DownloadDialog";
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
  const [showStreamingEditor, setShowStreamingEditor] = useState(false);
  const [showAgentTimeline, setShowAgentTimeline] = useState(false);
  const [showDownloadDialog, setShowDownloadDialog] = useState(false);
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

  // 监听打开下载对话框事件
  useEffect(() => {
    const handleOpenDownloadDialog = () => setShowDownloadDialog(true);
    window.addEventListener('openDownloadDialog', handleOpenDownloadDialog);
    return () => window.removeEventListener('openDownloadDialog', handleOpenDownloadDialog);
  }, []);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-zinc-50 font-sans text-zinc-900">
      <MainSidebar />

      <div className="flex flex-1 flex-col min-w-0 overflow-hidden">
        {/* 只在小说编辑模式显示顶栏 */}
        {isNovelEditingMode && <TopBar />}

        <div className={`flex flex-1 min-h-0 overflow-hidden ${!isNovelEditingMode ? 'pt-0' : ''}`}>
          {/* 只在小说编辑模式显示二级侧边栏 */}
          {isNovelEditingMode && <SecondarySidebar />}

          <main className="flex flex-1 flex-col min-w-0 bg-white relative shadow-2xl z-10 border-x border-zinc-200">
            <div className="flex-1 overflow-y-auto bg-white">
              {workspaceModule === 'novels' && !currentNovelId && <Library />}

              {workspaceModule === 'novels' && currentNovelId && currentSidebarView === 'chapter' && (
                <div className="w-full max-w-3xl mx-auto px-8 py-8 space-y-4">
                  <div className="flex items-center justify-between border-b border-zinc-200 pb-2">
                    <input
                      value={currentChapter?.title || ''}
                      onChange={(e) => currentNovel && currentChapter && updateChapterTitle(currentNovel.id, currentChapter.id, e.target.value)}
                      className="flex-1 text-2xl font-bold outline-none bg-transparent px-0"
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

          {/* 小说编辑模式下显示右侧聊天面板 */}
          {isNovelEditingMode && <AgentPanel />}
        </div>
      </div>

      {/* AI 写作弹窗 */}
      {showStreamingEditor && currentNovelId && currentChapterId && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-4xl h-[80vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-zinc-200">
              <h3 className="font-bold text-lg">✍️ AI 流式写作</h3>
              <button
                onClick={() => setShowStreamingEditor(false)}
                className="p-2 hover:bg-zinc-100 rounded-lg transition-colors"
              >
                ✕
              </button>
            </div>
            <div className="flex-1 p-4 overflow-hidden">
              <StreamingEditor
                novelId={currentNovelId}
                chapterId={currentChapterId}
                planText={currentChapter?.content?.substring(0, 500) || "继续故事"}
                onComplete={(text) => {
                  console.log("Generated:", text);
                }}
                onSave={(text) => {
                  if (currentNovel && currentChapter) {
                    // 保存生成的内容
                    console.log("Saving:", text);
                  }
                  setShowStreamingEditor(false);
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Agent 执行时间线弹窗 */}
      {showAgentTimeline && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-2xl h-[80vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-zinc-200">
              <h3 className="font-bold text-lg">⭐ Agent 执行过程</h3>
              <button
                onClick={() => setShowAgentTimeline(false)}
                className="p-2 hover:bg-zinc-100 rounded-lg transition-colors"
              >
                ✕
              </button>
            </div>
            <div className="flex-1 p-4 overflow-hidden">
              <AgentTimeline
                workflowId={`workflow-${currentNovelId}-${currentChapterId}`}
                onComplete={() => console.log("Workflow complete")}
              />
            </div>
          </div>
        </div>
      )}

      {/* 下载对话框 - 渲染在最外层避免被遮挡 */}
      {currentNovelId && (
        <DownloadDialog
          isOpen={showDownloadDialog}
          onClose={() => setShowDownloadDialog(false)}
          novelId={currentNovelId}
        />
      )}
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
