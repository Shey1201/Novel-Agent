"use client";

import React from "react";
import { useNovelStore } from "@/store/novelStore";

interface TopBarProps {
  onRunAgents: () => void;
  isProcessing: boolean;
}

const WritingModeSwitch: React.FC = () => {
  const { writingMode, setWritingMode } = useNovelStore();
  const modes = [
    { key: "manual", name: "Manual" },
    { key: "ai-assisted", name: "Assist" },
    { key: "ai-writer", name: "Auto" },
  ];

  return (
    <div className="flex items-center rounded-lg bg-zinc-100 p-1 border border-zinc-200">
      {modes.reverse().map((mode) => (
        <button
          key={mode.key}
          onClick={() => setWritingMode(mode.key as any)}
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

export const TopBar: React.FC<TopBarProps> = ({ onRunAgents, isProcessing }) => {
  const { novels, currentNovelId, currentChapterId, agents, updateAgent, constraints, addConstraint, removeConstraint, agentConfigs, updateAgentConfig } = useNovelStore();
  const currentNovel = novels.find(n => n.id === currentNovelId);
  const [showAgentModal, setShowAgentModal] = React.useState(false);
  const [showSettingsModal, setShowSettingsModal] = React.useState(false);
  const [newConstraint, setNewConstraint] = React.useState("");

  const handleExport = async () => {
    if (!currentNovelId || !currentChapterId) return;
    try {
      const url = `http://127.0.0.1:8000/api/novel/export/word?novel_id=${currentNovelId}&chapter_id=${currentChapterId}`;
      const response = await fetch(url);
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `${currentChapterId}.docx`;
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error("导出失败:", error);
    }
  };

  const handleAddConstraint = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && newConstraint.trim()) {
      addConstraint(newConstraint.trim());
      setNewConstraint("");
    }
  };

  return (
    <header className="flex h-12 items-center justify-between border-b border-zinc-200 bg-white px-4 shrink-0 relative">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-indigo-600 text-lg">📖</span>
          <h1 className="text-sm font-bold text-indigo-600 tracking-tight">小说工作室</h1>
        </div>
        <div className="h-4 w-[1px] bg-zinc-200" />
        <h2 className="text-sm font-medium text-zinc-800">{currentNovel?.title || "Untitled Story"}</h2>
      </div>

      <div className="flex items-center gap-4">
        <WritingModeSwitch />
        
        <div className="h-4 w-[1px] bg-zinc-200" />

        <div className="flex items-center gap-4 text-zinc-500">
          <button onClick={() => setShowAgentModal(true)} title="Agent 管理" className="hover:text-indigo-600 transition-colors flex items-center gap-1 text-xs font-semibold">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><polyline points="17 11 19 13 23 9"/></svg>
            <span>Agent 管理</span>
          </button>
          <button onClick={() => setShowSettingsModal(true)} title="系统设置" className="hover:text-indigo-600 transition-colors flex items-center gap-1 text-xs font-semibold">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
            <span>系统设置</span>
          </button>
        </div>

        <button onClick={handleExport} className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-1.5 text-xs font-bold text-white hover:bg-indigo-700 shadow-sm transition-all">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          <span>Export</span>
        </button>
      </div>

      {/* Agent Modal */}
      {showAgentModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl flex flex-col max-h-[85vh]">
            <div className="p-6 border-b border-zinc-100 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-zinc-800">Agent 管理</h3>
                <p className="text-xs text-zinc-400 mt-1">配置 AI 创作团队的角色、提示词与创造力参数</p>
              </div>
              <button onClick={() => setShowAgentModal(false)} className="text-zinc-400 hover:text-zinc-600 transition-colors">✕</button>
            </div>
            <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-zinc-50/30">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {agents.map(agent => (
                  <div key={agent.id} className={`space-y-4 p-5 rounded-2xl bg-white border transition-all ${agent.enabled ? 'border-indigo-100 shadow-sm' : 'border-zinc-200 opacity-60'}`}>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg ${agent.enabled ? 'bg-indigo-50 text-indigo-600' : 'bg-zinc-100 text-zinc-400'}`}>
                          {agent.id === 'writer' ? '✍️' : agent.id === 'editor' ? '🔍' : agent.id === 'reader' ? '📖' : agent.id === 'conflict' ? '💥' : agent.id === 'world' ? '🌍' : '📋'}
                        </div>
                        <div>
                          <h4 className="text-sm font-bold text-zinc-800">{agent.name}</h4>
                          <input 
                            value={agent.role}
                            onChange={(e) => updateAgent(agent.id, { role: e.target.value })}
                            placeholder="角色描述..."
                            className="text-[10px] text-indigo-600 font-medium bg-transparent border-none p-0 focus:ring-0 w-full"
                          />
                        </div>
                      </div>
                      <button 
                        onClick={() => updateAgent(agent.id, { enabled: !agent.enabled })}
                        className={`w-10 h-5 rounded-full relative transition-colors ${agent.enabled ? 'bg-indigo-600' : 'bg-zinc-300'}`}
                      >
                        <div className={`absolute top-1 w-3 h-3 bg-white rounded-full transition-all ${agent.enabled ? 'right-1' : 'left-1'}`} />
                      </button>
                    </div>

                    <div className="space-y-3">
                      <div className="space-y-1">
                        <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">System Prompt</label>
                        <textarea 
                          value={agent.prompt}
                          onChange={(e) => updateAgent(agent.id, { prompt: e.target.value })}
                          className="w-full h-28 p-3 text-xs border border-zinc-100 rounded-xl focus:ring-2 focus:ring-indigo-500/10 outline-none resize-none bg-zinc-50/50"
                        />
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between text-[10px] font-bold text-zinc-500">
                          <span>温度 (Temperature / 创造力)</span>
                          <span>{agent.temperature}</span>
                        </div>
                        <input 
                          type="range" min="0" max="1" step="0.1" 
                          value={agent.temperature} 
                          onChange={(e) => updateAgent(agent.id, { temperature: parseFloat(e.target.value) })} 
                          className="w-full accent-indigo-600 h-1 bg-zinc-100 rounded-lg appearance-none cursor-pointer" 
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Settings Modal */}
      {showSettingsModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg flex flex-col max-h-[85vh]">
            <div className="p-6 border-b border-zinc-100 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-zinc-800">系统设置</h3>
                <p className="text-xs text-zinc-400 mt-1">全局调控 AI 创作风格、节奏与深度参数</p>
              </div>
              <button onClick={() => setShowSettingsModal(false)} className="text-zinc-400 hover:text-zinc-600 transition-colors">✕</button>
            </div>
            <div className="flex-1 overflow-y-auto p-6 space-y-8 bg-zinc-50/30">
              {/* Constraints Section */}
              <div className="space-y-4 p-5 rounded-2xl bg-white border border-zinc-100 shadow-sm">
                <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">写作约束 (Constraints)</h4>
                <div className="space-y-3">
                  <div className="relative">
                    <input 
                      type="text" 
                      placeholder="添加新约束 (按回车)..." 
                      value={newConstraint}
                      onChange={(e) => setNewConstraint(e.target.value)}
                      onKeyDown={handleAddConstraint}
                      className="w-full pl-3 pr-10 py-2.5 text-xs border border-zinc-100 rounded-xl focus:ring-2 focus:ring-indigo-500/10 outline-none bg-zinc-50/50"
                    />
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-300 text-xs">⏎</div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {constraints.map((c, i) => (
                      <span key={i} className="flex items-center gap-2 px-3 py-1.5 bg-indigo-50/50 rounded-lg text-[10px] font-bold text-indigo-600 border border-indigo-100 group">
                        {c}
                        <button onClick={() => removeConstraint(i)} className="hover:text-red-500 opacity-40 group-hover:opacity-100 transition-all">✕</button>
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Agent Configs Section */}
              <div className="space-y-6 p-5 rounded-2xl bg-white border border-zinc-100 shadow-sm">
                <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">创作引擎参数 (Engine Parameters)</h4>
                
                <div className="space-y-6">
                  {/* Style Select */}
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-zinc-500 uppercase">创作风格 (Style)</label>
                    <select 
                      value={agentConfigs.style}
                      onChange={(e) => updateAgentConfig({ style: e.target.value })}
                      className="w-full p-2.5 text-xs border border-zinc-100 rounded-xl focus:ring-2 focus:ring-indigo-500/10 outline-none bg-zinc-50/50 text-zinc-600 font-medium"
                    >
                      <option value="经典文学">经典文学</option>
                      <option value="网络小说">网络小说</option>
                      <option value="轻小说">轻小说</option>
                      <option value="赛博朋克">赛博朋克</option>
                      <option value="武侠风">武侠风</option>
                      <option value="克苏鲁">克苏鲁</option>
                    </select>
                  </div>

                  {/* Range Sliders */}
                  {[
                    { label: "读者兴奋度", key: "excitement_level", low: "平淡", high: "极度刺激" },
                    { label: "编辑严格度", key: "strictness", low: "宽松", high: "极其严苛" },
                    { label: "叙事节奏", key: "pacing", low: "缓慢 (Slow)", high: "快速 (Fast)" },
                    { label: "人物深度", key: "character_depth", low: "扁平", high: "多维立体" },
                    { label: "冲突强度", key: "conflict_intensity", low: "微弱 (Low)", high: "剧烈 (High)" },
                    { label: "描写密度", key: "description_density", low: "简练 (Low)", high: "华丽 (High)" },
                  ].map((slider) => (
                    <div key={slider.key} className="space-y-2">
                      <div className="flex justify-between text-[10px] font-bold text-zinc-500">
                        <span>{slider.label}</span>
                        <span className="text-indigo-600">{(agentConfigs as any)[slider.key]}</span>
                      </div>
                      <input 
                        type="range" min="1" max="10" 
                        value={(agentConfigs as any)[slider.key]} 
                        onChange={(e) => updateAgentConfig({ [slider.key]: parseInt(e.target.value) })} 
                        className="w-full accent-indigo-600 h-1 bg-zinc-100 rounded-lg appearance-none cursor-pointer" 
                      />
                      <div className="flex justify-between text-[8px] font-bold text-zinc-300 uppercase tracking-widest">
                        <span>{slider.low}</span>
                        <span>{slider.high}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};
