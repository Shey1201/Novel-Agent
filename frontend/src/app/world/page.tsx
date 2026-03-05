"use client";

import { useNovelStore } from "@/store/novelStore";

export default function WorldPage() {
  const { worldBible, worldApproved } = useNovelStore();

  return (
    <main className="p-8 space-y-6">
      <h1 className="text-2xl font-bold">World Bible</h1>
      <p className="text-sm text-zinc-500">状态：{worldApproved ? "已锁定" : "待确认"}</p>
      <section className="space-y-3">
        <h2 className="font-semibold">World</h2>
        <p className="text-sm whitespace-pre-wrap">{worldBible.world_view || "暂无世界观"}</p>
      </section>
      <section className="space-y-3">
        <h2 className="font-semibold">Rules</h2>
        <p className="text-sm whitespace-pre-wrap">{worldBible.rules || "暂无规则"}</p>
      </section>
      <section className="space-y-3">
        <h2 className="font-semibold">Themes</h2>
        <ul className="list-disc pl-6 text-sm">
          {(worldBible.themes || []).map((t) => (
            <li key={t}>{t}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}
