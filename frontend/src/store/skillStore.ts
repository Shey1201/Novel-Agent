import { create } from 'zustand';

export type SkillCategoryType = 'system' | 'writing' | 'domain' | 'auditing';
export type AgentType = 'writer' | 'editor' | 'planner' | 'conflict' | 'reader' | 'summary' | 'critic' | 'consistency';

export interface SkillCategory {
  id: string;
  name: string;
  type: SkillCategoryType;
  parent_id: string | null;
  color: string;
  icon?: string;
  is_system: boolean;
  description?: string;
  default_agents?: AgentType[];
  order: number;
}

export interface SkillConstraint {
  id: string;
  content: string;
  priority: 'high' | 'medium' | 'low';
  enabled: boolean;
}

export interface Skill {
  id: string;
  name: string;
  description: string;
  category_id: string | null;
  constraints: SkillConstraint[];
  target_agents: AgentType[];
  version: string;
  is_active: boolean;
  is_system: boolean;
  linked_assets: string[];
  applicable_novels: string[];
  created_at: string;
  updated_at: string;
  author?: string;
  test_example?: string;
}

export interface SkillTestResult {
  passed: boolean;
  violations: string[];
  suggestions: string[];
}

interface SkillState {
  // 分类
  categories: SkillCategory[];
  selectedCategoryId: string | null;
  expandedCategories: string[];

  // 技能
  skills: Skill[];
  selectedSkillId: string | null;
  searchQuery: string;

  // 加载状态
  isLoading: boolean;
  error: string | null;

  // 测试
  testResult: SkillTestResult | null;
  isTesting: boolean;

  // Actions
  fetchCategories: () => Promise<void>;
  fetchSkills: () => Promise<void>;
  createCategory: (category: Omit<SkillCategory, 'id'>) => Promise<void>;
  updateCategory: (id: string, updates: Partial<SkillCategory>) => Promise<void>;
  deleteCategory: (id: string) => Promise<void>;
  moveCategory: (id: string, newParentId: string | null, newOrder: number) => Promise<void>;

  createSkill: (skill: Omit<Skill, 'id' | 'created_at' | 'updated_at' | 'version'>) => Promise<Skill | null>;
  updateSkill: (id: string, updates: Partial<Skill>) => Promise<void>;
  deleteSkill: (id: string) => Promise<void>;
  moveSkillToCategory: (skillId: string, categoryId: string) => Promise<void>;

  toggleSkillActive: (id: string) => Promise<void>;
  linkAssetToSkill: (skillId: string, assetId: string) => Promise<void>;
  unlinkAssetFromSkill: (skillId: string, assetId: string) => Promise<void>;

  testSkill: (skillId: string, testText: string) => Promise<SkillTestResult>;

  setSelectedCategoryId: (id: string | null) => void;
  setSelectedSkillId: (id: string | null) => void;
  setSearchQuery: (query: string) => void;
  toggleCategoryExpanded: (id: string) => void;

  // Getters
  getCategoryById: (id: string) => SkillCategory | undefined;
  getSkillById: (id: string) => Skill | undefined;
  getSkillsByCategory: (categoryId: string) => Skill[];
  getChildCategories: (parentId: string | null) => SkillCategory[];
  getSystemCategories: () => SkillCategory[];
  getUserCategories: () => SkillCategory[];
  getFilteredSkills: () => Skill[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export const useSkillStore = create<SkillState>((set, get) => ({
  categories: [],
  selectedCategoryId: null,
  expandedCategories: [],
  skills: [],
  selectedSkillId: null,
  searchQuery: '',
  isLoading: false,
  error: null,
  testResult: null,
  isTesting: false,

  fetchCategories: async () => {
    try {
      const response = await fetch(`${API_BASE}/api/skills/categories`);
      if (!response.ok) throw new Error('Failed to fetch categories');
      const data = await response.json();
      // 默认展开所有根分类（parent_id === null）
      const rootCategoryIds = data.filter((c: SkillCategory) => c.parent_id === null).map((c: SkillCategory) => c.id);
      set({ 
        categories: data,
        expandedCategories: rootCategoryIds
      });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Unknown error' });
    }
  },

  fetchSkills: async () => {
    try {
      const response = await fetch(`${API_BASE}/api/skills`);
      if (!response.ok) throw new Error('Failed to fetch skills');
      const data = await response.json();
      set({ skills: data });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Unknown error' });
    }
  },

  createCategory: async (category) => {
    try {
      const response = await fetch(`${API_BASE}/api/skills/categories`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(category),
      });
      if (!response.ok) throw new Error('Failed to create category');
      const newCategory = await response.json();
      set((state) => ({
        categories: [...state.categories, newCategory],
      }));
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Unknown error' });
    }
  },

  updateCategory: async (id, updates) => {
    try {
      const response = await fetch(`${API_BASE}/api/skills/categories/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      if (!response.ok) throw new Error('Failed to update category');
      const updated = await response.json();
      set((state) => ({
        categories: state.categories.map((c) => (c.id === id ? updated : c)),
      }));
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Unknown error' });
    }
  },

  deleteCategory: async (id) => {
    try {
      const response = await fetch(`${API_BASE}/api/skills/categories/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to delete category');
      }
      set((state) => ({
        categories: state.categories.filter((c) => c.id !== id),
        // 将该分类下的技能变为未归类 (category_id = null)
        skills: state.skills.map((s) =>
          s.category_id === id ? { ...s, category_id: null as any } : s
        ),
      }));
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Unknown error' });
      throw err;
    }
  },

  moveCategory: async (id, newParentId, newOrder) => {
    try {
      const response = await fetch(`${API_BASE}/api/skills/categories/${id}/move`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ parent_id: newParentId, order: newOrder }),
      });
      if (!response.ok) throw new Error('Failed to move category');
      await get().fetchCategories();
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Unknown error' });
    }
  },

  createSkill: async (skill) => {
    try {
      const response = await fetch(`${API_BASE}/api/skills`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(skill),
      });
      if (!response.ok) throw new Error('Failed to create skill');
      const newSkill = await response.json();
      set((state) => ({
        skills: [...state.skills, newSkill],
        selectedSkillId: newSkill.id,
      }));
      return newSkill;
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Unknown error' });
      return null;
    }
  },

  updateSkill: async (id, updates) => {
    try {
      const response = await fetch(`${API_BASE}/api/skills/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      if (!response.ok) throw new Error('Failed to update skill');
      const updated = await response.json();
      set((state) => ({
        skills: state.skills.map((s) => (s.id === id ? updated : s)),
      }));
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Unknown error' });
    }
  },

  deleteSkill: async (id) => {
    try {
      const response = await fetch(`${API_BASE}/api/skills/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete skill');
      set((state) => ({
        skills: state.skills.filter((s) => s.id !== id),
        selectedSkillId: state.selectedSkillId === id ? null : state.selectedSkillId,
      }));
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Unknown error' });
    }
  },

  moveSkillToCategory: async (skillId, categoryId) => {
    await get().updateSkill(skillId, { category_id: categoryId });
  },

  toggleSkillActive: async (id) => {
    const skill = get().getSkillById(id);
    if (skill) {
      await get().updateSkill(id, { is_active: !skill.is_active });
    }
  },

  linkAssetToSkill: async (skillId, assetId) => {
    const skill = get().getSkillById(skillId);
    if (skill && !skill.linked_assets.includes(assetId)) {
      await get().updateSkill(skillId, {
        linked_assets: [...skill.linked_assets, assetId],
      });
    }
  },

  unlinkAssetFromSkill: async (skillId, assetId) => {
    const skill = get().getSkillById(skillId);
    if (skill) {
      await get().updateSkill(skillId, {
        linked_assets: skill.linked_assets.filter((a) => a !== assetId),
      });
    }
  },

  testSkill: async (skillId, testText) => {
    set({ isTesting: true });
    try {
      const response = await fetch(`${API_BASE}/api/skills/${skillId}/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: testText }),
      });
      if (!response.ok) throw new Error('Failed to test skill');
      const result = await response.json();
      set({ testResult: result, isTesting: false });
      return result;
    } catch (err) {
      set({ isTesting: false, error: err instanceof Error ? err.message : 'Unknown error' });
      return { passed: false, violations: [], suggestions: [] };
    }
  },

  setSelectedCategoryId: (id) => set({ selectedCategoryId: id }),
  setSelectedSkillId: (id) => set({ selectedSkillId: id }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  toggleCategoryExpanded: (id) =>
    set((state) => ({
      expandedCategories: state.expandedCategories.includes(id)
        ? state.expandedCategories.filter((c) => c !== id)
        : [...state.expandedCategories, id],
    })),

  getCategoryById: (id) => get().categories.find((c) => c.id === id),
  getSkillById: (id) => get().skills.find((s) => s.id === id),
  getSkillsByCategory: (categoryId) =>
    get().skills.filter((s) => s.category_id === categoryId),
  getChildCategories: (parentId) =>
    get().categories
      .filter((c) => c.parent_id === parentId)
      .sort((a, b) => a.order - b.order),
  getSystemCategories: () =>
    get().categories.filter((c) => c.type === 'system'),
  getUserCategories: () =>
    get().categories.filter((c) => c.type !== 'system'),
  getFilteredSkills: () => {
    const { skills, searchQuery, selectedCategoryId } = get();
    let filtered = skills;

    if (selectedCategoryId) {
      if (selectedCategoryId === 'all') {
        // 显示全部技能，不过滤
        filtered = skills;
      } else if (selectedCategoryId === 'uncategorized') {
        // 显示未归类的技能
        filtered = filtered.filter((s) => !s.category_id);
      } else {
        // 显示特定分类的技能（包括子分类）
        const category = get().categories.find(c => c.id === selectedCategoryId);
        if (category) {
          // 获取该分类及其所有子分类的ID
          const getAllChildCategoryIds = (catId: string): string[] => {
            const childIds = get().categories
              .filter(c => c.parent_id === catId)
              .map(c => c.id);
            const grandChildIds = childIds.flatMap(id => getAllChildCategoryIds(id));
            return [catId, ...childIds, ...grandChildIds];
          };
          const categoryIds = getAllChildCategoryIds(selectedCategoryId);
          filtered = filtered.filter((s) => s.category_id && categoryIds.includes(s.category_id));
        } else {
          filtered = filtered.filter((s) => s.category_id === selectedCategoryId);
        }
      }
    }

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (s) =>
          s.name.toLowerCase().includes(query) ||
          s.description.toLowerCase().includes(query)
      );
    }

    return filtered;
  },
}));
