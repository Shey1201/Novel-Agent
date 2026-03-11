import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 允许图片域名
  images: {
    unoptimized: true,
  },
  // 禁用 trailing slash
  trailingSlash: false,
  // 代理 API 请求到后端
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
    ];
  },
};

export default nextConfig;
