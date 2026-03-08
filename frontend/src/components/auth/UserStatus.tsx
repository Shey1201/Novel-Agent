"use client";

import { useState } from "react";
import { useSupabaseStore } from "@/store/supabaseStore";
import { AuthModal } from "./AuthModal";

export function UserStatus() {
  const [showAuthModal, setShowAuthModal] = useState(false);
  const { user, isAuthenticated, signOut, isLoading } = useSupabaseStore();

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-zinc-500">
        <div className="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        加载中...
      </div>
    );
  }

  if (isAuthenticated && user) {
    return (
      <>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-indigo-50 rounded-lg">
            <div className="w-6 h-6 bg-indigo-600 rounded-full flex items-center justify-center text-white text-xs font-medium">
              {user.email?.[0].toUpperCase()}
            </div>
            <span className="text-sm text-zinc-700 truncate max-w-[120px]">
              {user.email}
            </span>
          </div>
          <button
            onClick={() => signOut()}
            className="text-xs text-zinc-500 hover:text-zinc-700 px-2 py-1 rounded hover:bg-zinc-100 transition-colors"
          >
            退出
          </button>
        </div>
        <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />
      </>
    );
  }

  return (
    <>
      <button
        onClick={() => setShowAuthModal(true)}
        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
        登录 / 注册
      </button>
      <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />
    </>
  );
}
