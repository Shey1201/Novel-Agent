"use client";

import React, { useState, useEffect } from "react";
import { useNovelStore } from "@/store/novelStore";

interface Character {
  id: string;
  name: string;
  role: string;
  personality: string;
  background: string;
}

interface WorldRule {
  id: string;
  name: string;
  description: string;
  category: string;
}

interface StoryBibleData {
  title: string;
  genre: string;
  world_view: string;
  tone: string;
  characters: Character[];
  world_rules: WorldRule[];
  major_plot_points: string[];
}

export const StoryBibleManager: React.FC = () => {
  const { currentNovelId, novels } = useNovelStore();
  const [activeTab, setActiveTab] = useState<"overview" | "characters" | "world" | "plot">("overview");
  const [bible, setBible] = useState<StoryBibleData>({
    title: "",
    genre: "",
    world_view: "",
    tone: "",
    characters: [],
    world_rules: [],
    major_plot_points: [],
  });
  const [isLoading, setIsLoading] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved">("idle");

  const currentNovel = novels.find((n) => n.id === currentNovelId);

  // 加载 Story Bible
  useEffect(() => {
    if (currentNovelId) {
      loadStoryBible();
    }
  }, [currentNovelId]);

  const loadStoryBible = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/world/${currentNovelId}`);
      if (response.ok) {
        const data = await response.json();
        setBible({
          title: data.world_bible?.title || currentNovel?.title || "",
          genre: data.world_bible?.genre || "",
          world_view: data.world_bible?.world_view || "",
          tone: data.world_bible?.tone || "",
          characters: data.world_bible?.characters || [],
          world_rules: data.world_bible?.world_rules || [],
          major_plot_points: data.world_bible?.major_plot_points || [],
        });
      }
    } catch (error) {
      console.error("Failed to load story bible:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const saveStoryBible = async () => {
    if (!currentNovelId) return;

    setSaveStatus("saving");
    try {
      const response = await fetch(`http://localhost:8000/api/world/${currentNovelId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          world_bible: bible,
        }),
      });

      if (response.ok) {
        setSaveStatus("saved");
        setTimeout(() => setSaveStatus("idle"), 2000);
      }
    } catch (error) {
      console.error("Failed to save story bible:", error);
      setSaveStatus("idle");
    }
  };

  const addCharacter = () => {
    const newCharacter: Character = {
      id: `char_${Date.now()}`,
      name: "新角色",
      role: "配角",
      personality: "",
      background: "",
    };
    setBible((prev) => ({
      ...prev,
      characters: [...prev.characters, newCharacter],
    }));
  };

  const updateCharacter = (id: string, field: keyof Character, value: string) => {
    setBible((prev) => ({
      ...prev,
      characters: prev.characters.map((c) => (c.id === id ? { ...c, [field]: value } : c)),
    }));
  };

  const removeCharacter = (id: string) => {
    setBible((prev) => ({
      ...prev,
      characters: prev.characters.filter((c) => c.id !== id),
    }));
  };

  const addWorldRule = () => {
    const newRule: WorldRule = {
      id: `rule_${Date.now()}`,
      name: "新规则",
      description: "",
      category: "general",
    };
    setBible((prev) => ({
      ...prev,
      world_rules: [...prev.world_rules, newRule],
    }));
  };

  const updateWorldRule = (id: string, field: keyof WorldRule, value: string) => {
    setBible((prev) => ({
      ...prev,
      world_rules: prev.world_rules.map((r) => (r.id === id ? { ...r, [field]: value } : r)),
    }));
  };

  const removeWorldRule = (id: string) => {
    setBible((prev) => ({
      ...prev,
      world_rules: prev.world_rules.filter((r) => r.id !== id),
    }));
  };

  const addPlotPoint = () => {
    setBible((prev) => ({
      ...prev,
      major_plot_points: [...prev.major_plot_points, ""],
    }));
  };

  const updatePlotPoint = (index: number, value: string) => {
    setBible((prev) => ({
      ...prev,
      major_plot_points: prev.major_plot_points.map((p, i) => (i === index ? value : p)),
    }));
  };

  const removePlotPoint = (index: number) => {
    setBible((prev) => ({
      ...prev,
      major_plot_points: prev.major_plot_points.filter((_, i) => i !== index),
    }));
  };

  if (!currentNovelId) {
    return (
      <div className="flex items-center justify-center h-full text-zinc-400">
        请先选择一部小说
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white">
      {/* 头部 */}
      <div className="border-b border-zinc-200 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-zinc-800">📚 Story Bible</h2>
            <p className="text-sm text-zinc-500">管理小说的核心设定</p>
          </div>
          <button
            onClick={saveStoryBible}
            disabled={saveStatus === "saving"}
            className={`px-4 py-2 rounded-lg font-medium text-white transition-colors ${
              saveStatus === "saved"
                ? "bg-emerald-600"
                : saveStatus === "saving"
                ? "bg-zinc-400"
                : "bg-indigo-600 hover:bg-indigo-700"
            }`}
          >
            {saveStatus === "saved" ? "已保存 ✓" : saveStatus === "saving" ? "保存中..." : "保存"}
          </button>
        </div>
      </div>

      {/* 标签页 */}
      <div className="border-b border-zinc-200">
        <div className="flex">
          {[
            { key: "overview", label: "概览", icon: "📖" },
            { key: "characters", label: "角色", icon: "👥" },
            { key: "world", label: "世界", icon: "🌍" },
            { key: "plot", label: "情节", icon: "📈" },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? "border-indigo-600 text-indigo-600"
                  : "border-transparent text-zinc-600 hover:text-zinc-800"
              }`}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* 内容区域 */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === "overview" && (
          <div className="space-y-6 max-w-2xl">
            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-700">作品标题</label>
              <input
                type="text"
                value={bible.title}
                onChange={(e) => setBible((prev) => ({ ...prev, title: e.target.value }))}
                className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-700">类型</label>
              <select
                value={bible.genre}
                onChange={(e) => setBible((prev) => ({ ...prev, genre: e.target.value }))}
                className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">选择类型</option>
                <option value="fantasy">奇幻</option>
                <option value="sci-fi">科幻</option>
                <option value="romance">言情</option>
                <option value="mystery">悬疑</option>
                <option value="historical">历史</option>
                <option value="modern">现代</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-700">基调</label>
              <select
                value={bible.tone}
                onChange={(e) => setBible((prev) => ({ ...prev, tone: e.target.value }))}
                className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">选择基调</option>
                <option value="dark">黑暗</option>
                <option value="light">轻松</option>
                <option value="epic">史诗</option>
                <option value="realistic">现实</option>
                <option value="humorous">幽默</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-zinc-700">世界观概述</label>
              <textarea
                value={bible.world_view}
                onChange={(e) => setBible((prev) => ({ ...prev, world_view: e.target.value }))}
                rows={6}
                className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                placeholder="描述故事发生的世界..."
              />
            </div>
          </div>
        )}

        {activeTab === "characters" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-zinc-800">角色列表 ({bible.characters.length})</h3>
              <button
                onClick={addCharacter}
                className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
              >
                + 添加角色
              </button>
            </div>

            <div className="space-y-4">
              {bible.characters.map((character) => (
                <div key={character.id} className="border border-zinc-200 rounded-lg p-4 space-y-3">
                  <div className="flex items-center gap-3">
                    <input
                      type="text"
                      value={character.name}
                      onChange={(e) => updateCharacter(character.id, "name", e.target.value)}
                      className="flex-1 px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="角色名称"
                    />
                    <select
                      value={character.role}
                      onChange={(e) => updateCharacter(character.id, "role", e.target.value)}
                      className="px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="protagonist">主角</option>
                      <option value="supporting">配角</option>
                      <option value="antagonist">反派</option>
                      <option value="mentor">导师</option>
                    </select>
                    <button
                      onClick={() => removeCharacter(character.id)}
                      className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      🗑️
                    </button>
                  </div>
                  <textarea
                    value={character.personality}
                    onChange={(e) => updateCharacter(character.id, "personality", e.target.value)}
                    className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                    rows={2}
                    placeholder="性格特征..."
                  />
                  <textarea
                    value={character.background}
                    onChange={(e) => updateCharacter(character.id, "background", e.target.value)}
                    className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                    rows={2}
                    placeholder="背景故事..."
                  />
                </div>
              ))}

              {bible.characters.length === 0 && (
                <div className="text-center py-8 text-zinc-400">
                  暂无角色，点击上方按钮添加
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === "world" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-zinc-800">世界规则 ({bible.world_rules.length})</h3>
              <button
                onClick={addWorldRule}
                className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
              >
                + 添加规则
              </button>
            </div>

            <div className="space-y-3">
              {bible.world_rules.map((rule) => (
                <div key={rule.id} className="border border-zinc-200 rounded-lg p-4 space-y-3">
                  <div className="flex items-center gap-3">
                    <input
                      type="text"
                      value={rule.name}
                      onChange={(e) => updateWorldRule(rule.id, "name", e.target.value)}
                      className="flex-1 px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="规则名称"
                    />
                    <select
                      value={rule.category}
                      onChange={(e) => updateWorldRule(rule.id, "category", e.target.value)}
                      className="px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="general">通用</option>
                      <option value="magic">魔法</option>
                      <option value="physics">物理</option>
                      <option value="society">社会</option>
                    </select>
                    <button
                      onClick={() => removeWorldRule(rule.id)}
                      className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      🗑️
                    </button>
                  </div>
                  <textarea
                    value={rule.description}
                    onChange={(e) => updateWorldRule(rule.id, "description", e.target.value)}
                    className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                    rows={2}
                    placeholder="规则描述..."
                  />
                </div>
              ))}

              {bible.world_rules.length === 0 && (
                <div className="text-center py-8 text-zinc-400">
                  暂无规则，点击上方按钮添加
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === "plot" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-zinc-800">主要情节点 ({bible.major_plot_points.length})</h3>
              <button
                onClick={addPlotPoint}
                className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
              >
                + 添加情节点
              </button>
            </div>

            <div className="space-y-3">
              {bible.major_plot_points.map((point, index) => (
                <div key={index} className="flex items-center gap-3">
                  <span className="w-8 h-8 flex items-center justify-center bg-zinc-100 rounded-full text-sm font-medium text-zinc-600">
                    {index + 1}
                  </span>
                  <input
                    type="text"
                    value={point}
                    onChange={(e) => updatePlotPoint(index, e.target.value)}
                    className="flex-1 px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="情节点描述..."
                  />
                  <button
                    onClick={() => removePlotPoint(index)}
                    className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    🗑️
                  </button>
                </div>
              ))}

              {bible.major_plot_points.length === 0 && (
                <div className="text-center py-8 text-zinc-400">
                  暂无情节点，点击上方按钮添加
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
