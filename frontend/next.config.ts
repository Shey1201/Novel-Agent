import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 允许图片域名
  images: {
    unoptimized: true,
  },
  // 禁用 trailing slash
  trailingSlash: false,
  // 输出静态导出
  output: 'export',
  // 设置静态资源前缀
  assetPrefix: ".",
  // 禁用图片优化（静态导出需要）
  distDir: 'dist',
};

export default nextConfig;
