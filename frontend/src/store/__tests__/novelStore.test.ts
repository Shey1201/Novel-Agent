import { describe, it, expect } from '@jest/globals';
import type { Novel, Chapter, Agent } from '../novelStore';

describe('NovelStore Types', () => {
  describe('Novel interface', () => {
    it('should create a valid novel object', () => {
      const novel: Novel = {
        id: 'test-id',
        title: 'Test Novel',
        chapters: [],
        assetRefs: {
          characters: [],
          worldbuilding: [],
          factions: [],
          locations: [],
          timeline: [],
        },
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };

      expect(novel.id).toBe('test-id');
      expect(novel.title).toBe('Test Novel');
      expect(novel.chapters).toEqual([]);
    });

    it('should handle novel with chapters', () => {
      const chapter: Chapter = {
        id: 'chapter-1',
        title: 'Chapter 1',
        content: 'Chapter content',
        trace_data: [],
      };

      const novel: Novel = {
        id: 'test-id',
        title: 'Test Novel',
        chapters: [chapter],
        assetRefs: {
          characters: [],
          worldbuilding: [],
          factions: [],
          locations: [],
          timeline: [],
        },
        createdAt: Date.now(),
        updatedAt: Date.now(),
        locked: false,
      };

      expect(novel.chapters).toHaveLength(1);
      expect(novel.chapters[0].title).toBe('Chapter 1');
      expect(novel.locked).toBe(false);
    });
  });

  describe('Chapter interface', () => {
    it('should create a valid chapter object', () => {
      const chapter: Chapter = {
        id: 'chapter-1',
        title: 'Chapter 1',
        content: 'Chapter content here',
        trace_data: [],
      };

      expect(chapter.id).toBe('chapter-1');
      expect(chapter.content).toBe('Chapter content here');
    });

    it('should handle chapter with trace data', () => {
      const chapter: Chapter = {
        id: 'chapter-1',
        title: 'Chapter 1',
        content: 'Content',
        trace_data: [
          {
            text: 'Generated text',
            source_agent: 'writer',
            revisions: ['revision 1', 'revision 2'],
          },
        ],
      };

      expect(chapter.trace_data).toHaveLength(1);
      expect(chapter.trace_data[0].source_agent).toBe('writer');
    });
  });

  describe('Agent interface', () => {
    it('should create a valid agent object', () => {
      const agent: Agent = {
        id: 'agent-1',
        name: 'Writer Agent',
        role: 'writer',
        prompt: 'You are a writer',
        temperature: 0.7,
        enabled: true,
        personality: 'creative',
      };

      expect(agent.id).toBe('agent-1');
      expect(agent.role).toBe('writer');
      expect(agent.enabled).toBe(true);
    });
  });

  describe('WorkspaceModule type', () => {
    it('should accept valid workspace modules', () => {
      const modules = [
        'novels',
        'agent-management',
        'story-assets',
        'skills',
        'settings',
        'recycle-bin',
        'performance',
      ];

      modules.forEach((module) => {
        expect(typeof module).toBe('string');
      });
    });
  });
});
