"use client";

import React, { useState, useCallback } from "react";
import { DiffView } from "@/components/visualization/DiffView";

interface EditorDiffProps {
  originalText: string;
  modifiedText: string;
  onAccept?: () => void;
  onReject?: () => void;
  onModify?: (text: string) => void;
  title?: string;
  description?: string;
}

/**
 * 编辑器差异对比组件
 * 用于显示AI修改建议并与原文对比
 */
export const EditorDiff: React.FC<EditorDiffProps> = ({
  originalText,
  modifiedText,
  onAccept,
  onReject,
  onModify,
  title = "修改建议",
  description = "AI 提出了以下修改建议，请查看并决定是否接受",
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [activeTab, setActiveTab] = useState<"diff" | "preview">("diff");

  const handleAccept = useCallback(() => {
    onAccept?.();
  }, [onAccept]);

  const handleReject = useCallback(() => {
    onReject?.();
  }, [onReject]);

  const hasChanges = originalText !== modifiedText;

  if (!hasChanges) {
    return (
      <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <p className="text-gray-600 dark:text-gray-400">没有检测到修改</p>
      </div>
    );
  }

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden bg-white dark:bg-gray-900">
      {/* 头部 */}
      <div className="px-4 py-3 bg-blue-50 dark:bg-blue-900/20 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <svg
              className="w-5 h-5 text-blue-600 dark:text-blue-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
              />
            </svg>
            <h3 className="font-medium text-gray-900 dark:text-gray-100">{title}</h3>
          </div>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <svg
              className={`w-5 h-5 transform transition-transform ${
                isExpanded ? "rotate-180" : ""
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
        </div>
        {description && (
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">{description}</p>
        )}
      </div>

      {/* 内容 */}
      {isExpanded && (
        <>
          {/* 标签页 */}
          <div className="flex border-b border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setActiveTab("diff")}
              className={`flex-1 px-4 py-2 text-sm font-medium ${
                activeTab === "diff"
                  ? "text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
              }`}
            >
              差异对比
            </button>
            <button
              onClick={() => setActiveTab("preview")}
              className={`flex-1 px-4 py-2 text-sm font-medium ${
                activeTab === "preview"
                  ? "text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
              }`}
            >
              预览效果
            </button>
          </div>

          {/* 差异视图 */}
          {activeTab === "diff" && (
            <div className="p-4">
              <DiffView
                oldText={originalText}
                newText={modifiedText}
                oldLabel="原文"
                newLabel="修改后"
                showLineNumbers={false}
              />
            </div>
          )}

          {/* 预览视图 */}
          {activeTab === "preview" && (
            <div className="p-4">
              <div className="prose dark:prose-invert max-w-none">
                <div className="whitespace-pre-wrap text-gray-800 dark:text-gray-200">
                  {modifiedText}
                </div>
              </div>
            </div>
          )}

          {/* 操作按钮 */}
          <div className="flex items-center justify-end space-x-3 px-4 py-3 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={handleReject}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
            >
              拒绝
            </button>
            <button
              onClick={handleAccept}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
            >
              接受修改
            </button>
          </div>
        </>
      )}
    </div>
  );
};

/**
 * 修改历史记录组件
 */
export interface Revision {
  id: string;
  timestamp: string;
  author: string;
  summary: string;
  content: string;
}

interface RevisionHistoryProps {
  revisions: Revision[];
  currentIndex: number;
  onSelect: (index: number) => void;
  onCompare: (index1: number, index2: number) => void;
}

export const RevisionHistory: React.FC<RevisionHistoryProps> = ({
  revisions,
  currentIndex,
  onSelect,
  onCompare,
}) => {
  const [compareMode, setCompareMode] = useState(false);
  const [selectedIndices, setSelectedIndices] = useState<number[]>([]);

  const handleSelect = (index: number) => {
    if (compareMode) {
      if (selectedIndices.includes(index)) {
        setSelectedIndices(selectedIndices.filter((i) => i !== index));
      } else if (selectedIndices.length < 2) {
        const newIndices = [...selectedIndices, index];
        setSelectedIndices(newIndices);
        if (newIndices.length === 2) {
          onCompare(newIndices[0], newIndices[1]);
        }
      }
    } else {
      onSelect(index);
    }
  };

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      {/* 头部 */}
      <div className="px-4 py-3 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <h3 className="font-medium text-gray-900 dark:text-gray-100">修改历史</h3>
        <button
          onClick={() => {
            setCompareMode(!compareMode);
            setSelectedIndices([]);
          }}
          className={`text-sm px-3 py-1 rounded ${
            compareMode
              ? "bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300"
              : "text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"
          }`}
        >
          {compareMode ? "取消对比" : "对比模式"}
        </button>
      </div>

      {/* 版本列表 */}
      <div className="max-h-64 overflow-y-auto">
        {revisions.map((revision, index) => {
          const isSelected = index === currentIndex;
          const isCompareSelected = selectedIndices.includes(index);

          return (
            <div
              key={revision.id}
              onClick={() => handleSelect(index)}
              className={`px-4 py-3 border-b border-gray-100 dark:border-gray-800 cursor-pointer transition-colors ${
                isSelected
                  ? "bg-blue-50 dark:bg-blue-900/20"
                  : isCompareSelected
                  ? "bg-green-50 dark:bg-green-900/20"
                  : "hover:bg-gray-50 dark:hover:bg-gray-800"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {compareMode && isCompareSelected && (
                    <span className="w-5 h-5 flex items-center justify-center bg-green-500 text-white text-xs rounded-full">
                      {selectedIndices.indexOf(index) + 1}
                    </span>
                  )}
                  <span className="font-medium text-gray-900 dark:text-gray-100">
                    {revision.author}
                  </span>
                </div>
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {new Date(revision.timestamp).toLocaleString()}
                </span>
              </div>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                {revision.summary}
              </p>
            </div>
          );
        })}
      </div>

      {compareMode && selectedIndices.length > 0 && (
        <div className="px-4 py-2 bg-gray-50 dark:bg-gray-800 text-sm text-gray-600 dark:text-gray-400">
          已选择 {selectedIndices.length}/2 个版本
        </div>
      )}
    </div>
  );
};

export default EditorDiff;
