import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type WorkspaceModule = 'novels' | 'agent-management' | 'story-assets' | 'settings';
export type SidebarView = 'chapter' | 'outline';
export type AssetCategory = 'characters' | 'worldbuilding' | 'factions' | 'locations' | 'timeline';

export interface TraceItem {
  text: string;
  source_agent: string;
  revisions?: string[];
}

export interface AgentConfig {
  excitement_level: number;
  strictness: number;
  pacing: number;
  character_depth: number;
  conflict_intensity: number;
  description_density: number;
  style: string;
}

export interface Chapter {
  id: string;
  title: string;
  content: string;
  trace_data: TraceItem[];
}

export interface NovelAssetRefs {
  characters: string[];
  worldbuilding: string[];
  factions: string[];
  locations: string[];
  timeline: string[];
}

export interface Novel {
  id: string;
  title: string;
  chapters: Chapter[];
  assetRefs: NovelAssetRefs;
}

export interface Agent {
  id: string;
  name: string;
  role: string;
  prompt: string;
  temperature: number;
  enabled: boolean;
}

export interface StoryAssetItem {
  id: string;
  name: string;
  novelId: string;
}

export interface StoryAssets {
  characters: StoryAssetItem[];
  worldbuilding: StoryAssetItem[];
  factions: StoryAssetItem[];
  locations: StoryAssetItem[];
  timeline: StoryAssetItem[];
}

export interface WorldBible {
  world_view?: string;
  rules?: string;
  themes: string[];
}

export interface Message {
  id: string;
  sender: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: number;
  agentId?: string;
}

interface NovelState {
  workspaceModule: WorkspaceModule;
  currentSidebarView: SidebarView;
  selectedAssetCategory: AssetCategory;
  novels: Novel[];
  currentNovelId: string | null;
  currentChapterId: string | null;
  constraints: string[];
  agentConfigs: AgentConfig;
  messages: Message[];
  writingMode: 'manual' | 'ai-writer' | 'ai-assisted';
  agents: Agent[];
  storyAssets: StoryAssets;
  worldBible: WorldBible;
  worldApproved: boolean;

  setWorkspaceModule: (m: WorkspaceModule) => void;
  setCurrentSidebarView: (view: SidebarView) => void;
  setSelectedAssetCategory: (c: AssetCategory) => void;
  addNovel: (novel: Novel) => void;
  updateNovel: (id: string, updates: Partial<Novel>) => void;
  deleteNovel: (id: string) => void;
  setCurrentNovelId: (id: string) => void;
  addChapter: (novelId: string, chapter: Chapter) => void;
  setCurrentChapterId: (id: string) => void;
  updateChapterContent: (novelId: string, chapterId: string, content: string, trace_data?: TraceItem[]) => void;
  updateChapterTitle: (novelId: string, chapterId: string, title: string) => void;
  toggleAssetReference: (novelId: string, category: AssetCategory, assetId: string) => void;
  addConstraint: (constraint: string) => void;
  removeConstraint: (index: number) => void;
  updateAgentConfig: (config: Partial<AgentConfig>) => void;
  addMessage: (message: Message) => void;
  clearMessages: () => void;
  setWritingMode: (mode: 'manual' | 'ai-writer' | 'ai-assisted') => void;
  updateAgent: (id: string, updates: Partial<Agent>) => void;
  setWorldBible: (worldBible: WorldBible) => void;
  setWorldApproved: (approved: boolean) => void;
}

const emptyRefs = (): NovelAssetRefs => ({
  characters: [],
  worldbuilding: [],
  factions: [],
  locations: [],
  timeline: [],
});

export const useNovelStore = create<NovelState>()(
  persist(
    (set) => ({
      workspaceModule: 'novels',
      currentSidebarView: 'chapter',
      selectedAssetCategory: 'characters',
      novels: [
        {
          id: 'novel-1',
          title: 'Untitled Story',
          chapters: [
            { id: 'chapter-1-1', title: '章节 1', content: '', trace_data: [] },
            { id: 'chapter-1-2', title: '章节 2', content: '', trace_data: [] },
          ],
          assetRefs: emptyRefs(),
        },
      ],
      currentNovelId: 'novel-1',
      currentChapterId: 'chapter-1-1',
      constraints: ['禁止血腥', '禁止 OOC', '避免翻译腔'],
      agentConfigs: {
        excitement_level: 5,
        strictness: 7,
        pacing: 5,
        character_depth: 5,
        conflict_intensity: 5,
        description_density: 5,
        style: '经典文学',
      },
      messages: [{ id: 'm1', sender: '系统', role: 'agent', content: '欢迎来到 Agent Room。', timestamp: 1 }],
      writingMode: 'manual',
      worldBible: { themes: [] },
      worldApproved: false,
      storyAssets: {
        characters: [{ id: 'char-linyuan', name: '林渊', novelId: 'novel-1' }],
        worldbuilding: [{ id: 'world-gaowu', name: '高武世界', novelId: 'novel-1' }],
        factions: [{ id: 'fac-zongmen', name: '青岚宗', novelId: 'novel-1' }],
        locations: [{ id: 'loc-shuyuan', name: '藏书阁', novelId: 'novel-1' }],
        timeline: [{ id: 'time-war', name: '百年前大战', novelId: 'novel-1' }],
      },
      agents: [
        { id: 'controller', name: 'Controller', role: '流程总控', prompt: '...', temperature: 0.4, enabled: true },
        { id: 'planner', name: 'Planner', role: '规划架构', prompt: '...', temperature: 0.7, enabled: true },
        { id: 'writer', name: 'Writer', role: '章节写作', prompt: '...', temperature: 0.9, enabled: true },
        { id: 'editor', name: 'Editor', role: '润色修订', prompt: '...', temperature: 0.4, enabled: true },
        { id: 'conflict', name: 'Conflict', role: '冲突设计', prompt: '...', temperature: 0.8, enabled: true },
        { id: 'reader', name: 'Reader', role: '读者评估', prompt: '...', temperature: 0.6, enabled: true },
      ],

      setWorkspaceModule: (m) => set({ workspaceModule: m }),
      setCurrentSidebarView: (view) => set({ currentSidebarView: view }),
      setSelectedAssetCategory: (c) => set({ selectedAssetCategory: c }),
      addNovel: (novel) => set((state) => ({ novels: [...state.novels, novel] })),
      updateNovel: (id, updates) => set((state) => ({ novels: state.novels.map((n) => (n.id === id ? { ...n, ...updates } : n)) })),
      deleteNovel: (id) => set((state) => ({ novels: state.novels.filter((n) => n.id !== id) })),
      setCurrentNovelId: (id) => set({ currentNovelId: id, currentChapterId: null }),
      addChapter: (novelId, chapter) => set((state) => ({ novels: state.novels.map((novel) => (novel.id === novelId ? { ...novel, chapters: [...novel.chapters, chapter] } : novel)) })),
      setCurrentChapterId: (id) => set({ currentChapterId: id, currentSidebarView: 'chapter' }),
      updateChapterContent: (novelId, chapterId, content, trace_data) => set((state) => ({
        novels: state.novels.map((novel) =>
          novel.id === novelId
            ? { ...novel, chapters: novel.chapters.map((ch) => (ch.id === chapterId ? { ...ch, content, trace_data: trace_data || ch.trace_data } : ch)) }
            : novel
        ),
      })),
      updateChapterTitle: (novelId, chapterId, title) => set((state) => ({
        novels: state.novels.map((novel) => (novel.id === novelId ? { ...novel, chapters: novel.chapters.map((ch) => (ch.id === chapterId ? { ...ch, title } : ch)) } : novel)),
      })),
      toggleAssetReference: (novelId, category, assetId) => set((state) => ({
        novels: state.novels.map((novel) => {
          if (novel.id !== novelId) return novel;
          const list = novel.assetRefs[category];
          const next = list.includes(assetId) ? list.filter((id) => id !== assetId) : [...list, assetId];
          return { ...novel, assetRefs: { ...novel.assetRefs, [category]: next } };
        }),
      })),
      addConstraint: (constraint) => set((state) => ({ constraints: [...state.constraints, constraint] })),
      removeConstraint: (index) => set((state) => ({ constraints: state.constraints.filter((_, i) => i !== index) })),
      updateAgentConfig: (config) => set((state) => ({ agentConfigs: { ...state.agentConfigs, ...config } })),
      addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
      clearMessages: () => set({ messages: [] }),
      setWritingMode: (mode) => set({ writingMode: mode }),
      updateAgent: (id, updates) => set((state) => ({ agents: state.agents.map((a) => (a.id === id ? { ...a, ...updates } : a)) })),
      setWorldBible: (worldBible) => set({ worldBible }),
      setWorldApproved: (approved) => set({ worldApproved: approved }),
    }),
    { name: 'novel-storage-v3' }
  )
);
