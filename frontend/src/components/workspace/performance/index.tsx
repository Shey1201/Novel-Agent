"use client";

import React, { useState, useEffect } from "react";
import { API_BASE } from "@/lib/api";

interface PerformanceStats {
  count: number;
  avg: number;
  min: number;
  max: number;
  p50: number;
  p95: number;
  p99: number;
}

interface PerformanceData {
  [path: string]: PerformanceStats;
}

export default function PerformanceDashboard() {
  const [performanceData, setPerformanceData] = useState<PerformanceData>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [refreshInterval, setRefreshInterval] = useState<number>(30);

  const fetchPerformanceData = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/debug/performance`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setPerformanceData(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取性能数据失败");
    } finally {
      setLoading(false);
    }
  };

  const clearPerformanceStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/debug/performance`, {
        method: "DELETE",
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      await fetchPerformanceData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "清除性能数据失败");
    }
  };

  useEffect(() => {
    fetchPerformanceData();
    const interval = setInterval(fetchPerformanceData, refreshInterval * 1000);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const formatDuration = (ms: number) => {
    if (ms < 1) return `${(ms * 1000).toFixed(2)}μs`;
    if (ms < 1000) return `${ms.toFixed(2)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const sortedPaths = Object.entries(performanceData).sort(
    ([, a], [, b]) => b.avg - a.avg
  );

  const totalRequests = sortedPaths.reduce((sum, [, stats]) => sum + stats.count, 0);
  const avgResponseTime =
    sortedPaths.length > 0
      ? sortedPaths.reduce((sum, [, stats]) => sum + stats.avg, 0) / sortedPaths.length
      : 0;

  return (
    <div className="h-full flex flex-col bg-zinc-50">
      {/* 头部 */}
      <div className="px-6 py-4 border-b border-zinc-200 bg-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-zinc-800">性能监控</h1>
            <p className="text-sm text-zinc-500 mt-1">
              实时监控API响应时间和性能指标
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm text-zinc-600">刷新间隔:</label>
              <select
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(Number(e.target.value))}
                className="px-3 py-1.5 text-sm border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-zinc-500"
              >
                <option value={10}>10秒</option>
                <option value={30}>30秒</option>
                <option value={60}>1分钟</option>
                <option value={300}>5分钟</option>
              </select>
            </div>
            <button
              onClick={fetchPerformanceData}
              className="px-4 py-2 bg-zinc-800 text-white text-sm rounded-lg hover:bg-zinc-700 transition-colors"
            >
              刷新
            </button>
            <button
              onClick={clearPerformanceStats}
              className="px-4 py-2 bg-red-50 text-red-600 text-sm rounded-lg hover:bg-red-100 transition-colors"
            >
              清除数据
            </button>
          </div>
        </div>
      </div>

      {/* 概览卡片 */}
      <div className="px-6 py-4 grid grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-zinc-200">
          <div className="text-sm text-zinc-500">总请求数</div>
          <div className="text-2xl font-semibold text-zinc-800 mt-1">
            {totalRequests.toLocaleString()}
          </div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-zinc-200">
          <div className="text-sm text-zinc-500">API端点数</div>
          <div className="text-2xl font-semibold text-zinc-800 mt-1">
            {sortedPaths.length}
          </div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-zinc-200">
          <div className="text-sm text-zinc-500">平均响应时间</div>
          <div className="text-2xl font-semibold text-zinc-800 mt-1">
            {formatDuration(avgResponseTime)}
          </div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-zinc-200">
          <div className="text-sm text-zinc-500">最后更新</div>
          <div className="text-lg font-semibold text-zinc-800 mt-1">
            {new Date().toLocaleTimeString()}
          </div>
        </div>
      </div>

      {/* 详细列表 */}
      <div className="flex-1 px-6 pb-6 overflow-hidden">
        <div className="bg-white rounded-xl border border-zinc-200 h-full flex flex-col">
          <div className="px-4 py-3 border-b border-zinc-200 bg-zinc-50 rounded-t-xl">
            <h2 className="font-medium text-zinc-800">API性能详情</h2>
          </div>

          {loading ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-zinc-800"></div>
            </div>
          ) : error ? (
            <div className="flex-1 flex items-center justify-center text-red-500">
              {error}
            </div>
          ) : sortedPaths.length === 0 ? (
            <div className="flex-1 flex items-center justify-center text-zinc-400">
              暂无性能数据
            </div>
          ) : (
            <div className="flex-1 overflow-auto">
              <table className="w-full">
                <thead className="bg-zinc-50 sticky top-0">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-zinc-500 uppercase tracking-wider">
                      API路径
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-zinc-500 uppercase tracking-wider">
                      请求数
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-zinc-500 uppercase tracking-wider">
                      平均
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-zinc-500 uppercase tracking-wider">
                      P50
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-zinc-500 uppercase tracking-wider">
                      P95
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-zinc-500 uppercase tracking-wider">
                      P99
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-zinc-500 uppercase tracking-wider">
                      最小
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-zinc-500 uppercase tracking-wider">
                      最大
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-200">
                  {sortedPaths.map(([path, stats]) => (
                    <tr
                      key={path}
                      className="hover:bg-zinc-50 cursor-pointer"
                      onClick={() => setSelectedPath(selectedPath === path ? null : path)}
                    >
                      <td className="px-4 py-3 text-sm text-zinc-800 font-mono">
                        {path}
                      </td>
                      <td className="px-4 py-3 text-sm text-zinc-600 text-right">
                        {stats.count.toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-sm text-zinc-600 text-right">
                        {formatDuration(stats.avg)}
                      </td>
                      <td className="px-4 py-3 text-sm text-zinc-600 text-right">
                        {formatDuration(stats.p50)}
                      </td>
                      <td className="px-4 py-3 text-sm text-zinc-600 text-right">
                        {formatDuration(stats.p95)}
                      </td>
                      <td className="px-4 py-3 text-sm text-zinc-600 text-right">
                        {formatDuration(stats.p99)}
                      </td>
                      <td className="px-4 py-3 text-sm text-zinc-600 text-right">
                        {formatDuration(stats.min)}
                      </td>
                      <td className="px-4 py-3 text-sm text-zinc-600 text-right">
                        {formatDuration(stats.max)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
