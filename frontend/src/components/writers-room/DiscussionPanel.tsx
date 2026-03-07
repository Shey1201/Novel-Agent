"use client";

import React, { useState, useEffect, useRef } from "react";
import { useNovelStore } from "@/store/novelStore";

interface Message {
  id: string;
  agent_id: string;
  agent_name: string;
  content: string;
  message_type: "proposal" | "suggestion" | "critique" | "consensus" | "interruption" | "summary";
  timestamp: string;
  internal_monologue?: string;
}

interface Discussion {
  id: string;
  proposal: {
    title: string;
    description: string;
  };
  status: string;
  consensus_score: number;
  round: number;
  max_rounds: number;
  messages: Message[];
}

export const WritersRoomPanel: React.FC = () => {
  const { currentNovelId } = useNovelStore();
  const [discussion, setDiscussion] = useState<Discussion | null>(null);
  const [proposalTitle, setProposalTitle] = useState("");
  const [proposalDesc, setProposalDesc] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [discussion?.messages]);

  // 创建新讨论
  const createDiscussion = async () => {
    if (!currentNovelId || !proposalTitle) return;

    try {
      const response = await fetch("http://localhost:8000/api/writers-room/discussions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          novel_id: currentNovelId,
          title: proposalTitle,
          description: proposalDesc,
          max_rounds: 10,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setDiscussion(data);
        connectWebSocket(data.id);
      }
    } catch (error) {
      console.error("Failed to create discussion:", error);
    }
  };

  // 连接 WebSocket
  const connectWebSocket = (discussionId: string) => {
    try {
      const websocket = new WebSocket(`ws://localhost:8000/api/writers-room/ws/${discussionId}`);
      
      websocket.onopen = () => {
        console.log("WebSocket connected");
      };

      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === "new_message") {
            setDiscussion((prev) => {
              if (!prev) return prev;
              return {
                ...prev,
                messages: [...prev.messages, data.data],
              };
            });
          } else if (data.type === "status") {
            setDiscussion(data.data);
          }
        } catch (e) {
          console.error("Failed to parse WebSocket message:", e);
        }
      };

      websocket.onerror = (error) => {
        console.error("WebSocket error:", error);
      };

      websocket.onclose = () => {
        console.log("WebSocket closed");
      };

      setWs(websocket);
    } catch (error) {
      console.error("Failed to connect WebSocket:", error);
    }
  };

  // 清理 WebSocket
  useEffect(() => {
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [ws]);

  // 运行一轮讨论
  const runRound = () => {
    if (!ws || !discussion) return;
    
    setIsRunning(true);
    ws.send(JSON.stringify({ action: "run_round" }));
    
    // 3秒后允许再次运行
    setTimeout(() => setIsRunning(false), 3000);
  };

  // 人工干预
  const intervene = (message: string, action: string) => {
    if (!ws) return;
    
    ws.send(JSON.stringify({
      action: "intervene",
      message,
      intervention_type: action,
    }));
  };

  // 获取 Agent 颜色
  const getAgentColor = (agentName: string) => {
    const colors: Record<string, string> = {
      "Planner": "bg-blue-100 text-blue-700 border-blue-200",
      "Conflict": "bg-red-100 text-red-700 border-red-200",
      "Writing": "bg-green-100 text-green-700 border-green-200",
      "Consistency": "bg-yellow-100 text-yellow-700 border-yellow-200",
      "System": "bg-gray-100 text-gray-700 border-gray-200",
      "作者": "bg-indigo-100 text-indigo-700 border-indigo-200",
    };
    return colors[agentName] || "bg-gray-100 text-gray-700 border-gray-200";
  };

  // 获取消息类型图标
  const getMessageTypeIcon = (type: string) => {
    switch (type) {
      case "proposal":
        return "💡";
      case "suggestion":
        return "💭";
      case "critique":
        return "⚠️";
      case "consensus":
        return "✅";
      case "interruption":
        return "🛑";
      case "summary":
        return "📝";
      default:
        return "💬";
    }
  };

  if (!currentNovelId) {
    return (
      <div className="flex items-center justify-center h-full text-zinc-400">
        请先选择一部小说
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white">
      {/* 头部 */}
      <div className="border-b border-zinc-200 p-4">
        <h2 className="text-lg font-bold text-zinc-800">💬 Writers Room</h2>
        <p className="text-sm text-zinc-500">Agent 协作讨论空间</p>
      </div>

      {!discussion ? (
        // 创建讨论表单
        <div className="flex-1 p-6 space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-zinc-700">议案标题</label>
            <input
              type="text"
              value={proposalTitle}
              onChange={(e) => setProposalTitle(e.target.value)}
              placeholder="例如：主角如何脱困？"
              className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          
          <div className="space-y-2">
            <label className="text-sm font-medium text-zinc-700">详细描述</label>
            <textarea
              value={proposalDesc}
              onChange={(e) => setProposalDesc(e.target.value)}
              placeholder="描述需要讨论的问题..."
              rows={4}
              className="w-full px-3 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
            />
          </div>
          
          <button
            onClick={createDiscussion}
            disabled={!proposalTitle}
            className="w-full py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:bg-zinc-300 disabled:cursor-not-allowed transition-colors"
          >
            开始讨论
          </button>
        </div>
      ) : (
        // 讨论界面
        <>
          {/* 议案信息 */}
          <div className="bg-zinc-50 p-4 border-b border-zinc-200">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-zinc-800">{discussion.proposal.title}</h3>
                <p className="text-sm text-zinc-500 mt-1">{discussion.proposal.description}</p>
              </div>
              <div className="text-right">
                <div className="text-sm text-zinc-500">
                  轮次: {discussion.round}/{discussion.max_rounds}
                </div>
                <div className="text-sm font-medium text-zinc-700">
                  共识度: {Math.round(discussion.consensus_score * 100)}%
                </div>
              </div>
            </div>
            
            {/* 共识度进度条 */}
            <div className="mt-2 h-2 bg-zinc-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-indigo-600 transition-all duration-500"
                style={{ width: `${discussion.consensus_score * 100}%` }}
              />
            </div>
          </div>

          {/* 消息列表 */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {discussion.messages.map((message, index) => (
              <div
                key={message.id || index}
                className={`flex gap-3 ${message.agent_id === "human" ? "flex-row-reverse" : ""}`}
              >
                {/* Agent 头像 */}
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border ${getAgentColor(
                    message.agent_name
                  )}`}
                >
                  {message.agent_name[0]}
                </div>

                {/* 消息内容 */}
                <div className={`flex-1 ${message.agent_id === "human" ? "text-right" : ""}`}>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-medium text-zinc-600">
                      {message.agent_name}
                    </span>
                    <span className="text-xs">{getMessageTypeIcon(message.message_type)}</span>
                    <span className="text-xs text-zinc-400">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  
                  <div
                    className={`inline-block max-w-[80%] px-4 py-2 rounded-2xl text-sm ${
                      message.agent_id === "human"
                        ? "bg-indigo-600 text-white"
                        : "bg-zinc-100 text-zinc-800"
                    }`}
                  >
                    {message.content}
                  </div>

                  {/* 心理活动（如果有） */}
                  {message.internal_monologue && (
                    <div className="mt-1 text-xs text-zinc-400 italic">
                      💭 {message.internal_monologue}
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* 控制按钮 */}
          <div className="border-t border-zinc-200 p-4 space-y-2">
            <div className="flex gap-2">
              <button
                onClick={runRound}
                disabled={isRunning || discussion.status !== "ongoing"}
                className="flex-1 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:bg-zinc-300 disabled:cursor-not-allowed transition-colors"
              >
                {isRunning ? "思考中..." : "下一轮讨论"}
              </button>
              
              <button
                onClick={() => intervene("我同意这个方案", "accept")}
                className="px-4 py-2 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 transition-colors"
              >
                接受
              </button>
              
              <button
                onClick={() => intervene("需要修改", "reject")}
                className="px-4 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors"
              >
                拒绝
              </button>
            </div>
            
            {/* 快速干预输入 */}
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="输入你的意见..."
                className="flex-1 px-3 py-2 border border-zinc-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    intervene(e.currentTarget.value, "comment");
                    e.currentTarget.value = "";
                  }
                }}
              />
              <button
                onClick={() => intervene("结束讨论", "end")}
                className="px-4 py-2 bg-zinc-600 text-white rounded-lg text-sm font-medium hover:bg-zinc-700 transition-colors"
              >
                结束
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
