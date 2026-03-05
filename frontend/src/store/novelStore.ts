import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AgentConfig {
  excitement_level: number;
  strictness: number;
  pacing: number;
  character_depth: number;
  conflict_intensity: number;
  description_density: number;
  style: string;
}

interface Chapter {
  id: string;
  title: string;
  content: string;
  trace_data: any[];
}

interface Novel {
  id: string;
  title: string;
  chapters: Chapter[];
}

interface Agent {
  id: string;
  name: string;
  role: string;
  prompt: string;
  temperature: number;
  enabled: boolean;
}

interface Message {
  id: string;
  sender: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: number;
  agentId?: string;
}

interface NovelState {
  novels: Novel[];
  currentNovelId: string | null;
  currentChapterId: string | null;
  constraints: string[];
  agentConfigs: AgentConfig;
  messages: Message[];
  writingMode: 'manual' | 'ai-writer' | 'ai-assisted';
  agents: Agent[];

  // Actions
  addNovel: (novel: Novel) => void;
  updateNovel: (id: string, updates: Partial<Novel>) => void;
  deleteNovel: (id: string) => void;
  setCurrentNovelId: (id: string) => void;
  addChapter: (novelId: string, chapter: Chapter) => void;
  setCurrentChapterId: (id: string) => void;
  updateChapterContent: (novelId: string, chapterId: string, content: string, trace_data?: any[]) => void;
  addConstraint: (constraint: string) => void;
  removeConstraint: (index: number) => void;
  updateAgentConfig: (config: Partial<AgentConfig>) => void;
  addMessage: (message: Message) => void;
  clearMessages: () => void;
  setWritingMode: (mode: 'manual' | 'ai-writer' | 'ai-assisted') => void;
  updateAgent: (id: string, updates: Partial<Agent>) => void;
}

export const useNovelStore = create<NovelState>()(
  persist(
    (set) => ({
      novels: [
        {
          id: 'novel-1',
          title: '我的第一部小说',
          chapters: [
            { id: 'chapter-1-1', title: '第一章：觉醒', content: '', trace_data: [] },
            { id: 'chapter-1-2', title: '第二章：神秘学院', content: '', trace_data: [] },
          ],
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
      messages: [
        { id: 'm1', sender: '系统', role: 'agent', content: '欢迎来到 Agent Room。在这里，你可以发布指令与 Agent 团队讨论并创作小说。', timestamp: Date.now() }
      ],
      writingMode: 'manual',
      agents: [
        { id: 'writer', name: 'Writer Agent', role: '负责写章节', prompt: '你是一个专业的小说作家...', temperature: 0.9, enabled: true },
        { id: 'editor', name: 'Editor Agent', role: '负责修改结构和语言', prompt: '你是一个严厉的编辑...', temperature: 0.3, enabled: true },
        { id: 'reader', name: 'Reader Agent', role: '从读者角度给出反馈', prompt: '你负责从读者角度给出反馈...', temperature: 0.7, enabled: true },
        { id: 'conflict', name: 'Conflict Agent', role: '增加剧情冲突', prompt: '你负责增加剧情冲突...', temperature: 0.9, enabled: true },
        { id: 'world', name: 'World Agent', role: '维护世界观一致性', prompt: '你负责维护世界观设定...', temperature: 0.5, enabled: true },
        { id: 'outline', name: 'Outline Agent', role: '规划故事情节大纲', prompt: '你负责规划整体故事情节...', temperature: 0.6, enabled: true },
      ],

      addNovel: (novel) => set((state) => ({ novels: [...state.novels, novel] })),
      updateNovel: (id, updates) => set((state) => ({
        novels: state.novels.map((n) => (n.id === id ? { ...n, ...updates } : n)),
      })),
      deleteNovel: (id) => set((state) => ({
        novels: state.novels.filter((n) => n.id !== id),
        currentNovelId: state.currentNovelId === id ? (state.novels.length > 1 ? state.novels.find(n => n.id !== id)?.id || null : null) : state.currentNovelId,
      })),
      setCurrentNovelId: (id) => set({ currentNovelId: id, currentChapterId: null }),
      addChapter: (novelId, chapter) => set((state) => ({
        novels: state.novels.map((novel) =>
          novel.id === novelId ? { ...novel, chapters: [...novel.chapters, chapter] } : novel
        ),
      })),
      setCurrentChapterId: (id) => set({ currentChapterId: id }),
      updateChapterContent: (novelId, chapterId, content, trace_data) => set((state) => ({
        novels: state.novels.map((novel) =>
          novel.id === novelId
            ? {
                ...novel,
                chapters: novel.chapters.map((ch) =>
                  ch.id === chapterId ? { ...ch, content, trace_data: trace_data || ch.trace_data } : ch
                ),
              }
            : novel
        ),
      })),
      addConstraint: (constraint) => set((state) => ({ constraints: [...state.constraints, constraint] })),
      removeConstraint: (index) => set((state) => ({ 
        constraints: state.constraints.filter((_, i) => i !== index) 
      })),
      updateAgentConfig: (config) => set((state) => ({ 
        agentConfigs: { ...state.agentConfigs, ...config } 
      })),
      addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
      clearMessages: () => set({ messages: [] }),
      setWritingMode: (mode) => set({ writingMode: mode }),
      updateAgent: (id, updates) => set((state) => ({
        agents: state.agents.map((a) => (a.id === id ? { ...a, ...updates } : a)),
      })),
    }),
    {
      name: 'novel-storage-v2', // 更改存储名称以强制重置
    }
  )
);
