import React, { useState, useMemo, useEffect } from 'react';
import { useAssetStore, type AssetType, type GlobalAsset, type AgentType } from '@/store/assetStore';
import { useNovelStore } from '@/store/novelStore';

type ViewMode = 'by-novel' | 'by-type' | 'starred';

const agentTypeLabels: Record<AgentType, string> = {
  writer: '写作Agent',
  editor: '编辑Agent',
  planner: '规划Agent',
  conflict: '冲突Agent',
  reader: '读者Agent',
  summary: '总结Agent'
};

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

// 获取按小说分组的资产
const getAssetsByNovel = (assets: GlobalAsset[]) => {
  const grouped: Record<string, { id: string; name: string; assets: GlobalAsset[] }> = {};
  assets.forEach(asset => {
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
    fetchSkillsByAsset,
    createSkillFromAsset,
    toggleSkillActive,
    deleteSkill,
    getSkillsByAssetId
  } = useAssetStore();

  const [viewMode, setViewMode] = useState<ViewMode>('by-novel');
  const [selectedNovelId, setSelectedNovelId] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<AssetType | null>(null);
  const [selectedAsset, setSelectedAsset] = useState<GlobalAsset | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showSkillModal, setShowSkillModal] = useState(false);
  const [skillName, setSkillName] = useState('');
  const [skillDescription, setSkillDescription] = useState('');
  const [selectedAgents, setSelectedAgents] = useState<AgentType[]>(['writer']);

  // 初始加载
  useEffect(() => {
    fetchAllAssets();
  }, [fetchAllAssets]);

  // 加载选中资产的技能
  useEffect(() => {
    if (selectedAsset) {
      fetchSkillsByAsset(selectedAsset.id);
      setSkillName(`${selectedAsset.name}约束`);
      setSkillDescription(`基于${selectedAsset.name}设定的创作约束`);
    }
  }, [selectedAsset, fetchSkillsByAsset]);

  // 按小说分组的资产
  const novelsWithAssets = useMemo(() => getAssetsByNovel(assets), [assets]);

  // 过滤资产
  const filteredAssets = useMemo(() => {
    let result = assets;

    // 根据视图模式过滤
    if (viewMode === 'by-novel' && selectedNovelId) {
      result = result.filter(a => a.source_novel_id === selectedNovelId);
    } else if (viewMode === 'by-type' && selectedType) {
      result = result.filter(a => a.type === selectedType);
    } else if (viewMode === 'starred') {
      result = result.filter(a => a.is_starred);
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
  }, [assets, viewMode, selectedNovelId, selectedType, searchQuery]);

  // 处理挂载/卸载
  const handleToggleMount = async (assetId: string, novelId: string) => {
    const isMounted = isAssetMounted(assetId, novelId);
    if (isMounted) {
      await unmountAssetFromNovel(assetId, novelId);
    } else {
      await mountAssetToNovel(assetId, novelId, 'linked');
    }
  };

  // 处理收藏
  const handleToggleStar = async (e: React.MouseEvent, assetId: string) => {
    e.stopPropagation();
    await toggleStarAsset(assetId);
  };

  // 处理创建技能
  const handleCreateSkill = async () => {
    if (!selectedAsset || selectedAgents.length === 0) return;

    await createSkillFromAsset(
      selectedAsset.id,
      skillName,
      skillDescription,
      selectedAgents,
      currentNovelId || undefined
    );

    setShowSkillModal(false);
  };

  // 切换Agent选择
  const toggleAgentSelection = (agent: AgentType) => {
    setSelectedAgents(prev =>
      prev.includes(agent)
        ? prev.filter(a => a !== agent)
        : [...prev, agent]
    );
  };

  // 获取当前资产的技能
  const assetSkills = selectedAsset ? getSkillsByAssetId(selectedAsset.id) : [];

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-zinc-400">加载中...</div>
      </div>
    );
  }

  return (
    <div className="h-full flex">
      {/* 左侧：全局分类树 */}
      <div className="w-64 bg-zinc-50 border-r border-zinc-200 flex flex-col">
        <div className="p-4 border-b border-zinc-200">
          <h2 className="text-sm font-semibold text-zinc-900">资产库</h2>
          <p className="text-xs text-zinc-500 mt-1">全局资源管理中心</p>
        </div>
        
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          {/* 按小说归类 */}
          <div className="mb-4">
            <button
              onClick={() => { setViewMode('by-novel'); setSelectedNovelId(null); }}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                viewMode === 'by-novel' && !selectedNovelId
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'text-zinc-700 hover:bg-zinc-100'
              }`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
              按小说归类
            </button>
            {viewMode === 'by-novel' && (
              <div className="ml-4 mt-1 space-y-1">
                {novelsWithAssets.map(novel => (
                  <button
                    key={novel.id}
                    onClick={() => setSelectedNovelId(novel.id)}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${
                      selectedNovelId === novel.id
                        ? 'bg-indigo-50 text-indigo-700'
                        : 'text-zinc-600 hover:bg-zinc-100'
                    }`}
                  >
                    <span className="truncate">{novel.name}</span>
                    <span className="text-xs text-zinc-400">{novel.assets.length}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* 按类型归类 */}
          <div className="mb-4">
            <button
              onClick={() => { setViewMode('by-type'); setSelectedType(null); }}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                viewMode === 'by-type' && !selectedType
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'text-zinc-700 hover:bg-zinc-100'
              }`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 7V4h3"/><path d="M4 17v3h3"/><path d="M20 7V4h-3"/><path d="M20 17v3h-3"/><circle cx="12" cy="12" r="3"/></svg>
              按类型归类
            </button>
            {viewMode === 'by-type' && (
              <div className="ml-4 mt-1 space-y-1">
                {(Object.keys(typeLabels) as AssetType[]).map(type => (
                  <button
                    key={type}
                    onClick={() => setSelectedType(type)}
                    className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                      selectedType === type
                        ? 'bg-indigo-50 text-indigo-700'
                        : 'text-zinc-600 hover:bg-zinc-100'
                    }`}
                  >
                    <span className="text-zinc-400">{typeIcons[type]}</span>
                    <span>{typeLabels[type]}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* 收藏/常用 */}
          <button
            onClick={() => setViewMode('starred')}
            className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              viewMode === 'starred'
                ? 'bg-indigo-100 text-indigo-700'
                : 'text-zinc-700 hover:bg-zinc-100'
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
            收藏/常用
          </button>
        </div>
      </div>

      {/* 中间：资产预览网格 */}
      <div className="flex-1 flex flex-col bg-zinc-50/50">
        {/* 顶部搜索栏 */}
        <div className="p-4 border-b border-zinc-200 bg-white">
          <div className="relative max-w-xl">
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              width="18" 
              height="18" 
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
              placeholder="搜索资产（如：林渊、青云宗...）"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 text-sm border border-zinc-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
            />
          </div>
        </div>

        {/* 资产网格 */}
        <div className="flex-1 overflow-y-auto p-6">
          {filteredAssets.length > 0 ? (
            <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {filteredAssets.map(asset => (
                <div
                  key={asset.id}
                  onClick={() => setSelectedAsset(asset)}
                  className={`group bg-white border rounded-xl p-4 cursor-pointer transition-all hover:shadow-md ${
                    selectedAsset?.id === asset.id
                      ? 'border-indigo-500 ring-2 ring-indigo-500/20'
                      : 'border-zinc-200 hover:border-zinc-300'
                  }`}
                >
                  {/* 卡片头部 */}
                  <div className="flex items-start justify-between mb-3">
                    <div 
                      className="w-10 h-10 rounded-lg flex items-center justify-center"
                      style={{ backgroundColor: `${asset.color || '#6366f1'}15`, color: asset.color || '#6366f1' }}
                    >
                      {typeIcons[asset.type]}
                    </div>
                    <div className="flex items-center gap-1">
                      {/* 收藏按钮 */}
                      <button
                        onClick={(e) => handleToggleStar(e, asset.id)}
                        className={`p-1.5 rounded-lg transition-colors ${
                          asset.is_starred 
                            ? 'text-amber-500 hover:bg-amber-50' 
                            : 'text-zinc-300 hover:text-amber-500 hover:bg-zinc-100'
                        }`}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill={asset.is_starred ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                      </button>
                      {/* 引用计数 */}
                      {asset.mount_count > 0 && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium text-amber-600 bg-amber-50 rounded-full">
                          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 17h.01"/><path d="M12 2a8 8 0 0 0-8 8c0 3.866 2.582 6.473 6.667 9.623.68.565 1.333.877 1.333.877s.653-.312 1.333-.877C17.418 16.473 20 13.866 20 10a8 8 0 0 0-8-8Z"/></svg>
                          {asset.mount_count}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* 资产名称 */}
                  <h3 className="font-semibold text-zinc-900 mb-1">{asset.name}</h3>
                  
                  {/* 描述 */}
                  {asset.description && (
                    <p className="text-xs text-zinc-500 mb-3 line-clamp-2">{asset.description}</p>
                  )}

                  {/* 所属作品 */}
                  <div className="flex items-center gap-1.5 text-xs text-zinc-400">
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
                    <span className="truncate">{asset.source_novel_name}</span>
                  </div>
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

      {/* 右侧：引用详情面板 */}
      <div className="w-80 bg-white border-l border-zinc-200 flex flex-col">
        {selectedAsset ? (
          <>
            {/* 面板头部 */}
            <div className="p-4 border-b border-zinc-200">
              <div className="flex items-center gap-3 mb-3">
                <div 
                  className="w-12 h-12 rounded-xl flex items-center justify-center"
                  style={{ backgroundColor: `${selectedAsset.color || '#6366f1'}15`, color: selectedAsset.color || '#6366f1' }}
                >
                  {typeIcons[selectedAsset.type]}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-zinc-900 truncate">{selectedAsset.name}</h3>
                  <span className="text-xs text-zinc-500">{typeLabels[selectedAsset.type]}</span>
                </div>
                <button
                  onClick={(e) => handleToggleStar(e, selectedAsset.id)}
                  className={`p-2 rounded-lg transition-colors ${
                    selectedAsset.is_starred 
                      ? 'text-amber-500 hover:bg-amber-50' 
                      : 'text-zinc-300 hover:text-amber-500 hover:bg-zinc-100'
                  }`}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill={selectedAsset.is_starred ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                </button>
              </div>
              <p className="text-sm text-zinc-600">{selectedAsset.description}</p>
            </div>

            {/* 引用管理 */}
            <div className="flex-1 overflow-y-auto p-4">
              <div className="mb-4">
                <h4 className="text-sm font-medium text-zinc-900 mb-3">挂载到作品</h4>
                <p className="text-xs text-zinc-500 mb-3">选择要引用此资产的小说</p>
                
                <div className="space-y-2">
                  {novels.map(novel => {
                    const isMounted = isAssetMounted(selectedAsset.id, novel.id);
                    return (
                      <label
                        key={novel.id}
                        className="flex items-center gap-3 p-3 border border-zinc-200 rounded-lg cursor-pointer hover:bg-zinc-50 transition-colors"
                      >
                        <input
                          type="checkbox"
                          checked={isMounted}
                          onChange={() => handleToggleMount(selectedAsset.id, novel.id)}
                          className="w-4 h-4 rounded border-zinc-300 text-indigo-600 focus:ring-indigo-500"
                        />
                        <div className="flex-1">
                          <div className="text-sm font-medium text-zinc-900">{novel.title}</div>
                          <div className="text-xs text-zinc-500">
                            {isMounted ? '已挂载' : '未挂载'}
                          </div>
                        </div>
                      </label>
                    );
                  })}
                </div>
              </div>

              {/* 版本控制 */}
              {selectedAsset.version_count > 0 && (
                <div className="pt-4 border-t border-zinc-200">
                  <h4 className="text-sm font-medium text-zinc-900 mb-3">版本控制</h4>
                  <div className="space-y-2">
                    <label className="flex items-center gap-3 p-3 bg-indigo-50 border border-indigo-200 rounded-lg cursor-pointer">
                      <input type="radio" name="link-mode" defaultChecked className="w-4 h-4 text-indigo-600" />
                      <div>
                        <div className="text-sm font-medium text-zinc-900">链接引用</div>
                        <div className="text-xs text-zinc-500">随原著更新</div>
                      </div>
                    </label>
                    <label className="flex items-center gap-3 p-3 border border-zinc-200 rounded-lg cursor-pointer hover:bg-zinc-50">
                      <input type="radio" name="link-mode" className="w-4 h-4 text-indigo-600" />
                      <div>
                        <div className="text-sm font-medium text-zinc-900">断开链接</div>
                        <div className="text-xs text-zinc-500">克隆到当前作品，独立演化</div>
                      </div>
                    </label>
                  </div>
                </div>
              )}

              {/* Agent技能联动 */}
              <div className="pt-4 border-t border-zinc-200">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-medium text-zinc-900">Agent约束</h4>
                  <button
                    onClick={() => setShowSkillModal(true)}
                    className="text-xs px-3 py-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-1"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14M5 12h14"/></svg>
                    设为Agent约束
                  </button>
                </div>

                {assetSkills.length > 0 ? (
                  <div className="space-y-2">
                    {assetSkills.map(skill => (
                      <div
                        key={skill.id}
                        className={`p-3 border rounded-lg transition-colors ${
                          skill.is_active
                            ? 'border-indigo-200 bg-indigo-50'
                            : 'border-zinc-200 bg-zinc-50 opacity-60'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-zinc-900">{skill.name}</span>
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => toggleSkillActive(skill.id)}
                              className={`p-1 rounded transition-colors ${
                                skill.is_active
                                  ? 'text-indigo-600 hover:bg-indigo-100'
                                  : 'text-zinc-400 hover:bg-zinc-200'
                              }`}
                              title={skill.is_active ? '禁用' : '启用'}
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                {skill.is_active ? (
                                  <><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></>
                                ) : (
                                  <><path d="M12 2v4M12 18v4"/></>
                                )}
                              </svg>
                            </button>
                            <button
                              onClick={() => deleteSkill(skill.id)}
                              className="p-1 text-zinc-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                              title="删除"
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
                            </button>
                          </div>
                        </div>
                        <p className="text-xs text-zinc-500 mb-2">{skill.description}</p>
                        <div className="flex flex-wrap gap-1">
                          {skill.target_agents.map(agent => (
                            <span
                              key={agent}
                              className="text-xs px-2 py-0.5 bg-white border border-zinc-200 rounded text-zinc-600"
                            >
                              {agentTypeLabels[agent]}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-4 text-zinc-400 text-sm">
                    <p>暂无Agent约束</p>
                    <p className="text-xs mt-1">点击上方按钮创建</p>
                  </div>
                )}
              </div>

              {/* 统计信息 */}
              <div className="pt-4 border-t border-zinc-200 mt-4">
                <h4 className="text-sm font-medium text-zinc-900 mb-3">统计信息</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-zinc-500">创建时间</span>
                    <span className="text-zinc-900">{new Date(selectedAsset.created_at).toLocaleDateString('zh-CN')}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">最后修改</span>
                    <span className="text-zinc-900">{new Date(selectedAsset.updated_at).toLocaleDateString('zh-CN')}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-500">引用次数</span>
                    <span className="text-zinc-900">{selectedAsset.mount_count || 0} 次</span>
                  </div>
                  {selectedAsset.version_count > 0 && (
                    <div className="flex justify-between">
                      <span className="text-zinc-500">版本数量</span>
                      <span className="text-zinc-900">{selectedAsset.version_count} 个</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* 底部操作 */}
            <div className="p-4 border-t border-zinc-200 space-y-2">
              <button className="w-full py-2.5 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors">
                编辑资产
              </button>
              <button className="w-full py-2.5 text-sm font-medium text-zinc-700 bg-zinc-100 hover:bg-zinc-200 rounded-lg transition-colors">
                设为 Agent 约束
              </button>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-zinc-400 p-6 text-center">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="mb-4"><path d="M12 2H2v10h10V2Z"/><path d="M12 12H2v10h10V12Z"/><path d="M22 2h-10v10h10V2Z"/><path d="M22 12h-10v10h10V12Z"/></svg>
            <p className="text-sm">选择一个资产查看详情</p>
            <p className="text-xs mt-1">点击左侧卡片进行管理</p>
          </div>
        )}
      </div>

      {/* 创建技能弹窗 */}
      {showSkillModal && selectedAsset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/30 backdrop-blur-sm"
            onClick={() => setShowSkillModal(false)}
          />
          <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 overflow-hidden">
            {/* 弹窗头部 */}
            <div className="px-6 py-4 border-b border-zinc-200">
              <h3 className="text-lg font-semibold text-zinc-900">设为Agent约束</h3>
              <p className="text-sm text-zinc-500 mt-1">
                将「{selectedAsset.name}」转化为Agent创作约束
              </p>
            </div>

            {/* 弹窗内容 */}
            <div className="p-6 space-y-4">
              {/* 技能名称 */}
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">
                  约束名称
                </label>
                <input
                  type="text"
                  value={skillName}
                  onChange={(e) => setSkillName(e.target.value)}
                  className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-sm"
                  placeholder="输入约束名称"
                />
              </div>

              {/* 技能描述 */}
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">
                  约束描述
                </label>
                <textarea
                  value={skillDescription}
                  onChange={(e) => setSkillDescription(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-sm resize-none"
                  placeholder="描述此约束的作用"
                />
              </div>

              {/* 目标Agent */}
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-2">
                  应用到Agent
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {(Object.keys(agentTypeLabels) as AgentType[]).map(agent => (
                    <label
                      key={agent}
                      className={`flex items-center gap-2 p-3 border rounded-lg cursor-pointer transition-colors ${
                        selectedAgents.includes(agent)
                          ? 'border-indigo-500 bg-indigo-50'
                          : 'border-zinc-200 hover:border-zinc-300'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedAgents.includes(agent)}
                        onChange={() => toggleAgentSelection(agent)}
                        className="w-4 h-4 rounded border-zinc-300 text-indigo-600 focus:ring-indigo-500"
                      />
                      <span className="text-sm text-zinc-700">{agentTypeLabels[agent]}</span>
                    </label>
                  ))}
                </div>
                {selectedAgents.length === 0 && (
                  <p className="text-xs text-amber-600 mt-2">请至少选择一个Agent</p>
                )}
              </div>

              {/* 预览 */}
              <div className="bg-zinc-50 rounded-lg p-3">
                <p className="text-xs text-zinc-500 mb-1">约束预览</p>
                <p className="text-sm text-zinc-700">
                  {selectedAsset.type === 'characters' && '角色设定约束：'}
                  {selectedAsset.type === 'worldbuilding' && '世界观约束：'}
                  {selectedAsset.type === 'factions' && '势力设定约束：'}
                  {selectedAsset.type === 'locations' && '地点设定约束：'}
                  {selectedAsset.type === 'timeline' && '时间线约束：'}
                  {selectedAsset.name}
                </p>
              </div>
            </div>

            {/* 弹窗底部 */}
            <div className="px-6 py-4 border-t border-zinc-200 flex justify-end gap-3">
              <button
                onClick={() => setShowSkillModal(false)}
                className="px-4 py-2 text-sm text-zinc-600 hover:text-zinc-900 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleCreateSkill}
                disabled={!skillName.trim() || selectedAgents.length === 0}
                className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                创建约束
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StoryAssets;
