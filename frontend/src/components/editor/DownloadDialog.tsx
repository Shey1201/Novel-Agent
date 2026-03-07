"use client";

import React, { useState } from "react";
import { useNovelStore } from "@/store/novelStore";

interface DownloadDialogProps {
  isOpen: boolean;
  onClose: () => void;
  novelId: string;
}

type DownloadType = "full" | "single" | "range";
type FileFormat = "docx" | "txt" | "md";

export const DownloadDialog: React.FC<DownloadDialogProps> = ({
  isOpen,
  onClose,
  novelId,
}) => {
  const { novels, currentChapterId } = useNovelStore();
  const novel = novels.find((n) => n.id === novelId);

  const [downloadType, setDownloadType] = useState<DownloadType>("full");
  const [selectedChapterId, setSelectedChapterId] = useState<string>(
    currentChapterId || ""
  );
  const [startChapter, setStartChapter] = useState<string>("");
  const [endChapter, setEndChapter] = useState<string>("");
  const [format, setFormat] = useState<FileFormat>("docx");
  const [isDownloading, setIsDownloading] = useState(false);

  // 安全返回 - 如果对话框关闭或小说不存在，不渲染任何内容
  if (!isOpen) return null;
  if (!novel) {
    console.error("DownloadDialog: novel not found for id:", novelId);
    return null;
  }

  // 确保 chapters 存在
  const chapters = novel.chapters || [];
  
  // 如果没有章节，显示提示
  if (chapters.length === 0) {
    return (
      <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50">
        <div className="w-[400px] rounded-lg bg-white p-6 shadow-xl">
          <h2 className="text-lg font-semibold text-zinc-900 mb-4">下载小说</h2>
          <p className="text-zinc-600 mb-4">该小说暂无章节，无法下载。</p>
          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="rounded-md px-4 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-100"
            >
              关闭
            </button>
          </div>
        </div>
      </div>
    );
  }

  const getChapterContent = (chapter: (typeof chapters)[0]) => {
    // 从HTML中提取纯文本
    const div = document.createElement("div");
    div.innerHTML = chapter.content || "";
    return div.textContent || div.innerText || "";
  };

  const generateFileName = () => {
    const timestamp = new Date().toISOString().slice(0, 10);
    const safeTitle = novel.title.replace(/[^a-zA-Z0-9一-龥]/g, "_");

    switch (downloadType) {
      case "full":
        return `${safeTitle}_全文_${timestamp}.${format}`;
      case "single":
        const chapter = chapters.find((c) => c.id === selectedChapterId);
        const chapterName =
          chapter?.title.replace(/[^a-zA-Z0-9一-龥]/g, "_") || "章节";
        return `${safeTitle}_${chapterName}_${timestamp}.${format}`;
      case "range":
        return `${safeTitle}_章节${startChapter}-${endChapter}_${timestamp}.${format}`;
      default:
        return `${safeTitle}_${timestamp}.${format}`;
    }
  };

  const generateContent = () => {
    let content = "";

    // 添加小说标题
    content += `# ${novel.title}\n\n`;

    switch (downloadType) {
      case "full":
        chapters.forEach((chapter, index) => {
          content += `## ${chapter.title}\n\n`;
          content += getChapterContent(chapter);
          content += "\n\n";
          if (index < chapters.length - 1) {
            content += "---\n\n";
          }
        });
        break;

      case "single":
        const chapter = chapters.find((c) => c.id === selectedChapterId);
        if (chapter) {
          content += `## ${chapter.title}\n\n`;
          content += getChapterContent(chapter);
        }
        break;

      case "range":
        const startIdx = parseInt(startChapter) - 1;
        const endIdx = parseInt(endChapter) - 1;

        if (!isNaN(startIdx) && !isNaN(endIdx)) {
          const selectedChapters = chapters.slice(
            Math.max(0, startIdx),
            Math.min(chapters.length, endIdx + 1)
          );

          selectedChapters.forEach((chapter, index) => {
            content += `## ${chapter.title}\n\n`;
            content += getChapterContent(chapter);
            content += "\n\n";
            if (index < selectedChapters.length - 1) {
              content += "---\n\n";
            }
          });
        }
        break;
    }

    return content;
  };

  const downloadTextFile = (content: string, filename: string) => {
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  };

  const downloadWordDocument = async () => {
    setIsDownloading(true);
    try {
      // 准备章节数据
      let selectedChapters: typeof chapters = [];

      if (downloadType === "full") {
        selectedChapters = chapters;
      } else if (downloadType === "single") {
        const chapter = chapters.find((c) => c.id === selectedChapterId);
        if (chapter) selectedChapters = [chapter];
      } else if (downloadType === "range") {
        const startIdx = parseInt(startChapter) - 1;
        const endIdx = parseInt(endChapter) - 1;
        if (!isNaN(startIdx) && !isNaN(endIdx)) {
          selectedChapters = chapters.slice(
            Math.max(0, startIdx),
            Math.min(chapters.length, endIdx + 1)
          );
        }
      }

      // 调用后端API生成Word文档
      const response = await fetch("http://localhost:8000/download/novel", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          novel_title: novel.title,
          chapters: selectedChapters.map((ch) => ({
            id: ch.id,
            title: ch.title,
            content: ch.content || "",
          })),
          download_type: downloadType,
          start_chapter:
            downloadType === "range" ? parseInt(startChapter) : null,
          end_chapter: downloadType === "range" ? parseInt(endChapter) : null,
          single_chapter_id:
            downloadType === "single" ? selectedChapterId : null,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "下载失败");
      }

      // 获取文件名
      const contentDisposition = response.headers.get("content-disposition");
      let filename = generateFileName();
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="(.+)"/);
        if (match) filename = match[1];
      }

      // 下载文件
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      onClose();
    } catch (error) {
      console.error("下载失败:", error);
      alert("下载失败: " + (error instanceof Error ? error.message : "未知错误"));
    } finally {
      setIsDownloading(false);
    }
  };

  const handleDownload = async () => {
    if (format === "docx") {
      await downloadWordDocument();
    } else {
      const content = generateContent();
      const filename = generateFileName();
      downloadTextFile(content, filename);
      onClose();
    }
  };

  const isValid = () => {
    switch (downloadType) {
      case "full":
        return chapters.length > 0;
      case "single":
        return selectedChapterId !== "";
      case "range":
        const start = parseInt(startChapter);
        const end = parseInt(endChapter);
        return (
          !isNaN(start) &&
          !isNaN(end) &&
          start > 0 &&
          end >= start &&
          start <= chapters.length &&
          end <= chapters.length
        );
      default:
        return false;
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50">
      <div className="w-[480px] rounded-lg bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-zinc-900">下载小说</h2>
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-zinc-600"
            disabled={isDownloading}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M18 6 6 18" />
              <path d="m6 6 12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-4">
          {/* 下载类型选择 */}
          <div>
            <label className="mb-2 block text-sm font-medium text-zinc-700">
              下载范围
            </label>
            <div className="space-y-2">
              <label className="flex cursor-pointer items-center gap-2 rounded-md border border-zinc-200 p-3 hover:bg-zinc-50">
                <input
                  type="radio"
                  name="downloadType"
                  value="full"
                  checked={downloadType === "full"}
                  onChange={(e) =>
                    setDownloadType(e.target.value as DownloadType)
                  }
                  className="h-4 w-4 text-indigo-600"
                  disabled={isDownloading}
                />
                <span className="text-sm text-zinc-700">
                  整本小说（全部章节）
                </span>
              </label>

              <label className="flex cursor-pointer items-center gap-2 rounded-md border border-zinc-200 p-3 hover:bg-zinc-50">
                <input
                  type="radio"
                  name="downloadType"
                  value="single"
                  checked={downloadType === "single"}
                  onChange={(e) =>
                    setDownloadType(e.target.value as DownloadType)
                  }
                  className="h-4 w-4 text-indigo-600"
                  disabled={isDownloading}
                />
                <span className="text-sm text-zinc-700">单个章节</span>
              </label>

              {downloadType === "single" && (
                <div className="ml-6">
                  <select
                    value={selectedChapterId}
                    onChange={(e) => setSelectedChapterId(e.target.value)}
                    className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-indigo-500"
                    disabled={isDownloading}
                  >
                    <option value="">请选择章节</option>
                    {chapters.map((chapter, index) => (
                      <option key={chapter.id} value={chapter.id}>
                        第{index + 1}章：{chapter.title}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <label className="flex cursor-pointer items-center gap-2 rounded-md border border-zinc-200 p-3 hover:bg-zinc-50">
                <input
                  type="radio"
                  name="downloadType"
                  value="range"
                  checked={downloadType === "range"}
                  onChange={(e) =>
                    setDownloadType(e.target.value as DownloadType)
                  }
                  className="h-4 w-4 text-indigo-600"
                  disabled={isDownloading}
                />
                <span className="text-sm text-zinc-700">章节范围</span>
              </label>

              {downloadType === "range" && (
                <div className="ml-6 flex items-center gap-2">
                  <input
                    type="number"
                    value={startChapter}
                    onChange={(e) => setStartChapter(e.target.value)}
                    placeholder="起始章节"
                    min="1"
                    max={chapters.length}
                    className="w-24 rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-indigo-500"
                    disabled={isDownloading}
                  />
                  <span className="text-zinc-500">至</span>
                  <input
                    type="number"
                    value={endChapter}
                    onChange={(e) => setEndChapter(e.target.value)}
                    placeholder="结束章节"
                    min="1"
                    max={chapters.length}
                    className="w-24 rounded-md border border-zinc-300 px-3 py-2 text-sm outline-none focus:border-indigo-500"
                    disabled={isDownloading}
                  />
                  <span className="text-xs text-zinc-400">
                    共 {chapters.length} 章
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* 格式选择 */}
          <div>
            <label className="mb-2 block text-sm font-medium text-zinc-700">
              文件格式
            </label>
            <div className="flex gap-4">
              <label className="flex cursor-pointer items-center gap-2">
                <input
                  type="radio"
                  name="format"
                  value="docx"
                  checked={format === "docx"}
                  onChange={(e) => setFormat(e.target.value as FileFormat)}
                  className="h-4 w-4 text-indigo-600"
                  disabled={isDownloading}
                />
                <span className="text-sm text-zinc-700">.docx Word文档</span>
              </label>
              <label className="flex cursor-pointer items-center gap-2">
                <input
                  type="radio"
                  name="format"
                  value="txt"
                  checked={format === "txt"}
                  onChange={(e) => setFormat(e.target.value as FileFormat)}
                  className="h-4 w-4 text-indigo-600"
                  disabled={isDownloading}
                />
                <span className="text-sm text-zinc-700">.txt 纯文本</span>
              </label>
              <label className="flex cursor-pointer items-center gap-2">
                <input
                  type="radio"
                  name="format"
                  value="md"
                  checked={format === "md"}
                  onChange={(e) => setFormat(e.target.value as FileFormat)}
                  className="h-4 w-4 text-indigo-600"
                  disabled={isDownloading}
                />
                <span className="text-sm text-zinc-700">.md Markdown</span>
              </label>
            </div>
          </div>
        </div>

        {/* 按钮 */}
        <div className="mt-6 flex justify-end gap-2">
          <button
            onClick={onClose}
            disabled={isDownloading}
            className="rounded-md px-4 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-100 disabled:opacity-50"
          >
            取消
          </button>
          <button
            onClick={handleDownload}
            disabled={!isValid() || isDownloading}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:bg-zinc-300 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isDownloading ? (
              <>
                <svg
                  className="animate-spin h-4 w-4"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                生成中...
              </>
            ) : (
              "下载"
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
