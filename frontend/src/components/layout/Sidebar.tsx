"use client";

import React, { useMemo, useState } from "react";
import { useNovelStore, type SidebarView } from "@/store/novelStore";

const novelNodes: Array<{ key: SidebarView; label: string; icon: string }> = [
  { key: "chapter", label: "Chapter", icon: "📄" },
  { key: "outline", label: "Global Outline", icon: "◫" },
];

export const Sidebar: React.FC = () => {
  const {
    novels,
    currentNovelId,
    currentChapterId,
    setCurrentNovelId,
    setCurrentChapterId,
    currentSidebarView,
    setCurrentSidebarView,
    addChapter,
  } = useNovelStore();

  const [expandChapters, setExpandChapters] = useState(true);
  const currentNovel = useMemo(() => novels.find((n) => n.id === currentNovelId), [novels, currentNovelId]);

  const addNewChapter = () => {
    if (!currentNovelId) return;
    const next = (currentNovel?.chapters.length || 0) + 1;
    const id = `chapter-${currentNovelId}-${next}`;
    addChapter(currentNovelId, { id, title: `章节 ${next}`, content: "", trace_data: [] });
    setCurrentChapterId(id);
    setCurrentSidebarView("chapter");
  };

  return (
    <aside className="w-72 border-r border-zinc-300 bg-zinc-100 h-full shrink-0 flex flex-col">
      <div className="px-3 py-3 border-b border-zinc-300 space-y-2">
        <div className="text-[10px] uppercase tracking-widest text-zinc-400 font-bold">Novels</div>
        <select
          value={currentNovelId || ""}
          onChange={(e) => setCurrentNovelId(e.target.value)}
          className="w-full border border-zinc-300 rounded-md px-2 py-1.5 text-sm bg-white"
        >
          {novels.map((novel) => (
            <option key={novel.id} value={novel.id}>
              {novel.title}
            </option>
          ))}
        </select>
      </div>

      <div className="p-3 space-y-2 overflow-y-auto">
        {novelNodes.map((node) => (
          <Item
            key={node.key}
            icon={node.icon}
            label={node.label}
            active={currentSidebarView === node.key}
            onClick={() => setCurrentSidebarView(node.key)}
          />
        ))}

        <div className="flex items-center justify-between px-1 mt-2">
          <button
            onClick={() => setExpandChapters((v) => !v)}
            className="text-[13px] uppercase tracking-wider text-zinc-500 font-bold"
          >
            {expandChapters ? "⌄" : "›"} Chapters
          </button>
          <button onClick={addNewChapter} className="text-indigo-500 font-bold">
            ＋
          </button>
        </div>

        {expandChapters && (
          <div className="pl-2 space-y-1">
            <div className="text-[10px] px-2 text-zinc-400 uppercase tracking-widest font-bold">Volume 1</div>
            {(currentNovel?.chapters || []).map((ch) => (
              <Item
                key={ch.id}
                icon="📄"
                label={ch.title}
                active={currentChapterId === ch.id && currentSidebarView === "chapter"}
                onClick={() => {
                  setCurrentChapterId(ch.id);
                  setCurrentSidebarView("chapter");
                }}
              />
            ))}
          </div>
        )}
      </div>
    </aside>
  );
};

const Item: React.FC<{ icon: string; label: string; active: boolean; onClick: () => void }> = ({
  icon,
  label,
  active,
  onClick,
}) => (
  <button
    onClick={onClick}
    className={`w-full text-left px-2.5 py-2 rounded-md text-sm flex items-center gap-2 ${
      active ? "bg-indigo-100 text-indigo-700" : "text-zinc-700 hover:bg-zinc-200"
    }`}
  >
    <span>{icon}</span>
    <span className="truncate">{label}</span>
  </button>
);
