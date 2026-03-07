"use client";

import React, { useState, useMemo } from "react";

interface DiffLine {
  type: "unchanged" | "added" | "removed" | "modified";
  oldLine?: number;
  newLine?: number;
  oldContent?: string;
  newContent?: string;
  content?: string;
}

interface DiffViewProps {
  oldText: string;
  newText: string;
  oldLabel?: string;
  newLabel?: string;
  showLineNumbers?: boolean;
  highlightSyntax?: boolean;
  splitView?: boolean;
  className?: string;
}

/**
 * 计算两个文本的差异
 * 使用简单的行级差异算法
 */
function computeDiff(oldText: string, newText: string): DiffLine[] {
  const oldLines = oldText.split("\n");
  const newLines = newText.split("\n");
  const diff: DiffLine[] = [];

  let oldIndex = 0;
  let newIndex = 0;

  while (oldIndex < oldLines.length || newIndex < newLines.length) {
    const oldLine = oldLines[oldIndex];
    const newLine = newLines[newIndex];

    if (oldIndex >= oldLines.length) {
      // 新增行
      diff.push({
        type: "added",
        newLine: newIndex + 1,
        newContent: newLine,
        content: newLine,
      });
      newIndex++;
    } else if (newIndex >= newLines.length) {
      // 删除行
      diff.push({
        type: "removed",
        oldLine: oldIndex + 1,
        oldContent: oldLine,
        content: oldLine,
      });
      oldIndex++;
    } else if (oldLine === newLine) {
      // 未变更
      diff.push({
        type: "unchanged",
        oldLine: oldIndex + 1,
        newLine: newIndex + 1,
        content: oldLine,
      });
      oldIndex++;
      newIndex++;
    } else {
      // 检查是否是修改
      const similarity = calculateSimilarity(oldLine, newLine);

      if (similarity > 0.5) {
        // 视为修改
        diff.push({
          type: "modified",
          oldLine: oldIndex + 1,
          newLine: newIndex + 1,
          oldContent: oldLine,
          newContent: newLine,
          content: newLine,
        });
        oldIndex++;
        newIndex++;
      } else {
        // 检查接下来几行是否有匹配
        const oldMatchInNew = findLineInArray(oldLine, newLines, newIndex + 1, 3);
        const newMatchInOld = findLineInArray(newLine, oldLines, oldIndex + 1, 3);

        if (oldMatchInNew !== -1 && (newMatchInOld === -1 || oldMatchInNew < newMatchInOld)) {
          // 新增行
          diff.push({
            type: "added",
            newLine: newIndex + 1,
            newContent: newLine,
            content: newLine,
          });
          newIndex++;
        } else if (newMatchInOld !== -1) {
          // 删除行
          diff.push({
            type: "removed",
            oldLine: oldIndex + 1,
            oldContent: oldLine,
            content: oldLine,
          });
          oldIndex++;
        } else {
          // 视为修改
          diff.push({
            type: "modified",
            oldLine: oldIndex + 1,
            newLine: newIndex + 1,
            oldContent: oldLine,
            newContent: newLine,
            content: newLine,
          });
          oldIndex++;
          newIndex++;
        }
      }
    }
  }

  return diff;
}

/**
 * 计算两行文本的相似度
 */
function calculateSimilarity(str1: string, str2: string): number {
  const longer = str1.length > str2.length ? str1 : str2;
  const shorter = str1.length > str2.length ? str2 : str1;

  if (longer.length === 0) return 1.0;

  const distance = levenshteinDistance(str1, str2);
  return (longer.length - distance) / longer.length;
}

/**
 * 计算 Levenshtein 距离
 */
function levenshteinDistance(str1: string, str2: string): number {
  const matrix: number[][] = [];

  for (let i = 0; i <= str2.length; i++) {
    matrix[i] = [i];
  }

  for (let j = 0; j <= str1.length; j++) {
    matrix[0][j] = j;
  }

  for (let i = 1; i <= str2.length; i++) {
    for (let j = 1; j <= str1.length; j++) {
      if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        );
      }
    }
  }

  return matrix[str2.length][str1.length];
}

/**
 * 在数组中查找行
 */
function findLineInArray(line: string, array: string[], startIndex: number, maxSearch: number): number {
  const endIndex = Math.min(startIndex + maxSearch, array.length);
  for (let i = startIndex; i < endIndex; i++) {
    if (array[i] === line) return i;
  }
  return -1;
}

/**
 * 高亮行内差异
 */
function highlightInlineDiff(oldText: string, newText: string): { oldHtml: string; newHtml: string } {
  const oldWords = oldText.split(/(\s+)/);
  const newWords = newText.split(/(\s+)/);

  let oldHtml = "";
  let newHtml = "";

  let oldIndex = 0;
  let newIndex = 0;

  while (oldIndex < oldWords.length || newIndex < newWords.length) {
    const oldWord = oldWords[oldIndex];
    const newWord = newWords[newIndex];

    if (oldIndex >= oldWords.length) {
      newHtml += `<span class="bg-green-200 dark:bg-green-900">${escapeHtml(newWord)}</span>`;
      newIndex++;
    } else if (newIndex >= newWords.length) {
      oldHtml += `<span class="bg-red-200 dark:bg-red-900 line-through">${escapeHtml(oldWord)}</span>`;
      oldIndex++;
    } else if (oldWord === newWord) {
      oldHtml += escapeHtml(oldWord);
      newHtml += escapeHtml(newWord);
      oldIndex++;
      newIndex++;
    } else {
      oldHtml += `<span class="bg-red-200 dark:bg-red-900 line-through">${escapeHtml(oldWord)}</span>`;
      newHtml += `<span class="bg-green-200 dark:bg-green-900">${escapeHtml(newWord)}</span>`;
      oldIndex++;
      newIndex++;
    }
  }

  return { oldHtml, newHtml };
}

/**
 * 转义 HTML 特殊字符
 */
function escapeHtml(text: string): string {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Diff 视图组件
 */
export const DiffView: React.FC<DiffViewProps> = ({
  oldText,
  newText,
  oldLabel = "旧版本",
  newLabel = "新版本",
  showLineNumbers = true,
  splitView = false,
  className = "",
}) => {
  const [viewMode, setViewMode] = useState<"unified" | "split">(splitView ? "split" : "unified");
  const [showUnchanged, setShowUnchanged] = useState(true);

  const diff = useMemo(() => computeDiff(oldText, newText), [oldText, newText]);

  const stats = useMemo(() => {
    const added = diff.filter((d) => d.type === "added").length;
    const removed = diff.filter((d) => d.type === "removed").length;
    const modified = diff.filter((d) => d.type === "modified").length;
    const unchanged = diff.filter((d) => d.type === "unchanged").length;
    return { added, removed, modified, unchanged };
  }, [diff]);

  const filteredDiff = useMemo(() => {
    if (showUnchanged) return diff;
    return diff.filter((d) => d.type !== "unchanged");
  }, [diff, showUnchanged]);

  const renderUnifiedView = () => (
    <div className="overflow-x-auto">
      <table className="w-full text-sm font-mono">
        <tbody>
          {filteredDiff.map((line, index) => {
            const lineClass = {
              unchanged: "bg-white dark:bg-gray-900",
              added: "bg-green-50 dark:bg-green-900/20",
              removed: "bg-red-50 dark:bg-red-900/20",
              modified: "bg-yellow-50 dark:bg-yellow-900/20",
            }[line.type];

            const lineIndicator = {
              unchanged: "",
              added: "+",
              removed: "−",
              modified: "~",
            }[line.type];

            return (
              <tr key={index} className={lineClass}>
                {showLineNumbers && (
                  <>
                    <td className="px-2 py-1 text-right text-gray-400 select-none w-12">
                      {line.oldLine || ""}
                    </td>
                    <td className="px-2 py-1 text-right text-gray-400 select-none w-12 border-r border-gray-200 dark:border-gray-700">
                      {line.newLine || ""}
                    </td>
                  </>
                )}
                <td className="px-2 py-1 text-gray-400 select-none w-6 text-center">
                  {lineIndicator}
                </td>
                <td className="px-2 py-1 whitespace-pre-wrap">
                  {line.type === "modified" && line.oldContent && line.newContent ? (
                    <ModifiedLine oldContent={line.oldContent} newContent={line.newContent} />
                  ) : (
                    escapeHtml(line.content || "")
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );

  const renderSplitView = () => {
    // 为分栏视图准备数据
    const leftLines: DiffLine[] = [];
    const rightLines: DiffLine[] = [];

    filteredDiff.forEach((line) => {
      if (line.type === "unchanged") {
        leftLines.push(line);
        rightLines.push(line);
      } else if (line.type === "removed") {
        leftLines.push(line);
        rightLines.push({ type: "unchanged", content: "" });
      } else if (line.type === "added") {
        leftLines.push({ type: "unchanged", content: "" });
        rightLines.push(line);
      } else if (line.type === "modified") {
        leftLines.push({ ...line, type: "removed" });
        rightLines.push({ ...line, type: "added" });
      }
    });

    return (
      <div className="flex overflow-x-auto">
        {/* 左侧 - 旧版本 */}
        <div className="flex-1 border-r border-gray-200 dark:border-gray-700">
          <div className="bg-gray-100 dark:bg-gray-800 px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400">
            {oldLabel}
          </div>
          <table className="w-full text-sm font-mono">
            <tbody>
              {leftLines.map((line, index) => (
                <tr
                  key={`left-${index}`}
                  className={
                    line.type === "removed"
                      ? "bg-red-50 dark:bg-red-900/20"
                      : "bg-white dark:bg-gray-900"
                  }
                >
                  {showLineNumbers && (
                    <td className="px-2 py-1 text-right text-gray-400 select-none w-12">
                      {line.oldLine || ""}
                    </td>
                  )}
                  <td className="px-2 py-1 whitespace-pre-wrap">
                    {line.type === "modified" && line.oldContent
                      ? escapeHtml(line.oldContent)
                      : escapeHtml(line.content || "")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* 右侧 - 新版本 */}
        <div className="flex-1">
          <div className="bg-gray-100 dark:bg-gray-800 px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400">
            {newLabel}
          </div>
          <table className="w-full text-sm font-mono">
            <tbody>
              {rightLines.map((line, index) => (
                <tr
                  key={`right-${index}`}
                  className={
                    line.type === "added"
                      ? "bg-green-50 dark:bg-green-900/20"
                      : "bg-white dark:bg-gray-900"
                  }
                >
                  {showLineNumbers && (
                    <td className="px-2 py-1 text-right text-gray-400 select-none w-12">
                      {line.newLine || ""}
                    </td>
                  )}
                  <td className="px-2 py-1 whitespace-pre-wrap">
                    {line.type === "modified" && line.newContent
                      ? escapeHtml(line.newContent)
                      : escapeHtml(line.content || "")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  return (
    <div className={`border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden ${className}`}>
      {/* 工具栏 */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-4">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            差异对比
          </span>
          <div className="flex items-center space-x-2 text-xs">
            <span className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded">
              +{stats.added}
            </span>
            <span className="px-2 py-1 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 rounded">
              −{stats.removed}
            </span>
            <span className="px-2 py-1 bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 rounded">
              ~{stats.modified}
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <label className="flex items-center space-x-1 text-sm text-gray-600 dark:text-gray-400">
            <input
              type="checkbox"
              checked={showUnchanged}
              onChange={(e) => setShowUnchanged(e.target.checked)}
              className="rounded border-gray-300"
            />
            <span>显示未变更</span>
          </label>

          <div className="flex border border-gray-200 dark:border-gray-700 rounded">
            <button
              onClick={() => setViewMode("unified")}
              className={`px-3 py-1 text-sm ${
                viewMode === "unified"
                  ? "bg-blue-500 text-white"
                  : "bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400"
              }`}
            >
              统一
            </button>
            <button
              onClick={() => setViewMode("split")}
              className={`px-3 py-1 text-sm ${
                viewMode === "split"
                  ? "bg-blue-500 text-white"
                  : "bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400"
              }`}
            >
              分栏
            </button>
          </div>
        </div>
      </div>

      {/* 差异内容 */}
      <div className="max-h-96 overflow-y-auto">
        {viewMode === "unified" ? renderUnifiedView() : renderSplitView()}
      </div>
    </div>
  );
};

/**
 * 修改行组件 - 显示行内差异
 */
const ModifiedLine: React.FC<{ oldContent: string; newContent: string }> = ({
  oldContent,
  newContent,
}) => {
  const { oldHtml, newHtml } = useMemo(
    () => highlightInlineDiff(oldContent, newContent),
    [oldContent, newContent]
  );

  return (
    <div className="space-y-1">
      <div
        className="text-red-700 dark:text-red-400 line-through opacity-70"
        dangerouslySetInnerHTML={{ __html: oldHtml }}
      />
      <div
        className="text-green-700 dark:text-green-400"
        dangerouslySetInnerHTML={{ __html: newHtml }}
      />
    </div>
  );
};

/**
 * 简化的 Diff 对比组件
 */
export const SimpleDiff: React.FC<{
  before: string;
  after: string;
  className?: string;
}> = ({ before, after, className = "" }) => {
  const isChanged = before !== after;

  if (!isChanged) {
    return <span className={className}>{after}</span>;
  }

  return (
    <span className={className}>
      <span className="text-red-600 dark:text-red-400 line-through mr-2">{before}</span>
      <span className="text-green-600 dark:text-green-400">{after}</span>
    </span>
  );
};

/**
 * 文本对比钩子
 */
export function useTextDiff(oldText: string, newText: string) {
  return useMemo(() => computeDiff(oldText, newText), [oldText, newText]);
}

export default DiffView;
