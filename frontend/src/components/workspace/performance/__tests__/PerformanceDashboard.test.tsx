import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import PerformanceDashboard from '../index';

// Mock fetch
global.fetch = jest.fn() as jest.MockedFunction<typeof fetch>;

const mockPerformanceData = {
  '/api/novels': {
    count: 100,
    avg: 0.15,
    min: 0.05,
    max: 0.5,
    p50: 0.12,
    p95: 0.35,
    p99: 0.45,
  },
  '/api/chapters': {
    count: 50,
    avg: 0.25,
    min: 0.1,
    max: 0.8,
    p50: 0.2,
    p95: 0.6,
    p99: 0.75,
  },
};

describe('PerformanceDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => mockPerformanceData,
    } as Response);
  });

  it('renders loading state initially', () => {
    render(<PerformanceDashboard />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders performance data after loading', async () => {
    render(<PerformanceDashboard />);

    await waitFor(() => {
      expect(screen.getByText('/api/novels')).toBeInTheDocument();
    });

    expect(screen.getByText('/api/chapters')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument(); // Total requests
  });

  it('displays correct statistics', async () => {
    render(<PerformanceDashboard />);

    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument(); // API endpoints count
    });

    // Check for summary cards
    expect(screen.getByText('总请求数')).toBeInTheDocument();
    expect(screen.getByText('API端点数')).toBeInTheDocument();
    expect(screen.getByText('平均响应时间')).toBeInTheDocument();
  });

  it('handles refresh button click', async () => {
    render(<PerformanceDashboard />);

    await waitFor(() => {
      expect(screen.getByText('/api/novels')).toBeInTheDocument();
    });

    const refreshButton = screen.getByText('刷新');
    fireEvent.click(refreshButton);

    expect(global.fetch).toHaveBeenCalledTimes(2);
  });

  it('handles clear data button click', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockPerformanceData,
    } as Response).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    } as Response);

    render(<PerformanceDashboard />);

    await waitFor(() => {
      expect(screen.getByText('/api/novels')).toBeInTheDocument();
    });

    const clearButton = screen.getByText('清除数据');
    fireEvent.click(clearButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/debug/performance'),
        expect.objectContaining({ method: 'DELETE' })
      );
    });
  });

  it('handles error state', async () => {
    (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

    render(<PerformanceDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('changes refresh interval', async () => {
    render(<PerformanceDashboard />);

    await waitFor(() => {
      expect(screen.getByText('/api/novels')).toBeInTheDocument();
    });

    const select = screen.getByLabelText('刷新间隔:');
    fireEvent.change(select, { target: { value: '60' } });

    expect(select).toHaveValue('60');
  });

  it('displays empty state when no data', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({}),
    } as Response);

    render(<PerformanceDashboard />);

    await waitFor(() => {
      expect(screen.getByText('暂无性能数据')).toBeInTheDocument();
    });
  });
});
