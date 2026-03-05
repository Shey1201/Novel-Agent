"use client";

import React, { useState } from "react";
import { useNovelStore } from "@/store/novelStore";

export const Sidebar: React.FC = () => {
  const {
    novels,
    currentNovelId,
    setCurrentNovelId,
    currentChapterId,
    setCurrentChapterId,
    addChapter,
    updateNovel,
    deleteNovel,
  } = useNovelStore();
  const [editingNovelId, setEditingNovelId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  const currentNovel = novels.find((n) => n.id === currentNovelId);

  const handleAddChapter = () => {
    if (!currentNovelId) return;
    const newId = `chapter-${currentNovelId}-${(currentNovel?.chapters.length || 0) + 1}`;
    addChapter(currentNovelId, {
      id: newId,
      title: `新章节 ${(currentNovel?.chapters.length || 0) + 1}`,
      content: "",
      trace_data: [],
    });
    setCurrentChapterId(newId);
  };

  const startEditing = (novel: { id: string; title: string }) => {
    setEditingNovelId(novel.id);
    setEditTitle(novel.title);
  };

  const saveEdit = (id: string) => {
    updateNovel(id, { title: editTitle });
    setEditingNovelId(null);
  };

  return (
    <aside className="flex w-64 flex-col border-r border-zinc-200 bg-white h-full shrink-0">
      <div className="p-4 border-b border-zinc-100 flex items-center gap-3">
        <span className="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center text-indigo-600 text-lg">
          📖
        </span>
        <h1 className="text-sm font-bold text-zinc-800">小说工作室</h1>
      </div>

      <div className="flex-1 overflow-y-auto flex flex-col p-4">
        <button
          onClick={handleAddChapter}
          className="w-full py-4 mb-6 border-2 border-dashed border-zinc-200 rounded-xl text-xs text-zinc-400 hover:border-indigo-300 hover:text-indigo-500 hover:bg-indigo-50/30 transition-all flex items-center justify-center gap-2 group"
        >
          <span className="text-lg group-hover:scale-110 transition-transform">+</span>
          <span>Add Chapter</span>
        </button>

        {/* Novel List Section */}
        <div className="mb-6">
          <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3 px-2">我的小说</div>
          <div className="space-y-1">
            {novels.map((novel) => (
              <div key={novel.id} className="group relative">
                {editingNovelId === novel.id ? (
                  <div className="flex gap-1 p-1">
                    <input
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onBlur={() => saveEdit(novel.id)}
                      onKeyDown={(e) => e.key === "Enter" && saveEdit(novel.id)}
                      autoFocus
                      className="flex-1 text-sm border border-indigo-300 rounded px-2 py-1 outline-none"
                    />
                  </div>
                ) : (
                  <div className="flex items-center">
                    <button
                      onClick={() => setCurrentNovelId(novel.id)}
                      className={`flex-1 text-left px-3 py-2 rounded-lg text-sm transition-all ${
                        currentNovelId === novel.id
                          ? "bg-indigo-50 text-indigo-700 font-semibold"
                          : "text-zinc-600 hover:bg-zinc-50"
                      }`}
                    >
                      {novel.title}
                    </button>
                    <div className="absolute right-2 opacity-0 group-hover:opacity-100 flex gap-1 transition-opacity">
                      <button onClick={() => startEditing(novel)} className="p-1 hover:text-indigo-600 text-zinc-400">
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                      </button>
                      <button onClick={() => deleteNovel(novel.id)} className="p-1 hover:text-red-600 text-zinc-400">
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Chapter List Section */}
        <div className="flex-1">
          <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-3 px-2">章节列表</div>
          <div className="space-y-1">
            {currentNovel?.chapters.map((chapter) => (
              <button
                key={chapter.id}
                onClick={() => setCurrentChapterId(chapter.id)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all ${
                  currentChapterId === chapter.id
                    ? "bg-indigo-50 text-indigo-700 font-semibold border-l-4 border-indigo-600 pl-2"
                    : "text-zinc-600 hover:bg-zinc-50 pl-3"
                }`}
              >
                {chapter.title}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-zinc-100 flex items-center justify-between">
        <span className="text-[10px] text-zinc-400 font-medium tracking-tight">v2.0.0</span>
        <button className="p-1.5 hover:bg-zinc-100 rounded-md text-zinc-400 transition-colors">
          🌙
        </button>
      </div>
    </aside>
  );
};
