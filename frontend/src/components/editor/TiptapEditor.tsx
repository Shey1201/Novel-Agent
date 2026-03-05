"use client";

import { useEffect, useState, forwardRef, useImperativeHandle } from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import { BubbleMenu } from "@tiptap/react/menus";
import StarterKit from "@tiptap/starter-kit";
import Highlight from "@tiptap/extension-highlight";
import BubbleMenuExtension from "@tiptap/extension-bubble-menu";
import { useNovelStore } from "@/store/novelStore";

export const TiptapEditor = forwardRef((props, ref) => {
  const { novels, currentNovelId, currentChapterId, updateChapterContent, addMessage } = useNovelStore();
  const currentNovel = novels.find(n => n.id === currentNovelId);
  const currentChapter = currentNovel?.chapters.find(c => c.id === currentChapterId);
  
  const [selectedTrace, setSelectedTrace] = useState<any>(null);

  const editor = useEditor({
    extensions: [
      StarterKit,
      Highlight.configure({ multicolor: true }),
      BubbleMenuExtension,
    ],
    content: currentChapter?.content || "<p>在这里开始你的小说创作...</p>",
    immediatelyRender: false,
    onUpdate: ({ editor }) => {
      if (currentNovelId && currentChapterId) {
        updateChapterContent(currentNovelId, currentChapterId, editor.getHTML());
      }
    },
    onSelectionUpdate: ({ editor }) => {
      const { from, to } = editor.state.selection;
      const text = editor.state.doc.textBetween(from, to);
      if (text && currentChapter?.trace_data) {
        // 查找对应的 trace data
        const trace = currentChapter.trace_data.find(t => t.text.includes(text) || text.includes(t.text));
        setSelectedTrace(trace);
      } else {
        setSelectedTrace(null);
      }
    }
  });

  // 当当前章节 ID 改变时更新编辑器内容
  useEffect(() => {
    if (editor && currentChapter) {
      const currentContent = editor.getHTML();
      if (currentContent !== currentChapter.content) {
        editor.commands.setContent(currentChapter.content || "<p>在这里开始你的小说创作...</p>", { emitUpdate: false });
      }
    }
  }, [currentChapterId, editor]);

  // 公开 handleRunAgents 方法
  useImperativeHandle(ref, () => ({
    handleRunAgents: async () => {
      const { agentConfigs, constraints } = useNovelStore.getState();
      if (!editor) return;
      const outline = editor.getText();
      try {
        const res = await fetch("http://127.0.0.1:8000/generate_chapter", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ 
            outline,
            agent_configs: agentConfigs,
            constraints: constraints
          }),
        });
        const data = await res.json();

        if (data?.final_text) {
          editor.commands.setContent(data.final_text, { emitUpdate: false });
          if (currentNovelId && currentChapterId) {
            updateChapterContent(currentNovelId, currentChapterId, data.final_text, data.trace_data);
          }
        }
        if (Array.isArray(data?.agent_logs)) {
          data.agent_logs.forEach((log: any) => {
            addMessage({
              id: Math.random().toString(36).substring(7),
              sender: log.agent,
              role: 'agent',
              content: log.message,
              timestamp: Date.now()
            });
          });
        }
      } catch (error) {
        console.error("Failed to run agents:", error);
      }
    }
  }));

  return (
    <div className="w-full h-full relative">
      {editor && (
        <>
          <BubbleMenu editor={editor} shouldShow={({ state }) => !state.selection.empty}>
            {selectedTrace && (
              <div className="bg-zinc-900 text-white p-3 rounded-lg shadow-2xl border border-zinc-700 w-64 animate-in fade-in zoom-in duration-200">
                <div className="flex items-center justify-between mb-2 border-b border-zinc-700 pb-1">
                  <span className="text-[10px] font-bold uppercase text-zinc-400">Agent 溯源</span>
                  <span className="text-[10px] bg-blue-500/20 text-blue-300 px-1.5 py-0.5 rounded border border-blue-500/30">
                    {selectedTrace.source_agent}
                  </span>
                </div>
                
                <div className="space-y-2">
                  <div>
                    <span className="text-[9px] text-zinc-500 block mb-1">修改历史 ({selectedTrace.revisions?.length || 0})</span>
                    {selectedTrace.revisions?.length > 0 ? (
                      <div className="space-y-1 max-h-32 overflow-y-auto pr-1">
                        {selectedTrace.revisions.map((rev: string, i: number) => (
                          <div key={i} className="text-[10px] bg-zinc-800 p-1.5 rounded text-zinc-400 line-through decoration-zinc-600">
                            {rev.substring(0, 50)}...
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-[10px] text-zinc-600 italic">暂无修改历史</div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </BubbleMenu>
          <EditorContent
            editor={editor}
            className="focus:outline-none min-h-[500px] py-4 prose prose-zinc max-w-none"
          />
        </>
      )}
    </div>
  );
});

TiptapEditor.displayName = "TiptapEditor";
