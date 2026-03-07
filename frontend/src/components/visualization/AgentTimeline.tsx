"use client";

import React, { useState, useEffect } from "react";

interface AgentExecution {
  id: string;
  agent: string;
  status: "pending" | "running" | "completed" | "error";
  startTime?: string;
  endTime?: string;
  thought?: string;
  output?: any;
  score?: number;
}

interface QualityScore {
  logic_consistency: number;
  plot_tension: number;
  prose_quality: number;
  character_voice: number;
  world_consistency: number;
  total: number;
}

export const AgentTimeline: React.FC<{
  workflowId?: string;
  onComplete?: () => void;
}> = ({ workflowId, onComplete }) => {
  const [executions, setExecutions] = useState<AgentExecution[]>([]);
  const [currentQuality, setCurrentQuality] = useState<QualityScore | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  // 模拟执行数据（实际应该从 SSE 获取）
  useEffect(() => {
    if (!workflowId) {
      // 演示模式
      const demoExecutions: AgentExecution[] = [
        { id: "1", agent: "Planner", status: "completed", startTime: "10:00:00", endTime: "10:00:05", thought: "为了提高冲突，我让主角发现叛徒" },
        { id: "2", agent: "Conflict", status: "completed", startTime: "10:00:05", endTime: "10:00:08", output: { tension_score: 0.75 } },
        { id: "3", agent: "Writing", status: "running", startTime: "10:00:08" },
        { id: "4", agent: "Editor", status: "pending" },
        { id: "5", agent: "Reader", status: "pending" },
        { id: "6", agent: "Critic", status: "pending" },
      ];
      setExecutions(demoExecutions);
    } else {
      // 连接 SSE
      connectToExecutionStream(workflowId);
    }
  }, [workflowId]);

  const connectToExecutionStream = (id: string) => {
    const eventSource = new EventSource(`http://localhost:8000/api/stream/execution/${id}`);
    
    eventSource.onopen = () => setIsConnected(true);
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === "agent_start") {
        setExecutions((prev) => [
          ...prev,
          {
            id: data.timestamp,
            agent: data.agent,
            status: "running",
            startTime: data.timestamp,
          },
        ]);
      } else if (data.type === "agent_thinking") {
        setExecutions((prev) =>
          prev.map((ex) =>
            ex.agent === data.agent && ex.status === "running"
              ? { ...ex, thought: data.thought }
              : ex
          )
        );
      } else if (data.type === "agent_complete") {
        setExecutions((prev) =>
          prev.map((ex) =>
            ex.agent === data.agent && ex.status === "running"
              ? { ...ex, status: "completed", endTime: data.timestamp, output: data.output }
              : ex
          )
        );
      } else if (data.type === "quality_check") {
        setCurrentQuality({
          ...data.breakdown,
          total: data.score,
        });
      } else if (data.type === "complete") {
        onComplete?.();
        eventSource.close();
      }
    };

    eventSource.onerror = () => {
      setIsConnected(false);
      eventSource.close();
    };

    return () => eventSource.close();
  };

  const getAgentIcon = (agent: string) => {
    const icons: Record<string, string> = {
      Planner: "📋",
      Conflict: "⚔️",
      Writing: "✍️",
      Editor: "📝",
      Reader: "👁️",
      Critic: "⭐",
      Summary: "📚",
    };
    return icons[agent] || "🤖";
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-emerald-500";
      case "running":
        return "bg-indigo-500 animate-pulse";
      case "error":
        return "bg-red-500";
      default:
        return "bg-zinc-300";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return "✓";
      case "running":
        return "⏳";
      case "error":
        return "✗";
      default:
        return "○";
    }
  };

  return (
    <div className="bg-white rounded-xl border border-zinc-200 overflow-hidden">
      {/* 头部 */}
      <div className="bg-zinc-50 px-4 py-3 border-b border-zinc-200">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-zinc-800">Agent 执行时间线</h3>
          <div className="flex items-center gap-2">
            {isConnected && (
              <span className="flex items-center gap-1 text-xs text-emerald-600">
                <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                实时
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 时间线 */}
      <div className="p-4">
        <div className="space-y-4">
          {executions.map((execution, index) => (
            <div key={execution.id} className="flex gap-4">
              {/* 左侧：状态和时间 */}
              <div className="flex flex-col items-center">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold ${getStatusColor(
                    execution.status
                  )}`}
                >
                  {getStatusIcon(execution.status)}
                </div>
                {index < executions.length - 1 && (
                  <div className="w-0.5 h-full bg-zinc-200 my-1" />
                )}
              </div>

              {/* 右侧：内容 */}
              <div className="flex-1 pb-4">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">{getAgentIcon(execution.agent)}</span>
                  <span className="font-bold text-zinc-800">{execution.agent}</span>
                  <span className="text-xs text-zinc-400">
                    {execution.startTime && new Date(execution.startTime).toLocaleTimeString()}
                  </span>
                </div>

                {/* 思考气泡 */}
                {execution.thought && (
                  <div className="mt-2 p-3 bg-blue-50 border border-blue-100 rounded-lg">
                    <div className="flex items-start gap-2">
                      <span className="text-blue-400">💭</span>
                      <p className="text-sm text-blue-700 italic">{execution.thought}</p>
                    </div>
                  </div>
                )}

                {/* 输出结果 */}
                {execution.output && (
                  <div className="mt-2 p-3 bg-zinc-50 border border-zinc-100 rounded-lg">
                    {execution.output.tension_score && (
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-zinc-600">张力分数:</span>
                        <div className="flex-1 h-2 bg-zinc-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-orange-500"
                            style={{ width: `${execution.output.tension_score * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium text-zinc-700">
                          {Math.round(execution.output.tension_score * 100)}%
                        </span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 质量评分 */}
      {currentQuality && (
        <div className="border-t border-zinc-200 p-4 bg-zinc-50">
          <h4 className="font-bold text-zinc-800 mb-3">质量评估</h4>
          <div className="grid grid-cols-2 gap-3">
            <ScoreBar label="逻辑一致性" score={currentQuality.logic_consistency} color="bg-blue-500" />
            <ScoreBar label="剧情张力" score={currentQuality.plot_tension} color="bg-orange-500" />
            <ScoreBar label="文笔质量" score={currentQuality.prose_quality} color="bg-green-500" />
            <ScoreBar label="角色声音" score={currentQuality.character_voice} color="bg-purple-500" />
            <ScoreBar label="世界观一致性" score={currentQuality.world_consistency} color="bg-yellow-500" />
            <div className="col-span-2 pt-2 border-t border-zinc-200">
              <div className="flex items-center justify-between">
                <span className="font-bold text-zinc-800">总分</span>
                <span className={`text-2xl font-bold ${
                  currentQuality.total >= 0.8 ? "text-emerald-600" :
                  currentQuality.total >= 0.6 ? "text-yellow-600" : "text-red-600"
                }`}>
                  {Math.round(currentQuality.total * 100)}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// 评分条组件
const ScoreBar: React.FC<{
  label: string;
  score: number;
  color: string;
}> = ({ label, score, color }) => (
  <div>
    <div className="flex items-center justify-between mb-1">
      <span className="text-xs text-zinc-600">{label}</span>
      <span className="text-xs font-medium text-zinc-700">{Math.round(score * 100)}</span>
    </div>
    <div className="h-2 bg-zinc-200 rounded-full overflow-hidden">
      <div
        className={`h-full ${color} transition-all duration-500`}
        style={{ width: `${score * 100}%` }}
      />
    </div>
  </div>
);
