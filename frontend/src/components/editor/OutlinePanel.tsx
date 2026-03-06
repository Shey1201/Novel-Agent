"use client";

import { useState } from "react";

export function OutlinePanel() {
  const [activeTab, setActiveTab] = useState<"constraints" | "lab">("constraints");
  const [constraints] = useState([
    "主角不能杀生",
    "每一章必须有一个反转",
    "文风偏向硬核奇幻"
  ]);
  const [agents] = useState([
    { name: "Writing Agent", personality: "沉稳、细腻" },
    { name: "Conflict Agent", personality: "激进、充满张力" },
    { name: "Editor Agent", personality: "严谨、优雅" },
  ]);

  return (
    <div className="flex h-full flex-col gap-4 rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
      <div className="flex border-b border-zinc-100 pb-2 gap-4">
        <button
          onClick={() => setActiveTab("constraints")}
          className={`text-sm font-bold pb-1 transition-colors ${
            activeTab === "constraints" ? "text-blue-600 border-b-2 border-blue-600" : "text-zinc-400 hover:text-zinc-600"
          }`}
        >
          全局写作约束
        </button>
        <button
          onClick={() => setActiveTab("lab")}
          className={`text-sm font-bold pb-1 transition-colors ${
            activeTab === "lab" ? "text-blue-600 border-b-2 border-blue-600" : "text-zinc-400 hover:text-zinc-600"
          }`}
        >
          Agent 实验室
        </button>
      </div>

      {activeTab === "constraints" ? (
        <div className="space-y-4">
          <p className="text-xs text-zinc-500">
            设置小说全局遵循的规则，所有 Agent 都会在处理时参考这些约束。
          </p>
          <div className="space-y-2">
            {constraints.map((c, i) => (
              <div key={i} className="flex items-center gap-2 bg-zinc-50 px-3 py-2 rounded-md border border-zinc-100">
                <div className="w-1.5 h-1.5 rounded-full bg-zinc-400" />
                <span className="text-xs text-zinc-700">{c}</span>
              </div>
            ))}
            <button className="w-full py-2 border border-dashed border-zinc-300 rounded-md text-xs text-zinc-500 hover:bg-zinc-50 transition-colors">
              + 添加新约束
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-xs text-zinc-500">
            调节各 Agent 的性格和行文偏好，打造独特的创作团队。
          </p>
          <div className="space-y-3">
            {agents.map((agent, i) => (
              <div key={i} className="p-3 bg-zinc-50 rounded-lg border border-zinc-100">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-bold text-zinc-800">{agent.name}</span>
                  <span className="text-[10px] text-blue-600 font-medium">调节中</span>
                </div>
                <input
                  type="text"
                  className="w-full bg-white border border-zinc-200 rounded px-2 py-1 text-xs text-zinc-600"
                  value={agent.personality}
                  onChange={() => {}}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-auto pt-4 border-t border-zinc-100">
        <div className="bg-blue-50 p-3 rounded-lg border border-blue-100">
          <h4 className="text-xs font-bold text-blue-800 mb-1">系统状态</h4>
          <p className="text-[10px] text-blue-600 leading-relaxed">
            所有 Agent 已准备就绪。当前使用默认 LLM 驱动。
          </p>
        </div>
      </div>
    </div>
  );
}

