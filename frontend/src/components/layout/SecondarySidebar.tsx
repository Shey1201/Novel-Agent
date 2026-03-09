"use client";

import React, { useMemo, useState, useEffect } from "react";
import { useSupabaseStore, type SidebarView } from "@/store/supabaseStore";
import { useAssetStore, type AssetType } from "@/store/assetStore";
import { SkillMountPanel } from "@/components/workspace/skills/SkillMountPanel";

interface Volume {
  id: string;
  name: string;
  chapterIds: string[];
  order: number;
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
    updateChapter,
    deleteChapter,
    addVolume,
    deleteVolume,
    fetchVolumes,
  } = useSupabaseStore();

  const {
    assets,
    mountedAssets,
    fetchAllAssets,
    fetchMountedAssets,
  } = useAssetStore();

  const [editingVolumeId, setEditingVolumeId] = useState<string | null>(null);
  const [editVolumeName, setEditVolumeName] = useState("");
  const [isAddingVolume, setIsAddingVolume] = useState(false);
  const [newVolumeName, setNewVolumeName] = useState("");
  const [expandedVolumes, setExpandedVolumes] = useState<Set<string>>(new Set(['vol-default']));
  const [chapterMenuOpen, setChapterMenuOpen] = useState<string | null>(null);
  // 存储用户创建的"空卷"（还没有章节的卷）
  const [emptyVolumes, setEmptyVolumes] = useState<Volume[]>([]);
  const [activeTab, setActiveTab] = useState<SidebarTab>('structure');
  const [expandStoryBible, setExpandStoryBible] = useState(false);
  const [expandOutline, setExpandOutline] = useState(false);
  const [arcs, setArcs] = useState<Arc[]>([
    { id: 'arc-1', name: '第一幕：开端' },
    { id: 'arc-2', name: '第二幕：发展' },
    { id: 'arc-3', name: '第三幕：高潮' },
    { id: 'arc-4', name: '第四幕：结局' },
  ]);



  const currentNovel = useMemo(() => novels.find((n) => n.id === currentNovelId), [novels, currentNovelId]);

  // 从章节数据聚合卷信息
  const volumes = useMemo(() => {
    if (!currentNovel) return [];
    
    // 从章节中聚合卷信息
    const volumeMap = new Map<string, Volume>();
    
    currentNovel.chapters.forEach(ch => {
      const volName = ch.volumeName || '未分卷';
      const volOrder = ch.volumeOrder || 0;
      // 未分卷使用固定的 id，其他卷使用动态 id
      const volId = volName === '未分卷' ? 'vol-default' : `vol-${volOrder}-${volName}`;
      
      if (!volumeMap.has(volId)) {
        volumeMap.set(volId, {
          id: volId,
          name: volName,
          chapterIds: [],
          order: volOrder,
        });
      }
      volumeMap.get(volId)!.chapterIds.push(ch.id);
    });
    
    // 如果没有章节，返回默认卷
    if (volumeMap.size === 0) {
      volumeMap.set('vol-default', { id: "vol-default", name: "未分卷", chapterIds: [], order: 0 });
    }
    
    // 合并空卷（排除已经在 volumeMap 中的）
    const existingVolIds = new Set(volumeMap.keys());
    const uniqueEmptyVolumes = emptyVolumes.filter(ev => !existingVolIds.has(ev.id));
    
    // 合并并排序
    const allVolumes = [...Array.from(volumeMap.values()), ...uniqueEmptyVolumes];
    return allVolumes.sort((a, b) => a.order - b.order);
  }, [currentNovel?.chapters, emptyVolumes]);

  // 初始化展开状态
  useEffect(() => {
    if (volumes.length > 0 && expandedVolumes.size === 0) {
      setExpandedVolumes(new Set(volumes.map(v => v.id)));
    }
  }, [volumes]);

  // 加载分卷数据
  useEffect(() => {
    if (currentNovelId) {
      fetchVolumes(currentNovelId).then(volumesFromApi => {
        // 将 API 返回的分卷转换为本地 Volume 格式
        const formattedVolumes = (volumesFromApi as any[])
          .filter((v: any) => v.chapter_count === 0) // 只保留空卷
          .map((v: any) => ({
            id: v.id,
            name: v.name,
            chapterIds: [] as string[],
            order: v.order,
          }));
        setEmptyVolumes(formattedVolumes);
      });
    }
  }, [currentNovelId, fetchVolumes]);

  useEffect(() => {
    if (currentNovel?.chapters.length && !currentChapterId) {
      setCurrentChapterId(currentNovel.chapters[0].id);
      setCurrentSidebarView("chapter");
    }
  }, [currentNovel, currentChapterId, setCurrentChapterId, setCurrentSidebarView]);

  if (!currentNovelId) return null;

  const getChaptersByVolume = (volumeId: string) => {
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

  const toggleVolumeExpanded = (volumeId: string) => {
    setExpandedVolumes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(volumeId)) {
        newSet.delete(volumeId);
      } else {
        newSet.add(volumeId);
      }
      return newSet;
    });
  };

  const addNewChapter = async (volumeId: string = "vol-default") => {
    if (!currentNovelId) return;
    const next = (currentNovel?.chapters.length || 0) + 1;
    const id = `chapter-${currentNovelId}-${next}`;
    
    // 获取目标卷的名称和顺序
    const targetVolume = volumes.find(v => v.id === volumeId);
    const volumeName = targetVolume?.name || '未分卷';
    const volumeOrder = targetVolume?.order || 0;
    
    // 创建章节时包含卷信息
    await addChapter(currentNovelId, { 
      id, 
      title: `章节 ${next}`, 
      content: "", 
      trace_data: [],
      volumeName,
      volumeOrder,
    });
    setCurrentChapterId(id);
    setCurrentSidebarView("chapter");
    
    // 展开该卷
    setExpandedVolumes(prev => new Set([...prev, volumeId]));
  };

  const handleAddVolume = async () => {
    if (newVolumeName.trim() && currentNovelId) {
      // 获取当前最大卷序
      const maxOrder = volumes.length > 0 
        ? Math.max(...volumes.map(v => v.order))
        : 0;
      const newOrder = maxOrder + 1;
      const newVolumeId = `vol-${newOrder}-${newVolumeName.trim()}`;
      
      // 调用 API 保存分卷到数据库
      const savedVolume = await addVolume(currentNovelId, {
        id: newVolumeId,
        novelId: currentNovelId,
        name: newVolumeName.trim(),
        order: newOrder,
      });
      
      if (savedVolume) {
        // 创建一个空卷（不创建章节）
        const newVolume: Volume = {
          id: newVolumeId,
          name: newVolumeName.trim(),
          chapterIds: [],
          order: newOrder,
        };
        
        setEmptyVolumes(prev => [...prev, newVolume]);
        
        // 展开新卷
        setExpandedVolumes(prev => new Set([...prev, newVolumeId]));
      }
      
      setNewVolumeName("");
      setIsAddingVolume(false);
    }
  };

  const handleUpdateVolume = async (id: string) => {
    if (!editVolumeName.trim() || !currentNovelId) return;
    
    const volume = volumes.find(v => v.id === id);
    if (!volume) return;
    
    // 更新该卷下所有章节的卷名称
    const chaptersInVolume = currentNovel?.chapters.filter(ch => volume.chapterIds.includes(ch.id)) || [];
    for (const ch of chaptersInVolume) {
      await updateChapter(currentNovelId, ch.id, { volumeName: editVolumeName.trim() });
    }
    
    setEditingVolumeId(null);
    setEditVolumeName("");
  };

  const handleDeleteVolume = async (id: string) => {
    if (id === 'vol-default') {
      alert('不能删除"未分卷"');
      return;
    }
    
    if (!currentNovelId) return;
    
    // 检查是否是空卷
    const emptyVolume = emptyVolumes.find(v => v.id === id);
    if (emptyVolume) {
      // 空卷从数据库和本地状态中删除
      if (confirm('确定要删除这个空卷吗？')) {
        const success = await deleteVolume(currentNovelId, id);
        if (success) {
          setEmptyVolumes(prev => prev.filter(v => v.id !== id));
        }
      }
      return;
    }
    
    if (confirm('确定要删除这个卷吗？该卷下的章节将移动到"未分卷"。')) {
      const volumeToDelete = volumes.find(v => v.id === id);
      if (volumeToDelete) {
        // 将该卷下的所有章节移动到未分卷
        for (const chapterId of volumeToDelete.chapterIds) {
          await updateChapter(currentNovelId, chapterId, { 
            volumeName: '未分卷',
            volumeOrder: 0 
          });
        }
        // 从数据库删除该卷
        await deleteVolume(currentNovelId, id);
      }
    }
  };

  const startEditingVolume = (volume: Volume) => {
    if (volume.id === 'vol-default') {
      alert('不能编辑"未分卷"名称');
      return;
    }
    setEditingVolumeId(volume.id);
    setEditVolumeName(volume.name);
  };

  const moveChapterToVolume = async (chapterId: string, targetVolumeId: string) => {
    if (!currentNovelId) return;
    
    const targetVolume = volumes.find(v => v.id === targetVolumeId);
    if (!targetVolume) return;
    
    // 更新章节的卷信息
    await updateChapter(currentNovelId, chapterId, { 
      volumeName: targetVolume.name,
      volumeOrder: targetVolume.order 
    });
    setChapterMenuOpen(null);
  };

  const handleDeleteChapter = async (chapterId: string) => {
    if (!currentNovelId) return;
    
    if (confirm('确定要删除这个章节吗？此操作不可恢复。')) {
      await deleteChapter(currentNovelId, chapterId);
      
      // 如果删除的是当前选中的章节，切换到其他章节
      if (currentChapterId === chapterId) {
        const remainingChapters = currentNovel?.chapters.filter(ch => ch.id !== chapterId) || [];
        if (remainingChapters.length > 0) {
          setCurrentChapterId(remainingChapters[0].id);
        } else {
          setCurrentChapterId(null);
          setCurrentSidebarView("outline");
        }
      }
    }
  };

  // 计算字数 - 从 HTML 中提取纯文本
  const calculateWordCount = (content: string = ""): number => {
    // 如果是 HTML，先提取纯文本
    let text = content;
    if (content.includes('<') && content.includes('>')) {
      // 简单的 HTML 标签移除
      text = content.replace(/<[^>]+>/g, '');
      // 移除 HTML 实体
      text = text.replace(/&nbsp;/g, ' ').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
    }
    // 移除空白字符
    text = text.replace(/\s+/g, '');
    // 统计中文字符
    const chineseChars = (text.match(/[\u4e00-\u9fa5]/g) || []).length;
    // 统计英文单词（连续的英文字母）
    const englishWords = (text.match(/[a-zA-Z]+/g) || []).length;
    // 统计单个数字字符（不是数字组）
    const numberChars = (text.match(/\d/g) || []).length;
    // 统计其他字符（标点符号等）
    const otherChars = text.length - chineseChars - englishWords - numberChars;
    return chineseChars + englishWords + numberChars + otherChars;
  };

  const renderChapterItem = (ch: { id: string; title: string; content?: string }) => {
    const isActive = currentChapterId === ch.id;
    const currentVolumeId = getChapterVolumeId(ch.id);
    const wordCount = calculateWordCount(ch.content);
    const isMenuOpen = chapterMenuOpen === ch.id;
    
    return (
      <div key={ch.id} className="group/chapter relative">
        <button
          onClick={() => {
            setCurrentChapterId(ch.id);
            setCurrentSidebarView("chapter");
          }}
          className={`w-full text-left px-2.5 py-1.5 rounded-md text-[13px] flex items-center gap-2 transition-colors ${
            isActive ? "bg-indigo-100 text-indigo-700" : "text-zinc-700 hover:bg-zinc-200"
          }`}
        >
          <span className="text-xs">📄</span>
          <span className="truncate flex-1">{ch.title}</span>
          <span className="text-[10px] text-zinc-400 ml-1 tabular-nums">{wordCount > 0 ? `${wordCount}字` : ''}</span>
        </button>
        
        {/* 章节操作按钮 */}
        <div className="absolute right-1 top-1/2 -translate-y-1/2 opacity-0 group-hover/chapter:opacity-100 transition-opacity flex items-center gap-0.5">
          {/* 移动按钮 */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              setChapterMenuOpen(isMenuOpen ? null : ch.id);
            }}
            className="p-1 text-zinc-400 hover:text-indigo-600 hover:bg-white/50 rounded"
            title="移动到..."
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M4 12h16"/><path d="M13 5l7 7-7 7"/>
            </svg>
          </button>
          
          {/* 删除按钮 */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleDeleteChapter(ch.id);
            }}
            className="p-1 text-zinc-400 hover:text-red-600 hover:bg-white/50 rounded"
            title="删除章节"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
            </svg>
          </button>
        </div>
        
        {/* 移动弹窗 - 移到 group/chapter 外部，使用 Portal 方式 */}
        {isMenuOpen && (
          <>
            <div
              className="fixed inset-0 z-40"
              onClick={() => setChapterMenuOpen(null)}
            />
            <div 
              className="absolute right-0 top-full mt-1 w-40 bg-white rounded-lg shadow-lg border border-zinc-200 py-1 z-50"
              style={{ marginTop: '4px' }}
            >
              <div className="px-3 py-1.5 text-xs text-zinc-400 border-b border-zinc-100">
                移动到
              </div>
              {volumes.map((volume) => (
                <button
                  key={volume.id}
                  onClick={(e) => {
                    e.stopPropagation();
                    moveChapterToVolume(ch.id, volume.id);
                  }}
                  className={`w-full px-3 py-2 text-left text-xs hover:bg-zinc-50 flex items-center gap-2 ${
                    currentVolumeId === volume.id ? 'text-indigo-600 bg-indigo-50' : 'text-zinc-700'
                  }`}
                >
                  <span className="text-[10px]">{volume.id === 'vol-default' ? '📄' : '📁'}</span>
                  {volume.name}
                </button>
              ))}
            </div>
          </>
        )}
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
        ) : activeTab === 'bible' ? (
          <>
            {/* Story Bible */}
            <div className="mb-2">
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
            <div className="mb-2">
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
          </>
        ) : (
          <>
            {/* Novel 根节点 - 加粗文字，不可展开 */}
            <div>
              <div className="flex items-center justify-between px-2 py-1.5">
                <span className="text-[13px] font-bold text-zinc-800">Novel</span>
                {/* Novel 右侧按钮组 - 下载和新建卷 */}
                <div className="flex items-center gap-0.5">
                  {/* 下载按钮 */}
                  <button
                    onClick={() => window.dispatchEvent(new CustomEvent('openDownloadDialog'))}
                    className="p-1 text-zinc-400 hover:text-indigo-600 hover:bg-zinc-100 rounded transition-all"
                    title="下载小说"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                      <polyline points="7 10 12 15 17 10"/>
                      <line x1="12" x2="12" y1="15" y2="3"/>
                    </svg>
                  </button>
                  {/* 新建卷按钮 */}
                  <button
                    onClick={() => setIsAddingVolume(true)}
                    className="p-1 text-zinc-400 hover:text-indigo-600 hover:bg-zinc-100 rounded transition-all"
                    title="新建卷"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M5 12h14"/><path d="M12 5v14"/>
                    </svg>
                  </button>
                </div>
              </div>
              <p className="px-2 text-[10px] text-zinc-400 mb-2">内容可通过右侧 Agent Room 生成</p>

              <div className="space-y-1 mt-1">
                {/* 卷列表 - 按顺序排列 */}
                {[...volumes].sort((a, b) => a.order - b.order).map((volume) => (
                  <div key={volume.id} className="group/volume">
                    {editingVolumeId === volume.id ? (
                      <div className="flex items-center gap-1 px-2 py-1.5">
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
                      <div className="group/volume-header">
                        {/* 卷标题行 */}
                        <div className="flex items-center justify-between px-2 py-1.5 rounded-md hover:bg-zinc-200 transition-colors">
                          <button
                            onClick={() => toggleVolumeExpanded(volume.id)}
                            className="flex items-center gap-1 flex-1 text-left"
                          >
                            <span className="text-xs transition-transform inline-flex items-center justify-center w-3 h-4">{expandedVolumes.has(volume.id) ? "⌄" : "›"}</span>
                            <span className="text-[13px] text-zinc-700">{volume.name}</span>
                            <span className="text-[10px] text-zinc-400 ml-1">({volume.chapterIds.length})</span>
                          </button>
                          
                          {/* 卷操作按钮 */}
                          <div className="flex items-center gap-0.5 opacity-0 group-hover/volume:opacity-100 transition-opacity">
                            {/* 新建章节按钮 - 所有卷都显示 */}
                            <button
                              onClick={() => addNewChapter(volume.id)}
                              className="p-1 text-zinc-400 hover:text-indigo-600 hover:bg-white/50 rounded"
                              title="新建章节"
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M5 12h14"/><path d="M12 5v14"/>
                              </svg>
                            </button>
                            {/* 编辑和删除按钮 - 未分卷不显示 */}
                            {volume.id !== 'vol-default' && (
                              <>
                                <button
                                  onClick={() => startEditingVolume(volume)}
                                  className="p-1 text-zinc-400 hover:text-indigo-600 hover:bg-white/50 rounded"
                                  title="编辑卷名"
                                >
                                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                                  </svg>
                                </button>
                                <button
                                  onClick={() => handleDeleteVolume(volume.id)}
                                  className="p-1 text-zinc-400 hover:text-red-600 hover:bg-white/50 rounded"
                                  title="删除卷"
                                >
                                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
                                  </svg>
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                        
                        {/* 章节列表 */}
                        {expandedVolumes.has(volume.id) && (
                          <div className="pl-4 space-y-0.5 mt-0.5">
                            {getChaptersByVolume(volume.id).map((ch) => renderChapterItem(ch))}
                            {getChaptersByVolume(volume.id).length === 0 && (
                              <div className="text-[12px] text-zinc-400 px-2 py-1 italic">暂无章节</div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}

                {/* 添加新卷输入框 */}
                {isAddingVolume ? (
                  <div className="px-2 py-1.5">
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
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M20 6 9 17l-5-5"/>
                        </svg>
                      </button>
                      <button
                        onClick={() => {
                          setIsAddingVolume(false);
                          setNewVolumeName("");
                        }}
                        className="p-1 text-zinc-400 hover:text-red-500"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
                        </svg>
                      </button>
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          </>
        )}
      </div>
    </aside>
  );
};
