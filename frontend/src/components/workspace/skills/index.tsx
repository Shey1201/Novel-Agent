"use client";

import React, { useState, useEffect, useMemo } from 'react';
import { useSkillStore, type SkillCategory, type Skill, type AgentType, type SkillConstraint } from '@/store/skillStore';
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
  critic: '评论Agent',
  consistency: '一致性Agent',
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
    linkAssetToSkill,
    unlinkAssetFromSkill,
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
  const [newCategoryParentId, setNewCategoryParentId] = useState<string | null>(null);
  const [isRootCategory, setIsRootCategory] = useState(true);
  const [editingCategoryId, setEditingCategoryId] = useState<string | null>(null);
  const [editCategoryName, setEditCategoryName] = useState('');

  const [isAddingSkill, setIsAddingSkill] = useState(false);
  const [newSkillName, setNewSkillName] = useState('');

  const [activeTab, setActiveTab] = useState<'constraints' | 'assets'>('constraints');

  // 技能编辑相关状态
  const [isAddingConstraint, setIsAddingConstraint] = useState(false);
  const [newConstraintContent, setNewConstraintContent] = useState('');
  const [newConstraintPriority, setNewConstraintPriority] = useState<'high' | 'medium' | 'low'>('medium');
  const [editingConstraintId, setEditingConstraintId] = useState<string | null>(null);
  const [editConstraintContent, setEditConstraintContent] = useState('');
  const [editConstraintPriority, setEditConstraintPriority] = useState<'high' | 'medium' | 'low'>('medium');

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
    
    let parentId: string | null = isRootCategory ? null : newCategoryParentId;
    let type: SkillCategory['type'] = newCategoryType;
    
    // 如果是子分类，继承父分类的类型
    if (!isRootCategory && newCategoryParentId) {
      const parentCat = categories.find(c => c.id === newCategoryParentId);
      if (parentCat) {
        type = parentCat.type;
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
    setNewCategoryParentId(null);
    setIsRootCategory(true);
    setIsAddingCategory(false);
  };

  const openAddCategoryModal = () => {
    setNewCategoryName('');
    setNewCategoryType('writing');
    setNewCategoryParentId(null);
    setIsRootCategory(true);
    setIsAddingCategory(true);
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

  // 约束条件相关函数
  const handleAddConstraint = async () => {
    if (!selectedSkill || !newConstraintContent.trim()) return;
    const newConstraint: SkillConstraint = {
      id: `constraint-${Date.now()}`,
      content: newConstraintContent.trim(),
      priority: newConstraintPriority,
      enabled: true,
    };
    await updateSkill(selectedSkill.id, {
      constraints: [...selectedSkill.constraints, newConstraint],
    });
    setNewConstraintContent('');
    setNewConstraintPriority('medium');
    setIsAddingConstraint(false);
  };

  const handleUpdateConstraint = async (constraintId: string) => {
    if (!selectedSkill) return;
    const updatedConstraints = selectedSkill.constraints.map(c =>
      c.id === constraintId 
        ? { ...c, content: editConstraintContent, priority: editConstraintPriority }
        : c
    );
    await updateSkill(selectedSkill.id, { constraints: updatedConstraints });
    setEditingConstraintId(null);
  };

  const handleDeleteConstraint = async (constraintId: string) => {
    if (!selectedSkill) return;
    if (!confirm('确定要删除此约束条件吗？')) return;
    const updatedConstraints = selectedSkill.constraints.filter(c => c.id !== constraintId);
    await updateSkill(selectedSkill.id, { constraints: updatedConstraints });
  };

  const startEditingConstraint = (constraint: SkillConstraint) => {
    setEditingConstraintId(constraint.id);
    setEditConstraintContent(constraint.content);
    setEditConstraintPriority(constraint.priority);
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
      const isRootCat = category.parent_id === null;
      
      return (
        <div key={category.id} style={{ marginLeft: level * 8 }}>
          {editingCategoryId === category.id ? (
            <div className="flex items-center gap-1 px-3 py-2">
              <input
                autoFocus
                value={editCategoryName}
                onChange={(e) => setEditCategoryName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleUpdateCategory(category.id);
                  if (e.key === 'Escape') setEditingCategoryId(null);
                }}
                onBlur={() => handleUpdateCategory(category.id)}
                className="flex-1 text-[13px] px-2 py-1 border border-zinc-300 rounded outline-none focus:border-indigo-500"
              />
            </div>
          ) : (
            <div
              onClick={() => setSelectedCategoryId(category.id)}
              className={`group flex items-center gap-1 px-3 py-2 rounded-lg cursor-pointer transition-colors ${
                selectedCategoryId === category.id
                  ? 'bg-zinc-100 text-zinc-900'
                  : 'hover:bg-zinc-50 text-zinc-600'
              }`}
            >
              {hasChildren && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleCategoryExpanded(category.id);
                  }}
                  className="p-0.5 hover:bg-zinc-200 rounded text-zinc-400"
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
              
              <span className="flex-1 text-[13px] truncate">{category.name}</span>
              
              <span className="text-[11px] text-zinc-400">{skillCount}</span>
              
              {/* 所有非系统分类都可以编辑和删除 */}
              {!category.is_system && (
                <div className="opacity-0 group-hover:opacity-100 flex items-center gap-0.5 transition-opacity">
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
                </div>
              )}
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
      <div className="w-56 bg-zinc-50/50 border-r border-zinc-200 flex flex-col">
        <div className="p-4 border-b border-zinc-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-zinc-900">技能管理</h2>
              <p className="text-xs text-zinc-500 mt-0.5">Agent 技能插件中心</p>
            </div>
            <button
              onClick={openAddCategoryModal}
              className="p-1.5 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
              title="新增分类"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          {/* 全部技能 */}
          <button
            onClick={() => setSelectedCategoryId('all')}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-left transition-colors ${
              selectedCategoryId === 'all'
                ? 'bg-zinc-100 text-zinc-900'
                : 'hover:bg-zinc-50 text-zinc-600'
            }`}
          >
            <span className="text-[13px]">全部</span>
            <span className="text-[11px] text-zinc-400">{skills.length}</span>
          </button>

          {/* 未归类 - 放在全部下方 */}
          {(() => {
            const uncategorizedSkills = skills.filter(s => !s.category_id);
            return (
              <button
                onClick={() => setSelectedCategoryId('uncategorized')}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-left transition-colors ${
                  selectedCategoryId === 'uncategorized'
                    ? 'bg-zinc-100 text-zinc-900'
                    : 'hover:bg-zinc-50 text-zinc-600'
                }`}
              >
                <span className="text-[13px]">未归类</span>
                <span className="text-[11px] text-zinc-400">{uncategorizedSkills.length}</span>
              </button>
            );
          })()}

          {/* 分类树 */}
          {renderCategoryTree(null)}


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
              onClick={() => {
                setSelectedSkillId(skill.id);
                setIsAddingConstraint(false);
              }}
              className={`p-3 border rounded-xl cursor-pointer transition-all ${
                selectedSkillId === skill.id
                  ? 'border-indigo-500 ring-2 ring-indigo-500/20 bg-indigo-50'
                  : 'border-zinc-200 hover:border-zinc-300 hover:shadow-sm'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-medium text-sm text-zinc-900">{skill.name}</h3>
                <div className="flex items-center gap-1">
                  {skill.is_system && (
                    <span className="text-[10px] px-1.5 py-0.5 bg-zinc-200 text-zinc-600 rounded">
                      系统
                    </span>
                  )}
                  {/* 删除按钮 - 仅非系统技能，放在最右侧 */}
                  {!skill.is_system && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (confirm('确定要删除此技能吗？')) {
                          deleteSkill(skill.id);
                        }
                      }}
                      className="p-1 text-zinc-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                      title="删除"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/></svg>
                    </button>
                  )}
                </div>
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
              <p className="text-xs mt-1">点击下方按钮创建新技能</p>
            </div>
          )}
        </div>

        {/* 添加技能按钮 - 在选择子分类或未归类时显示 */}
        {(selectedCategory?.parent_id !== null || selectedCategoryId === 'uncategorized') && (
          <div className="p-4 border-t border-zinc-200">
            <button
              onClick={() => setIsAddingSkill(true)}
              className="w-full py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14"/><path d="M12 5v14"/>
              </svg>
              新建技能
            </button>
          </div>
        )}
      </div>

      {/* 右侧：技能详情 */}
      <div className="flex-1 bg-zinc-50/50 flex flex-col overflow-hidden">
        {selectedSkill ? (
          <div className="h-full flex flex-col">
            {/* 头部 - V3版本样式 */}
            <div className="bg-white border-b border-zinc-200 px-6 py-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  {/* 技能名称 */}
                  <input
                    value={selectedSkill.name}
                    onChange={(e) => !selectedSkill.is_system && updateSkill(selectedSkill.id, { name: e.target.value })}
                    readOnly={selectedSkill.is_system}
                    className={`w-full text-lg font-semibold bg-transparent border-0 p-0 focus:ring-0 ${
                      selectedSkill.is_system ? 'text-zinc-900' : 'text-zinc-900 hover:bg-zinc-50 focus:bg-white focus:border-indigo-500 border-b border-transparent focus:border-indigo-500'
                    }`}
                    placeholder="技能名称"
                  />
                  
                  {/* 技能描述 */}
                  <textarea
                    value={selectedSkill.description}
                    onChange={(e) => !selectedSkill.is_system && updateSkill(selectedSkill.id, { description: e.target.value })}
                    readOnly={selectedSkill.is_system}
                    rows={2}
                    className={`w-full text-sm mt-2 bg-transparent border-0 p-0 resize-none focus:ring-0 ${
                      selectedSkill.is_system ? 'text-zinc-600' : 'text-zinc-600 hover:bg-zinc-50 focus:bg-white focus:border-indigo-500 border-b border-transparent focus:border-indigo-500'
                    }`}
                    placeholder="技能描述"
                  />
                  
                  {/* 适用 Agent */}
                  <div className="mt-3 flex items-center gap-2">
                    <span className="text-xs text-zinc-500">适用 Agent:</span>
                    <div className="flex items-center gap-1">
                      {(['writer', 'editor', 'planner', 'conflict', 'reader', 'summary'] as AgentType[]).map((agent) => (
                        <button
                          key={agent}
                          onClick={() => {
                            if (selectedSkill.is_system) return;
                            const newAgents = selectedSkill.target_agents.includes(agent)
                              ? selectedSkill.target_agents.filter((a) => a !== agent)
                              : [...selectedSkill.target_agents, agent];
                            updateSkill(selectedSkill.id, { target_agents: newAgents });
                          }}
                          className={`text-xs px-2 py-1 rounded transition-colors ${
                            selectedSkill.target_agents.includes(agent)
                              ? 'bg-indigo-100 text-indigo-700'
                              : 'bg-zinc-100 text-zinc-500 hover:bg-zinc-200'
                          } ${selectedSkill.is_system ? 'cursor-default' : 'cursor-pointer'}`}
                        >
                          {agentTypeLabels[agent]}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-2 ml-4">
                  {!selectedSkill.is_system && (
                    <button
                      onClick={() => deleteSkill(selectedSkill.id)}
                      className="px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      删除
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* 标签页 - V3版本样式 */}
            <div className="flex border-b border-zinc-200 bg-white">
              {[
                { key: 'constraints', label: '约束条件', icon: '🔒' },
                { key: 'assets', label: '关联小说', icon: '📎' },
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

            {/* 内容区 - V3版本样式 */}
            <div className="flex-1 overflow-y-auto p-4">
              {activeTab === 'constraints' && (
                <div className="space-y-4">
                  {/* 添加新约束按钮 - 仅非系统技能显示 */}
                  {!selectedSkill.is_system && (
                    <button
                      onClick={() => setIsAddingConstraint(true)}
                      className="w-full px-4 py-2 border border-dashed border-zinc-300 text-zinc-600 text-sm rounded-lg hover:border-indigo-500 hover:text-indigo-600 transition-colors flex items-center justify-center gap-2"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
                      添加约束条目
                    </button>
                  )}

                  {/* 新增约束表单 */}
                  {isAddingConstraint && (
                    <div className="p-4 bg-zinc-50 border border-zinc-200 rounded-lg">
                      <textarea
                        value={newConstraintContent}
                        onChange={(e) => setNewConstraintContent(e.target.value)}
                        placeholder="输入约束条件内容..."
                        className="w-full p-3 text-sm border border-zinc-200 rounded-lg focus:outline-none focus:border-indigo-500 resize-none"
                        rows={3}
                      />
                      <div className="flex items-center gap-4 mt-3">
                        <select
                          value={newConstraintPriority}
                          onChange={(e) => setNewConstraintPriority(e.target.value as 'high' | 'medium' | 'low')}
                          className="px-3 py-1.5 text-sm border border-zinc-200 rounded-lg focus:outline-none focus:border-indigo-500"
                        >
                          <option value="high">高优先级</option>
                          <option value="medium">中优先级</option>
                          <option value="low">低优先级</option>
                        </select>
                        <div className="flex-1"></div>
                        <button
                          onClick={() => setIsAddingConstraint(false)}
                          className="px-3 py-1.5 text-sm text-zinc-600 hover:bg-zinc-200 rounded-lg transition-colors"
                        >
                          取消
                        </button>
                        <button
                          onClick={handleAddConstraint}
                          disabled={!newConstraintContent.trim()}
                          className="px-3 py-1.5 text-sm bg-indigo-600 hover:bg-indigo-700 disabled:bg-zinc-300 text-white rounded-lg transition-colors"
                        >
                          添加
                        </button>
                      </div>
                    </div>
                  )}

                  {/* 约束列表 */}
                  <div className="space-y-2">
                    {selectedSkill.constraints.map((constraint, index) => (
                      <div
                        key={constraint.id}
                        className={`p-3 bg-white border rounded-lg ${
                          constraint.enabled !== false ? 'border-zinc-200' : 'border-zinc-100 opacity-60'
                        }`}
                      >
                        {editingConstraintId === constraint.id ? (
                          <div className="flex-1">
                            <textarea
                              value={editConstraintContent}
                              onChange={(e) => setEditConstraintContent(e.target.value)}
                              className="w-full p-2 text-sm border border-zinc-200 rounded-lg focus:outline-none focus:border-indigo-500 resize-none"
                              rows={2}
                            />
                            <div className="flex items-center gap-4 mt-2">
                              <select
                                value={editConstraintPriority}
                                onChange={(e) => setEditConstraintPriority(e.target.value as 'high' | 'medium' | 'low')}
                                className="px-3 py-1 text-sm border border-zinc-200 rounded-lg focus:outline-none focus:border-indigo-500"
                              >
                                <option value="high">高优先级</option>
                                <option value="medium">中优先级</option>
                                <option value="low">低优先级</option>
                              </select>
                              <div className="flex-1"></div>
                              <button
                                onClick={() => setEditingConstraintId(null)}
                                className="px-3 py-1 text-xs text-zinc-600 hover:bg-zinc-200 rounded transition-colors"
                              >
                                取消
                              </button>
                              <button
                                onClick={() => handleUpdateConstraint(constraint.id)}
                                className="px-3 py-1 text-xs bg-indigo-600 hover:bg-indigo-700 text-white rounded transition-colors"
                              >
                                保存
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-start gap-3">
                            <span className="text-xs text-zinc-400 mt-2">{index + 1}.</span>
                            <div className="flex-1">
                              {selectedSkill.is_system ? (
                                // 系统技能约束只读显示
                                <div className="w-full text-sm px-3 py-2 bg-zinc-50 border border-zinc-200 rounded-lg text-zinc-700">
                                  {constraint.content}
                                </div>
                              ) : (
                                // 非系统技能可编辑
                                <textarea
                                  value={constraint.content}
                                  onChange={(e) => {
                                    updateSkill(selectedSkill.id, {
                                      constraints: selectedSkill.constraints.map((c) =>
                                        c.id === constraint.id ? { ...c, content: e.target.value } : c
                                      ),
                                    });
                                  }}
                                  className="w-full text-sm px-3 py-2 border border-zinc-200 rounded-lg focus:outline-none focus:border-indigo-500 resize-none"
                                  rows={2}
                                  placeholder="输入约束条件..."
                                />
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              {/* 启用/禁用切换 */}
                              {!selectedSkill.is_system && (
                                <button
                                  onClick={() => {
                                    updateSkill(selectedSkill.id, {
                                      constraints: selectedSkill.constraints.map((c) =>
                                        c.id === constraint.id ? { ...c, enabled: c.enabled !== false ? false : true } : c
                                      ),
                                    });
                                  }}
                                  className={`text-xs px-2 py-1 rounded transition-colors inline-flex items-center justify-center leading-none ${
                                    constraint.enabled !== false
                                      ? 'bg-emerald-100 text-emerald-700'
                                      : 'bg-zinc-100 text-zinc-500'
                                  }`}
                                >
                                  {constraint.enabled !== false ? '启用' : '禁用'}
                                </button>
                              )}
                              {/* 优先级 */}
                              <span className={`text-[10px] px-1.5 py-0.5 rounded inline-flex items-center justify-center leading-none h-5 min-w-[20px] ${
                                constraint.priority === 'high' ? 'bg-red-100 text-red-600' :
                                constraint.priority === 'medium' ? 'bg-amber-100 text-amber-600' :
                                'bg-blue-100 text-blue-600'
                              }`}>
                                {constraint.priority === 'high' ? '高' : constraint.priority === 'medium' ? '中' : '低'}
                              </span>
                              {/* 删除按钮 */}
                              {!selectedSkill.is_system && (
                                <button
                                  onClick={() => handleDeleteConstraint(constraint.id)}
                                  className="p-1 text-zinc-400 hover:text-red-600"
                                  title="删除"
                                >
                                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                                </button>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                    {selectedSkill.constraints.length === 0 && (
                      <div className="text-center py-8 text-zinc-400">
                        <p className="text-sm">暂无约束条件</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {activeTab === 'assets' && (
                <div className="space-y-4">
                  {/* 系统内置技能只显示文字说明 */}
                  {selectedSkill.is_system ? (
                    <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
                      <p className="text-sm text-indigo-700">
                        系统内置技能默认关联所有小说，无需手动配置。
                      </p>
                    </div>
                  ) : (
                    <>
                      {/* 已关联资产 */}
                      <div>
                        <h4 className="text-sm font-medium text-zinc-700 mb-2">已关联小说</h4>
                        <div className="space-y-2">
                          {selectedSkill.linked_assets.map((assetId) => {
                            const asset = assets.find(a => a.id === assetId);
                            return asset ? (
                              <div key={assetId} className="group flex items-center gap-3 p-3 bg-white border border-zinc-200 rounded-lg">
                                <div className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center text-indigo-600">
                                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/>
                                  </svg>
                                </div>
                                <div className="flex-1">
                                  <p className="text-sm font-medium text-zinc-900">{asset.name}</p>
                                  <p className="text-xs text-zinc-500">{asset.source_novel_name}</p>
                                </div>
                                <button
                                  onClick={() => unlinkAssetFromSkill(selectedSkill.id, assetId)}
                                  className="opacity-0 group-hover:opacity-100 p-1 text-zinc-400 hover:text-red-600 transition-opacity"
                                  title="解除关联"
                                >
                                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                                </button>
                              </div>
                            ) : null;
                          })}
                          {selectedSkill.linked_assets.length === 0 && (
                            <div className="text-center py-4 text-zinc-400 bg-white border border-dashed border-zinc-300 rounded-lg">
                              <p className="text-xs">暂无关联小说</p>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* 可关联资产 - 仅非系统技能显示 */}
                      {assets.filter(a => !selectedSkill.linked_assets.includes(a.id)).length > 0 && (
                        <div>
                          <h4 className="text-sm font-medium text-zinc-700 mb-2">可关联小说</h4>
                          <div className="space-y-2 max-h-64 overflow-y-auto">
                            {assets
                              .filter(a => !selectedSkill.linked_assets.includes(a.id))
                              .slice(0, 10)
                              .map((asset) => (
                                <div
                                  key={asset.id}
                                  onClick={() => linkAssetToSkill(selectedSkill.id, asset.id)}
                                  className="flex items-center gap-3 p-3 bg-white border border-zinc-200 rounded-lg hover:border-indigo-300 transition-colors cursor-pointer"
                                >
                                  <div className="w-8 h-8 rounded-lg bg-zinc-100 flex items-center justify-center text-zinc-600">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                      <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/>
                                    </svg>
                                  </div>
                                  <div className="flex-1">
                                    <p className="text-sm font-medium text-zinc-900">{asset.name}</p>
                                    <p className="text-xs text-zinc-500">{asset.source_novel_name}</p>
                                  </div>
                                  <button className="text-xs px-2 py-1 bg-indigo-100 text-indigo-600 rounded hover:bg-indigo-200 transition-colors">
                                    关联
                                  </button>
                                </div>
                              ))}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}


            </div>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-zinc-400">
            <div className="text-center">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="48"
                height="48"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="mx-auto mb-4"
              >
                <path d="M12 2H2v10h10V2Z" />
                <path d="M12 12H2v10h10V12Z" />
                <path d="M22 2h-10v10h10V2Z" />
                <path d="M22 12h-10v10h10V12Z" />
              </svg>
              <p>选择一个技能查看详情</p>
            </div>
          </div>
        )}
      </div>

      {/* 新建技能弹窗 */}
      {isAddingSkill && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 p-6">
            <h3 className="text-lg font-semibold text-zinc-900 mb-4">新建技能</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">技能名称</label>
                <input
                  autoFocus
                  type="text"
                  value={newSkillName}
                  onChange={(e) => setNewSkillName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleAddSkill();
                    if (e.key === 'Escape') {
                      setNewSkillName('');
                      setIsAddingSkill(false);
                    }
                  }}
                  placeholder="输入技能名称"
                  className="w-full px-3 py-2 text-sm border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                />
              </div>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => {
                    setNewSkillName('');
                    setIsAddingSkill(false);
                  }}
                  className="px-4 py-2 text-sm text-zinc-600 hover:text-zinc-900"
                >
                  取消
                </button>
                <button
                  onClick={handleAddSkill}
                  disabled={!newSkillName.trim()}
                  className="px-4 py-2 text-sm bg-indigo-600 hover:bg-indigo-700 disabled:bg-zinc-300 text-white rounded-lg transition-colors"
                >
                  创建
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 移动技能弹窗 */}
      {isMovingSkill && skillToMove && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 p-6">
            <h3 className="text-lg font-semibold text-zinc-900 mb-4">移动技能</h3>
            <p className="text-sm text-zinc-500 mb-4">选择目标分类</p>
            <div className="max-h-60 overflow-y-auto space-y-1">
              {categories
                .filter(c => !c.is_system && c.id !== skills.find(s => s.id === skillToMove)?.category_id)
                .map((category) => (
                  <button
                    key={category.id}
                    onClick={() => {
                      updateSkill(skillToMove, { category_id: category.id });
                      setIsMovingSkill(false);
                      setSkillToMove(null);
                    }}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-zinc-50 rounded-lg transition-colors"
                  >
                    {category.name}
                  </button>
                ))}
            </div>
            <div className="flex justify-end gap-3 mt-4">
              <button
                onClick={() => {
                  setIsMovingSkill(false);
                  setSkillToMove(null);
                }}
                className="px-4 py-2 text-sm text-zinc-600 hover:text-zinc-900"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 创建分类弹窗 */}
      {isAddingCategory && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 p-6">
            <h3 className="text-lg font-semibold text-zinc-900 mb-4">创建分类</h3>
            <div className="space-y-4">
              {/* 选择根分类或子分类 - 单选选项 */}
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-2">分类层级</label>
                <div className="flex gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="categoryLevel"
                      checked={isRootCategory}
                      onChange={() => {
                        setIsRootCategory(true);
                        setNewCategoryParentId(null);
                      }}
                      className="w-4 h-4 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span className="text-sm text-zinc-700">根分类</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="categoryLevel"
                      checked={!isRootCategory}
                      onChange={() => {
                        setIsRootCategory(false);
                        // 默认选择第一个根分类
                        const firstRoot = categories.find(c => c.parent_id === null);
                        if (firstRoot) setNewCategoryParentId(firstRoot.id);
                      }}
                      className="w-4 h-4 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span className="text-sm text-zinc-700">子分类</span>
                  </label>
                </div>
              </div>

              {/* 如果是子分类，选择父分类 */}
              {!isRootCategory && (
                <div>
                  <label className="block text-sm font-medium text-zinc-700 mb-1">所属分类</label>
                  <select
                    value={newCategoryParentId || ''}
                    onChange={(e) => setNewCategoryParentId(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                  >
                    {categories
                      .filter(c => c.parent_id === null)
                      .map((category) => (
                        <option key={category.id} value={category.id}>
                          {category.name}
                        </option>
                      ))}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">分类名称</label>
                <input
                  autoFocus
                  type="text"
                  value={newCategoryName}
                  onChange={(e) => setNewCategoryName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleAddCategory();
                    if (e.key === 'Escape') {
                      setNewCategoryName('');
                      setIsAddingCategory(false);
                    }
                  }}
                  placeholder="输入分类名称"
                  className="w-full px-3 py-2 text-sm border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                />
              </div>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => {
                    setNewCategoryName('');
                    setNewCategoryParentId(null);
                    setIsRootCategory(true);
                    setIsAddingCategory(false);
                  }}
                  className="px-4 py-2 text-sm text-zinc-600 hover:text-zinc-900"
                >
                  取消
                </button>
                <button
                  onClick={handleAddCategory}
                  disabled={!newCategoryName.trim() || (!isRootCategory && !newCategoryParentId)}
                  className="px-4 py-2 text-sm bg-indigo-600 hover:bg-indigo-700 disabled:bg-zinc-300 text-white rounded-lg transition-colors"
                >
                  创建
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SkillsManagement;
