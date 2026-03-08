"use client";

import { useEffect, useState } from "react";

export function StoreProvider({ children }: { children: React.ReactNode }) {
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    // 延迟 hydration，确保 localStorage 数据已加载
    const timer = setTimeout(() => {
      setIsHydrated(true);
    }, 100);
    return () => clearTimeout(timer);
  }, []);

  // 在 hydration 完成前显示空白或加载状态
  if (!isHydrated) {
    return (
      <div className="min-h-screen bg-zinc-50">
        {/* 可以添加一个更精致的加载界面 */}
      </div>
    );
  }

  return <>{children}</>;
}
