import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { supabase } from '@/lib/supabase';
import type { User } from '@supabase/supabase-js';
import type {
  WorkspaceModule,
  SidebarView,
  AssetCategory,
  Novel,
  DeletedNovel,
  Chapter,
  Agent,
  NovelCategory,
  WorldBible,
  StoryAssets,
  AgentConfig,
  Message,
  TraceItem,
} from './novelStore';

// 重新导出类型
export type {
  WorkspaceModule,
  SidebarView,
  AssetCategory,
  Novel,
  Chapter,
  Agent,
  NovelCategory,
  WorldBible,
  StoryAssets,
  AgentConfig,
  Message,
  TraceItem,
} from './novelStore';

interface NovelState {
  // 用户认证
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  // UI 状态
  workspaceModule: WorkspaceModule;
  currentSidebarView: SidebarView;
  selectedAssetCategory: AssetCategory;

  // 数据
  novels: Novel[];
  deletedNovels: DeletedNovel[];
  currentNovelId: string | null;
  currentChapterId: string | null;
  constraints: string[];
  agentConfigs: AgentConfig;
  messages: Message[];
  writingMode: 'manual' | 'ai-writer' | 'ai-assisted';
  worldBible: WorldBible;
  worldApproved: boolean;
  categories: NovelCategory[];
  selectedCategoryId: string;
  storyAssets: StoryAssets;
  agents: Agent[];

  // 方法
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  signOut: () => Promise<void>;

  // UI 方法
  setWorkspaceModule: (m: WorkspaceModule) => void;
  setCurrentSidebarView: (view: SidebarView) => void;
  setSelectedAssetCategory: (c: AssetCategory) => void;

  // 小说方法
  addNovel: (novel: Novel) => void;
  updateNovel: (id: string, updates: Partial<Novel>) => void;
  deleteNovel: (id: string) => void;
  restoreNovel: (id: string) => void;
  permanentlyDeleteNovel: (id: string) => void;
  setCurrentNovelId: (id: string | null) => void;
  setCurrentChapterId: (id: string | null) => void;

  // 章节方法
  addChapter: (novelId: string, chapter: Chapter) => void;
  updateChapter: (novelId: string, chapterId: string, updates: Partial<Chapter>) => void;
  deleteChapter: (novelId: string, chapterId: string) => void;

  // 约束方法
  addConstraint: (constraint: string) => void;
  removeConstraint: (index: number) => void;

  // Agent 方法
  updateAgentConfig: (config: Partial<AgentConfig>) => void;
  updateAgent: (id: string, updates: Partial<Agent>) => void;

  // 消息方法
  addMessage: (message: Message) => void;
  clearMessages: () => void;

  // 写作模式
  setWritingMode: (mode: 'manual' | 'ai-writer' | 'ai-assisted') => void;

  // 世界设定
  setWorldBible: (worldBible: WorldBible) => void;
  setWorldApproved: (approved: boolean) => void;

  // 分类方法
  addCategory: (category: NovelCategory) => void;
  updateCategory: (id: string, updates: Partial<NovelCategory>) => void;
  deleteCategory: (id: string) => void;
  setSelectedCategoryId: (id: string) => void;
  setNovelCategory: (novelId: string, categoryId: string | null) => void;

  // 资源方法
  addStoryAsset: (category: keyof StoryAssets, asset: { id: string; name: string; novelId: string }) => void;
  removeStoryAsset: (category: keyof StoryAssets, id: string) => void;

  // 回收站
  checkRecycleBin: () => void;

  // 数据同步
  syncWithSupabase: () => Promise<void>;
  loadFromSupabase: () => Promise<void>;
}

const emptyRefs = () => ({
  characters: [],
  worldbuilding: [],
  factions: [],
  locations: [],
  timeline: [],
});

const defaultAgentConfig: AgentConfig = {
  excitement_level: 5,
  strictness: 7,
  pacing: 5,
  character_depth: 5,
  conflict_intensity: 5,
  description_density: 5,
  style: 'balanced',
};

const defaultAgents: Agent[] = [
  { id: 'facilitator', name: 'Facilitator', role: '调度协调', prompt: '负责Agent调度和讨论主持', temperature: 0.5, enabled: true, personality: 'structure' },
  { id: 'planner', name: 'Planner', role: '规划架构', prompt: '负责章节规划和剧情架构', temperature: 0.7, enabled: true, personality: 'structure' },
  { id: 'writer', name: 'Writer', role: '章节写作', prompt: '负责具体章节写作', temperature: 0.9, enabled: true, personality: 'literary' },
  { id: 'editor', name: 'Editor', role: '润色修订', prompt: '负责文本润色和结构优化', temperature: 0.4, enabled: true, personality: 'logic' },
  { id: 'conflict', name: 'Conflict', role: '冲突设计', prompt: '负责冲突设计和戏剧性增强', temperature: 0.8, enabled: true, personality: 'drama' },
  { id: 'reader', name: 'Reader', role: '读者评估', prompt: '负责读者视角评估', temperature: 0.6, enabled: true, personality: 'reader' },
  { id: 'consistency', name: 'Consistency', role: '一致性检查', prompt: '负责逻辑一致性检查', temperature: 0.3, enabled: true, personality: 'logic' },
  { id: 'critic', name: 'Critic', role: '批判评估', prompt: '负责批判性评估和改进建议', temperature: 0.5, enabled: true, personality: 'logic' },
  { id: 'summary', name: 'Summary', role: '摘要总结', prompt: '负责内容摘要和总结', temperature: 0.4, enabled: true, personality: 'structure' },
];

export const useSupabaseStore = create<NovelState>()(
  persist(
    (set, get) => ({
      // 用户状态
      user: null,
      isLoading: true,
      isAuthenticated: false,

      // UI 状态
      workspaceModule: 'novels',
      currentSidebarView: 'chapter',
      selectedAssetCategory: 'characters',

      // 数据
      novels: [],
      deletedNovels: [],
      currentNovelId: null,
      currentChapterId: null,
      constraints: ['禁止血腥', '禁止 OOC', '避免翻译腔'],
      agentConfigs: defaultAgentConfig,
      messages: [],
      writingMode: 'manual',
      worldBible: { themes: [] },
      worldApproved: false,
      categories: [
        { id: 'cat-all', name: '全部', color: '#6366f1' },
        { id: 'cat-uncategorized', name: '未分类', color: '#9ca3af' },
      ],
      selectedCategoryId: 'cat-all',
      storyAssets: {
        characters: [],
        worldbuilding: [],
        factions: [],
        locations: [],
        timeline: [],
      },
      agents: defaultAgents,

      // 用户方法
      setUser: (user) => set({ user, isAuthenticated: !!user, isLoading: false }),
      setLoading: (loading) => set({ isLoading: loading }),
      signOut: async () => {
        await supabase.auth.signOut();
        set({ user: null, isAuthenticated: false });
      },

      // UI 方法
      setWorkspaceModule: (m) => set({ workspaceModule: m }),
      setCurrentSidebarView: (view) => set({ currentSidebarView: view }),
      setSelectedAssetCategory: (c) => set({ selectedAssetCategory: c }),

      // 小说方法
      addNovel: async (novel) => {
        // 先更新本地状态
        set((state) => ({ novels: [...state.novels, novel] }));
        
        // 同步到 Supabase
        try {
          const { error } = await supabase.from('novels').insert({
            id: novel.id,
            title: novel.title,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          });
          
          if (error) {
            console.error('Failed to create novel in Supabase:', error);
          } else {
            console.log('Novel created in Supabase:', novel.id);
          }
        } catch (err) {
          console.error('Error creating novel:', err);
        }
      },
      updateNovel: async (id, updates) => {
        // 先更新本地状态
        set((state) => ({
          novels: state.novels.map((n) => (n.id === id ? { ...n, ...updates } : n)),
        }));
        
        // 同步到 Supabase
        try {
          const { error } = await supabase
            .from('novels')
            .update({
              ...updates,
              updated_at: new Date().toISOString(),
            })
            .eq('id', id);
          
          if (error) {
            console.error('Failed to update novel in Supabase:', error);
          }
        } catch (err) {
          console.error('Error updating novel:', err);
        }
      },
      deleteNovel: async (id) => {
        const novel = get().novels.find((n) => n.id === id);
        if (!novel) return;
        
        // 更新本地状态
        set((state) => ({
          novels: state.novels.filter((n) => n.id !== id),
          deletedNovels: [...state.deletedNovels, { ...novel, deletedAt: Date.now() }],
          currentNovelId: state.currentNovelId === id ? null : state.currentNovelId,
        }));
        
        // 同步到 Supabase：标记为已删除
        try {
          const { error } = await supabase
            .from('novels')
            .update({ deleted_at: new Date().toISOString() })
            .eq('id', id);
          
          if (error) {
            console.error('Failed to mark novel as deleted:', error);
          }
        } catch (err) {
          console.error('Error marking novel as deleted:', err);
        }
      },
      restoreNovel: async (id) => {
        const novel = get().deletedNovels.find((n) => n.id === id);
        if (!novel) return;
        
        const { deletedAt, ...rest } = novel;
        
        // 更新本地状态
        set((state) => ({
          deletedNovels: state.deletedNovels.filter((n) => n.id !== id),
          novels: [...state.novels, rest],
        }));
        
        // 同步到 Supabase：恢复小说
        try {
          const { error } = await supabase
            .from('novels')
            .update({ deleted_at: null })
            .eq('id', id);
          
          if (error) {
            console.error('Failed to restore novel:', error);
          }
        } catch (err) {
          console.error('Error restoring novel:', err);
        }
      },
      permanentlyDeleteNovel: async (id) => {
        // 更新本地状态
        set((state) => ({
          deletedNovels: state.deletedNovels.filter((n) => n.id !== id),
        }));
        
        // 同步到 Supabase：真正删除
        try {
          const { error } = await supabase
            .from('novels')
            .delete()
            .eq('id', id);
          
          if (error) {
            console.error('Failed to permanently delete novel:', error);
          } else {
            console.log(`Novel ${id} permanently deleted`);
          }
        } catch (err) {
          console.error('Error permanently deleting novel:', err);
        }
      },
      setCurrentNovelId: (id) => set({ currentNovelId: id }),
      setCurrentChapterId: (id) => set({ currentChapterId: id }),

      // 章节方法
      addChapter: async (novelId, chapter) => {
        // 先更新本地状态
        set((state) => ({
          novels: state.novels.map((n) =>
            n.id === novelId ? { ...n, chapters: [...n.chapters, chapter] } : n
          ),
        }));
        
        // 同步到 Supabase
        try {
          const { error } = await supabase.from('chapters').insert({
            id: chapter.id,
            novel_id: novelId,
            title: chapter.title,
            content: chapter.content,
            order_index: chapter.orderIndex || 0,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          });
          
          if (error) {
            console.error('Failed to create chapter in Supabase:', error);
          }
        } catch (err) {
          console.error('Error creating chapter:', err);
        }
      },
      updateChapter: async (novelId, chapterId, updates) => {
        // 先更新本地状态
        set((state) => ({
          novels: state.novels.map((n) =>
            n.id === novelId
              ? {
                  ...n,
                  chapters: n.chapters.map((c) =>
                    c.id === chapterId ? { ...c, ...updates } : c
                  ),
                }
              : n
          ),
        }));
        
        // 同步到 Supabase
        try {
          const { error } = await supabase
            .from('chapters')
            .update({
              ...updates,
              updated_at: new Date().toISOString(),
            })
            .eq('id', chapterId);
          
          if (error) {
            console.error('Failed to update chapter in Supabase:', error);
          }
        } catch (err) {
          console.error('Error updating chapter:', err);
        }
      },
      deleteChapter: async (novelId, chapterId) => {
        // 先更新本地状态
        set((state) => ({
          novels: state.novels.map((n) =>
            n.id === novelId
              ? { ...n, chapters: n.chapters.filter((c) => c.id !== chapterId) }
              : n
          ),
        }));
        
        // 同步到 Supabase
        try {
          const { error } = await supabase
            .from('chapters')
            .delete()
            .eq('id', chapterId);
          
          if (error) {
            console.error('Failed to delete chapter in Supabase:', error);
          }
        } catch (err) {
          console.error('Error deleting chapter:', err);
        }
      },

      // 约束方法
      addConstraint: async (constraint) => {
        // 先更新本地状态
        set((state) => {
          const newConstraints = [...state.constraints, constraint];
          
          // 同步到 Supabase
          (async () => {
            try {
              const { error } = await supabase
                .from('user_settings')
                .upsert({
                  id: 'default',
                  constraints: newConstraints,
                  updated_at: new Date().toISOString(),
                }, { onConflict: 'id' });
              
              if (error) {
                console.error('Failed to sync constraints to Supabase:', error);
              }
            } catch (err) {
              console.error('Error syncing constraints:', err);
            }
          })();
          
          return { constraints: newConstraints };
        });
      },
      removeConstraint: async (index) => {
        // 先更新本地状态
        set((state) => {
          const newConstraints = state.constraints.filter((_, i) => i !== index);
          
          // 同步到 Supabase
          (async () => {
            try {
              const { error } = await supabase
                .from('user_settings')
                .upsert({
                  id: 'default',
                  constraints: newConstraints,
                  updated_at: new Date().toISOString(),
                }, { onConflict: 'id' });
              
              if (error) {
                console.error('Failed to sync constraints to Supabase:', error);
              }
            } catch (err) {
              console.error('Error syncing constraints:', err);
            }
          })();
          
          return { constraints: newConstraints };
        });
      },

      // Agent 方法
      updateAgentConfig: (config) => set((state) => ({
        agentConfigs: { ...state.agentConfigs, ...config },
      })),
      updateAgent: async (id, updates) => {
        // 先更新本地状态
        set((state) => ({
          agents: state.agents.map((a) => (a.id === id ? { ...a, ...updates } : a)),
        }));
        
        // 同步到 Supabase（不需要用户登录）
        try {
          const { error } = await supabase
            .from('agent_configs')
            .update({
              ...updates,
              updated_at: new Date().toISOString(),
            })
            .eq('agent_id', id);
          
          if (error) {
            console.error('Failed to sync agent config to Supabase:', error);
          } else {
            console.log(`Agent ${id} updated successfully`);
          }
        } catch (err) {
          console.error('Error syncing agent config:', err);
        }
      },

      // 消息方法
      addMessage: (message) => set((state) => ({
        messages: [...state.messages, message],
      })),
      clearMessages: () => set({ messages: [] }),

      // 写作模式
      setWritingMode: (mode) => set({ writingMode: mode }),

      // 世界设定
      setWorldBible: async (worldBible) => {
        // 先更新本地状态
        set({ worldBible });
        
        // 同步到 Supabase
        try {
          const { error } = await supabase
            .from('world_bibles')
            .upsert({
              id: worldBible.id || crypto.randomUUID(),
              content: worldBible,
              updated_at: new Date().toISOString(),
            }, { onConflict: 'id' });
          
          if (error) {
            console.error('Failed to sync world bible to Supabase:', error);
          }
        } catch (err) {
          console.error('Error syncing world bible:', err);
        }
      },
      setWorldApproved: (approved) => set({ worldApproved: approved }),

      // 分类方法
      addCategory: async (category) => {
        // 先更新本地状态
        set((state) => ({
          categories: [...state.categories, category],
        }));
        
        // 同步到 Supabase
        try {
          const { error } = await supabase.from('categories').insert({
            id: category.id,
            name: category.name,
            color: category.color,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          });
          
          if (error) {
            console.error('Failed to create category in Supabase:', error);
          }
        } catch (err) {
          console.error('Error creating category:', err);
        }
      },
      updateCategory: async (id, updates) => {
        // 先更新本地状态
        set((state) => ({
          categories: state.categories.map((c) => (c.id === id ? { ...c, ...updates } : c)),
        }));
        
        // 同步到 Supabase
        try {
          const { error } = await supabase
            .from('categories')
            .update({
              ...updates,
              updated_at: new Date().toISOString(),
            })
            .eq('id', id);
          
          if (error) {
            console.error('Failed to update category in Supabase:', error);
          }
        } catch (err) {
          console.error('Error updating category:', err);
        }
      },
      deleteCategory: async (id) => {
        // 先更新本地状态
        set((state) => ({
          categories: state.categories.filter((c) => c.id !== id),
          novels: state.novels.map((n) => (n.categoryId === id ? { ...n, categoryId: null } : n)),
          selectedCategoryId: state.selectedCategoryId === id ? 'cat-all' : state.selectedCategoryId,
        }));
        
        // 同步到 Supabase
        try {
          const { error } = await supabase
            .from('categories')
            .delete()
            .eq('id', id);
          
          if (error) {
            console.error('Failed to delete category in Supabase:', error);
          }
        } catch (err) {
          console.error('Error deleting category:', err);
        }
      },
      setSelectedCategoryId: (id) => set({ selectedCategoryId: id }),
      setNovelCategory: async (novelId, categoryId) => {
        // 先更新本地状态
        set((state) => ({
          novels: state.novels.map((n) => (n.id === novelId ? { ...n, categoryId } : n)),
        }));
        
        // 同步到 Supabase
        try {
          const { error } = await supabase
            .from('novels')
            .update({ category_id: categoryId })
            .eq('id', novelId);
          
          if (error) {
            console.error('Failed to update novel category in Supabase:', error);
          }
        } catch (err) {
          console.error('Error updating novel category:', err);
        }
      },

      // 资源方法
      addStoryAsset: async (category, asset) => {
        // 先更新本地状态
        set((state) => ({
          storyAssets: {
            ...state.storyAssets,
            [category]: [...state.storyAssets[category], asset],
          },
        }));
        
        // 同步到 Supabase
        try {
          const { error } = await supabase.from('story_assets').insert({
            id: asset.id,
            novel_id: asset.novelId,
            category: category,
            name: asset.name,
            content: {},
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          });
          
          if (error) {
            console.error('Failed to create story asset in Supabase:', error);
          }
        } catch (err) {
          console.error('Error creating story asset:', err);
        }
      },
      removeStoryAsset: async (category, id) => {
        // 先更新本地状态
        set((state) => ({
          storyAssets: {
            ...state.storyAssets,
            [category]: state.storyAssets[category].filter((a) => a.id !== id),
          },
        }));
        
        // 同步到 Supabase
        try {
          const { error } = await supabase
            .from('story_assets')
            .delete()
            .eq('id', id);
          
          if (error) {
            console.error('Failed to delete story asset in Supabase:', error);
          }
        } catch (err) {
          console.error('Error deleting story asset:', err);
        }
      },

      // 回收站
      checkRecycleBin: () => set((state) => {
        const now = Date.now();
        const thirtyDays = 30 * 24 * 60 * 60 * 1000;
        const remaining = state.deletedNovels.filter((n) => now - (n.deletedAt || 0) < thirtyDays);
        if (remaining.length === state.deletedNovels.length) return state;
        return { deletedNovels: remaining };
      }),

      // 数据同步（预留接口）
      syncWithSupabase: async () => {
        // TODO: 实现数据同步到 Supabase
        console.log('Syncing with Supabase...');
      },
      loadFromSupabase: async () => {
        try {
          set({ isLoading: true });
          
          // 加载 Agent 配置
          const { data: agentConfigs, error: agentError } = await supabase
            .from('agent_configs')
            .select('*');
          
          if (agentError) {
            console.error('Failed to load agent configs:', agentError);
          } else if (agentConfigs && agentConfigs.length > 0) {
            // 将数据库中的配置合并到本地 agents
            set((state) => ({
              agents: state.agents.map((agent) => {
                const dbConfig = agentConfigs.find((c) => c.agent_id === agent.id);
                if (dbConfig) {
                  return {
                    ...agent,
                    role: dbConfig.role || agent.role,
                    personality: dbConfig.personality || agent.personality,
                    temperature: dbConfig.temperature ?? agent.temperature,
                    prompt: dbConfig.prompt || agent.prompt,
                  };
                }
                return agent;
              }),
            }));
          } else {
            // 数据库中没有配置，将本地默认配置同步到数据库
            console.log('No agent configs in database, syncing local defaults...');
            const { agents } = get();
            for (const agent of agents) {
              try {
                await supabase.from('agent_configs').insert({
                  agent_id: agent.id,
                  name: agent.name,
                  role: agent.role,
                  personality: agent.personality,
                  temperature: agent.temperature,
                  prompt: agent.prompt,
                  enabled: true,
                });
              } catch (err) {
                console.error(`Failed to sync agent ${agent.id}:`, err);
              }
            }
          }
          
          console.log('Data loaded from Supabase successfully');
        } catch (err) {
          console.error('Error loading from Supabase:', err);
        } finally {
          set({ isLoading: false });
        }
      },
    }),
    {
      name: 'novel-supabase-store',
      partialize: (state) => ({
        // 只持久化 UI 状态，数据将从 Supabase 加载
        workspaceModule: state.workspaceModule,
        currentSidebarView: state.currentSidebarView,
        selectedAssetCategory: state.selectedAssetCategory,
        constraints: state.constraints,
        agentConfigs: state.agentConfigs,
        writingMode: state.writingMode,
        categories: state.categories,
        selectedCategoryId: state.selectedCategoryId,
      }),
    }
  )
);

// 初始化时加载数据（不需要登录）
useSupabaseStore.getState().loadFromSupabase();

// 监听登录状态变化（可选功能）
supabase.auth.onAuthStateChange((_event, session) => {
  useSupabaseStore.getState().setUser(session?.user ?? null);
});
