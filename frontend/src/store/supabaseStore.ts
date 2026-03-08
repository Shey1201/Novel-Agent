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

// API 基础URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

// 匿名用户ID，用于没有登录系统的情况
// 使用随机生成的UUID，避免与真实用户ID冲突
const ANONYMOUS_USER_ID = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890';

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
  clearRecycleBin: () => void;
  renameNovel: (id: string, newTitle: string) => void;
  toggleLockNovel: (id: string) => void;
  setCurrentNovelId: (id: string | null) => void;
  setCurrentChapterId: (id: string | null) => void;

  // 章节方法
  addChapter: (novelId: string, chapter: Chapter) => void;
  updateChapter: (novelId: string, chapterId: string, updates: Partial<Chapter>) => void;
  deleteChapter: (novelId: string, chapterId: string) => void;
  updateChapterContent: (novelId: string, chapterId: string, content: string, trace_data?: TraceItem[]) => void;

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
      agents: [],

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
        // 通过后端API创建小说
        try {
          const response = await fetch(`${API_BASE}/api/novels`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              title: novel.title,
              locked: novel.locked || false,
              category_id: novel.categoryId || null,
            }),
          });
          
          if (!response.ok) {
            const error = await response.json();
            console.error('Failed to create novel via API:', error);
            return;
          }
          
          const data = await response.json();
          
          // 使用数据库返回的ID更新本地状态
          const novelWithDbId = { 
            ...novel, 
            id: data.id,
            categoryId: data.category_id,
            locked: data.locked,
          };
          set((state) => ({ novels: [...state.novels, novelWithDbId] }));
          console.log('Novel created via API:', data.id);
        } catch (err) {
          console.error('Error creating novel:', err);
        }
      },
      updateNovel: async (id, updates) => {
        // 先更新本地状态
        set((state) => ({
          novels: state.novels.map((n) => (n.id === id ? { ...n, ...updates } : n)),
        }));
        
        // 通过后端API同步到数据库
        try {
          const response = await fetch(`${API_BASE}/api/novels/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates),
          });
          
          if (!response.ok) {
            const error = await response.json();
            console.error('Failed to update novel via API:', error);
          } else {
            console.log('Novel updated via API:', id);
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
      clearRecycleBin: () => set((state) => {
        const now = Date.now();
        const thirtyDays = 30 * 24 * 60 * 60 * 1000;
        const expired = state.deletedNovels.filter((n) => now - (n.deletedAt || 0) >= thirtyDays);
        const remaining = state.deletedNovels.filter((n) => now - (n.deletedAt || 0) < thirtyDays);
        
        // 同步到 Supabase：删除过期的小说
        expired.forEach(async (novel) => {
          try {
            await supabase.from('novels').delete().eq('id', novel.id);
          } catch (err) {
            console.error('Error deleting expired novel:', err);
          }
        });
        
        return { deletedNovels: remaining };
      }),
      renameNovel: async (id, newTitle) => {
        // 先更新本地状态
        set((state) => ({
          novels: state.novels.map((n) =>
            n.id === id ? { ...n, title: newTitle } : n
          ),
        }));
        
        // 同步到 Supabase
        try {
          const { error } = await supabase
            .from('novels')
            .update({ title: newTitle, updated_at: new Date().toISOString() })
            .eq('id', id);
          
          if (error) {
            console.error('Failed to rename novel in Supabase:', error);
          }
        } catch (err) {
          console.error('Error renaming novel:', err);
        }
      },
      toggleLockNovel: async (id) => {
        // 先获取当前状态
        const novel = get().novels.find((n) => n.id === id);
        if (!novel) return;
        
        const newLockState = !novel.locked;
        
        // 更新本地状态
        set((state) => ({
          novels: state.novels.map((n) =>
            n.id === id ? { ...n, locked: newLockState } : n
          ),
        }));
        
        // 同步到 Supabase
        try {
          const { error } = await supabase
            .from('novels')
            .update({ locked: newLockState, updated_at: new Date().toISOString() })
            .eq('id', id);
          
          if (error) {
            console.error('Failed to toggle lock in Supabase:', error);
          }
        } catch (err) {
          console.error('Error toggling lock:', err);
        }
      },
      setCurrentNovelId: (id) => set({ currentNovelId: id }),
      setCurrentChapterId: (id) => set({ currentChapterId: id }),

      // 章节方法
      addChapter: async (novelId, chapter) => {
        // 通过后端API创建章节
        try {
          const response = await fetch(`${API_BASE}/api/novels/${novelId}/chapters`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              title: chapter.title,
              content: chapter.content || '',
              order_index: (chapter as any).orderIndex || 0,
              status: 'draft',
              volume_name: chapter.volumeName || '未分卷',
              volume_order: chapter.volumeOrder || 0,
            }),
          });
          
          if (!response.ok) {
            const error = await response.json();
            console.error('Failed to create chapter via API:', error);
            return;
          }
          
          const data = await response.json();
          
          // 使用数据库返回的ID更新本地状态
          const chapterWithDbId: Chapter = { 
            ...chapter, 
            id: data.id,
            volumeName: data.volume_name,
            volumeOrder: data.volume_order,
          };
          set((state) => ({
            novels: state.novels.map((n) =>
              n.id === novelId ? { ...n, chapters: [...n.chapters, chapterWithDbId] } : n
            ),
          }));
          console.log('Chapter created via API:', data.id);
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
        
        // 通过后端API同步到数据库
        try {
          const response = await fetch(`${API_BASE}/api/novels/${novelId}/chapters/${chapterId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates),
          });
          
          if (!response.ok) {
            const error = await response.json();
            console.error('Failed to update chapter via API:', error);
          } else {
            console.log('Chapter updated via API:', chapterId);
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
        
        // 通过后端API删除
        try {
          const response = await fetch(`${API_BASE}/api/novels/${novelId}/chapters/${chapterId}`, {
            method: 'DELETE',
          });
          
          if (!response.ok) {
            const error = await response.json();
            console.error('Failed to delete chapter via API:', error);
          } else {
            console.log('Chapter deleted via API:', chapterId);
          }
        } catch (err) {
          console.error('Error deleting chapter:', err);
        }
      },
      updateChapterContent: async (novelId, chapterId, content, trace_data) => {
        // 先更新本地状态
        set((state) => ({
          novels: state.novels.map((n) =>
            n.id === novelId
              ? {
                  ...n,
                  chapters: n.chapters.map((c) =>
                    c.id === chapterId ? { ...c, content, trace_data: trace_data || c.trace_data } : c
                  ),
                }
              : n
          ),
        }));
        
        // 通过后端API同步到数据库
        try {
          const response = await fetch(`${API_BASE}/api/novels/${novelId}/chapters/${chapterId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              content,
              trace_data: trace_data || [],
            }),
          });
          
          if (!response.ok) {
            const error = await response.json();
            console.error('Failed to update chapter content via API:', error);
          } else {
            console.log('Chapter content updated via API:', chapterId);
          }
        } catch (err) {
          console.error('Error updating chapter content:', err);
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
                  user_id: ANONYMOUS_USER_ID,
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
                  user_id: ANONYMOUS_USER_ID,
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

        // 通过后端API同步到数据库
        try {
          const response = await fetch(`${API_BASE}/api/agents/configs/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates),
          });

          if (!response.ok) {
            const error = await response.json();
            console.error('Failed to update agent via API:', error);
          } else {
            console.log(`Agent ${id} updated via API successfully`);
          }
        } catch (err) {
          console.error('Error updating agent via API:', err);
        }
      },

      // 消息方法
      addMessage: async (message) => {
        // 同步到 Supabase - 不指定ID，让数据库自动生成UUID
        try {
          const { data, error } = await supabase.from('messages').insert({
            user_id: ANONYMOUS_USER_ID,
            role: message.role,
            content: message.content,
            agent_id: (message as any).agentId || null,
            agent_name: (message as any).agentName || null,
            timestamp: (message as any).timestamp || new Date().toISOString(),
            created_at: new Date().toISOString(),
          }).select('id').single();

          if (error) {
            console.error('Failed to create message in Supabase:', error);
            return;
          }
          
          // 使用数据库返回的ID更新本地状态
          const messageWithDbId = { ...message, id: data.id };
          set((state) => ({
            messages: [...state.messages, messageWithDbId],
          }));
          console.log('Message created in Supabase:', data.id);
        } catch (err) {
          console.error('Error creating message:', err);
        }
      },
      clearMessages: async () => {
        // 先更新本地状态
        set({ messages: [] });
        
        // 同步到 Supabase - 删除所有消息
        try {
          const { error } = await supabase
            .from('messages')
            .delete()
            .neq('id', '00000000-0000-0000-0000-000000000000'); // 删除所有记录
          
          if (error) {
            console.error('Failed to clear messages in Supabase:', error);
          }
        } catch (err) {
          console.error('Error clearing messages:', err);
        }
      },

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
              id: (worldBible as any).id || crypto.randomUUID(),
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

      // 分类方法 - 使用后端API
      addCategory: async (category) => {
        // 通过后端API创建分类
        try {
          const response = await fetch(`${API_BASE}/api/categories`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              name: category.name,
              color: category.color,
            }),
          });
          
          if (!response.ok) {
            const error = await response.json();
            console.error('Failed to create category via API:', error);
            return;
          }
          
          const data = await response.json();
          
          // 使用数据库返回的ID更新本地状态
          const categoryWithDbId = {
            ...category,
            id: data.id,
          };
          set((state) => ({
            categories: [...state.categories, categoryWithDbId],
          }));
          console.log('Category created via API:', data.id);
        } catch (err) {
          console.error('Error creating category:', err);
        }
      },
      updateCategory: async (id, updates) => {
        // 先更新本地状态
        set((state) => ({
          categories: state.categories.map((c) => (c.id === id ? { ...c, ...updates } : c)),
        }));
        
        // 通过后端API同步到数据库
        try {
          const response = await fetch(`${API_BASE}/api/categories/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates),
          });
          
          if (!response.ok) {
            const error = await response.json();
            console.error('Failed to update category via API:', error);
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
        
        // 通过后端API删除
        try {
          const response = await fetch(`${API_BASE}/api/categories/${id}`, {
            method: 'DELETE',
          });
          
          if (!response.ok) {
            const error = await response.json();
            console.error('Failed to delete category via API:', error);
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
        // 同步到 Supabase - 不指定ID，让数据库自动生成UUID
        try {
          const { data, error } = await supabase.from('story_assets').insert({
            user_id: ANONYMOUS_USER_ID,
            novel_id: asset.novelId,
            category: category,
            name: asset.name,
            content: {},
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }).select('id').single();

          if (error) {
            console.error('Failed to create story asset in Supabase:', error);
            return;
          }

          // 使用数据库返回的ID更新本地状态
          const assetWithDbId = { ...asset, id: data.id };
          set((state) => ({
            storyAssets: {
              ...state.storyAssets,
              [category]: [...state.storyAssets[category], assetWithDbId],
            },
          }));
          console.log('Story asset created in Supabase:', data.id);
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

          // 通过后端API加载小说列表（包含章节）
          const response = await fetch(`${API_BASE}/api/novels/with-chapters`);
          if (!response.ok) {
            const error = await response.json();
            console.error('Failed to load novels from API:', error);
          } else {
            const novelsData = await response.json();
            
            if (novelsData && novelsData.length > 0) {
              const novelsWithChapters = novelsData.map((novel: any) => ({
                id: novel.id,
                title: novel.title,
                outline: novel.outline || '',
                locked: novel.locked || false,
                categoryId: novel.category_id || null,  // 添加分类ID映射
                createdAt: new Date(novel.created_at).getTime(),
                updatedAt: new Date(novel.updated_at).getTime(),
                chapters: (novel.chapters || []).map((ch: any) => ({
                  id: ch.id,
                  title: ch.title,
                  content: ch.content || '',
                  order: ch.order || 0,
                  summary: '',
                  wordCount: 0,
                  status: ch.status || 'draft',
                  volumeName: ch.volume_name || '未分卷',
                  volumeOrder: ch.volume_order || 0,
                  createdAt: new Date(ch.created_at).getTime(),
                  updatedAt: new Date(ch.updated_at).getTime(),
                })),
              }));

              set({ novels: novelsWithChapters });
              console.log(`Loaded ${novelsWithChapters.length} novels from API`);
            }
          }

          // 加载已删除的小说（回收站）- 暂时仍使用Supabase直连
          // TODO: 添加后端API支持
          const { data: deletedNovelsData, error: deletedError } = await supabase
            .from('novels')
            .select('*')
            .not('deleted_at', 'is', null)
            .order('deleted_at', { ascending: false });

          if (deletedError) {
            console.error('Failed to load deleted novels:', deletedError);
          } else if (deletedNovelsData && deletedNovelsData.length > 0) {
            const deletedNovels = deletedNovelsData.map((novel: any) => ({
              id: novel.id,
              title: novel.title,
              outline: novel.outline || '',
              locked: novel.locked || false,
              createdAt: new Date(novel.created_at).getTime(),
              updatedAt: new Date(novel.updated_at).getTime(),
              chapters: [],
              deletedAt: new Date(novel.deleted_at).getTime(),
            }));
            set({ deletedNovels });
            console.log(`Loaded ${deletedNovels.length} deleted novels from Supabase`);
          }

          // 加载分类 - 使用后端API
          try {
            const categoryResponse = await fetch(`${API_BASE}/api/categories`);
            if (categoryResponse.ok) {
              const categoriesData = await categoryResponse.json();
              if (categoriesData && categoriesData.length > 0) {
                const loadedCategories = categoriesData.map((cat: any) => ({
                  id: cat.id,
                  name: cat.name,
                  color: cat.color,
                }));
                set({ categories: loadedCategories });
                console.log(`Loaded ${categoriesData.length} categories from API`);
              }
            } else {
              console.error('Failed to load categories from API:', await categoryResponse.text());
            }
          } catch (categoryError) {
            console.error('Error loading categories from API:', categoryError);
          }

          // 加载 Agent 配置 - 使用后端API
          try {
            const agentResponse = await fetch(`${API_BASE}/api/agents/configs`);
            if (agentResponse.ok) {
              const agentConfigs = await agentResponse.json();
              if (agentConfigs && agentConfigs.length > 0) {
                // 将数据库配置转换为本地 agents 格式
                const loadedAgents = agentConfigs.map((config: any) => ({
                  id: config.agent_id,
                  name: config.name,
                  role: config.role,
                  personality: config.personality,
                  temperature: config.temperature,
                  prompt: config.prompt,
                  enabled: config.enabled,
                }));
                set({ agents: loadedAgents });
                console.log(`Loaded ${agentConfigs.length} agent configs from API`);
              } else {
                // 数据库中没有配置，使用默认配置创建
                console.log('No agent configs in database, creating default agents...');
                const defaultAgentsList = [
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
                
                // 同步默认配置到数据库
                for (const agent of defaultAgentsList) {
                  try {
                    await fetch(`${API_BASE}/api/agents/configs/${agent.id}/sync`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        name: agent.name,
                        role: agent.role,
                        personality: agent.personality,
                        temperature: agent.temperature,
                        prompt: agent.prompt,
                        enabled: agent.enabled,
                      }),
                    });
                  } catch (err) {
                    console.error(`Failed to sync agent ${agent.id}:`, err);
                  }
                }
                
                // 设置本地状态
                set({ agents: defaultAgentsList });
                console.log('Default agents created and synced to database');
              }
            } else {
              console.error('Failed to load agent configs from API:', await agentResponse.text());
            }
          } catch (agentError) {
            console.error('Error loading agent configs from API:', agentError);
          }

          console.log('Data loaded successfully');
        } catch (err) {
          console.error('Error loading data:', err);
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
supabase.auth.onAuthStateChange((_event: any, session: any) => {
  useSupabaseStore.getState().setUser(session?.user ?? null);
});
