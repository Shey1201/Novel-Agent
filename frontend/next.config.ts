import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 允许图片域名
  images: {
    unoptimized: true,
  },
  // 禁用 trailing slash
  trailingSlash: false,
  // 仅本地开发时代理 /api 到本地后端，线上由 NEXT_PUBLIC_API_URL 指向真实后端
  async rewrites() {
    if (process.env.NODE_ENV !== 'development') return [];
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
    ];
  },
};

export default nextConfig;
