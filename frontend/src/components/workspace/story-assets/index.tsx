"use client";

import React, { useState, useMemo, useEffect, useRef } from 'react';
import { useAssetStore, type AssetType, type GlobalAsset } from '@/store/assetStore';
import { useNovelStore } from '@/store/novelStore';

type ViewMode = 'by-type' | 'starred' | 'uncategorized';
type PanelMode = 'view' | 'edit';

// 自定义分类类型
interface CustomCategory {
  id: string;
  name: string;
  color: string;
}

const typeLabels: Record<AssetType, string> = {
  characters: '角色',
  worldbuilding: '世界观',
  factions: '势力',
  locations: '地点',
  timeline: '时间线',
};

const typeIcons: Record<AssetType, React.ReactNode> = {
  characters: (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
  ),
  worldbuilding: (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>
  ),
  factions: (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
  ),
  locations: (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>
  ),
  timeline: (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
  ),
};

const typeColors: Record<AssetType, string> = {
  characters: '#8b5cf6',
  worldbuilding: '#10b981',
  factions: '#f59e0b',
  locations: '#3b82f6',
  timeline: '#ec4899',
};

// 从localStorage加载自定义分类
const loadCustomCategories = (): CustomCategory[] => {
  if (typeof window === 'undefined') return [];
  const saved = localStorage.getItem('asset-custom-categories');
  return saved ? JSON.parse(saved) : [];
};

// 保存自定义分类到localStorage
const saveCustomCategories = (categories: CustomCategory[]) => {
  localStorage.setItem('asset-custom-categories', JSON.stringify(categories));
};

// 获取按小说分组的资产
const getAssetsByNovel = (assets: GlobalAsset[]) => {
  const grouped: Record<string, { id: string; name: string; assets: GlobalAsset[] }> = {};
  assets.forEach(asset => {
    if (asset.source_novel_id === 'uncategorized') return;
    if (!grouped[asset.source_novel_id]) {
      grouped[asset.source_novel_id] = {
        id: asset.source_novel_id,
        name: asset.source_novel_name,
        assets: []
      };
    }
    grouped[asset.source_novel_id].assets.push(asset);
  });
  return Object.values(grouped);
};

// 获取未分类资产
const getUncategorizedAssets = (assets: GlobalAsset[]) => {
  return assets.filter(a => a.source_novel_id === 'uncategorized');
};

const StoryAssets: React.FC = () => {
  const { novels, currentNovelId } = useNovelStore();
  const {
    assets,
    isLoading,
    fetchAllAssets,
    mountAssetToNovel,
    unmountAssetFromNovel,
    toggleStarAsset,
    isAssetMounted,
    setSelectedAsset: setStoreSelectedAsset,
    updateAssetAPI,
    deleteAssetAPI,
    createAsset
  } = useAssetStore();

  const [viewMode, setViewMode] = useState<ViewMode>('by-type');

  const [selectedType, setSelectedType] = useState<AssetType | null>(null);
  const [selectedAsset, setSelectedAsset] = useState<GlobalAsset | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  // 展开/收起状态
  const [expandedSections, setExpandedSections] = useState({
    byType: true,
    customCategories: true,
  });
  
  // 面板模式：view = 只读, edit = 编辑
  const [panelMode, setPanelMode] = useState<PanelMode>('view');
  
  // 编辑状态
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [hasChanges, setHasChanges] = useState(false);
  
  // 创建资产弹窗
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createName, setCreateName] = useState('');
  const [createDescription, setCreateDescription] = useState('');
  const [createType, setCreateType] = useState<AssetType | string>('');
  const [createCategoryId, setCreateCategoryId] = useState<string | null>(null);
  const [typeDropdownOpen, setTypeDropdownOpen] = useState(false);
  const [typeSearchQuery, setTypeSearchQuery] = useState('');
  const typeDropdownRef = useRef<HTMLDivElement>(null);
  
  // 同步提示
  const [syncNotice, setSyncNotice] = useState<string | null>(null);

  // 移动资产弹窗
  const [showMoveModal, setShowMoveModal] = useState(false);
  const [targetNovelId, setTargetNovelId] = useState<string>('');

  // 自定义分类
  const [customCategories, setCustomCategories] = useState<CustomCategory[]>([]);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newCategoryColor, setNewCategoryColor] = useState('#6366f1');
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null);

  // 加载自定义分类
  useEffect(() => {
    setCustomCategories(loadCustomCategories());
  }, []);

  // 初始加载
  useEffect(() => {
    fetchAllAssets();
  }, [fetchAllAssets]);

  // 点击外部关闭类型下拉框
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (typeDropdownRef.current && !typeDropdownRef.current.contains(event.target as Node)) {
        setTypeDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 加载选中资产时重置状态
  useEffect(() => {
    if (selectedAsset) {
      setStoreSelectedAsset(selectedAsset.id);
      setEditName(selectedAsset.name);
      setEditDescription(selectedAsset.description || '');
      setPanelMode('view');
      setHasChanges(false);
    } else {
      setStoreSelectedAsset(null);
    }
  }, [selectedAsset, setStoreSelectedAsset]);
  
  // 处理资产选择
  const handleSelectAsset = (asset: GlobalAsset | null) => {
    setSelectedAsset(asset);
    setPanelMode('view');
    setHasChanges(false);
    setSyncNotice(null);
  };
  
  // 进入编辑模式
  const handleStartEdit = () => {
    if (!selectedAsset) return;
    setEditName(selectedAsset.name);
    setEditDescription(selectedAsset.description || '');
    setPanelMode('edit');
    setHasChanges(false);
  };

  // 取消编辑
  const handleCancelEdit = () => {
    if (!selectedAsset) return;
    setEditName(selectedAsset.name);
    setEditDescription(selectedAsset.description || '');
    setPanelMode('view');
    setHasChanges(false);
  };
  
  // 保存编辑
  const handleSaveEdit = async () => {
    if (!selectedAsset) return;
    
    const updates: Partial<GlobalAsset> = {};
    if (editName.trim() && editName !== selectedAsset.name) {
      updates.name = editName.trim();
    }
    if (editDescription !== (selectedAsset.description || '')) {
      updates.description = editDescription.trim();
    }
    
    if (Object.keys(updates).length > 0) {
      const updated = await updateAssetAPI(selectedAsset.id, updates);
      if (updated) {
        setSelectedAsset(updated);
        setPanelMode('view');
        setHasChanges(false);
        // 显示同步提示
        setSyncNotice('已同步至 Agent Room，Agent 将在下一轮讨论中自动对齐新设定');
        setTimeout(() => setSyncNotice(null), 3000);
      }
    } else {
      setPanelMode('view');
      setHasChanges(false);
    }
  };
  
  // 删除资产（仅用户创建的可删除）
  const handleDeleteAsset = async () => {
    if (!selectedAsset) return;
    
    if (confirm(`确定要删除资产「${selectedAsset.name}」吗？此操作不可撤销。`)) {
      const success = await deleteAssetAPI(selectedAsset.id);
      if (success) {
        setSelectedAsset(null);
        setPanelMode('view');
      }
    }
  };

  // 开始移动资产
  const handleStartMove = () => {
    if (!selectedAsset) return;
    setTargetNovelId(selectedAsset.source_novel_id === 'uncategorized' ? '' : selectedAsset.source_novel_id);
    setShowMoveModal(true);
  };

  // 确认移动资产
  const handleConfirmMove = async () => {
    if (!selectedAsset || !targetNovelId) return;
    
    const targetNovel = novels.find(n => n.id === targetNovelId);
    if (!targetNovel) return;

    const updates: Partial<GlobalAsset> = {
      source_novel_id: targetNovelId,
      source_novel_name: targetNovel.title,
    };
    
    const updated = await updateAssetAPI(selectedAsset.id, updates);
    if (updated) {
      setSelectedAsset(updated);
      setShowMoveModal(false);
      setSyncNotice(`已移动至「${targetNovel.title}」`);
      setTimeout(() => setSyncNotice(null), 3000);
    }
  };
  
  // 开始创建资产（可指定默认类型和分类）
  const handleStartCreate = (defaultType?: AssetType, defaultCategoryId?: string | null) => {
    setCreateName('');
    setCreateDescription('');
    setCreateType(defaultType || '');
    setCreateCategoryId(defaultCategoryId || null);
    setShowCreateModal(true);
  };
  
  // 保存创建（放置到未分类或指定分类）
  const handleSaveCreate = async () => {
    if (!createName.trim()) return;
    
    // 如果没有选择类型，默认为 characters
    const finalType = createType || 'characters';
    
    const newAsset = await createAsset({
      id: `asset_${Date.now()}`,
      name: createName.trim(),
      type: finalType as AssetType,
      description: createDescription.trim(),
      source_novel_id: 'uncategorized',
      source_novel_name: '未分类',
      color: typeColors[finalType as AssetType] || '#6366f1',
      is_starred: false,
      created_by: 'user',
    });
    
    if (newAsset) {
      setShowCreateModal(false);
      setSelectedAsset(newAsset);
      // 根据创建时的选择切换视图
      if (createCategoryId) {
        setSelectedCategoryId(createCategoryId);
        setViewMode('by-type');
      } else if (createType && Object.keys(typeLabels).includes(createType)) {
        setSelectedType(createType as AssetType);
        setViewMode('by-type');
      } else {
        setViewMode('uncategorized');
      }
      setCreateCategoryId(null);
    }
  };

  // 创建自定义分类
  const handleCreateCategory = () => {
    if (!newCategoryName.trim()) return;
    
    // 随机颜色
    const colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6', '#ef4444', '#6b7280', '#14b8a6', '#f97316'];
    const randomColor = colors[Math.floor(Math.random() * colors.length)];
    
    const newCategory: CustomCategory = {
      id: `cat_${Date.now()}`,
      name: newCategoryName.trim(),
      color: randomColor,
    };
    
    const updated = [...customCategories, newCategory];
    setCustomCategories(updated);
    saveCustomCategories(updated);
    setNewCategoryName('');
    setShowCategoryModal(false);
  };

  // 删除自定义分类
  const handleDeleteCategory = (categoryId: string) => {
    if (!confirm('确定要删除此分类吗？分类中的资产将被移至未分类。')) return;
    
    const updated = customCategories.filter(c => c.id !== categoryId);
    setCustomCategories(updated);
    saveCustomCategories(updated);
    
    if (selectedCategoryId === categoryId) {
      setSelectedCategoryId(null);
    }
  };

  // 未分类资产
  const uncategorizedAssets = useMemo(() => getUncategorizedAssets(assets), [assets]);

  // 过滤资产
  const filteredAssets = useMemo(() => {
    let result = assets;

    // 根据视图模式过滤
    if (viewMode === 'by-type' && selectedType) {
      result = result.filter(a => a.type === selectedType);
    } else if (viewMode === 'starred') {
      result = result.filter(a => a.is_starred);
    } else if (viewMode === 'uncategorized') {
      result = result.filter(a => a.source_novel_id === 'uncategorized');
    }

    // 搜索过滤
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(a => 
        a.name.toLowerCase().includes(query) ||
        a.description?.toLowerCase().includes(query) ||
        a.source_novel_name.toLowerCase().includes(query)
      );
    }

    return result;
  }, [assets, viewMode, selectedType, searchQuery]);

  // 处理挂载/卸载
  const handleToggleMount = async (assetId: string, novelId: string) => {
    const isMounted = isAssetMounted(assetId, novelId);
    if (isMounted) {
      await unmountAssetFromNovel(assetId, novelId);
    } else {
      await mountAssetToNovel(assetId, novelId);
    }
  };

  // 处理收藏
  const handleToggleStar = async (e: React.MouseEvent, assetId: string) => {
    e.stopPropagation();
    await toggleStarAsset(assetId);
  };

  // 检查是否有修改
  useEffect(() => {
    if (selectedAsset && panelMode === 'edit') {
      const nameChanged = editName !== selectedAsset.name;
      const descChanged = editDescription !== (selectedAsset.description || '');
      setHasChanges(nameChanged || descChanged);
    }
  }, [editName, editDescription, selectedAsset, panelMode]);

  return (
    <div className="h-full flex bg-zinc-50">
      {/* 左侧：全局分类树 */}
      <div className="w-64 bg-white border-r border-zinc-200 flex flex-col shadow-sm">
        <div className="p-3 border-b border-zinc-100">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-zinc-900">资产库</h2>
              <p className="text-[11px] text-zinc-500 mt-0.5">全局资源管理中心</p>
            </div>
            <button
              onClick={() => handleStartCreate()}
              className="p-1.5 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
              title="新增资产"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            </button>
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto py-2">
          {/* 收藏 - 独立项，带填充图标，显示数量 */}
          <div className="px-2 mb-1">
            <button
              onClick={() => { 
                setViewMode('starred');
                setSelectedType(null);
                setSelectedCategoryId(null);
              }}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-left transition-colors text-[13px] ${
                viewMode === 'starred' 
                  ? 'bg-zinc-100 text-zinc-900' 
                  : 'hover:bg-zinc-50 text-zinc-600'
              }`}
            >
              <div className="flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={viewMode === 'starred' ? 'text-amber-500' : 'text-zinc-400'}><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                <span>收藏</span>
              </div>
              <span className="text-[11px] text-zinc-400">{assets.filter(a => a.is_starred).length}</span>
            </button>
          </div>

          {/* 全部类型 - 直接显示，显示数量 */}
          <div className="px-2 mb-1">
            <button
              onClick={() => { 
                setViewMode('by-type'); 
                setSelectedType(null);
                setSelectedCategoryId(null);
              }}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-left transition-colors text-[13px] font-medium ${
                viewMode === 'by-type' && !selectedType && !selectedCategoryId
                  ? 'bg-zinc-100 text-zinc-900' 
                  : 'hover:bg-zinc-50 text-zinc-600'
              }`}
            >
              <span>全部</span>
              <span className="text-[11px] text-zinc-400">{assets.length}</span>
            </button>
          </div>

          {/* 未分类 - 带数量 */}
          <div className="px-2 mb-1">
            <button
              onClick={() => {
                setViewMode('uncategorized');
                setSelectedType(null);
                setSelectedCategoryId(null);
              }}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-left transition-colors text-[13px] ${
                viewMode === 'uncategorized'
                  ? 'bg-zinc-100 text-zinc-900' 
                  : 'hover:bg-zinc-50 text-zinc-600'
              }`}
            >
              <span>未分类</span>
              <span className="text-[11px] text-zinc-400">{uncategorizedAssets.length}</span>
            </button>
          </div>

          {/* 按类型 - 一级平铺，带彩色圆点，显示数量 */}
          <div className="px-2 mb-1">
            <div className="space-y-0.5">
              {(Object.keys(typeLabels) as AssetType[]).map(type => {
                const count = assets.filter(a => a.type === type).length;
                const isSelected = viewMode === 'by-type' && selectedType === type;
                return (
                  <button
                    key={type}
                    onClick={() => {
                      setViewMode('by-type');
                      setSelectedType(type);
                      setSelectedCategoryId(null);
                    }}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-left transition-colors text-[13px] ${
                      isSelected
                        ? 'bg-zinc-100 text-zinc-900' 
                        : 'hover:bg-zinc-50 text-zinc-600'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span 
                        className="w-2 h-2 rounded-full" 
                        style={{ backgroundColor: typeColors[type] }}
                      />
                      <span>{typeLabels[type]}</span>
                    </div>
                    <span className="text-[11px] text-zinc-400">{count}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* 自定义分类 - 一级平铺，带彩色圆点，显示数量 */}
          <div className="px-2">
            <div className="flex items-center justify-between px-3 py-2">
              <span className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider">自定义</span>
              <button
                onClick={() => setShowCategoryModal(true)}
                className="p-1 text-zinc-400 hover:text-indigo-600 rounded transition-colors"
                title="新建分类"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
              </button>
            </div>
            
            <div className="space-y-0.5">
              {customCategories.map(category => {
                const count = assets.filter(a => (a as GlobalAsset & { category_id?: string }).category_id === category.id).length;
                const isSelected = selectedCategoryId === category.id;
                return (
                  <div
                    key={category.id}
                    className={`flex items-center justify-between px-3 py-2 rounded-lg transition-colors ${
                      isSelected
                        ? 'bg-zinc-100' 
                        : 'hover:bg-zinc-50'
                    }`}
                  >
                    <button
                      onClick={() => setSelectedCategoryId(category.id)}
                      className={`flex items-center gap-2 text-left flex-1 text-[13px] ${
                        isSelected ? 'text-zinc-900' : 'text-zinc-600 hover:text-zinc-900'
                      }`}
                    >
                      <span 
                        className="w-2 h-2 rounded-full" 
                        style={{ backgroundColor: category.color }}
                      />
                      <span>{category.name}</span>
                    </button>
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] text-zinc-400">{count}</span>
                      <button
                        onClick={() => handleDeleteCategory(category.id)}
                        className="p-1 text-zinc-300 hover:text-red-500 transition-colors"
                        title="删除分类"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                      </button>
                    </div>
                  </div>
                );
              })}
              {customCategories.length === 0 && (
                <p className="text-[11px] text-zinc-400 px-3 py-2 italic">暂无自定义分类</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 中间：资产列表 */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* 搜索栏 */}
        <div className="p-4 border-b border-zinc-200 bg-white">
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索资产..."
              className="w-full pl-10 pr-4 py-2 bg-zinc-50 border border-zinc-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
            />
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
          </div>
        </div>

        {/* 资产列表 */}
        <div className="flex-1 overflow-y-auto p-4">
          {isLoading ? (
            <div className="flex items-center justify-center h-full text-zinc-400">
              <div className="animate-spin mr-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
              </div>
              加载中...
            </div>
          ) : filteredAssets.length > 0 ? (
            <div className="grid grid-cols-3 gap-2">
              {filteredAssets.map(asset => (
                <div
                  key={asset.id}
                  onClick={() => handleSelectAsset(asset)}
                  className={`p-3 rounded-lg cursor-pointer transition-all relative group ${
                    selectedAsset?.id === asset.id
                      ? 'bg-white shadow-sm ring-1 ring-indigo-500'
                      : 'bg-white hover:shadow-sm border border-zinc-100'
                  }`}
                >
                  {/* 移动按钮 */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedAsset(asset);
                      handleStartMove();
                    }}
                    className="absolute top-1.5 right-1.5 p-1 text-zinc-300 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-all"
                    title="移动资产"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 9l7-7 7 7"/><path d="M12 16V2"/></svg>
                  </button>
                  
                  {/* 图标和名称同行 */}
                  <div className="flex items-center gap-2 mb-1.5">
                    <div 
                      className="w-6 h-6 rounded flex items-center justify-center shrink-0"
                      style={{ backgroundColor: `${asset.color || '#6366f1'}15`, color: asset.color || '#6366f1' }}
                    >
                      <span className="scale-75">{typeIcons[asset.type]}</span>
                    </div>
                    <h3 className="font-medium text-zinc-900 truncate text-[13px] flex-1 pr-5">{asset.name}</h3>
                  </div>
                  
                  {/* 元信息 */}
                  <div className="flex items-center gap-1.5 text-[11px] text-zinc-400">
                    <span>{typeLabels[asset.type]}</span>
                    <span>·</span>
                    <span className="truncate">{asset.source_novel_name}</span>
                    {asset.is_starred && (
                      <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="#f59e0b" stroke="#f59e0b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="ml-auto"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                    )}
                  </div>
                  
                  {asset.description && (
                    <p className="text-[11px] text-zinc-400 mt-1.5 line-clamp-1">{asset.description}</p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-zinc-400">
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="mb-4"><path d="m21 21-4.34-4.34"/><circle cx="11" cy="11" r="8"/></svg>
              <p className="text-sm">未找到匹配的资产</p>
              <p className="text-xs mt-1">尝试其他搜索词或切换分类</p>
            </div>
          )}
        </div>
      </div>

      {/* 右侧：资产详情面板 */}
      <div className="w-80 bg-white border-l border-zinc-200 flex flex-col shadow-sm">
        {selectedAsset ? (
          <>
            {/* A. 顶部：资产名片（Status） */}
            <div className="p-5 border-b border-zinc-100">
              {/* 同步提示 */}
              {syncNotice && (
                <div className="mb-3 px-3 py-2 bg-emerald-50 border border-emerald-200 rounded-lg">
                  <p className="text-[11px] text-emerald-700 flex items-center gap-1.5">
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                    {syncNotice}
                  </p>
                </div>
              )}
              
              <div className="flex items-start gap-3">
                <div 
                  className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0"
                  style={{ backgroundColor: `${selectedAsset.color || '#6366f1'}15`, color: selectedAsset.color || '#6366f1' }}
                >
                  {typeIcons[selectedAsset.type]}
                </div>
                <div className="flex-1 min-w-0">
                  {/* 名称 */}
                  <div className="group relative">
                    {panelMode === 'edit' ? (
                      <input
                        type="text"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        autoFocus
                        className="w-full px-2 py-1 text-base font-semibold text-zinc-900 border border-indigo-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    ) : (
                      <h3 className="font-semibold text-zinc-900 truncate">{selectedAsset.name}</h3>
                    )}
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-zinc-100 text-zinc-600">#{typeLabels[selectedAsset.type]}</span>
                      {selectedAsset.created_by === 'agent' && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-600">AI生成</span>
                      )}
                    </div>
                  </div>
                </div>
                
                {/* 编辑/保存按钮 */}
                {panelMode === 'edit' ? (
                  <div className="flex items-center gap-1">
                    <button
                      onClick={handleSaveEdit}
                      disabled={!hasChanges}
                      className="p-2 rounded-lg transition-colors bg-emerald-100 text-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed"
                      title="保存"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                    </button>
                    <button
                      onClick={handleCancelEdit}
                      className="p-2 rounded-lg transition-colors hover:bg-zinc-100 text-zinc-400 hover:text-zinc-600"
                      title="取消"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={handleStartEdit}
                    className="p-2 rounded-lg transition-colors hover:bg-zinc-100 text-zinc-400 hover:text-zinc-600"
                    title="编辑"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg>
                  </button>
                )}
              </div>
              
              {/* 描述 */}
              <div className="mt-3 group">
                {panelMode === 'edit' ? (
                  <textarea
                    value={editDescription}
                    onChange={(e) => setEditDescription(e.target.value)}
                    rows={3}
                    className="w-full px-2 py-1.5 text-sm text-zinc-600 border border-indigo-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                    placeholder="添加描述..."
                  />
                ) : (
                  <p className="text-sm text-zinc-600 leading-relaxed">
                    {selectedAsset.description || (
                      <span className="text-zinc-400 italic">暂无描述</span>
                    )}
                  </p>
                )}
              </div>
            </div>

            {/* B. 中部：挂载与版本（查看模式下也可调整） */}
            <div className="flex-1 overflow-y-auto p-5">
              {/* 挂载到作品 */}
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-3">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-indigo-500"><path d="M12 2v20"/><path d="M2 12h20"/><path d="m4.93 4.93 14.14 14.14"/><path d="m19.07 4.93-14.14 14.14"/></svg>
                  <h4 className="text-sm font-medium text-zinc-900">挂载到作品</h4>
                </div>
                <div className="space-y-1.5">
                  {novels.map(novel => {
                    const isMounted = isAssetMounted(selectedAsset.id, novel.id);
                    return (
                      <label
                        key={novel.id}
                        className="flex items-center gap-2 p-2 rounded-lg hover:bg-zinc-50 cursor-pointer transition-colors"
                      >
                        <div className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${
                          isMounted ? 'bg-indigo-600 border-indigo-600' : 'border-zinc-300'
                        }`}>
                          {isMounted && (
                            <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                          )}
                        </div>
                        <input
                          type="checkbox"
                          checked={isMounted}
                          onChange={() => handleToggleMount(selectedAsset.id, novel.id)}
                          className="sr-only"
                        />
                        <span className="text-sm text-zinc-700">{novel.title}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
              
              {/* 版本控制 */}
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-3">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-indigo-500"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                  <h4 className="text-sm font-medium text-zinc-900">版本控制</h4>
                </div>
                <div className="space-y-2">
                  {/* 链接引用选项 */}
                  <label className="flex items-start gap-3 p-3 bg-indigo-50 border border-indigo-200 rounded-lg cursor-pointer">
                    <input
                      type="radio"
                      name="version-control"
                      value="linked"
                      checked={true}
                      readOnly
                      className="mt-0.5 w-4 h-4 text-indigo-600 border-zinc-300 focus:ring-indigo-500"
                    />
                    <div>
                      <p className="text-sm font-medium text-zinc-900">链接引用</p>
                      <p className="text-xs text-zinc-500 mt-0.5">随原著更新</p>
                    </div>
                  </label>
                  
                  {/* 断开链接选项 */}
                  <label className="flex items-start gap-3 p-3 bg-zinc-50 border border-zinc-200 rounded-lg cursor-pointer hover:bg-zinc-100 transition-colors">
                    <input
                      type="radio"
                      name="version-control"
                      value="cloned"
                      className="mt-0.5 w-4 h-4 text-indigo-600 border-zinc-300 focus:ring-indigo-500"
                    />
                    <div>
                      <p className="text-sm font-medium text-zinc-900">断开链接</p>
                      <p className="text-xs text-zinc-500 mt-0.5">克隆到当前作品，独立演化</p>
                    </div>
                  </label>
                </div>
              </div>

            </div>

            {/* C. 底部：操作按钮 */}
            {selectedAsset.created_by === 'user' && (
              <div className="p-5 border-t border-zinc-100">
                <button
                  onClick={handleDeleteAsset}
                  className="w-full py-2 text-sm text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
                  删除资产
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-zinc-400 p-6 text-center">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="mb-4"><path d="M12 2H2v10h10V2Z"/><path d="M12 12H2v10h10V12Z"/><path d="M22 2h-10v10h10V2Z"/><path d="M22 12h-10v10h10V12Z"/></svg>
            <p className="text-sm">选择一个资产查看详情</p>
            <p className="text-xs mt-1">点击左侧卡片进行管理</p>
          </div>
        )}
      </div>

      {/* 创建资产弹窗 */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/30 backdrop-blur-sm"
            onClick={() => setShowCreateModal(false)}
          />
          <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 overflow-hidden">
            <div className="px-6 py-4 border-b border-zinc-200">
              <h3 className="text-lg font-semibold text-zinc-900">新增资产</h3>
              <p className="text-sm text-zinc-500 mt-1">创建新的灵感设定（将放入未分类）</p>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">
                  资产名称 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={createName}
                  onChange={(e) => setCreateName(e.target.value)}
                  className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-sm"
                  placeholder="输入资产名称"
                />
              </div>

              <div ref={typeDropdownRef}>
                <label className="block text-sm font-medium text-zinc-700 mb-1">
                  资产类型
                </label>
                <div className="relative">
                  <button
                    onClick={() => setTypeDropdownOpen(!typeDropdownOpen)}
                    className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-sm bg-white flex items-center justify-between"
                  >
                    <span className={createType ? 'text-zinc-900' : 'text-zinc-400'}>
                      {createType 
                        ? (typeLabels[createType as AssetType] || customCategories.find(c => c.id === createType)?.name || '请选择资产类型')
                        : '请选择资产类型'
                      }
                    </span>
                    <span className="text-zinc-400 text-xs">可选</span>
                  </button>
                  
                  {typeDropdownOpen && (
                    <div className="absolute z-50 w-full mt-1 bg-white border border-zinc-200 rounded-lg shadow-lg max-h-60 overflow-hidden">
                      <div className="p-2 border-b border-zinc-100">
                        <input
                          type="text"
                          value={typeSearchQuery}
                          onChange={(e) => setTypeSearchQuery(e.target.value)}
                          placeholder="搜索类型..."
                          className="w-full px-2 py-1.5 text-sm border border-zinc-200 rounded focus:outline-none focus:border-indigo-500"
                          autoFocus
                        />
                      </div>
                      <div className="overflow-y-auto max-h-48">
                        <button
                          onClick={() => {
                            setCreateType('');
                            setTypeDropdownOpen(false);
                            setTypeSearchQuery('');
                          }}
                          className={`w-full px-3 py-2 text-left text-sm hover:bg-zinc-50 ${!createType ? 'bg-indigo-50 text-indigo-700' : 'text-zinc-600'}`}
                        >
                          请选择资产类型
                        </button>
                        
                        <div className="px-3 py-1 text-xs text-zinc-400 bg-zinc-50">固定类型</div>
                        {(Object.keys(typeLabels) as AssetType[])
                          .filter(type => typeLabels[type].toLowerCase().includes(typeSearchQuery.toLowerCase()))
                          .map(type => (
                            <button
                              key={type}
                              onClick={() => {
                                setCreateType(type);
                                setTypeDropdownOpen(false);
                                setTypeSearchQuery('');
                              }}
                              className={`w-full px-3 py-2 text-left text-sm hover:bg-zinc-50 flex items-center gap-2 ${
                                createType === type ? 'bg-indigo-50 text-indigo-700' : 'text-zinc-700'
                              }`}
                            >
                              <span 
                                className="w-2 h-2 rounded-full" 
                                style={{ backgroundColor: typeColors[type] }}
                              />
                              {typeLabels[type]}
                            </button>
                          ))}
                        
                        {customCategories.length > 0 && (
                          <>
                            <div className="px-3 py-1 text-xs text-zinc-400 bg-zinc-50">自定义分类</div>
                            {customCategories
                              .filter(cat => cat.name.toLowerCase().includes(typeSearchQuery.toLowerCase()))
                              .map(category => (
                                <button
                                  key={category.id}
                                  onClick={() => {
                                    setCreateType(category.id);
                                    setTypeDropdownOpen(false);
                                    setTypeSearchQuery('');
                                  }}
                                  className={`w-full px-3 py-2 text-left text-sm hover:bg-zinc-50 flex items-center gap-2 ${
                                    createType === category.id ? 'bg-indigo-50 text-indigo-700' : 'text-zinc-700'
                                  }`}
                                >
                                  <span 
                                    className="w-2 h-2 rounded-full" 
                                    style={{ backgroundColor: category.color }}
                                  />
                                  {category.name}
                                </button>
                              ))}
                          </>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">
                  资产描述
                </label>
                <textarea
                  value={createDescription}
                  onChange={(e) => setCreateDescription(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-sm resize-none"
                  placeholder="描述资产的详细信息..."
                />
              </div>
            </div>

            <div className="px-6 py-4 border-t border-zinc-200 flex justify-end gap-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-sm text-zinc-600 hover:text-zinc-900 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleSaveCreate}
                disabled={!createName.trim()}
                className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                创建资产
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 移动资产弹窗 */}
      {showMoveModal && selectedAsset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/30 backdrop-blur-sm"
            onClick={() => setShowMoveModal(false)}
          />
          <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-sm mx-4 overflow-hidden">
            <div className="px-6 py-4 border-b border-zinc-200">
              <h3 className="text-lg font-semibold text-zinc-900">移动资产</h3>
              <p className="text-sm text-zinc-500 mt-1">将「{selectedAsset.name}」移动到指定分类</p>
            </div>

            <div className="p-6">
              <label className="block text-sm font-medium text-zinc-700 mb-2">目标分类</label>
              <div className="space-y-1 max-h-60 overflow-y-auto">
                <button
                  onClick={() => setTargetNovelId('uncategorized')}
                  className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left transition-colors ${
                    targetNovelId === 'uncategorized'
                      ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                      : 'hover:bg-zinc-50 text-zinc-700'
                  }`}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-zinc-400"><path d="M3 7v14a2 2 0 0 0 2 2h14"/><path d="M3 7V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v2"/><path d="M3 7h18"/></svg>
                  <span className="text-sm">未分类</span>
                </button>
                {novels.map(novel => (
                  <button
                    key={novel.id}
                    onClick={() => setTargetNovelId(novel.id)}
                    className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left transition-colors ${
                      targetNovelId === novel.id
                        ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                        : 'hover:bg-zinc-50 text-zinc-700'
                    }`}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-zinc-400"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
                    <span className="text-sm">{novel.title}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="px-6 py-4 border-t border-zinc-200 flex justify-end gap-3">
              <button
                onClick={() => setShowMoveModal(false)}
                className="px-4 py-2 text-sm text-zinc-600 hover:text-zinc-900 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleConfirmMove}
                disabled={!targetNovelId || targetNovelId === selectedAsset.source_novel_id}
                className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                确认移动
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 创建分类弹窗 */}
      {showCategoryModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/30 backdrop-blur-sm"
            onClick={() => setShowCategoryModal(false)}
          />
          <div className="relative bg-white rounded-xl shadow-xl w-full max-w-sm mx-4 overflow-hidden">
            <div className="px-5 py-3 border-b border-zinc-200">
              <h3 className="text-base font-semibold text-zinc-900">新建分类</h3>
            </div>

            <div className="p-5">
              <input
                type="text"
                value={newCategoryName}
                onChange={(e) => setNewCategoryName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && newCategoryName.trim()) {
                    handleCreateCategory();
                  }
                  if (e.key === 'Escape') {
                    setShowCategoryModal(false);
                    setNewCategoryName('');
                  }
                }}
                autoFocus
                className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-sm"
                placeholder="输入分类名称"
              />
            </div>

            <div className="px-5 py-3 border-t border-zinc-200 flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowCategoryModal(false);
                  setNewCategoryName('');
                }}
                className="px-3 py-1.5 text-sm text-zinc-600 hover:text-zinc-900 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleCreateCategory}
                disabled={!newCategoryName.trim()}
                className="px-3 py-1.5 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                创建
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StoryAssets;
