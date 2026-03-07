import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 允许图片域名
  images: {
    unoptimized: true,
  },
  // 禁用 trailing slash
  trailingSlash: false,
};

export default nextConfig;
