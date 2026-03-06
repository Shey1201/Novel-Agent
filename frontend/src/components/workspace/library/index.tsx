"use client";

import React, { useState } from "react";
import { useNovelStore, type Novel, type NovelCategory } from "@/store/novelStore";

export default function Library() {
  const {
    novels,
    renameNovel,
    toggleLockNovel,
    deleteNovel,
    setCurrentNovelId,
    addNovel,
    categories,
    selectedCategoryId,
    setSelectedCategoryId,
    addCategory,
    updateCategory,
    deleteCategory,
    setNovelCategory,
  } = useNovelStore();

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [isAddingCategory, setIsAddingCategory] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState("");
  const [editingCategoryId, setEditingCategoryId] = useState<string | null>(null);
  const [editCategoryName, setEditCategoryName] = useState("");
  const [novelMenuOpen, setNovelMenuOpen] = useState<string | null>(null);

  // 过滤小说
  const filteredNovels = selectedCategoryId === 'cat-all'
    ? novels
    : selectedCategoryId === 'cat-uncategorized'
    ? novels.filter(n => !n.categoryId)
    : novels.filter(n => n.categoryId === selectedCategoryId);

  // 获取每个分类的小说数量
  const getCategoryCount = (categoryId: string) => {
    if (categoryId === 'cat-all') return novels.length;
    if (categoryId === 'cat-uncategorized') return novels.filter(n => !n.categoryId).length;
    return novels.filter(n => n.categoryId === categoryId).length;
  };

  const handleRename = (id: string) => {
    if (editTitle.trim()) {
      renameNovel(id, editTitle.trim());
      setEditingId(null);
    }
  };

  const handleCreateNovel = () => {
    const id = `novel-${Date.now()}`;
    addNovel({
      id,
      title: "新小说",
      chapters: [],
      assetRefs: {
        characters: [],
        worldbuilding: [],
        factions: [],
        locations: [],
        timeline: [],
      },
      locked: false,
      categoryId: selectedCategoryId === 'cat-all' || selectedCategoryId === 'cat-uncategorized' ? null : selectedCategoryId,
    });
  };

  const [categoryError, setCategoryError] = useState<string>("");

  const handleAddCategory = () => {
    const trimmedName = newCategoryName.trim();
    if (!trimmedName) return;

    // 检查是否已存在同名分类
    const exists = categories.some(
      c => c.name.toLowerCase() === trimmedName.toLowerCase()
    );
    if (exists) {
      setCategoryError("该分类名称已存在");
      return;
    }

    const colors = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#ef4444', '#84cc16'];
    const randomColor = colors[Math.floor(Math.random() * colors.length)];
    addCategory({
      id: `cat-${Date.now()}`,
      name: trimmedName,
      color: randomColor,
    });
    setNewCategoryName("");
    setCategoryError("");
    setIsAddingCategory(false);
  };

  const cancelAddCategory = () => {
    setNewCategoryName("");
    setCategoryError("");
    setIsAddingCategory(false);
  };

  const handleUpdateCategory = (id: string) => {
    if (editCategoryName.trim()) {
      updateCategory(id, { name: editCategoryName.trim() });
      setEditingCategoryId(null);
    }
  };

  const handleDeleteCategory = (id: string) => {
    if (confirm('确定要删除这个分类吗？该分类下的小说将变为未分类。')) {
      deleteCategory(id);
    }
  };

  const startEditingCategory = (category: NovelCategory) => {
    setEditingCategoryId(category.id);
    setEditCategoryName(category.name);
  };

  return (
    <div className="flex h-full">
      {/* 左侧分类栏 */}
      <div className="w-56 border-r border-zinc-200 bg-zinc-50/50 flex flex-col">
        <div className="p-4 border-b border-zinc-200 flex items-center justify-between">
          <div className="flex items-center gap-2 text-zinc-700">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>
            </svg>
          </div>
          {/* 新建分类按钮 */}
          {isAddingCategory ? (
            <div className="flex-1 ml-2 min-w-0">
              <div className="flex items-center gap-1">
                <input
                  autoFocus
                  value={newCategoryName}
                  onChange={(e) => {
                    setNewCategoryName(e.target.value);
                    setCategoryError("");
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleAddCategory();
                    if (e.key === 'Escape') cancelAddCategory();
                  }}
                  placeholder="新分类"
                  className={`flex-1 min-w-0 text-xs px-2 py-1 border rounded outline-none focus:border-indigo-500 ${
                    categoryError ? 'border-red-400 focus:border-red-500' : 'border-zinc-300'
                  }`}
                />
                <button
                  onClick={handleAddCategory}
                  disabled={!newCategoryName.trim()}
                  className="p-1 text-green-600 hover:bg-green-50 rounded disabled:text-zinc-300 disabled:hover:bg-transparent transition-colors shrink-0"
                  title="保存"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M20 6 9 17l-5-5"/>
                  </svg>
                </button>
                <button
                  onClick={cancelAddCategory}
                  className="p-1 text-zinc-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors shrink-0"
                  title="取消"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
                  </svg>
                </button>
              </div>
              {categoryError && (
                <div className="text-[10px] text-red-500 mt-1">{categoryError}</div>
              )}
            </div>
          ) : (
            <button
              onClick={() => setIsAddingCategory(true)}
              className="p-1.5 text-zinc-400 hover:text-indigo-600 hover:bg-zinc-200 rounded transition-colors"
              title="新建分类"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14"/><path d="M12 5v14"/>
              </svg>
            </button>
          )}
        </div>

        <div className="flex-1 overflow-y-auto py-2">
          {/* 全部分类 */}
          <button
            onClick={() => setSelectedCategoryId('cat-all')}
            className={`w-full px-4 py-2.5 text-left text-sm flex items-center justify-between transition-colors ${
              selectedCategoryId === 'cat-all'
                ? 'bg-white text-zinc-900 shadow-sm border-r-2 border-indigo-500'
                : 'text-zinc-600 hover:bg-zinc-100'
            }`}
          >
            <span className="font-medium">全部</span>
            <span className="text-xs text-zinc-400 bg-zinc-100 px-2 py-0.5 rounded-full">
              {getCategoryCount('cat-all')}
            </span>
          </button>

          {/* 未分类 */}
          <button
            onClick={() => setSelectedCategoryId('cat-uncategorized')}
            className={`w-full px-4 py-2.5 text-left text-sm flex items-center justify-between transition-colors ${
              selectedCategoryId === 'cat-uncategorized'
                ? 'bg-white text-zinc-900 shadow-sm border-r-2 border-indigo-500'
                : 'text-zinc-600 hover:bg-zinc-100'
            }`}
          >
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-zinc-300" />
              <span className="font-medium">未分类</span>
            </div>
            <span className="text-xs text-zinc-400 bg-zinc-100 px-2 py-0.5 rounded-full">
              {getCategoryCount('cat-uncategorized')}
            </span>
          </button>

          {/* 自定义分类 */}
          {categories.filter(c => c.id !== 'cat-all').map((category) => (
            <div key={category.id} className="group relative">
              {editingCategoryId === category.id ? (
                <div className="px-4 py-2 flex items-center gap-2">
                  <input
                    autoFocus
                    value={editCategoryName}
                    onChange={(e) => setEditCategoryName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleUpdateCategory(category.id);
                      if (e.key === 'Escape') setEditingCategoryId(null);
                    }}
                    onBlur={() => handleUpdateCategory(category.id)}
                    className="flex-1 text-sm px-2 py-1 border border-zinc-300 rounded outline-none focus:border-indigo-500"
                  />
                </div>
              ) : (
                <div
                  onClick={() => setSelectedCategoryId(category.id)}
                  className={`w-full px-4 py-2.5 text-left text-sm flex items-center justify-between transition-colors cursor-pointer ${
                    selectedCategoryId === category.id
                      ? 'bg-white text-zinc-900 shadow-sm border-r-2 border-indigo-500'
                      : 'text-zinc-600 hover:bg-zinc-100'
                  }`}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      setSelectedCategoryId(category.id);
                    }
                  }}
                >
                  <div className="flex items-center gap-2">
                    <span
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: category.color }}
                    />
                    <span>{category.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-zinc-400 bg-zinc-100 px-2 py-0.5 rounded-full">
                      {getCategoryCount(category.id)}
                    </span>
                    {/* 编辑/删除按钮 */}
                    <div className="opacity-0 group-hover:opacity-100 flex items-center gap-1">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          startEditingCategory(category);
                        }}
                        className="p-1 text-zinc-400 hover:text-indigo-600"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg>
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteCategory(category.id);
                        }}
                        className="p-1 text-zinc-400 hover:text-red-600"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/></svg>
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 右侧内容区 */}
      <div className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-5xl mx-auto space-y-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-zinc-900">
                {selectedCategoryId === 'cat-all'
                  ? '全部小说'
                  : selectedCategoryId === 'cat-uncategorized'
                  ? '未分类'
                  : categories.find(c => c.id === selectedCategoryId)?.name || '我的书库'}
              </h1>
              <p className="text-sm text-zinc-500 mt-1">
                共 {filteredNovels.length} 部作品
              </p>
            </div>
            <button
              onClick={handleCreateNovel}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-xl text-sm font-bold shadow-lg transition-all flex items-center gap-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
              创建小说
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredNovels.map((novel) => (
              <div
                key={novel.id}
                className={`group relative border rounded-2xl p-5 shadow-sm transition-all ${
                  novel.locked
                    ? 'bg-zinc-50 border-zinc-200 opacity-60'
                    : 'bg-white border-zinc-200 hover:shadow-md'
                }`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className={`p-3 rounded-2xl ${novel.locked ? 'bg-zinc-200 text-zinc-500' : 'bg-indigo-50 text-indigo-600'}`}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/></svg>
                  </div>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => toggleLockNovel(novel.id)}
                      title={novel.locked ? "解锁" : "锁定"}
                      className={`p-2 rounded-lg hover:bg-zinc-100 ${novel.locked ? 'text-amber-500' : 'text-zinc-400'}`}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        {novel.locked ? (
                          <>
                            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                            <rect width="18" height="11" x="3" y="11" rx="2" ry="2"/>
                            <path d="M12 14.5v1.5"/>
                          </>
                        ) : (
                          <>
                            <path d="M7 11V7a5 5 0 0 1 9.9-1"/>
                            <rect width="18" height="11" x="3" y="11" rx="2" ry="2"/>
                            <path d="M12 14.5v1.5"/>
                          </>
                        )}
                      </svg>
                    </button>
                    {/* 分类选择下拉菜单 */}
                    <div className="relative">
                      <button
                        onClick={() => setNovelMenuOpen(novelMenuOpen === novel.id ? null : novel.id)}
                        className="p-2 text-zinc-400 hover:text-indigo-600 hover:bg-zinc-100 rounded-lg"
                        title="移动到分类"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 7v14a2 2 0 0 0 2 2h14"/><path d="M3 7l9-4 9 4"/><path d="M21 7v14"/></svg>
                      </button>
                      {novelMenuOpen === novel.id && (
                        <>
                          <div
                            className="fixed inset-0 z-40"
                            onClick={() => setNovelMenuOpen(null)}
                          />
                          <div className="absolute right-0 top-full mt-1 w-40 bg-white rounded-lg shadow-lg border border-zinc-200 py-1 z-50">
                            <div className="px-3 py-1.5 text-xs text-zinc-400 border-b border-zinc-100">
                              移动到分类
                            </div>
                            <button
                              onClick={() => {
                                setNovelCategory(novel.id, null);
                                setNovelMenuOpen(null);
                              }}
                              className={`w-full px-3 py-2 text-left text-sm hover:bg-zinc-50 flex items-center gap-2 ${!novel.categoryId ? 'text-indigo-600 bg-indigo-50' : 'text-zinc-700'}`}
                            >
                              <span className="w-2 h-2 rounded-full bg-zinc-300" />
                              未分类
                            </button>
                            {categories.filter(c => c.id !== 'cat-all').map((category) => (
                              <button
                                key={category.id}
                                onClick={() => {
                                  setNovelCategory(novel.id, category.id);
                                  setNovelMenuOpen(null);
                                }}
                                className={`w-full px-3 py-2 text-left text-sm hover:bg-zinc-50 flex items-center gap-2 ${novel.categoryId === category.id ? 'text-indigo-600 bg-indigo-50' : 'text-zinc-700'}`}
                              >
                                <span
                                  className="w-2 h-2 rounded-full"
                                  style={{ backgroundColor: category.color }}
                                />
                                {category.name}
                              </button>
                            ))}
                          </div>
                        </>
                      )}
                    </div>
                    {!novel.locked && (
                      <>
                        <button
                          onClick={() => { setEditingId(novel.id); setEditTitle(novel.title); }}
                          className="p-2 text-zinc-400 hover:text-indigo-600 hover:bg-zinc-100 rounded-lg"
                          title="重命名"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/></svg>
                        </button>
                        <button
                          onClick={() => { if(confirm('确定要删除这部小说吗？它将被移入回收站。')) deleteNovel(novel.id); }}
                          className="p-2 text-zinc-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                          title="删除"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {editingId === novel.id ? (
                  <div className="flex items-center gap-2">
                    <input
                      autoFocus
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleRename(novel.id)}
                      onBlur={() => setEditingId(null)}
                      className="flex-1 text-lg font-bold outline-none border-b-2 border-indigo-500 bg-transparent py-1"
                    />
                  </div>
                ) : (
                  <div
                    className={`cursor-pointer group/title ${novel.locked ? 'pointer-events-none' : ''}`}
                    onClick={() => setCurrentNovelId(novel.id)}
                  >
                    <h3 className={`text-lg font-bold transition-colors line-clamp-1 ${novel.locked ? 'text-zinc-500' : 'text-zinc-800 group-hover/title:text-indigo-600'}`}>
                      {novel.title}
                    </h3>
                    <div className="mt-1 flex items-center gap-3 text-xs text-zinc-400 font-medium">
                      <span>{novel.chapters.length} 章节</span>
                      <span>•</span>
                      <span className={novel.locked ? 'text-amber-500' : ''}>{novel.locked ? '已锁定' : '创作中'}</span>
                      {novel.categoryId && (
                        <>
                          <span>•</span>
                          <span
                            className="px-1.5 py-0.5 rounded text-white text-[10px]"
                            style={{ backgroundColor: categories.find(c => c.id === novel.categoryId)?.color || '#6366f1' }}
                          >
                            {categories.find(c => c.id === novel.categoryId)?.name}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {filteredNovels.length === 0 && (
            <div className="text-center py-20 bg-zinc-50/50 rounded-3xl border-2 border-dashed border-zinc-200">
              <div className="text-zinc-400 text-4xl mb-4">📚</div>
              <h3 className="text-lg font-bold text-zinc-800">
                {selectedCategoryId === 'cat-all' ? '书库空空如也' : selectedCategoryId === 'cat-uncategorized' ? '未分类小说' : '该分类下暂无小说'}
              </h3>
              <p className="text-sm text-zinc-500 mt-2">
                {selectedCategoryId === 'cat-all'
                  ? '点击"创建小说"开始您的创作之旅吧！'
                  : '点击"创建小说"在该分类下创建新作品'}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
