/**
 * API 配置
 * 根据环境自动选择 API 基础 URL
 */

// API 基础 URL - 从环境变量读取，默认为本地开发地址
export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

// 构建完整 API URL
export function apiUrl(path: string): string {
  // 如果 path 已经以 http 开头，直接返回
  if (path.startsWith('http')) {
    return path;
  }
  // 如果 path 不以 / 开头，添加 /
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE}${normalizedPath}`;
}

// WebSocket URL
export function wsUrl(path: string): string {
  if (path.startsWith('ws')) {
    return path;
  }
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  // 将 http 替换为 ws
  const wsBase = API_BASE.replace('https://', 'wss://').replace('http://', 'ws://');
  return `${wsBase}${normalizedPath}`;
}
