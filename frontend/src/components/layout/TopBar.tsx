"use client";

import React from "react";
import { useNovelStore, type WorkspaceModule } from "@/store/novelStore";

interface TopBarProps {
  // 所有操作已移至对话框，此组件不再需要props
}

const WritingModeSwitch: React.FC = () => {
  const { writingMode, setWritingMode } = useNovelStore();
  const modes: Array<{ key: "manual" | "ai-assisted" | "ai-writer"; name: string }> = [
    { key: "manual", name: "Manual" },
    { key: "ai-assisted", name: "Assist" },
    { key: "ai-writer", name: "Auto" },
  ];

  return (
    <div className="flex items-center rounded-lg bg-zinc-100 p-1 border border-zinc-200">
      {[...modes].reverse().map((mode) => (
        <button
          key={mode.key}
          onClick={() => setWritingMode(mode.key)}
          className={`px-4 py-1 text-xs font-semibold rounded-md transition-all ${
            writingMode === mode.key 
              ? "bg-indigo-600 text-white shadow-sm" 
              : "text-zinc-400 hover:text-zinc-600"
          }`}
        >
          {mode.name}
        </button>
      ))}
    </div>
  );
};

export const TopBar: React.FC<TopBarProps> = () => {
  const {
    workspaceModule,
    setWorkspaceModule,
    novels,
    currentNovelId,
    setCurrentNovelId,
    currentChapterId,
    agents,
    updateAgent,
    constraints,
    addConstraint,
    removeConstraint,
    agentConfigs,
    updateAgentConfig,
  } = useNovelStore();
  const currentNovel = novels.find(n => n.id === currentNovelId);

  // 只有在选中小说且在工作区模块为 novels 时才显示操作按钮
  const showNovelActions = currentNovel && workspaceModule === 'novels';

  return (
    <header className="flex h-12 items-center justify-between border-b border-zinc-200 bg-white px-4 shrink-0 relative z-30 shadow-sm">
      <div className="flex items-center gap-4 min-w-0">
        {showNovelActions && (
          <>
            <button
              onClick={() => setCurrentNovelId(null)}
              className="flex items-center gap-1 text-zinc-400 hover:text-indigo-600 transition-colors"
              title="返回书库"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m15 18-6-6 6-6"/></svg>
            </button>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-zinc-800 truncate max-w-[300px]">{currentNovel.title}</h2>
            </div>
            <div className="h-4 w-[1px] bg-zinc-200" />
          </>
        )}
      </div>

      <div className="flex items-center gap-4">
        {showNovelActions && (
          <>
            <WritingModeSwitch />
          </>
        )}
      </div>
    </header>
  );
};
