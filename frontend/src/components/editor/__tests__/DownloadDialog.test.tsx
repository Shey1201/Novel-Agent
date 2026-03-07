/**
 * DownloadDialog 组件测试
 * 测试下载对话框的各项功能
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DownloadDialog } from '../DownloadDialog';

// Mock fetch
global.fetch = jest.fn();

describe('DownloadDialog 组件测试', () => {
  const mockOnClose = jest.fn();
  const mockNovelId = 'test-novel-1';

  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockClear();
  });

  test('应该正确渲染对话框', () => {
    render(
      <DownloadDialog
        isOpen={true}
        onClose={mockOnClose}
        novelId={mockNovelId}
      />
    );

    expect(screen.getByText('下载小说')).toBeInTheDocument();
    expect(screen.getByText('下载范围')).toBeInTheDocument();
    expect(screen.getByText('文件格式')).toBeInTheDocument();
  });

  test('关闭按钮应该能关闭对话框', () => {
    render(
      <DownloadDialog
        isOpen={true}
        onClose={mockOnClose}
        novelId={mockNovelId}
      />
    );

    const closeButton = screen.getByText('取消');
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  test('点击遮罩层应该能关闭对话框', () => {
    render(
      <DownloadDialog
        isOpen={true}
        onClose={mockOnClose}
        novelId={mockNovelId}
      />
    );

    const overlay = screen.getByTestId('dialog-overlay');
    fireEvent.click(overlay);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  test('应该能选择下载范围', () => {
    render(
      <DownloadDialog
        isOpen={true}
        onClose={mockOnClose}
        novelId={mockNovelId}
      />
    );

    const fullRadio = screen.getByLabelText('全部章节');
    const singleRadio = screen.getByLabelText('单章');
    const rangeRadio = screen.getByLabelText('章节范围');

    expect(fullRadio).toBeInTheDocument();
    expect(singleRadio).toBeInTheDocument();
    expect(rangeRadio).toBeInTheDocument();

    // 默认选中全部章节
    expect(fullRadio).toBeChecked();
  });

  test('应该能选择文件格式', () => {
    render(
      <DownloadDialog
        isOpen={true}
        onClose={mockOnClose}
        novelId={mockNovelId}
      />
    );

    const txtRadio = screen.getByLabelText('TXT 文本');
    const mdRadio = screen.getByLabelText('Markdown');
    const docxRadio = screen.getByLabelText('Word 文档');

    expect(txtRadio).toBeInTheDocument();
    expect(mdRadio).toBeInTheDocument();
    expect(docxRadio).toBeInTheDocument();
  });

  test('isOpen为false时不应该渲染', () => {
    const { container } = render(
      <DownloadDialog
        isOpen={false}
        onClose={mockOnClose}
        novelId={mockNovelId}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  test('下载按钮应该触发下载', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(new Blob(['test content'])),
      headers: new Headers({
        'content-disposition': 'attachment; filename="test.docx"',
      }),
    });

    render(
      <DownloadDialog
        isOpen={true}
        onClose={mockOnClose}
        novelId={mockNovelId}
      />
    );

    const downloadButton = screen.getByText('下载');
    fireEvent.click(downloadButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        'http://127.0.0.1:8000/download/novel',
        expect.any(Object)
      );
    });
  });

  test('下载失败应该显示错误信息', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(
      <DownloadDialog
        isOpen={true}
        onClose={mockOnClose}
        novelId={mockNovelId}
      />
    );

    const downloadButton = screen.getByText('下载');
    fireEvent.click(downloadButton);

    await waitFor(() => {
      expect(screen.getByText(/下载失败/)).toBeInTheDocument();
    });
  });
});
