"use client";

import { useEffect, useState } from "react";

export function StoreProvider({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // 在客户端挂载前不渲染内容，避免 hydration 不匹配
  if (!mounted) {
    return null;
  }

  return <>{children}</>;
}
