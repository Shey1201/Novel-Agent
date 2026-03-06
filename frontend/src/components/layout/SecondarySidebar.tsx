"use client";

import React, { useMemo, useState, useEffect } from "react";
import { useNovelStore, type SidebarView } from "@/store/novelStore";
import { useAssetStore, type AssetType } from "@/store/assetStore";
import { SkillMountPanel } from "@/components/workspace/skills/SkillMountPanel";

interface Volume {
  id: string;
  name: string;
  chapterIds: string[];
}

interface Arc {
  id: string;
  name: string;
}

type SidebarTab = 'structure' | 'bible' | 'skills';

const typeIcons: Record<AssetType, React.ReactNode> = {
  characters: (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
  ),
  worldbuilding: (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>
  ),
  factions: (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
  ),
  locations: (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>
  ),
  timeline: (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
  ),
};

const typeLabels: Record<AssetType, string> = {
  characters: '角色',
  worldbuilding: '世界观',
  factions: '势力',
  locations: '地点',
  timeline: '时间线',
};

export const SecondarySidebar: React.FC = () => {
  const {
    novels,
    currentNovelId,
    currentChapterId,
    setCurrentChapterId,
    setCurrentSidebarView,
    addChapter,
  } = useNovelStore();

  const {
    assets,
    mountedAssets,
    fetchAllAssets,
    fetchMountedAssets,
  } = useAssetStore();

  const [expandStoryBible, setExpandStoryBible] = useState(false);
  const [expandOutline, setExpandOutline] = useState(false);
  const [expandChapters, setExpandChapters] = useState(true);
  const [volumes, setVolumes] = useState<Volume[]>([
    { id: "vol-1", name: "Volume 1", chapterIds: [] },
  ]);
  const [arcs] = useState<Arc[]>([
    { id: "arc-1", name: "Arc 1" },
    { id: "arc-2", name: "Arc 2" },
  ]);
  const [editingVolumeId, setEditingVolumeId] = useState<string | null>(null);
  const [editVolumeName, setEditVolumeName] = useState("");
  const [isAddingVolume, setIsAddingVolume] = useState(false);
  const [newVolumeName, setNewVolumeName] = useState("");
  const [selectedVolumeId, setSelectedVolumeId] = useState<string | null>("vol-1");
  const [chapterMenuOpen, setChapterMenuOpen] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<SidebarTab>('structure');
  const [showAssetModal, setShowAssetModal] = useState(false);
  const [assetSearchQuery, setAssetSearchQuery] = useState('');

  const currentNovel = useMemo(() => novels.find((n) => n.id === currentNovelId), [novels, currentNovelId]);

  useEffect(() => {
    fetchAllAssets();
  }, [fetchAllAssets]);

  useEffect(() => {
    if (currentNovelId) {
      fetchMountedAssets(currentNovelId);
    }
  }, [currentNovelId, fetchMountedAssets]);

  const novelMountedAssets = useMemo(() => {
    const assetIds = mountedAssets[currentNovelId || ''] || [];
    return assets.filter(a => assetIds.includes(a.id));
  }, [assets, mountedAssets, currentNovelId]);

  const mountedAssetsByType = useMemo(() => {
    const grouped: Record<AssetType, typeof novelMountedAssets> = {
      characters: [],
      worldbuilding: [],
      factions: [],
      locations: [],
      timeline: [],
    };
    novelMountedAssets.forEach(asset => {
      if (grouped[asset.type]) {
        grouped[asset.type].push(asset);
      }
    });
    return grouped;
  }, [novelMountedAssets]);

  const availableAssets = useMemo(() => {
    const mountedIds = new Set(mountedAssets[currentNovelId || ''] || []);
    return assets.filter(a => !mountedIds.has(a.id));
  }, [assets, mountedAssets, currentNovelId]);

  const filteredAvailableAssets = useMemo(() => {
    if (!assetSearchQuery) return availableAssets;
    const query = assetSearchQuery.toLowerCase();
    return availableAssets.filter(a => 
      a.name.toLowerCase().includes(query) ||
      a.source_novel_name.toLowerCase().includes(query)
    );
  }, [availableAssets, assetSearchQuery]);

  useEffect(() => {
    if (currentNovel?.chapters.length && !currentChapterId) {
      setCurrentChapterId(currentNovel.chapters[0].id);
      setCurrentSidebarView("chapter");
    }
  }, [currentNovel, currentChapterId, setCurrentChapterId, setCurrentSidebarView]);

  if (!currentNovelId) return null;

  const getChaptersByVolume = (volumeId: string) => {
    if (volumeId === "vol-default") {
      const allAssignedChapterIds = volumes.flatMap(v => v.chapterIds);
      return currentNovel?.chapters.filter(ch => !allAssignedChapterIds.includes(ch.id)) || [];
    }
    const volume = volumes.find(v => v.id === volumeId);
    if (!volume) return [];
    return currentNovel?.chapters.filter(ch => volume.chapterIds.includes(ch.id)) || [];
  };

  const getChapterVolumeId = (chapterId: string): string => {
    for (const vol of volumes) {
      if (vol.chapterIds.includes(chapterId)) {
        return vol.id;
      }
    }
    return "vol-default";
  };

  const addNewChapter = () => {
    if (!currentNovelId) return;
    const next = (currentNovel?.chapters.length || 0) + 1;
    const id = `chapter-${currentNovelId}-${next}`;
    addChapter(currentNovelId, { id, title: `章节 ${next}`, content: "", trace_data: [] });
    setCurrentChapterId(id);
    setCurrentSidebarView("chapter");
    
    if (selectedVolumeId && selectedVolumeId !== "vol-default") {
      setVolumes(prev => prev.map(v => 
        v.id === selectedVolumeId 
          ? { ...v, chapterIds: [...v.chapterIds, id] }
          : v
      ));
    }
  };

  const handleAddVolume = () => {
    if (newVolumeName.trim()) {
      const newVolume: Volume = {
        id: `vol-${Date.now()}`,
        name: newVolumeName.trim(),
        chapterIds: [],
      };
      setVolumes([...volumes, newVolume]);
      setNewVolumeName("");
      setIsAddingVolume(false);
      setSelectedVolumeId(newVolume.id);
    }
  };

  const handleUpdateVolume = (id: string) => {
    if (editVolumeName.trim()) {
      setVolumes(prev => prev.map(v => 
        v.id === id ? { ...v, name: editVolumeName.trim() } : v
      ));
      setEditingVolumeId(null);
    }
  };

  const handleDeleteVolume = (id: string) => {
    if (confirm('确定要删除这个卷吗？该卷下的章节将变为未分卷状态。')) {
      setVolumes(prev => prev.filter(v => v.id !== id));
      if (selectedVolumeId === id) {
        setSelectedVolumeId("vol-default");
      }
    }
  };

  const startEditingVolume = (volume: Volume) => {
    setEditingVolumeId(volume.id);
    setEditVolumeName(volume.name);
  };

  const moveChapterToVolume = (chapterId: string, targetVolumeId: string) => {
    setVolumes(prev => prev.map(v => {
      const newChapterIds = v.chapterIds.filter(id => id !== chapterId);
      if (v.id === targetVolumeId && targetVolumeId !== "vol-default") {
        return { ...v, chapterIds: [...newChapterIds, chapterId] };
      }
      return { ...v, chapterIds: newChapterIds };
    }));
    setChapterMenuOpen(null);
  };

  const unassignedChapters = getChaptersByVolume("vol-default");
  const hasUnassignedChapters = unassignedChapters.length > 0;

  const renderChapterItem = (ch: { id: string; title: string; content?: string }) => {
    const isActive = currentChapterId === ch.id;
    const currentVolumeId = getChapterVolumeId(ch.id);
    // 计算字数（中文字符 + 英文单词）
    const wordCount = ch.content ? 
      (ch.content.match(/[\u4e00-\u9fa5]/g) || []).length + 
      (ch.content.match(/[a-zA-Z]+/g) || []).length : 0;
    
    return (
      <div key={ch.id} className="group/chapter relative">
        <button
          onClick={() => {
            setCurrentChapterId(ch.id);
            setCurrentSidebarView("chapter");
          }}
          className={`w-full text-left px-2.5 py-1.5 rounded-md text-[13px] flex items-center gap-2 ${
            isActive ? "bg-indigo-100 text-indigo-700" : "text-zinc-700 hover:bg-zinc-200"
          }`}
        >
          <span className="text-xs">📄</span>
          <span className="truncate flex-1">{ch.title}</span>
          <span className="text-[10px] text-zinc-400 ml-1">{wordCount > 0 ? `${wordCount}字` : ''}</span>
        </button>
        
        <div className="absolute right-1 top-1/2 -translate-y-1/2 opacity-0 group-hover/chapter:opacity-100">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setChapterMenuOpen(chapterMenuOpen === ch.id ? null : ch.id);
            }}
            className="p-1 text-zinc-400 hover:text-indigo-600 hover:bg-white/50 rounded"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/>
            </svg>
          </button>
          
          {chapterMenuOpen === ch.id && (
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setChapterMenuOpen(null)}
              />
              <div className="absolute right-0 top-full mt-1 w-36 bg-white rounded-lg shadow-lg border border-zinc-200 py-1 z-50">
                <div className="px-3 py-1.5 text-xs text-zinc-400 border-b border-zinc-100">
                  移动到
                </div>
                {volumes.map((volume) => (
                  <button
                    key={volume.id}
                    onClick={() => moveChapterToVolume(ch.id, volume.id)}
                    className={`w-full px-3 py-2 text-left text-xs hover:bg-zinc-50 flex items-center gap-2 ${
                      currentVolumeId === volume.id ? 'text-indigo-600 bg-indigo-50' : 'text-zinc-700'
                    }`}
                  >
                    <span className="text-[10px]">📁</span>
                    {volume.name}
                  </button>
                ))}
                <button
                  onClick={() => moveChapterToVolume(ch.id, "vol-default")}
                  className={`w-full px-3 py-2 text-left text-xs hover:bg-zinc-50 flex items-center gap-2 ${
                    currentVolumeId === "vol-default" ? 'text-indigo-600 bg-indigo-50' : 'text-zinc-700'
                  }`}
                >
                  <span className="text-[10px]">📄</span>
                  未分卷
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    );
  };

  return (
    <aside className="w-64 border-r border-zinc-200 bg-zinc-50 h-full shrink-0 flex flex-col z-10 shadow-sm">
      {/* Tab 切换 */}
      <div className="flex border-b border-zinc-200 bg-white">
        <button
          onClick={() => setActiveTab('structure')}
          className={`flex-1 py-2.5 text-xs font-medium transition-colors ${
            activeTab === 'structure'
              ? 'text-indigo-600 border-b-2 border-indigo-600'
              : 'text-zinc-500 hover:text-zinc-700'
          }`}
        >
          结构
        </button>
        <button
          onClick={() => setActiveTab('bible')}
          className={`flex-1 py-2.5 text-xs font-medium transition-colors ${
            activeTab === 'bible'
              ? 'text-indigo-600 border-b-2 border-indigo-600'
              : 'text-zinc-500 hover:text-zinc-700'
          }`}
        >
          设定
        </button>
        <button
          onClick={() => setActiveTab('skills')}
          className={`flex-1 py-2.5 text-xs font-medium transition-colors ${
            activeTab === 'skills'
              ? 'text-indigo-600 border-b-2 border-indigo-600'
              : 'text-zinc-500 hover:text-zinc-700'
          }`}
        >
          技能
        </button>
      </div>

      <div className="p-3 space-y-1 overflow-y-auto flex-1">
        {activeTab === 'skills' ? (
          <SkillMountPanel novelId={currentNovelId || ''} />
        ) : activeTab === 'structure' ? (
          <>
            {/* Novel 根节点 */}
            <div className="text-[13px] font-bold text-zinc-800 px-2 py-1.5">Novel</div>
            
            {/* Story Bible */}
            <div className="pl-2">
              <button
                onClick={() => setExpandStoryBible(!expandStoryBible)}
                className="w-full flex items-center gap-1 text-[13px] text-zinc-700 hover:bg-zinc-200 rounded-md px-2 py-1.5"
              >
                <span className="text-xs">{expandStoryBible ? "⌄" : "›"}</span>
                <span>Story Bible</span>
              </button>
              
              {expandStoryBible && (
                <div className="pl-4 space-y-0.5 mt-0.5">
                  <button className="w-full text-left text-[13px] text-zinc-600 hover:bg-zinc-200 rounded-md px-2 py-1.5">
                    World
                  </button>
                  <button className="w-full text-left text-[13px] text-zinc-600 hover:bg-zinc-200 rounded-md px-2 py-1.5">
                    Characters
                  </button>
                  <button className="w-full text-left text-[13px] text-zinc-600 hover:bg-zinc-200 rounded-md px-2 py-1.5">
                    Factions
                  </button>
                  <button className="w-full text-left text-[13px] text-zinc-600 hover:bg-zinc-200 rounded-md px-2 py-1.5">
                    Timeline
                  </button>
                </div>
              )}
            </div>

            {/* Outline */}
            <div className="pl-2">
              <button
                onClick={() => setExpandOutline(!expandOutline)}
                className="w-full flex items-center gap-1 text-[13px] text-zinc-700 hover:bg-zinc-200 rounded-md px-2 py-1.5"
              >
                <span className="text-xs">{expandOutline ? "⌄" : "›"}</span>
                <span>Outline</span>
              </button>
              
              {expandOutline && (
                <div className="pl-4 space-y-0.5 mt-0.5">
                  {arcs.map((arc) => (
                    <button
                      key={arc.id}
                      className="w-full text-left text-[13px] text-zinc-600 hover:bg-zinc-200 rounded-md px-2 py-1.5"
                    >
                      {arc.name}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Chapters */}
            <div className="pl-2">
              <div className="flex items-center justify-between pr-1">
                <button
                  onClick={() => setExpandChapters(!expandChapters)}
                  className="flex-1 flex items-center gap-1 text-[13px] text-zinc-700 hover:bg-zinc-200 rounded-md px-2 py-1.5"
                >
                  <span className="text-xs">{expandChapters ? "⌄" : "›"}</span>
                  <span>Chapters</span>
                </button>
                <button 
                  onClick={addNewChapter} 
                  className="w-6 h-6 flex items-center justify-center text-indigo-500 hover:bg-indigo-50 rounded transition-colors"
                  title="添加章节"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
                </button>
              </div>

              {expandChapters && (
                <div className="pl-4 space-y-2 mt-1">
                  {/* 卷列表 */}
                  {volumes.map((volume) => (
                    <div key={volume.id} className="group/volume">
                      {editingVolumeId === volume.id ? (
                        <div className="px-2 py-1 flex items-center gap-1">
                          <input
                            autoFocus
                            value={editVolumeName}
                            onChange={(e) => setEditVolumeName(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleUpdateVolume(volume.id);
                              if (e.key === 'Escape') setEditingVolumeId(null);
                            }}
                            onBlur={() => handleUpdateVolume(volume.id)}
                            className="flex-1 text-[13px] px-2 py-1 border border-zinc-300 rounded outline-none focus:border-indigo-500"
                          />
                        </div>
                      ) : (
                        <div className="flex items-center justify-between px-2 py-1 group/volume-header">
                          <button
                            onClick={() => setSelectedVolumeId(selectedVolumeId === volume.id ? null : volume.id)}
                            className="flex items-center gap-1 text-[13px] text-zinc-500 hover:text-zinc-700"
                          >
                            <span className="text-xs">{selectedVolumeId === volume.id ? "⌄" : "›"}</span>
                            <span>{volume.name}</span>
                          </button>
                          <div className="opacity-0 group-hover/volume:opacity-100 flex items-center gap-1">
                            <button
                              onClick={() => startEditingVolume(volume)}
                              className="p-1 text-zinc-400 hover:text-indigo-600"
                              title="编辑"
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg>
                            </button>
                            <button
                              onClick={() => handleDeleteVolume(volume.id)}
                              className="p-1 text-zinc-400 hover:text-red-600"
                              title="删除"
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/></svg>
                            </button>
                          </div>
                        </div>
                      )}
                      
                      {selectedVolumeId === volume.id && (
                        <div className="pl-3 space-y-0.5 mt-0.5">
                          {getChaptersByVolume(volume.id).map((ch) => renderChapterItem(ch))}
                          {getChaptersByVolume(volume.id).length === 0 && (
                            <div className="text-[12px] text-zinc-400 px-2 py-1">暂无章节</div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}

                  {/* 未分卷章节 */}
                  {(hasUnassignedChapters || volumes.length === 0) && (
                    <div>
                      <button
                        onClick={() => setSelectedVolumeId(selectedVolumeId === "vol-default" ? null : "vol-default")}
                        className="flex items-center gap-1 px-2 py-1 text-[13px] text-zinc-500 hover:text-zinc-700"
                      >
                        <span className="text-xs">{selectedVolumeId === "vol-default" ? "⌄" : "›"}</span>
                        <span>未分卷</span>
                      </button>
                      {selectedVolumeId === "vol-default" && (
                        <div className="pl-3 space-y-0.5 mt-0.5">
                          {unassignedChapters.map((ch) => renderChapterItem(ch))}
                          {unassignedChapters.length === 0 && (
                            <div className="text-[12px] text-zinc-400 px-2 py-1">暂无未分卷章节</div>
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  {/* 添加新卷 */}
                  {isAddingVolume ? (
                    <div className="px-2 py-1">
                      <div className="flex items-center gap-1">
                        <input
                          autoFocus
                          value={newVolumeName}
                          onChange={(e) => setNewVolumeName(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleAddVolume();
                            if (e.key === 'Escape') {
                              setIsAddingVolume(false);
                              setNewVolumeName("");
                            }
                          }}
                          placeholder="卷名称"
                          className="flex-1 text-[13px] px-2 py-1 border border-zinc-300 rounded outline-none focus:border-indigo-500"
                        />
                        <button
                          onClick={handleAddVolume}
                          disabled={!newVolumeName.trim()}
                          className="p-1 text-green-600 hover:bg-green-50 rounded disabled:text-zinc-300"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
                        </button>
                        <button
                          onClick={() => {
                            setIsAddingVolume(false);
                            setNewVolumeName("");
                          }}
                          className="p-1 text-zinc-400 hover:text-red-500"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => setIsAddingVolume(true)}
                      className="w-full px-2 py-1.5 text-left text-[13px] text-zinc-400 hover:text-indigo-600 hover:bg-zinc-100 rounded flex items-center gap-1 transition-colors"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
                      添加新卷
                    </button>
                  )}
                </div>
              )}
            </div>
          </>
        ) : (
          <>
            {/* Bible Tab 内容 */}
            <div className="space-y-4">
              {/* 已挂载的资产列表 */}
              {(Object.keys(mountedAssetsByType) as AssetType[]).map((type) => {
                const typeAssets = mountedAssetsByType[type];
                if (typeAssets.length === 0) return null;
                
                return (
                  <div key={type}>
                    <div className="flex items-center gap-2 px-2 py-1.5 text-[13px] font-medium text-zinc-700">
                      <span className="text-zinc-400">{typeIcons[type]}</span>
                      <span>{typeLabels[type]}</span>
                      <span className="text-xs text-zinc-400">({typeAssets.length})</span>
                    </div>
                    <div className="pl-6 space-y-0.5">
                      {typeAssets.map((asset) => (
                        <button
                          key={asset.id}
                          className="w-full text-left px-2 py-1.5 text-[13px] text-zinc-600 hover:bg-zinc-200 rounded-md flex items-center gap-2 group"
                        >
                          <span className="truncate flex-1">{asset.name}</span>
                          {asset.is_starred && (
                            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="currentColor" className="text-amber-400"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })}

              {novelMountedAssets.length === 0 && (
                <div className="text-center py-8 text-zinc-400">
                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-2"><path d="M12 2H2v10h10V2Z"/><path d="M12 12H2v10h10V12Z"/><path d="M22 2h-10v10h10V2Z"/><path d="M22 12h-10v10h10V12Z"/></svg>
                  <p className="text-xs">暂无引用的设定</p>
                </div>
              )}

              {/* 从全局库添加按钮 */}
              <button
                onClick={() => setShowAssetModal(true)}
                className="w-full py-2.5 text-xs font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg flex items-center justify-center gap-2 transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/><path d="M11 8v6"/><path d="M8 11h6"/></svg>
                从全局库添加
              </button>
            </div>
          </>
        )}
      </div>

      {/* 全局库弹窗 */}
      {showAssetModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div 
            className="absolute inset-0 bg-black/30 backdrop-blur-sm"
            onClick={() => setShowAssetModal(false)}
          />
          <div className="relative bg-white rounded-xl shadow-xl w-[480px] max-h-[600px] flex flex-col">
            {/* 弹窗头部 */}
            <div className="flex items-center justify-between p-4 border-b border-zinc-200">
              <h3 className="font-semibold text-zinc-900">从全局库添加设定</h3>
              <button
                onClick={() => setShowAssetModal(false)}
                className="p-1.5 text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100 rounded-lg transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
              </button>
            </div>

            {/* 搜索框 */}
            <div className="p-4 border-b border-zinc-200">
              <div className="relative">
                <svg 
                  xmlns="http://www.w3.org/2000/svg" 
                  width="16" 
                  height="16" 
                  viewBox="0 0 24 24" 
                  fill="none" 
                  stroke="currentColor" 
                  strokeWidth="2" 
                  strokeLinecap="round" 
                  strokeLinejoin="round"
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400"
                >
                  <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
                </svg>
                <input
                  type="text"
                  placeholder="搜索资产..."
                  value={assetSearchQuery}
                  onChange={(e) => setAssetSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 text-sm border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                />
              </div>
            </div>

            {/* 资产列表 */}
            <div className="flex-1 overflow-y-auto p-4">
              {filteredAvailableAssets.length > 0 ? (
                <div className="space-y-2">
                  {filteredAvailableAssets.map((asset) => (
                    <div
                      key={asset.id}
                      className="flex items-center gap-3 p-3 border border-zinc-200 rounded-lg hover:border-indigo-300 hover:bg-indigo-50/30 transition-colors"
                    >
                      <div 
                        className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
                        style={{ backgroundColor: `${asset.color || '#6366f1'}15`, color: asset.color || '#6366f1' }}
                      >
                        {typeIcons[asset.type]}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm text-zinc-900 truncate">{asset.name}</div>
                        <div className="text-xs text-zinc-500 truncate">{asset.source_novel_name}</div>
                      </div>
                      <button
                        onClick={async () => {
                          if (currentNovelId) {
                            await useAssetStore.getState().mountAssetToNovel(asset.id, currentNovelId, 'linked');
                            await fetchMountedAssets(currentNovelId);
                          }
                        }}
                        className="px-3 py-1.5 text-xs font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors"
                      >
                        添加
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-zinc-400">
                  <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-3"><path d="m21 21-4.34-4.34"/><circle cx="11" cy="11" r="8"/></svg>
                  <p className="text-sm">{assetSearchQuery ? '未找到匹配的资产' : '暂无可添加的资产'}</p>
                </div>
              )}
            </div>

            {/* 底部 */}
            <div className="p-4 border-t border-zinc-200 flex justify-between items-center">
              <span className="text-xs text-zinc-500">
                {filteredAvailableAssets.length} 个可用资产
              </span>
              <button
                onClick={() => setShowAssetModal(false)}
                className="px-4 py-2 text-sm font-medium text-zinc-700 bg-zinc-100 hover:bg-zinc-200 rounded-lg transition-colors"
              >
                完成
              </button>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
};
