/**
 * Novel Store 功能测试
 * 测试小说状态管理的各项功能
 */

import { useNovelStore } from '../novelStore';

describe('Novel Store 功能测试', () => {
  // 每个测试前重置 store
  beforeEach(() => {
    const store = useNovelStore.getState();
    // 重置到初始状态
    store.setCurrentNovelId(null);
    store.setCurrentChapterId(null);
  });

  describe('小说管理', () => {
    test('应该能添加新小说', () => {
      const store = useNovelStore.getState();
      const newNovel = {
        id: 'test-novel-1',
        title: '测试小说',
        chapters: [],
        assetRefs: {
          characters: [],
          worldbuilding: [],
          factions: [],
          locations: [],
          timeline: [],
        },
      };

      store.addNovel(newNovel);
      const novels = useNovelStore.getState().novels;
      
      expect(novels.some(n => n.id === 'test-novel-1')).toBe(true);
    });

    test('应该能更新小说标题', () => {
      const store = useNovelStore.getState();
      const novelId = 'novel-1';
      
      store.renameNovel(novelId, '新标题');
      const novel = useNovelStore.getState().novels.find(n => n.id === novelId);
      
      expect(novel?.title).toBe('新标题');
    });

    test('应该能删除小说到回收站', () => {
      const store = useNovelStore.getState();
      const novelId = 'novel-1';
      
      store.deleteNovel(novelId);
      const state = useNovelStore.getState();
      
      expect(state.novels.some(n => n.id === novelId)).toBe(false);
      expect(state.deletedNovels.some(n => n.id === novelId)).toBe(true);
    });

    test('应该能从回收站恢复小说', () => {
      const store = useNovelStore.getState();
      const novelId = 'novel-1';
      
      store.deleteNovel(novelId);
      store.restoreNovel(novelId);
      const state = useNovelStore.getState();
      
      expect(state.novels.some(n => n.id === novelId)).toBe(true);
      expect(state.deletedNovels.some(n => n.id === novelId)).toBe(false);
    });

    test('应该能永久删除小说', () => {
      const store = useNovelStore.getState();
      const novelId = 'novel-1';
      
      store.deleteNovel(novelId);
      store.permanentlyDeleteNovel(novelId);
      const state = useNovelStore.getState();
      
      expect(state.deletedNovels.some(n => n.id === novelId)).toBe(false);
    });
  });

  describe('章节管理', () => {
    test('应该能添加新章节', () => {
      const store = useNovelStore.getState();
      // 先添加一本小说
      const novelId = 'test-novel-for-chapter';
      store.addNovel({
        id: novelId,
        title: '测试小说',
        chapters: [],
        assetRefs: {
          characters: [],
          worldbuilding: [],
          factions: [],
          locations: [],
          timeline: [],
        },
      });
      
      const newChapter = {
        id: 'chapter-new',
        title: '新章节',
        content: '',
        trace_data: [],
      };

      store.addChapter(novelId, newChapter);
      const novel = useNovelStore.getState().novels.find(n => n.id === novelId);
      
      expect(novel?.chapters.some(c => c.id === 'chapter-new')).toBe(true);
    });

    test('应该能更新章节内容', () => {
      const store = useNovelStore.getState();
      const novelId = 'test-novel-for-content';
      const chapterId = 'chapter-1';
      
      // 先添加小说和章节
      store.addNovel({
        id: novelId,
        title: '测试小说',
        chapters: [{
          id: chapterId,
          title: '第一章',
          content: '',
          trace_data: [],
        }],
        assetRefs: {
          characters: [],
          worldbuilding: [],
          factions: [],
          locations: [],
          timeline: [],
        },
      });
      
      const newContent = '<p>新的章节内容</p>';
      store.updateChapterContent(novelId, chapterId, newContent);
      const novel = useNovelStore.getState().novels.find(n => n.id === novelId);
      const chapter = novel?.chapters.find(c => c.id === chapterId);
      
      expect(chapter?.content).toBe(newContent);
    });

    test('应该能更新章节标题', () => {
      const store = useNovelStore.getState();
      const novelId = 'test-novel-for-title';
      const chapterId = 'chapter-1';
      
      // 先添加小说和章节
      store.addNovel({
        id: novelId,
        title: '测试小说',
        chapters: [{
          id: chapterId,
          title: '第一章',
          content: '',
          trace_data: [],
        }],
        assetRefs: {
          characters: [],
          worldbuilding: [],
          factions: [],
          locations: [],
          timeline: [],
        },
      });
      
      const newTitle = '新章节标题';
      store.updateChapterTitle(novelId, chapterId, newTitle);
      const novel = useNovelStore.getState().novels.find(n => n.id === novelId);
      const chapter = novel?.chapters.find(c => c.id === chapterId);
      
      expect(chapter?.title).toBe(newTitle);
    });
  });

  describe('分类管理', () => {
    test('应该能添加新分类', () => {
      const store = useNovelStore.getState();
      const newCategory = {
        id: 'cat-test',
        name: '测试分类',
        color: '#ff0000',
      };

      store.addCategory(newCategory);
      const categories = useNovelStore.getState().categories;
      
      expect(categories.some(c => c.id === 'cat-test')).toBe(true);
    });

    test('应该能设置小说分类', () => {
      const store = useNovelStore.getState();
      const novelId = 'test-novel-for-category';
      const categoryId = 'cat-technology';
      
      // 先添加小说
      store.addNovel({
        id: novelId,
        title: '测试小说',
        chapters: [],
        assetRefs: {
          characters: [],
          worldbuilding: [],
          factions: [],
          locations: [],
          timeline: [],
        },
      });

      store.setNovelCategory(novelId, categoryId);
      const novel = useNovelStore.getState().novels.find(n => n.id === novelId);
      
      expect(novel?.categoryId).toBe(categoryId);
    });
  });

  describe('状态切换', () => {
    test('应该能切换工作区模块', () => {
      const store = useNovelStore.getState();
      
      store.setWorkspaceModule('agent-management');
      expect(useNovelStore.getState().workspaceModule).toBe('agent-management');
      
      store.setWorkspaceModule('story-assets');
      expect(useNovelStore.getState().workspaceModule).toBe('story-assets');
    });

    test('应该能切换侧边栏视图', () => {
      const store = useNovelStore.getState();
      
      store.setCurrentSidebarView('outline');
      expect(useNovelStore.getState().currentSidebarView).toBe('outline');
    });

    test('应该能设置当前小说和章节', () => {
      const store = useNovelStore.getState();
      
      store.setCurrentNovelId('novel-1');
      store.setCurrentChapterId('chapter-1-1');
      
      expect(useNovelStore.getState().currentNovelId).toBe('novel-1');
      expect(useNovelStore.getState().currentChapterId).toBe('chapter-1-1');
    });
  });

  describe('Agent 配置', () => {
    test('应该能更新 Agent 配置', () => {
      const store = useNovelStore.getState();
      
      store.updateAgentConfig({ excitement_level: 8, style: '科幻' });
      const config = useNovelStore.getState().agentConfigs;
      
      expect(config.excitement_level).toBe(8);
      expect(config.style).toBe('科幻');
    });
  });
});
