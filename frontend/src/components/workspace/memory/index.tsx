"use client";

import React, { useState, useEffect } from "react";
import { useSupabaseStore } from "@/store/supabaseStore";
import { API_BASE } from "@/lib/api";

interface Character {
  id: string;
  name: string;
  aliases: string[];
  age?: number;
  gender?: string;
  appearance: string;
  personality: string;
  background: string;
  current_state: string;
  tags: string[];
}

interface ChapterSummary {
  chapter_id: string;
  title: string;
  summary: string;
  pov?: string;
  word_count: number;
  key_events: string[];
  mood: string;
  created_at: string;
}

interface StoryBible {
  title: string;
  genre: string;
  world_view: string;
  themes: Array<{ name: string; description: string }>;
  world_rules: Array<{ name: string; description: string }>;
  locations: Array<{ name: string; description: string }>;
  factions: Array<{ name: string; description: string }>;
}

interface MemoryData {
  story_id: string;
  bible: StoryBible;
  characters: Character[];
  chapter_summaries: ChapterSummary[];
  world_locked: boolean;
  unresolved_clues: Array<{ clue: string; status: string }>;
}

type TabType = "overview" | "characters" | "summaries" | "bible";

export default function MemoryPanel() {
  const { currentNovelId, novels } = useSupabaseStore();
  const [activeTab, setActiveTab] = useState<TabType>("overview");
  const [memoryData, setMemoryData] = useState<MemoryData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingCharacter, setEditingCharacter] = useState<Character | null>(null);
  const [isAddingCharacter, setIsAddingCharacter] = useState(false);

  const currentNovel = novels.find((n) => n.id === currentNovelId);

  useEffect(() => {
    if (currentNovelId) {
      fetchMemoryData();
    }
  }, [currentNovelId]);

  const fetchMemoryData = async () => {
    if (!currentNovelId) return;
    
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/memory/${currentNovelId}`);
      const result = await response.json();
      if (result.success) {
        setMemoryData(result.data);
      } else {
        setError(result.message || "加载记忆数据失败");
      }
    } catch (err) {
      setError("无法连接到服务器");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveCharacter = async (character: Partial<Character>) => {
    if (!currentNovelId) return;

    try {
      const url = editingCharacter
        ? `${API_BASE}/api/memory/${currentNovelId}/characters/${editingCharacter.id}`
        : `${API_BASE}/api/memory/${currentNovelId}/characters`;
      
      const method = editingCharacter ? "PUT" : "POST";
      
      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(character),
      });
      
      const result = await response.json();
      if (result.success) {
        setEditingCharacter(null);
        setIsAddingCharacter(false);
        fetchMemoryData();
      } else {
        setError(result.message || "保存角色失败");
      }
    } catch (err) {
      setError("保存角色失败");
      console.error(err);
    }
  };

  const handleDeleteCharacter = async (characterId: string) => {
    if (!currentNovelId || !confirm("确定要删除这个角色吗？")) return;

    try {
      const response = await fetch(
        `${API_BASE}/api/memory/${currentNovelId}/characters/${characterId}`,
        { method: "DELETE" }
      );
      const result = await response.json();
      if (result.success) {
        fetchMemoryData();
      } else {
        setError(result.message || "删除角色失败");
      }
    } catch (err) {
      setError("删除角色失败");
      console.error(err);
    }
  };

  const handleSaveBible = async (bible: StoryBible) => {
    if (!currentNovelId) return;

    try {
      const response = await fetch(
        `${API_BASE}/api/memory/${currentNovelId}/bible`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(bible),
        }
      );
      const result = await response.json();
      if (result.success) {
        fetchMemoryData();
      } else {
        setError(result.message || "保存故事圣经失败");
      }
    } catch (err) {
      setError("保存故事圣经失败");
      console.error(err);
    }
  };

  if (!currentNovelId) {
    return (
      <div className="w-full h-full flex items-center justify-center p-8">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-zinc-100 rounded-full flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-zinc-400">
              <path d="M12 2a10 10 0 1 0 10 10 4 4 0 0 1-5-5 4 4 0 0 1-5-5"/>
              <path d="M8.5 8.5v.01"/>
              <path d="M16 15.5v.01"/>
              <path d="M12 12v.01"/>
              <path d="M11 17v.01"/>
              <path d="M7 14v.01"/>
            </svg>
          </div>
          <h3 className="text-lg font-bold text-zinc-600 mb-2">请选择一部小说</h3>
          <p className="text-sm text-zinc-400">从左侧选择一部小说以查看其记忆数据</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="w-full h-full flex items-center justify-center p-8">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-sm text-zinc-500">加载中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-full flex items-center justify-center p-8">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-red-50 rounded-full flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-red-500">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
          </div>
          <h3 className="text-lg font-bold text-red-600 mb-2">加载失败</h3>
          <p className="text-sm text-zinc-500 mb-4">{error}</p>
          <button
            onClick={fetchMemoryData}
            className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-bold hover:bg-indigo-700 transition-colors"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: "overview", label: "总览" },
    { id: "characters", label: "角色" },
    { id: "summaries", label: "章节摘要" },
    { id: "bible", label: "故事圣经" },
  ] as const;

  return (
    <div className="w-full h-full flex flex-col bg-white">
      {/* Header */}
      <div className="border-b border-zinc-200 px-6 py-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold text-zinc-900">历史记忆</h1>
            <p className="text-sm text-zinc-500">{currentNovel?.title || "未命名小说"}</p>
          </div>
          <button
            onClick={fetchMemoryData}
            className="p-2 hover:bg-zinc-100 rounded-lg transition-colors"
            title="刷新"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
              <path d="M21 3v5h-5"/>
              <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
              <path d="M8 16H3v5"/>
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-zinc-100 p-1 rounded-xl">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? "bg-white text-zinc-900 shadow-sm"
                  : "text-zinc-500 hover:text-zinc-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-zinc-50 rounded-2xl p-4 border border-zinc-100">
                <div className="text-2xl font-bold text-zinc-900">
                  {memoryData?.characters.length || 0}
                </div>
                <div className="text-sm text-zinc-500">角色数量</div>
              </div>
              <div className="bg-zinc-50 rounded-2xl p-4 border border-zinc-100">
                <div className="text-2xl font-bold text-zinc-900">
                  {memoryData?.chapter_summaries.length || 0}
                </div>
                <div className="text-sm text-zinc-500">章节摘要</div>
              </div>
              <div className="bg-zinc-50 rounded-2xl p-4 border border-zinc-100">
                <div className="text-2xl font-bold text-zinc-900">
                  {memoryData?.unresolved_clues?.length || 0}
                </div>
                <div className="text-sm text-zinc-500">待回收伏笔</div>
              </div>
            </div>

            {/* Recent Summaries */}
            <div>
              <h3 className="text-sm font-bold text-zinc-900 mb-3">最近章节摘要</h3>
              <div className="space-y-2">
                {memoryData?.chapter_summaries.slice(-3).reverse().map((summary) => (
                  <div
                    key={summary.chapter_id}
                    className="bg-zinc-50 rounded-xl p-4 border border-zinc-100"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-zinc-900">{summary.title}</span>
                      <span className="text-xs text-zinc-400">{summary.word_count} 字</span>
                    </div>
                    <p className="text-sm text-zinc-600 line-clamp-2">{summary.summary}</p>
                  </div>
                ))}
                {(!memoryData?.chapter_summaries || memoryData.chapter_summaries.length === 0) && (
                  <p className="text-sm text-zinc-400 text-center py-4">暂无章节摘要</p>
                )}
              </div>
            </div>

            {/* Unresolved Clues */}
            {memoryData?.unresolved_clues && memoryData.unresolved_clues.length > 0 && (
              <div>
                <h3 className="text-sm font-bold text-zinc-900 mb-3">待回收伏笔</h3>
                <div className="space-y-2">
                  {memoryData.unresolved_clues.map((clue, index) => (
                    <div
                      key={index}
                      className="bg-amber-50 rounded-xl p-4 border border-amber-100"
                    >
                      <span className="text-sm text-amber-800">{clue.clue}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "characters" && (
          <div className="space-y-4">
            <div className="flex justify-end">
              <button
                onClick={() => {
                  setIsAddingCharacter(true);
                  setEditingCharacter({
                    id: "",
                    name: "",
                    aliases: [],
                    appearance: "",
                    personality: "",
                    background: "",
                    current_state: "",
                    tags: [],
                  });
                }}
                className="bg-indigo-600 text-white px-4 py-2 rounded-xl text-sm font-bold hover:bg-indigo-700 transition-colors flex items-center gap-2"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14"/>
                  <path d="M12 5v14"/>
                </svg>
                添加角色
              </button>
            </div>

            {(isAddingCharacter || editingCharacter) && (
              <div className="bg-zinc-50 rounded-2xl p-6 border border-zinc-200 mb-4">
                <h3 className="text-lg font-bold text-zinc-900 mb-4">
                  {editingCharacter?.id ? "编辑角色" : "新增角色"}
                </h3>
                <CharacterForm
                  character={editingCharacter!}
                  onSave={handleSaveCharacter}
                  onCancel={() => {
                    setEditingCharacter(null);
                    setIsAddingCharacter(false);
                  }}
                />
              </div>
            )}

            <div className="grid gap-4">
              {memoryData?.characters.map((character) => (
                <div
                  key={character.id}
                  className="bg-white rounded-2xl p-4 border border-zinc-200 hover:border-zinc-300 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600 font-bold">
                        {character.name[0]}
                      </div>
                      <div>
                        <div className="font-bold text-zinc-900">{character.name}</div>
                        {character.aliases.length > 0 && (
                          <div className="text-xs text-zinc-400">
                            别名: {character.aliases.join(", ")}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setEditingCharacter(character)}
                        className="p-2 hover:bg-zinc-100 rounded-lg transition-colors"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-zinc-400">
                          <path d="M17 3a2.85 2.85 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                        </svg>
                      </button>
                      <button
                        onClick={() => handleDeleteCharacter(character.id)}
                        className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-red-400">
                          <path d="M3 6h18"/>
                          <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
                          <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                        </svg>
                      </button>
                    </div>
                  </div>
                  {character.personality && (
                    <div className="mt-3 text-sm text-zinc-600">
                      <span className="font-medium">性格:</span> {character.personality}
                    </div>
                  )}
                  {character.background && (
                    <div className="mt-2 text-sm text-zinc-600 line-clamp-2">
                      <span className="font-medium">背景:</span> {character.background}
                    </div>
                  )}
                </div>
              ))}
              {(!memoryData?.characters || memoryData.characters.length === 0) && (
                <div className="text-center py-8">
                  <p className="text-zinc-400">暂无角色数据</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === "summaries" && (
          <div className="space-y-4">
            {memoryData?.chapter_summaries.map((summary, index) => (
              <div
                key={summary.chapter_id}
                className="bg-zinc-50 rounded-2xl p-4 border border-zinc-100"
              >
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <span className="font-bold text-zinc-900">{summary.title}</span>
                    {summary.pov && (
                      <span className="ml-2 text-xs bg-indigo-100 text-indigo-600 px-2 py-0.5 rounded-full">
                        {summary.pov}视角
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-xs text-zinc-400">
                    <span>{summary.word_count} 字</span>
                    <span>{summary.key_events.length} 个关键事件</span>
                  </div>
                </div>
                <p className="text-sm text-zinc-600 mb-2">{summary.summary}</p>
                {summary.key_events.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {summary.key_events.map((event, i) => (
                      <span
                        key={i}
                        className="text-xs bg-zinc-200 text-zinc-600 px-2 py-1 rounded-full"
                      >
                        {event}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {(!memoryData?.chapter_summaries || memoryData.chapter_summaries.length === 0) && (
              <div className="text-center py-8">
                <p className="text-zinc-400">暂无章节摘要</p>
                <p className="text-sm text-zinc-400 mt-1">AI 写作时会自动生成章节摘要</p>
              </div>
            )}
          </div>
        )}

        {activeTab === "bible" && memoryData && (
          <BibleEditor
            bible={memoryData.bible}
            onSave={handleSaveBible}
          />
        )}
      </div>
    </div>
  );
}

function CharacterForm({
  character,
  onSave,
  onCancel,
}: {
  character: Partial<Character>;
  onSave: (character: Partial<Character>) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState(character);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-zinc-700 mb-1">角色名称 *</label>
          <input
            type="text"
            value={formData.name || ""}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-zinc-700 mb-1">年龄</label>
          <input
            type="number"
            value={formData.age || ""}
            onChange={(e) => setFormData({ ...formData, age: parseInt(e.target.value) || undefined })}
            className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-zinc-700 mb-1">别名（用逗号分隔）</label>
        <input
          type="text"
          value={formData.aliases?.join(", ") || ""}
          onChange={(e) => setFormData({ ...formData, aliases: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) })}
          className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-zinc-700 mb-1">性格特征</label>
        <textarea
          value={formData.personality || ""}
          onChange={(e) => setFormData({ ...formData, personality: e.target.value })}
          rows={2}
          className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-zinc-700 mb-1">外貌描述</label>
        <textarea
          value={formData.appearance || ""}
          onChange={(e) => setFormData({ ...formData, appearance: e.target.value })}
          rows={2}
          className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-zinc-700 mb-1">背景故事</label>
        <textarea
          value={formData.background || ""}
          onChange={(e) => setFormData({ ...formData, background: e.target.value })}
          rows={3}
          className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-zinc-700 mb-1">当前状态</label>
        <textarea
          value={formData.current_state || ""}
          onChange={(e) => setFormData({ ...formData, current_state: e.target.value })}
          rows={2}
          className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none"
        />
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-100 rounded-lg transition-colors"
        >
          取消
        </button>
        <button
          type="submit"
          className="px-4 py-2 text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
        >
          保存
        </button>
      </div>
    </form>
  );
}

function BibleEditor({
  bible,
  onSave,
}: {
  bible: StoryBible;
  onSave: (bible: StoryBible) => void;
}) {
  const [formData, setFormData] = useState(bible);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    await onSave(formData);
    setSaving(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-bold text-zinc-900 mb-2">小说标题</label>
        <input
          type="text"
          value={formData.title || ""}
          onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          className="w-full px-4 py-3 border border-zinc-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none text-lg font-medium"
          placeholder="输入小说标题..."
        />
      </div>

      <div>
        <label className="block text-sm font-bold text-zinc-900 mb-2">类型/题材</label>
        <input
          type="text"
          value={formData.genre || ""}
          onChange={(e) => setFormData({ ...formData, genre: e.target.value })}
          className="w-full px-4 py-3 border border-zinc-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
          placeholder="如：仙侠、玄幻、都市..."
        />
      </div>

      <div>
        <label className="block text-sm font-bold text-zinc-900 mb-2">世界观概述</label>
        <textarea
          value={formData.world_view || ""}
          onChange={(e) => setFormData({ ...formData, world_view: e.target.value })}
          rows={6}
          className="w-full px-4 py-3 border border-zinc-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none"
          placeholder="描述故事发生的世界..."
        />
      </div>

      <div>
        <label className="block text-sm font-bold text-zinc-900 mb-2">世界规则</label>
        <textarea
          value={formData.world_rules?.map((r) => `${r.name}: ${r.description}`).join("\n") || ""}
          onChange={(e) => {
            const rules = e.target.value.split("\n").filter(Boolean).map((line) => {
              const [name, ...descParts] = line.split(":");
              return { name: name.trim(), description: descParts.join(":").trim() };
            });
            setFormData({ ...formData, world_rules: rules });
          }}
          rows={4}
          className="w-full px-4 py-3 border border-zinc-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none font-mono text-sm"
          placeholder="每行一个规则，格式：规则名: 描述"
        />
      </div>

      <div>
        <label className="block text-sm font-bold text-zinc-900 mb-2">地点</label>
        <textarea
          value={formData.locations?.map((l) => `${l.name}: ${l.description}`).join("\n") || ""}
          onChange={(e) => {
            const locations = e.target.value.split("\n").filter(Boolean).map((line) => {
              const [name, ...descParts] = line.split(":");
              return { name: name.trim(), description: descParts.join(":").trim() };
            });
            setFormData({ ...formData, locations: locations });
          }}
          rows={4}
          className="w-full px-4 py-3 border border-zinc-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none font-mono text-sm"
          placeholder="每行一个地点，格式：地点名: 描述"
        />
      </div>

      <div>
        <label className="block text-sm font-bold text-zinc-900 mb-2">势力/组织</label>
        <textarea
          value={formData.factions?.map((f) => `${f.name}: ${f.description}`).join("\n") || ""}
          onChange={(e) => {
            const factions = e.target.value.split("\n").filter(Boolean).map((line) => {
              const [name, ...descParts] = line.split(":");
              return { name: name.trim(), description: descParts.join(":").trim() };
            });
            setFormData({ ...formData, factions: factions });
          }}
          rows={4}
          className="w-full px-4 py-3 border border-zinc-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none font-mono text-sm"
          placeholder="每行一个势力，格式：势力名: 描述"
        />
      </div>

      <button
        onClick={handleSave}
        disabled={saving}
        className="w-full py-3 bg-indigo-600 text-white font-bold rounded-xl hover:bg-indigo-700 transition-colors disabled:opacity-50"
      >
        {saving ? "保存中..." : "保存故事圣经"}
      </button>
    </div>
  );
}
