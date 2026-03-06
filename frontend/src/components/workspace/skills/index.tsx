"use client";

import React, { useState, useEffect, useMemo } from 'react';
import { useSkillStore, type SkillCategory, type Skill, type AgentType } from '@/store/skillStore';
import { useAssetStore } from '@/store/assetStore';

const categoryTypeLabels: Record<SkillCategory['type'], string> = {
  system: '系统内置',
  writing: '创作文风',
  domain: '领域知识',
  auditing: '质量审计',
};

const categoryTypeColors: Record<SkillCategory['type'], string> = {
  system: '#ef4444',
  writing: '#3b82f6',
  domain: '#10b981',
  auditing: '#f59e0b',
};

const agentTypeLabels: Record<AgentType, string> = {
  writer: '写作Agent',
  editor: '编辑Agent',
  planner: '规划Agent',
  conflict: '冲突Agent',
  reader: '读者Agent',
  summary: '总结Agent',
};

const SkillsManagement: React.FC = () => {
  const {
    categories,
    skills,
    selectedCategoryId,
    selectedSkillId,
    searchQuery,
    isLoading,
    expandedCategories,
    fetchCategories,
    fetchSkills,
    createCategory,
    updateCategory,
    deleteCategory,
    createSkill,
    updateSkill,
    deleteSkill,
    toggleSkillActive,
    testSkill,
    setSelectedCategoryId,
    setSelectedSkillId,
    setSearchQuery,
    toggleCategoryExpanded,
    getChildCategories,
    getSkillsByCategory,
    getFilteredSkills,
  } = useSkillStore();

  const { assets, fetchAllAssets } = useAssetStore();

  const [isAddingCategory, setIsAddingCategory] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newCategoryType, setNewCategoryType] = useState<SkillCategory['type']>('writing');
  const [editingCategoryId, setEditingCategoryId] = useState<string | null>(null);
  const [editCategoryName, setEditCategoryName] = useState('');

  const [isAddingSkill, setIsAddingSkill] = useState(false);
  const [newSkillName, setNewSkillName] = useState('');

  const [testText, setTestText] = useState('');
  const [activeTab, setActiveTab] = useState<'constraints' | 'assets' | 'test'>('constraints');

  // Skill 移动相关状态
  const [isMovingSkill, setIsMovingSkill] = useState(false);
  const [skillToMove, setSkillToMove] = useState<string | null>(null);

  useEffect(() => {
    fetchCategories();
    fetchSkills();
    fetchAllAssets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selectedSkill = useMemo(() => 
    skills.find(s => s.id === selectedSkillId),
    [skills, selectedSkillId]
  );

  const selectedCategory = useMemo(() =>
    categories.find(c => c.id === selectedCategoryId),
    [categories, selectedCategoryId]
  );

  // 根据选中的分类过滤技能
  const filteredSkills = useMemo(() => {
    if (!selectedCategoryId) return skills;
    
    if (selectedCategoryId === 'all') {
      return skills;
    } else if (selectedCategoryId === 'uncategorized') {
      return skills.filter(s => !s.category_id);
    } else {
      // 获取该分类及其所有子分类的ID
      const getAllChildCategoryIds = (catId: string): string[] => {
        const childIds = categories
          .filter(c => c.parent_id === catId)
          .map(c => c.id);
        const grandChildIds = childIds.flatMap(id => getAllChildCategoryIds(id));
        return [catId, ...childIds, ...grandChildIds];
      };
      const categoryIds = getAllChildCategoryIds(selectedCategoryId);
      return skills.filter(s => s.category_id && categoryIds.includes(s.category_id));
    }
  }, [skills, selectedCategoryId, categories]);

  const handleAddCategory = async () => {
    if (!newCategoryName.trim()) return;
    // 根据当前选中的分类确定类型和父分类
    let parentId: string | null = null;
    let type: SkillCategory['type'] = 'writing';
    
    if (selectedCategoryId && selectedCategoryId !== 'uncategorized') {
      const selectedCat = categories.find(c => c.id === selectedCategoryId);
      if (selectedCat) {
        if (selectedCat.parent_id === null) {
          // 选中的是根分类，作为父分类
          parentId = selectedCat.id;
          type = selectedCat.type;
        } else {
          // 选中的是子分类，使用其父分类
          parentId = selectedCat.parent_id;
          type = selectedCat.type;
        }
      }
    }
    
    await createCategory({
      name: newCategoryName.trim(),
      type,
      parent_id: parentId,
      color: categoryTypeColors[type],
      is_system: false,
      order: categories.length,
    });
    setNewCategoryName('');
    setIsAddingCategory(false);
  };

  const handleUpdateCategory = async (id: string) => {
    if (!editCategoryName.trim()) return;
    await updateCategory(id, { name: editCategoryName.trim() });
    setEditingCategoryId(null);
  };

  const handleAddSkill = async () => {
    if (!newSkillName.trim() || !selectedCategoryId) return;
    
    // 确定 category_id：如果是"未归类"或"全部"，则设为 null
    let categoryId: string | null = selectedCategoryId;
    if (selectedCategoryId === 'uncategorized' || selectedCategoryId === 'all') {
      categoryId = null;
    }
    
    // 确定 target_agents
    let targetAgents: AgentType[] = ['writer'];
    if (selectedCategoryId !== 'uncategorized' && selectedCategoryId !== 'all' && selectedCategory) {
      targetAgents = (selectedCategory.default_agents as AgentType[]) || ['writer'];
    }
    
    await createSkill({
      name: newSkillName.trim(),
      description: '',
      category_id: categoryId,
      constraints: [],
      target_agents: targetAgents,
      is_active: true,
      is_system: false,
      linked_assets: [],
      applicable_novels: [],
    });
    setNewSkillName('');
    setIsAddingSkill(false);
  };

  // 递归获取分类及其所有子分类的技能数量
  const getAllSkillsCount = (categoryId: string): number => {
    const directSkills = skills.filter(s => s.category_id === categoryId).length;
    const childCats = categories.filter(c => c.parent_id === categoryId);
    const childSkills = childCats.reduce((sum, cat) => sum + getAllSkillsCount(cat.id), 0);
    return directSkills + childSkills;
  };

  const renderCategoryTree = (parentId: string | null = null, level: number = 0) => {
    const childCategories = getChildCategories(parentId);
    
    return childCategories.map((category) => {
      const isExpanded = expandedCategories.includes(category.id);
      const hasChildren = categories.some(c => c.parent_id === category.id);
      // 根分类显示所有子分类的技能总数，子分类只显示直接属于它的技能数
      const skillCount = category.parent_id === null 
        ? getAllSkillsCount(category.id)
        : skills.filter(s => s.category_id === category.id).length;
      const isRootCategory = category.parent_id === null;
      
      return (
        <div key={category.id} style={{ marginLeft: level * 12 }}>
          {editingCategoryId === category.id ? (
            <div className="flex items-center gap-1 px-2 py-1">
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
              className={`group flex items-center gap-1 px-2 py-1.5 rounded-lg cursor-pointer transition-colors ${
                selectedCategoryId === category.id
                  ? 'bg-indigo-50 text-indigo-700'
                  : 'hover:bg-zinc-100 text-zinc-700'
              } ${isRootCategory ? 'font-medium' : ''}`}
            >
              {hasChildren && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleCategoryExpanded(category.id);
                  }}
                  className="p-0.5 hover:bg-zinc-200 rounded"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className={`transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                  >
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </button>
              )}
              {!hasChildren && <span className="w-5" />}
              
              <span className="flex-1 text-sm truncate">{category.name}</span>
              
              <span className="text-xs text-zinc-400">{skillCount}</span>
              
              {/* 添加子分类按钮 - 只有第一层（根分类）可以添加子分类，最多二层 */}
              <div className="opacity-0 group-hover:opacity-100 flex items-center gap-0.5 transition-opacity">
                {level === 0 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedCategoryId(category.id);
                      setIsAddingCategory(true);
                    }}
                    className="p-1 text-zinc-400 hover:text-indigo-600"
                    title="添加子分类"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
                  </button>
                )}
                
                {/* 所有非系统分类都可以编辑和删除 */}
                {!category.is_system && (
                  <>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setEditingCategoryId(category.id);
                        setEditCategoryName(category.name);
                      }}
                      className="p-1 text-zinc-400 hover:text-indigo-600"
                      title="编辑"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (confirm('确定要删除此分类吗？该分类下的技能将变为未归类。')) {
                          deleteCategory(category.id);
                        }
                      }}
                      className="p-1 text-zinc-400 hover:text-red-600"
                      title="删除"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/></svg>
                    </button>
                  </>
                )}
              </div>
            </div>
          )}
          
          {isExpanded && hasChildren && renderCategoryTree(category.id, level + 1)}
        </div>
      );
    });
  };

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-zinc-400">加载中...</div>
      </div>
    );
  }

  return (
    <div className="h-full flex">
      {/* 左侧：分类树 */}
      <div className="w-64 bg-zinc-50 border-r border-zinc-200 flex flex-col">
        <div className="p-4 border-b border-zinc-200">
          <h2 className="text-sm font-semibold text-zinc-900">技能库</h2>
          <p className="text-xs text-zinc-500 mt-1">管理 Agent 技能插件</p>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {/* 全部技能 */}
          <div
            onClick={() => setSelectedCategoryId('all')}
            className={`group flex items-center gap-1 px-2 py-1.5 rounded-lg cursor-pointer transition-colors ${
              selectedCategoryId === 'all'
                ? 'bg-indigo-50 text-indigo-700'
                : 'hover:bg-zinc-100 text-zinc-700'
            }`}
          >
            <span className="w-5" />
            <span className="flex-1 text-sm font-medium truncate">全部</span>
            <span className="text-xs text-zinc-400">{skills.length}</span>
          </div>

          <div className="border-t border-zinc-200 my-2" />

          {/* 四大基础分类 */}
          {renderCategoryTree(null)}

          {/* 未归类 - 始终显示 */}
          {(() => {
            const uncategorizedSkills = skills.filter(s => !s.category_id);
            return (
              <div
                onClick={() => setSelectedCategoryId('uncategorized')}
                className={`group flex items-center gap-1 px-2 py-1.5 rounded-lg cursor-pointer transition-colors ${
                  selectedCategoryId === 'uncategorized'
                    ? 'bg-indigo-50 text-indigo-700'
                    : 'hover:bg-zinc-100 text-zinc-700'
                }`}
              >
                <span className="w-5" />
                <span className="flex-1 text-sm truncate">未归类</span>
                <span className="text-xs text-zinc-400">{uncategorizedSkills.length}</span>
              </div>
            );
          })()}


        </div>
      </div>

      {/* 中间：技能列表 */}
      <div className="w-80 bg-white border-r border-zinc-200 flex flex-col">
        {/* 搜索栏 */}
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
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.3-4.3" />
            </svg>
            <input
              type="text"
              placeholder="搜索技能..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-sm border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
            />
          </div>
        </div>

        {/* 技能列表 */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {filteredSkills.map((skill) => (
            <div
              key={skill.id}
              onClick={() => setSelectedSkillId(skill.id)}
              className={`p-3 border rounded-xl cursor-pointer transition-all ${
                selectedSkillId === skill.id
                  ? 'border-indigo-500 ring-2 ring-indigo-500/20 bg-indigo-50'
                  : 'border-zinc-200 hover:border-zinc-300 hover:shadow-sm'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-medium text-sm text-zinc-900">{skill.name}</h3>
                {skill.is_system && (
                  <span className="text-[10px] px-1.5 py-0.5 bg-zinc-200 text-zinc-600 rounded">
                    系统
                  </span>
                )}
              </div>
              
              <p className="text-xs text-zinc-500 line-clamp-2 mb-2">
                {skill.description || '暂无描述'}
              </p>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1">
                  {skill.target_agents.slice(0, 3).map((agent) => (
                    <span
                      key={agent}
                      className="text-[10px] px-1.5 py-0.5 bg-zinc-100 text-zinc-600 rounded"
                    >
                      {agentTypeLabels[agent].split('Agent')[0]}
                    </span>
                  ))}
                </div>
                
                <div className="flex items-center gap-1">
                  {/* 移动按钮 - 仅非系统技能 */}
                  {!skill.is_system && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSkillToMove(skill.id);
                        setIsMovingSkill(true);
                      }}
                      className="p-1 text-zinc-400 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-colors"
                      title="移动到..."
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 9l7-7 7 7"/><path d="M12 16V2"/></svg>
                    </button>
                  )}
                  {/* 系统技能固定显示启用，不可操作 */}
                  {skill.is_system ? (
                    <span className="text-xs px-2 py-1 rounded bg-emerald-100 text-emerald-700">
                      启用
                    </span>
                  ) : (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleSkillActive(skill.id);
                      }}
                      className={`text-xs px-2 py-1 rounded transition-colors ${
                        skill.is_active
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-zinc-100 text-zinc-500'
                      }`}
                    >
                      {skill.is_active ? '启用' : '禁用'}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}

          {filteredSkills.length === 0 && (
            <div className="text-center py-8 text-zinc-400">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="40"
                height="40"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="mx-auto mb-3"
              >
                <path d="M12 2H2v10h10V2Z" />
                <path d="M12 12H2v10h10V12Z" />
                <path d="M22 2h-10v10h10V2Z" />
                <path d="M22 12h-10v10h10V12Z" />
              </svg>
              <p className="text-sm">暂无技能</p>
              <p className="text-xs mt-1">选择一个分类或创建新技能</p>
            </div>
          )}
        </div>

        {/* 新建技能按钮 - 只要选中了分类（包括未归类）就可以创建 */}
        {selectedCategoryId && (
          <div className="p-4 border-t border-zinc-200">
            {isAddingSkill ? (
              <div className="space-y-2">
                <input
                  autoFocus
                  value={newSkillName}
                  onChange={(e) => setNewSkillName(e.target.value)}
                  placeholder="技能名称"
                  className="w-full text-sm px-3 py-2 border border-zinc-300 rounded-lg outline-none focus:border-indigo-500"
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleAddSkill}
                    disabled={!newSkillName.trim()}
                    className="flex-1 px-3 py-2 text-xs bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                  >
                    创建
                  </button>
                  <button
                    onClick={() => {
                      setIsAddingSkill(false);
                      setNewSkillName('');
                    }}
                    className="flex-1 px-3 py-2 text-xs bg-zinc-200 text-zinc-700 rounded-lg hover:bg-zinc-300"
                  >
                    取消
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setIsAddingSkill(true)}
                className="w-full py-2.5 text-sm font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg flex items-center justify-center gap-2 transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
                新建技能
              </button>
            )}
          </div>
        )}
      </div>

      {/* 右侧：技能编辑器 */}
      <div className="flex-1 bg-zinc-50 flex flex-col">
        {selectedSkill ? (
          <>
            {/* 头部 */}
            <div className="p-4 bg-white border-b border-zinc-200">
              <div className="flex items-center justify-between mb-3">
                <input
                  value={selectedSkill.name}
                  onChange={(e) => updateSkill(selectedSkill.id, { name: e.target.value })}
                  className="text-lg font-semibold text-zinc-900 bg-transparent border-none outline-none focus:ring-2 focus:ring-indigo-500/20 rounded px-2 -ml-2"
                />
                <div className="flex items-center gap-2">
                  <span className="text-xs text-zinc-500">
                    版本 {selectedSkill.version || '1.0.0'}
                  </span>
                  <button
                    onClick={() => deleteSkill(selectedSkill.id)}
                    className="p-2 text-zinc-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="删除技能"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/></svg>
                  </button>
                </div>
              </div>
              
              <textarea
                value={selectedSkill.description}
                onChange={(e) => updateSkill(selectedSkill.id, { description: e.target.value })}
                placeholder="技能描述..."
                rows={2}
                className="w-full text-sm text-zinc-600 bg-transparent border-none outline-none resize-none focus:ring-2 focus:ring-indigo-500/20 rounded px-2 -ml-2"
              />
              
              {/* 适用 Agent */}
              <div className="mt-3 flex items-center gap-2">
                <span className="text-xs text-zinc-500">适用 Agent:</span>
                <div className="flex items-center gap-1">
                  {(['writer', 'editor', 'planner', 'conflict', 'reader', 'summary'] as AgentType[]).map((agent) => (
                    <button
                      key={agent}
                      onClick={() => {
                        const newAgents = selectedSkill.target_agents.includes(agent)
                          ? selectedSkill.target_agents.filter((a) => a !== agent)
                          : [...selectedSkill.target_agents, agent];
                        updateSkill(selectedSkill.id, { target_agents: newAgents });
                      }}
                      className={`text-xs px-2 py-1 rounded transition-colors ${
                        selectedSkill.target_agents.includes(agent)
                          ? 'bg-indigo-100 text-indigo-700'
                          : 'bg-zinc-100 text-zinc-500 hover:bg-zinc-200'
                      }`}
                    >
                      {agentTypeLabels[agent]}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* 标签页 */}
            <div className="flex border-b border-zinc-200 bg-white">
              {[
                { key: 'constraints', label: '约束条目', icon: '📋' },
                { key: 'assets', label: '关联资产', icon: '🔗' },
                { key: 'test', label: '测试区', icon: '🧪' },
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key as typeof activeTab)}
                  className={`flex-1 py-3 text-sm font-medium transition-colors flex items-center justify-center gap-2 ${
                    activeTab === tab.key
                      ? 'text-indigo-600 border-b-2 border-indigo-600'
                      : 'text-zinc-500 hover:text-zinc-700'
                  }`}
                >
                  <span>{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </div>

            {/* 内容区 */}
            <div className="flex-1 overflow-y-auto p-4">
              {activeTab === 'constraints' && (
                <SkillConstraintsEditor skill={selectedSkill} />
              )}
              {activeTab === 'assets' && (
                <SkillAssetsLinker skill={selectedSkill} />
              )}
              {activeTab === 'test' && (
                <SkillTester skill={selectedSkill} />
              )}
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-zinc-400">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="64"
              height="64"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="mb-4"
            >
              <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
            </svg>
            <p className="text-sm">选择一个技能进行编辑</p>
            <p className="text-xs mt-1">或创建新技能</p>
          </div>
        )}
      </div>

      {/* Skill 移动弹窗 */}
      {isMovingSkill && skillToMove && (
        <SkillMoveModal
          skillId={skillToMove}
          onClose={() => {
            setIsMovingSkill(false);
            setSkillToMove(null);
          }}
        />
      )}

      {/* 新建分类弹窗 */}
      <CreateCategoryModal
        isOpen={isAddingCategory}
        onClose={() => {
          setIsAddingCategory(false);
          setNewCategoryName('');
        }}
        parentCategoryId={selectedCategoryId}
      />
    </div>
  );
};

// Skill 移动弹窗组件
const SkillMoveModal: React.FC<{
  skillId: string;
  onClose: () => void;
}> = ({ skillId, onClose }) => {
  const { skills, categories, moveSkillToCategory } = useSkillStore();
  const [selectedTargetCategory, setSelectedTargetCategory] = useState<string>('');

  const skill = skills.find(s => s.id === skillId);
  const currentCategory = categories.find(c => c.id === skill?.category_id);

  // 获取可移动到的分类（排除当前分类和系统分类）
  const availableCategories = categories.filter(c => 
    c.id !== skill?.category_id && 
    !c.is_system &&
    c.parent_id !== null // 只能移动到子分类
  );

  const handleMove = async () => {
    if (!selectedTargetCategory) return;
    await moveSkillToCategory(skillId, selectedTargetCategory);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl w-[400px] p-6">
        <h3 className="text-lg font-semibold text-zinc-900 mb-2">移动技能</h3>
        <p className="text-sm text-zinc-500 mb-4">
          将 "{skill?.name}" 移动到以下分类
        </p>
        <p className="text-xs text-zinc-400 mb-4">
          当前分类: {currentCategory?.name || '未分类'}
        </p>

        <div className="space-y-2 max-h-60 overflow-y-auto mb-4">
          {categories
            .filter(c => c.parent_id === null && c.type !== 'system')
            .map(parentCat => (
              <div key={parentCat.id}>
                <div className="px-3 py-2 text-sm font-medium text-zinc-700 bg-zinc-50 rounded">
                  {parentCat.name}
                </div>
                <div className="pl-4 mt-1 space-y-1">
                  {categories
                    .filter(c => c.parent_id === parentCat.id)
                    .map(childCat => (
                      <button
                        key={childCat.id}
                        onClick={() => setSelectedTargetCategory(childCat.id)}
                        className={`w-full text-left px-3 py-2 text-sm rounded transition-colors ${
                          selectedTargetCategory === childCat.id
                            ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                            : 'hover:bg-zinc-50 text-zinc-600'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span
                            className="w-2 h-2 rounded-full"
                            style={{ backgroundColor: childCat.color }}
                          />
                          {childCat.name}
                        </div>
                      </button>
                    ))}
                </div>
              </div>
            ))}
        </div>

        <div className="flex gap-2">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 text-sm text-zinc-600 hover:bg-zinc-100 rounded-lg transition-colors"
          >
            取消
          </button>
          <button
            onClick={handleMove}
            disabled={!selectedTargetCategory}
            className="flex-1 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            移动
          </button>
        </div>
      </div>
    </div>
  );
};

// 约束条目编辑器
const SkillConstraintsEditor: React.FC<{ skill: Skill }> = ({ skill }) => {
  const { updateSkill } = useSkillStore();
  const [constraintTexts, setConstraintTexts] = useState<Record<string, string>>({});
  const [hasChanges, setHasChanges] = useState<Record<string, boolean>>({});

  // 系统技能的约束不可编辑
  const isSystemSkill = skill.is_system;

  // 初始化约束文本
  React.useEffect(() => {
    const texts: Record<string, string> = {};
    skill.constraints.forEach(c => {
      if (!constraintTexts[c.id]) {
        texts[c.id] = c.content;
      }
    });
    if (Object.keys(texts).length > 0) {
      setConstraintTexts(prev => ({ ...prev, ...texts }));
    }
  }, [skill.constraints]);

  const addConstraint = () => {
    if (isSystemSkill) return; // 系统技能不可添加约束
    const newId = `constraint-${Date.now()}`;
    const constraint = {
      id: newId,
      content: '',
      priority: 'medium' as const,
      enabled: true,
    };
    updateSkill(skill.id, {
      constraints: [...skill.constraints, constraint],
    });
    setConstraintTexts(prev => ({ ...prev, [newId]: '' }));
    setHasChanges(prev => ({ ...prev, [newId]: true }));
  };

  const updateConstraintText = (constraintId: string, text: string) => {
    if (isSystemSkill) return; // 系统技能不可编辑
    setConstraintTexts(prev => ({ ...prev, [constraintId]: text }));
    const original = skill.constraints.find(c => c.id === constraintId);
    setHasChanges(prev => ({ ...prev, [constraintId]: original?.content !== text }));
  };

  const saveConstraint = (constraintId: string) => {
    if (isSystemSkill) return; // 系统技能不可保存
    const text = constraintTexts[constraintId]?.trim() || '';
    updateSkill(skill.id, {
      constraints: skill.constraints.map((c) =>
        c.id === constraintId ? { ...c, content: text } : c
      ),
    });
    setHasChanges(prev => ({ ...prev, [constraintId]: false }));
  };

  const toggleConstraint = (constraintId: string) => {
    if (isSystemSkill) return; // 系统技能不可禁用
    updateSkill(skill.id, {
      constraints: skill.constraints.map((c) =>
        c.id === constraintId ? { ...c, enabled: !c.enabled } : c
      ),
    });
  };

  const deleteConstraint = (constraintId: string) => {
    if (isSystemSkill) return; // 系统技能不可删除约束
    updateSkill(skill.id, {
      constraints: skill.constraints.filter((c) => c.id !== constraintId),
    });
    setConstraintTexts(prev => {
      const newTexts = { ...prev };
      delete newTexts[constraintId];
      return newTexts;
    });
  };

  return (
    <div className="space-y-4">
      {/* 添加新约束按钮 - 仅非系统技能显示 */}
      {!isSystemSkill && (
        <button
          onClick={addConstraint}
          className="w-full px-4 py-2 border border-dashed border-zinc-300 text-zinc-600 text-sm rounded-lg hover:border-indigo-500 hover:text-indigo-600 transition-colors flex items-center justify-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
          添加约束条目
        </button>
      )}

      {/* 约束列表 */}
      <div className="space-y-2">
        {skill.constraints.map((constraint, index) => (
          <div
            key={constraint.id}
            className={`p-3 bg-white border rounded-lg ${
              constraint.enabled ? 'border-zinc-200' : 'border-zinc-100 opacity-60'
            }`}
          >
            <div className="flex items-start gap-3">
              <span className="text-xs text-zinc-400 mt-2">{index + 1}.</span>
              <div className="flex-1">
                {isSystemSkill ? (
                  // 系统技能约束只读显示
                  <div className="w-full text-sm px-3 py-2 bg-zinc-50 border border-zinc-200 rounded-lg text-zinc-700">
                    {constraint.content}
                  </div>
                ) : (
                  // 非系统技能可编辑
                  <textarea
                    value={constraintTexts[constraint.id] ?? constraint.content}
                    onChange={(e) => updateConstraintText(constraint.id, e.target.value)}
                    placeholder="输入约束内容..."
                    className={`w-full text-sm px-3 py-2 border rounded-lg outline-none resize-none transition-colors ${
                      hasChanges[constraint.id]
                        ? 'border-amber-400 bg-amber-50 focus:border-amber-500'
                        : 'border-zinc-200 focus:border-indigo-500'
                    }`}
                    rows={2}
                  />
                )}
              </div>
              {!isSystemSkill && (
                <div className="flex flex-col gap-1">
                  {/* 保存按钮 */}
                  {hasChanges[constraint.id] && (
                    <button
                      onClick={() => saveConstraint(constraint.id)}
                      className="p-1.5 text-emerald-600 hover:bg-emerald-50 rounded transition-colors"
                      title="保存"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
                    </button>
                  )}
                  {/* 启用/禁用 */}
                  <button
                    onClick={() => toggleConstraint(constraint.id)}
                    className={`p-1.5 rounded transition-colors ${
                      constraint.enabled
                        ? 'text-emerald-600 hover:bg-emerald-50'
                        : 'text-zinc-400 hover:bg-zinc-100'
                    }`}
                    title={constraint.enabled ? '禁用' : '启用'}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      {constraint.enabled ? (
                        <><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></>
                      ) : (
                        <><path d="M12 2v4M12 18v4"/></>
                      )}
                    </svg>
                  </button>
                  {/* 删除 */}
                  <button
                    onClick={() => deleteConstraint(constraint.id)}
                    className="p-1.5 text-zinc-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                    title="删除"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/></svg>
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}

        {skill.constraints.length === 0 && (
          <div className="text-center py-8 text-zinc-400 bg-white border border-dashed border-zinc-300 rounded-lg">
            <p className="text-sm">暂无约束条目</p>
            {!isSystemSkill && <p className="text-xs mt-1">点击上方按钮添加约束</p>}
          </div>
        )}
      </div>
    </div>
  );
};

// 关联资产
const SkillAssetsLinker: React.FC<{ skill: Skill }> = ({ skill }) => {
  const { assets } = useAssetStore();
  const { linkAssetToSkill, unlinkAssetFromSkill } = useSkillStore();

  const linkedAssets = assets.filter((a) => skill.linked_assets.includes(a.id));
  const availableAssets = assets.filter((a) => !skill.linked_assets.includes(a.id));

  return (
    <div className="space-y-4">
      {/* 已关联资产 */}
      <div>
        <h4 className="text-sm font-medium text-zinc-700 mb-2">已关联资产</h4>
        <div className="space-y-2">
          {linkedAssets.map((asset) => (
            <div
              key={asset.id}
              className="flex items-center gap-3 p-3 bg-white border border-zinc-200 rounded-lg"
            >
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center"
                style={{ backgroundColor: `${asset.color || '#6366f1'}15`, color: asset.color || '#6366f1' }}
              >
                <span className="text-xs">{asset.type[0].toUpperCase()}</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-zinc-900 truncate">{asset.name}</p>
                <p className="text-xs text-zinc-500 truncate">{asset.source_novel_name}</p>
              </div>
              <button
                onClick={() => unlinkAssetFromSkill(skill.id, asset.id)}
                className="p-1.5 text-zinc-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
              </button>
            </div>
          ))}

          {linkedAssets.length === 0 && (
            <div className="text-center py-4 text-zinc-400 bg-white border border-dashed border-zinc-300 rounded-lg">
              <p className="text-xs">暂无关联资产</p>
            </div>
          )}
        </div>
      </div>

      {/* 可关联资产 */}
      {availableAssets.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-zinc-700 mb-2">可关联资产</h4>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {availableAssets.slice(0, 10).map((asset) => (
              <div
                key={asset.id}
                className="flex items-center gap-3 p-3 bg-white border border-zinc-200 rounded-lg hover:border-indigo-300 transition-colors"
              >
                <div
                  className="w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: `${asset.color || '#6366f1'}15`, color: asset.color || '#6366f1' }}
                >
                  <span className="text-xs">{asset.type[0].toUpperCase()}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-zinc-900 truncate">{asset.name}</p>
                  <p className="text-xs text-zinc-500 truncate">{asset.source_novel_name}</p>
                </div>
                <button
                  onClick={() => linkAssetToSkill(skill.id, asset.id)}
                  className="px-3 py-1.5 text-xs bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100 transition-colors"
                >
                  关联
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// 技能测试器
const SkillTester: React.FC<{ skill: Skill }> = ({ skill }) => {
  const { testSkill, testResult, isTesting } = useSkillStore();
  const [testText, setTestText] = useState('');

  const handleTest = async () => {
    if (!testText.trim()) return;
    await testSkill(skill.id, testText);
  };

  return (
    <div className="space-y-4">
      {/* 测试输入 */}
      <div>
        <label className="block text-sm font-medium text-zinc-700 mb-2">
          输入测试文本
        </label>
        <textarea
          value={testText}
          onChange={(e) => setTestText(e.target.value)}
          placeholder="输入一段文字来测试技能约束是否生效..."
          rows={6}
          className="w-full px-3 py-2 text-sm border border-zinc-300 rounded-lg outline-none focus:border-indigo-500 resize-none"
        />
        <button
          onClick={handleTest}
          disabled={!testText.trim() || isTesting}
          className="mt-2 px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
        >
          {isTesting ? (
            <>
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              测试中...
            </>
          ) : (
            <>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
              运行测试
            </>
          )}
        </button>
      </div>

      {/* 测试结果 */}
      {testResult && (
        <div className={`p-4 rounded-lg ${testResult.passed ? 'bg-emerald-50 border border-emerald-200' : 'bg-red-50 border border-red-200'}`}>
          <div className="flex items-center gap-2 mb-3">
            {testResult.passed ? (
              <>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-emerald-600"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                <span className="font-medium text-emerald-800">测试通过</span>
              </>
            ) : (
              <>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-red-600"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
                <span className="font-medium text-red-800">发现违规</span>
              </>
            )}
          </div>

          {testResult.violations.length > 0 && (
            <div className="mb-3">
              <h5 className="text-sm font-medium text-red-800 mb-2">违规项：</h5>
              <ul className="space-y-1">
                {testResult.violations.map((violation, index) => (
                  <li key={index} className="text-sm text-red-700 flex items-start gap-2">
                    <span className="text-red-500 mt-0.5">•</span>
                    {violation}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {testResult.suggestions.length > 0 && (
            <div>
              <h5 className="text-sm font-medium text-amber-800 mb-2">改进建议：</h5>
              <ul className="space-y-1">
                {testResult.suggestions.map((suggestion, index) => (
                  <li key={index} className="text-sm text-amber-700 flex items-start gap-2">
                    <span className="text-amber-500 mt-0.5">•</span>
                    {suggestion}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// 新建分类弹窗组件
const CreateCategoryModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  parentCategoryId: string | null;
}> = ({ isOpen, onClose, parentCategoryId }) => {
  const { categories, createCategory } = useSkillStore();
  const [categoryName, setCategoryName] = useState('');
  const [selectedParentId, setSelectedParentId] = useState<string | null>(parentCategoryId);

  // 重置状态当弹窗打开时
  React.useEffect(() => {
    if (isOpen) {
      setCategoryName('');
      setSelectedParentId(parentCategoryId);
    }
  }, [isOpen, parentCategoryId]);

  if (!isOpen) return null;

  const handleCreate = async () => {
    if (!categoryName.trim()) return;

    // 确定类型和父分类
    let type: SkillCategory['type'] = 'writing';
    let parentId: string | null = null;

    if (selectedParentId) {
      const selectedCat = categories.find(c => c.id === selectedParentId);
      if (selectedCat) {
        if (selectedCat.parent_id === null) {
          // 选中的是根分类，作为父分类
          parentId = selectedCat.id;
          type = selectedCat.type;
        } else {
          // 选中的是子分类，使用其父分类
          parentId = selectedCat.parent_id;
          type = selectedCat.type;
        }
      }
    }

    await createCategory({
      name: categoryName.trim(),
      type,
      parent_id: parentId,
      color: categoryTypeColors[type],
      is_system: false,
      order: categories.length,
    });
    onClose();
  };

  // 获取可选的父分类（只有根分类可以作为父分类）
  const rootCategories = categories.filter(c => c.parent_id === null);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl w-[400px] p-6">
        <h3 className="text-lg font-semibold text-zinc-900 mb-4">新建分类</h3>

        <div className="space-y-4">
          {/* 分类名称输入 */}
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1">
              分类名称
            </label>
            <input
              autoFocus
              value={categoryName}
              onChange={(e) => setCategoryName(e.target.value)}
              placeholder="请输入分类名称"
              className="w-full text-sm px-3 py-2 border border-zinc-300 rounded-lg outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && categoryName.trim()) {
                  handleCreate();
                }
              }}
            />
          </div>

          {/* 父分类选择 */}
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-1">
              所属分类
            </label>
            <div className="space-y-2 max-h-48 overflow-y-auto border border-zinc-200 rounded-lg p-2">
              <button
                onClick={() => setSelectedParentId(null)}
                className={`w-full text-left px-3 py-2 text-sm rounded transition-colors ${
                  selectedParentId === null
                    ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                    : 'hover:bg-zinc-50 text-zinc-600'
                }`}
              >
                不选择（创建根分类）
              </button>
              {rootCategories.map(cat => (
                <button
                  key={cat.id}
                  onClick={() => setSelectedParentId(cat.id)}
                  className={`w-full text-left px-3 py-2 text-sm rounded transition-colors ${
                    selectedParentId === cat.id
                      ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                      : 'hover:bg-zinc-50 text-zinc-600'
                  }`}
                >
                  {cat.name}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 text-sm text-zinc-600 hover:bg-zinc-100 rounded-lg transition-colors"
          >
            取消
          </button>
          <button
            onClick={handleCreate}
            disabled={!categoryName.trim()}
            className="flex-1 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            创建
          </button>
        </div>
      </div>
    </div>
  );
};

export default SkillsManagement;
