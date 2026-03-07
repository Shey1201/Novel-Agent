/**
 * DownloadDialog 组件测试
 * 测试下载对话框的基本功能
 */

import React from 'react';
import { render } from '@testing-library/react';

// Mock the store before importing the component
const mockNovels: any[] = [];
const mockSetCurrentNovelId = jest.fn();

jest.mock('../../../store/novelStore', () => ({
  useNovelStore: () => ({
    novels: mockNovels,
    setCurrentNovelId: mockSetCurrentNovelId,
  }),
}));

import { DownloadDialog } from '../DownloadDialog';

// Mock fetch
global.fetch = jest.fn();

describe('DownloadDialog 组件测试', () => {
  const mockOnClose = jest.fn();
  const mockNovelId = 'test-novel-1';

  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockClear();
    // Reset mock novels
    mockNovels.length = 0;
  });

  test('对话框关闭时不应该渲染', () => {
    const { container } = render(
      <DownloadDialog
        isOpen={false}
        onClose={mockOnClose}
        novelId={mockNovelId}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  test('当小说不存在时应该返回null', () => {
    // No novels in store
    const { container } = render(
      <DownloadDialog
        isOpen={true}
        onClose={mockOnClose}
        novelId={mockNovelId}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  test('当小说存在时应该正确渲染对话框', () => {
    // Add a novel to the mock store
    mockNovels.push({
      id: mockNovelId,
      title: '测试小说',
      chapters: [
        { id: 'ch1', title: '第一章', content: '<p>内容</p>' },
      ],
    });

    const { getByText } = render(
      <DownloadDialog
        isOpen={true}
        onClose={mockOnClose}
        novelId={mockNovelId}
      />
    );

    expect(getByText('下载小说')).toBeInTheDocument();
  });

  test('关闭按钮应该能关闭对话框', () => {
    // Add a novel to the mock store
    mockNovels.push({
      id: mockNovelId,
      title: '测试小说',
      chapters: [
        { id: 'ch1', title: '第一章', content: '<p>内容</p>' },
      ],
    });

    const { getByText } = render(
      <DownloadDialog
        isOpen={true}
        onClose={mockOnClose}
        novelId={mockNovelId}
      />
    );

    const closeButton = getByText('取消');
    closeButton.click();

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });
});
