"use client";

import React from "react";
import { useNovelStore } from "@/store/novelStore";

export default function RecycleBin() {
  const { deletedNovels, restoreNovel, permanentlyDeleteNovel, clearRecycleBin } = useNovelStore();

  const getDaysRemaining = (deletedAt: number) => {
    const now = Date.now();
    const diff = now - deletedAt;
    const days = 30 - Math.floor(diff / (1000 * 60 * 60 * 24));
    return days > 0 ? days : 0;
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleDateString();
  };

  return (
    <div className="w-full h-full p-8 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">回收站</h1>
          <p className="text-sm text-zinc-500 mt-1">小说将在 30 天后自动清空。</p>
        </div>
        {deletedNovels.length > 0 && (
          <button
            onClick={() => { if(confirm('确定要一键清空回收站吗？此操作不可逆！')) clearRecycleBin(); }}
            className="bg-red-50 text-red-600 hover:bg-red-100 px-4 py-2 rounded-xl text-sm font-bold transition-all flex items-center gap-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
            一键清空
          </button>
        )}
      </div>

      <div className="bg-white border border-zinc-200 rounded-3xl overflow-hidden shadow-sm">
        <table className="w-full text-left">
          <thead className="bg-zinc-50/50 border-b border-zinc-200">
            <tr>
              <th className="px-6 py-4 text-xs font-bold text-zinc-400 uppercase tracking-widest">小说名称</th>
              <th className="px-6 py-4 text-xs font-bold text-zinc-400 uppercase tracking-widest">删除时间</th>
              <th className="px-6 py-4 text-xs font-bold text-zinc-400 uppercase tracking-widest">剩余天数</th>
              <th className="px-6 py-4 text-xs font-bold text-zinc-400 uppercase tracking-widest text-right">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {deletedNovels.map((novel) => (
              <tr key={novel.id} className="hover:bg-zinc-50/50 transition-colors">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-zinc-100 text-zinc-400 rounded-lg">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/></svg>
                    </div>
                    <span className="text-sm font-bold text-zinc-800">{novel.title}</span>
                  </div>
                </td>
                <td className="px-6 py-4 text-sm text-zinc-500 font-medium">
                  {formatDate(novel.deletedAt)}
                </td>
                <td className="px-6 py-4">
                  <span className={`text-xs font-bold px-2 py-1 rounded-full ${getDaysRemaining(novel.deletedAt) < 7 ? 'bg-red-50 text-red-600' : 'bg-zinc-100 text-zinc-600'}`}>
                    {getDaysRemaining(novel.deletedAt)} 天
                  </span>
                </td>
                <td className="px-6 py-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button 
                      onClick={() => restoreNovel(novel.id)}
                      className="text-indigo-600 hover:bg-indigo-50 p-2 rounded-lg transition-colors font-bold text-xs"
                    >
                      恢复
                    </button>
                    <button 
                      onClick={() => { if(confirm('确定要永久删除这部小说吗？此操作不可逆！')) permanentlyDeleteNovel(novel.id); }}
                      className="text-red-500 hover:bg-red-50 p-2 rounded-lg transition-colors font-bold text-xs"
                    >
                      永久删除
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {deletedNovels.length === 0 && (
          <div className="text-center py-20">
            <div className="text-zinc-300 text-4xl mb-4">🗑️</div>
            <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest">回收站是空的</h3>
          </div>
        )}
      </div>
    </div>
  );
}
