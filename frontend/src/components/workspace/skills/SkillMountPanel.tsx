"use client";

import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { useSkillStore, type Skill, type SkillCategory } from '@/store/skillStore';
import { useNovelStore } from '@/store/novelStore';

interface SkillMountPanelProps {
  novelId: string;
}

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

export const SkillMountPanel: React.FC<SkillMountPanelProps> = ({ novelId }) => {
  const {
    categories,
    skills,
    fetchCategories,
    fetchSkills,
  } = useSkillStore();

  const { novels, updateNovel } = useNovelStore();
  const [expandedCategories, setExpandedCategories] = useState<string[]>([]);
  const [showGlobalLibrary, setShowGlobalLibrary] = useState(false);

  const novel = novels.find((n) => n.id === novelId);
  const mountedSkillIds = novel?.mountedSkills || [];

  useEffect(() => {
    fetchCategories();
    fetchSkills();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 自动展开有已挂载技能的分类
  useEffect(() => {
    const categoriesWithMountedSkills = categories
      .filter((cat) =>
        skills.some(
          (s) =>
            s.category_id === cat.id &&
            mountedSkillIds.includes(s.id) &&
            s.is_active
        )
      )
      .map((cat) => cat.id);
    setExpandedCategories((prev) => {
      // 只在有变化时才更新，避免无限循环
      const newSet = new Set(categoriesWithMountedSkills);
      const prevSet = new Set(prev);
      if (newSet.size === prevSet.size && [...newSet].every(id => prevSet.has(id))) {
        return prev;
      }
      return categoriesWithMountedSkills;
    });
  }, [categories, skills, mountedSkillIds]);

  const toggleCategoryExpanded = (categoryId: string) => {
    setExpandedCategories((prev) =>
      prev.includes(categoryId)
        ? prev.filter((id) => id !== categoryId)
        : [...prev, categoryId]
    );
  };

  const toggleSkillMount = (skillId: string) => {
    if (!novel) return;
    
    const currentMountedSkills = novel.mountedSkills || [];
    const newMountedSkills = currentMountedSkills.includes(skillId)
      ? currentMountedSkills.filter((id) => id !== skillId)
      : [...currentMountedSkills, skillId];
    
    updateNovel(novelId, { mountedSkills: newMountedSkills });
  };

  const getSkillsByCategory = (categoryId: string) => {
    return skills.filter((s) => s.category_id === categoryId && s.is_active);
  };

  const getCategoryById = (categoryId: string | null) => {
    if (!categoryId) return undefined;
    return categories.find((c) => c.id === categoryId);
  };

  // 按类型分组分类
  const systemCategories = categories.filter((c) => c.type === 'system');
  const userCategories = categories.filter((c) => c.type !== 'system');

  // 渲染分类及其技能
  const renderCategoryWithSkills = (category: SkillCategory) => {
    const categorySkills = getSkillsByCategory(category.id);
    const mountedCount = categorySkills.filter((s) =>
      mountedSkillIds.includes(s.id)
    ).length;
    const isExpanded = expandedCategories.includes(category.id);

    if (categorySkills.length === 0 && !category.is_system) return null;

    return (
      <div key={category.id} className="mb-2">
        <button
          onClick={() => toggleCategoryExpanded(category.id)}
          className="w-full flex items-center justify-between px-2 py-1.5 text-left hover:bg-zinc-100 rounded-lg transition-colors"
        >
          <div className="flex items-center gap-2">
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
              className={`text-zinc-400 transition-transform ${
                isExpanded ? 'rotate-90' : ''
              }`}
            >
              <polyline points="9 18 15 12 9 6" />
            </svg>
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: category.color }}
            />
            <span className="text-[13px] text-zinc-700">{category.name}</span>
          </div>
          {mountedCount > 0 && (
            <span className="text-[10px] px-1.5 py-0.5 bg-indigo-100 text-indigo-700 rounded-full">
              {mountedCount}
            </span>
          )}
        </button>

        {isExpanded && (
          <div className="pl-6 mt-1 space-y-1">
            {categorySkills.map((skill) => {
              const isMounted = mountedSkillIds.includes(skill.id);
              return (
                <div
                  key={skill.id}
                  onClick={() => toggleSkillMount(skill.id)}
                  className={`flex items-center gap-2 px-2 py-1.5 rounded-lg cursor-pointer transition-colors ${
                    isMounted
                      ? 'bg-indigo-50 border border-indigo-200'
                      : 'hover:bg-zinc-50 border border-transparent'
                  }`}
                >
                  <div
                    className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${
                      isMounted
                        ? 'bg-indigo-600 border-indigo-600'
                        : 'border-zinc-300'
                    }`}
                  >
                    {isMounted && (
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="12"
                        height="12"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="white"
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p
                      className={`text-[12px] truncate ${
                        isMounted ? 'text-indigo-700 font-medium' : 'text-zinc-600'
                      }`}
                    >
                      {skill.name}
                    </p>
                    {skill.description && (
                      <p className="text-[10px] text-zinc-400 truncate">
                        {skill.description}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  // 系统技能（始终显示且不可取消）
  const systemSkills = skills.filter(
    (s) => s.is_system && s.is_active
  );

  // 获取已挂载的用户技能（非系统技能）
  const mountedUserSkills = skills.filter(
    (s) => !s.is_system && s.is_active && mountedSkillIds.includes(s.id)
  );

  // 按分类分组已挂载的技能
  const mountedSkillsByCategory = mountedUserSkills.reduce((acc, skill) => {
    const category = getCategoryById(skill.category_id);
    if (category) {
      if (!acc[category.id]) {
        acc[category.id] = { category, skills: [] };
      }
      acc[category.id].skills.push(skill);
    }
    return acc;
  }, {} as Record<string, { category: SkillCategory; skills: Skill[] }>);

  return (
    <div className="h-full flex flex-col">
      {/* 头部 */}
      <div className="p-3 border-b border-zinc-200">
        <h3 className="text-sm font-semibold text-zinc-900">技能挂载</h3>
        <p className="text-[11px] text-zinc-500 mt-0.5">
          选择要应用到本书的 Agent 技能
        </p>
      </div>

      {/* 系统技能（始终激活） */}
      {systemSkills.length > 0 && (
        <div className="p-3 border-b border-zinc-200 bg-zinc-50">
          <div className="flex items-center gap-2 mb-2">
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
              className="text-emerald-600"
            >
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
            <span className="text-[12px] font-medium text-zinc-700">
              已激活：安全基座
            </span>
          </div>
          <div className="space-y-1">
            {systemSkills.map((skill) => (
              <div
                key={skill.id}
                className="flex items-center gap-2 px-2 py-1 bg-white border border-emerald-200 rounded-lg"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="text-emerald-600"
                >
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <span className="text-[11px] text-zinc-700">{skill.name}</span>
              </div>
            ))}
          </div>
          <p className="text-[10px] text-zinc-400 mt-2">
            系统技能默认启用，不可关闭
          </p>
        </div>
      )}

      {/* 用户技能列表 - 只显示已挂载的技能 */}
      <div className="flex-1 overflow-y-auto p-3">
        {Object.values(mountedSkillsByCategory).length > 0 ? (
          Object.values(mountedSkillsByCategory).map(({ category, skills }) => (
            <div key={category.id} className="mb-4">
              <div className="flex items-center gap-2 mb-2">
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: category.color }}
                />
                <span className="text-[11px] font-medium text-zinc-500 uppercase">
                  {categoryTypeLabels[category.type]}
                </span>
                <span className="text-[10px] text-zinc-400">· {category.name}</span>
              </div>
              <div className="space-y-1">
                {skills.map((skill) => (
                  <div
                    key={skill.id}
                    onClick={() => toggleSkillMount(skill.id)}
                    className="flex items-center gap-2 px-2 py-1.5 rounded-lg cursor-pointer transition-colors bg-indigo-50 border border-indigo-200 hover:bg-indigo-100"
                  >
                    <div className="w-4 h-4 rounded border flex items-center justify-center bg-indigo-600 border-indigo-600">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="12"
                        height="12"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="white"
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[12px] truncate text-indigo-700 font-medium">
                        {skill.name}
                      </p>
                      {skill.description && (
                        <p className="text-[10px] text-zinc-500 truncate">
                          {skill.description}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-8 text-zinc-400">
            <p className="text-[12px]">暂无挂载的技能</p>
            <p className="text-[10px] mt-1">点击下方按钮添加</p>
          </div>
        )}
      </div>

      {/* 底部操作 */}
      <div className="p-3 border-t border-zinc-200">
        <button
          onClick={() => setShowGlobalLibrary(true)}
          className="w-full py-2 text-[12px] font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg flex items-center justify-center gap-2 transition-colors"
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
          >
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.3-4.3" />
          </svg>
          从全局库添加
        </button>
      </div>

      {/* 全局库弹窗 */}
      {showGlobalLibrary && typeof document !== 'undefined' && createPortal(
        <GlobalSkillLibraryModal
          novelId={novelId}
          onClose={() => setShowGlobalLibrary(false)}
        />,
        document.body
      )}
    </div>
  );
};

// 全局技能库弹窗
const GlobalSkillLibraryModal: React.FC<{
  novelId: string;
  onClose: () => void;
}> = ({ novelId, onClose }) => {
  const { categories, skills, fetchCategories, fetchSkills } = useSkillStore();
  const { novels, updateNovel } = useNovelStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const novel = novels.find((n) => n.id === novelId);
  const mountedSkillIds = novel?.mountedSkills || [];

  useEffect(() => {
    fetchCategories();
    fetchSkills();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filteredSkills = skills.filter((skill) => {
    if (!skill.is_active) return false;
    if (skill.is_system) return false; // 排除系统固定技能
    if (selectedCategory && skill.category_id !== selectedCategory) return false;
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        skill.name.toLowerCase().includes(query) ||
        skill.description.toLowerCase().includes(query)
      );
    }
    return true;
  });

  const toggleSkillMount = (skillId: string) => {
    if (!novel) return;
    
    const currentMountedSkills = novel.mountedSkills || [];
    const newMountedSkills = currentMountedSkills.includes(skillId)
      ? currentMountedSkills.filter((id) => id !== skillId)
      : [...currentMountedSkills, skillId];
    
    updateNovel(novelId, { mountedSkills: newMountedSkills });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center" style={{ zIndex: 9999 }}>
      <div className="bg-white rounded-xl w-[600px] max-h-[80vh] flex flex-col">
        {/* 头部 */}
        <div className="p-4 border-b border-zinc-200 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-zinc-900">全局技能库</h3>
            <p className="text-sm text-zinc-500">选择要挂载到本书的技能</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-zinc-100 rounded-lg transition-colors"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M18 6 6 18" />
              <path d="m6 6 12 12" />
            </svg>
          </button>
        </div>

        {/* 搜索和筛选 */}
        <div className="p-4 border-b border-zinc-200 space-y-3">
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

          {/* 分类筛选 */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedCategory(null)}
              className={`px-3 py-1 text-xs rounded-full transition-colors ${
                selectedCategory === null
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'
              }`}
            >
              全部
            </button>
            {categories
              .filter((c) => c.type !== 'system')
              .map((category) => (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  className={`px-3 py-1 text-xs rounded-full transition-colors ${
                    selectedCategory === category.id
                      ? 'bg-indigo-100 text-indigo-700'
                      : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'
                  }`}
                >
                  {category.name}
                </button>
              ))}
          </div>
        </div>

        {/* 技能列表 */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="space-y-2">
            {filteredSkills.map((skill) => {
              const isMounted = mountedSkillIds.includes(skill.id);
              const category = categories.find((c) => c.id === skill.category_id);

              return (
                <div
                  key={skill.id}
                  onClick={() => toggleSkillMount(skill.id)}
                  className={`p-3 border rounded-lg cursor-pointer transition-all ${
                    isMounted
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-zinc-200 hover:border-zinc-300'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={`w-5 h-5 rounded border flex items-center justify-center shrink-0 mt-0.5 ${
                        isMounted
                          ? 'bg-indigo-600 border-indigo-600'
                          : 'border-zinc-300'
                      }`}
                    >
                      {isMounted && (
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          width="14"
                          height="14"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="white"
                          strokeWidth="3"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h4
                          className={`font-medium text-sm ${
                            isMounted ? 'text-indigo-700' : 'text-zinc-900'
                          }`}
                        >
                          {skill.name}
                        </h4>
                        {category && (
                          <span
                            className="text-[10px] px-1.5 py-0.5 rounded"
                            style={{
                              backgroundColor: `${category.color}20`,
                              color: category.color,
                            }}
                          >
                            {category.name}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-zinc-500 mt-1 line-clamp-2">
                        {skill.description || '暂无描述'}
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        {skill.target_agents.map((agent) => (
                          <span
                            key={agent}
                            className="text-[10px] px-1.5 py-0.5 bg-zinc-100 text-zinc-600 rounded"
                          >
                            {agent}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}

            {filteredSkills.length === 0 && (
              <div className="text-center py-8 text-zinc-400">
                <p className="text-sm">未找到匹配的技能</p>
              </div>
            )}
          </div>
        </div>

        {/* 底部 */}
        <div className="p-4 border-t border-zinc-200 flex items-center justify-between">
          <span className="text-sm text-zinc-500">
            已挂载 {mountedSkillIds.length} 个技能
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 transition-colors"
          >
            完成
          </button>
        </div>
      </div>
    </div>
  );
};
