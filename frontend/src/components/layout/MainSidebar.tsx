"use client";

import React, { useState } from "react";
import { useNovelStore, type WorkspaceModule } from "@/store/novelStore";
import { SettingsModal } from "@/components/workspace/settings";

const navItems: Array<{ key: WorkspaceModule; label: string; icon: React.ReactNode }> = [
  {
    key: "novels",
    label: "Library",
    icon: <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
  },
  {
    key: "story-assets",
    label: "Story Assets",
    icon: <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><path d="M8 6h10"/><path d="M8 10h10"/><path d="M8 14h10"/></svg>
  },
  {
    key: "agent-management",
    label: "Agent Management",
    icon: <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
  },
  {
    key: "skills",
    label: "Agent Skills",
    icon: <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
  },
];

export const MainSidebar: React.FC = () => {
  const { workspaceModule, setWorkspaceModule, setCurrentNovelId } = useNovelStore();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const handleNavClick = (key: WorkspaceModule) => {
    setWorkspaceModule(key);
    if (key === 'novels') {
      setCurrentNovelId(null);
    }
  };

  return (
    <>
      <aside className="w-16 border-r border-zinc-200 bg-zinc-50 flex flex-col items-center py-4 shrink-0 shadow-sm z-20">
        {/* 小说工作室图标 - 最上方（纯装饰，不可点击） */}
        <div
          title="小说工作室"
          className="p-3 rounded-xl mb-6 bg-zinc-800 text-white shadow-lg cursor-default"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/>
            <path d="M8 6h10"/>
            <path d="M8 10h10"/>
            <path d="M8 14h6"/>
          </svg>
        </div>

        <div className="flex flex-col gap-4 flex-1">
          {navItems.map((item) => (
            <button
              key={item.key}
              onClick={() => handleNavClick(item.key)}
              title={item.label}
              className={`p-3 rounded-xl transition-all ${
                workspaceModule === item.key
                  ? "bg-zinc-200 text-zinc-800"
                  : "text-zinc-400 hover:bg-zinc-200 hover:text-zinc-600"
              }`}
            >
              {item.icon}
            </button>
          ))}
        </div>

        <div className="flex flex-col gap-4 mt-auto">
          <button
            onClick={() => setWorkspaceModule('recycle-bin')}
            title="Recycle Bin"
            className={`p-3 rounded-xl transition-all ${
              workspaceModule === 'recycle-bin'
                ? "bg-zinc-200 text-zinc-800"
                : "text-zinc-400 hover:bg-zinc-200 hover:text-zinc-600"
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
          </button>

          <button
            onClick={() => setIsSettingsOpen(true)}
            title="Settings"
            className={`p-3 rounded-xl transition-all ${
              isSettingsOpen
                ? "bg-zinc-200 text-zinc-800"
                : "text-zinc-400 hover:bg-zinc-200 hover:text-zinc-600"
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          </button>
        </div>
      </aside>

      {/* Settings Modal */}
      <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
    </>
  );
};
