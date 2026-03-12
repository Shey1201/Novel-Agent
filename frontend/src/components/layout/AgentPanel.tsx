"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { useSupabaseStore } from "@/store/supabaseStore";
import { apiUrl, AgentRoomWebSocket, fetchAgentChatStream, AgentStreamCallbacks } from "@/lib/api";

interface ChatResponse {
  error?: string;
  final_text?: string;
  world_bible?: { world_view?: string; rules?: string; themes?: string[] };
  approved?: boolean;
  context?: { recent_summaries?: string[] };
  agent_logs?: Array<{ 
    agent?: string; 
    message?: string; 
    content?: string; 
    requires_user_input?: boolean;
    auto_fill?: {
      type: string;
      content?: string;
      items?: Array<{name: string; role?: string}> | string[];
    };
  }>;
  conversation_state?: {
    stage?: string;
    workflow_type?: string;
    waiting_for_user?: boolean;
    accumulated_content?: string[];
    story_id?: string;
    chapter_id?: string;
    context_confirmed?: boolean;
  };
  requires_user_input?: boolean;
  final_agent?: string;
  trace_data?: Array<{
    text?: string;
    source_agent?: string;
    revisions?: string[];
  }>;
}

// 字数范围选项
const WORD_COUNT_OPTIONS = [
  { label: "短篇 (1000-2000字)", min: 1000, max: 2000 },
  { label: "中篇 (2000-3000字)", min: 2000, max: 3000 },
  { label: "标准 (3000-4000字)", min: 3000, max: 4000 },
  { label: "长篇 (4000-6000字)", min: 4000, max: 6000 },
  { label: "超长 (6000-10000字)", min: 6000, max: 10000 },
];

export const AgentPanel: React.FC = () => {
  const { messages, addMessage, loadMessages, clearMessages, currentNovelId, currentChapterId, updateChapterContent, setWorldBible, setWorldApproved, updateNovel, updateChapter, novels, addStoryAsset } =
    useSupabaseStore();

  // 根据 currentNovelId 获取当前小说名称
  const currentNovel = novels.find(n => n.id === currentNovelId);
  const currentNovelName = currentNovel?.title || null;
  // 根据 currentChapterId 获取当前章节名称
  const currentChapter = currentNovel?.chapters.find(c => c.id === currentChapterId);
  const currentChapterName = currentChapter?.title || null;
  const [inputValue, setEditValue] = useState("");
  const [selectedWordCount, setSelectedWordCount] = useState(WORD_COUNT_OPTIONS[2]); // 默认标准
  const [showSettings, setShowSettings] = useState(false);
  const [conversationState, setConversationState] = useState<ChatResponse['conversation_state'] | null>(null);
  const [isWaitingForUser, setIsWaitingForUser] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [consensusScore, setConsensusScore] = useState<number | null>(null);
  const [currentStep, setCurrentStep] = useState<string>('');
  const wsRef = useRef<AgentRoomWebSocket | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const seqRef = useRef(100);



  const nextMeta = () => {
    seqRef.current += 1;
    return { id: `msg-${seqRef.current}`, timestamp: seqRef.current };
  };

  const push = (sender: string, role: "user" | "agent", content: string) => {
    const meta = nextMeta();
    addMessage({ ...meta, sender, role, content });
  };

  // 进入 Agent Room 时加载历史消息
  useEffect(() => {
    loadMessages?.();
  }, [loadMessages]);

  // 处理 Agent 消息的回调
  const handleAgentMessage = useCallback((data: any) => {
    if (data.log) {
      const log = data.log;
      const text = log.content ? `${log.message || ""}\n${String(log.content)}` : log.message || "";
      push(log.agent_name || log.agent || "agent", "agent", text);

      if (log.requires_user_input) {
        setIsWaitingForUser(true);
      }
    }
  }, []);

  // 处理进度更新
  const handleProgressUpdate = useCallback((data: any) => {
    setCurrentStep(data.message || data.step || '');
  }, []);

  // 处理共识度更新
  const handleConsensusUpdate = useCallback((data: any) => {
    if (data.consensus_score !== undefined) {
      setConsensusScore(data.consensus_score);
    }
  }, []);

  // 处理需要用户输入
  const handleUserInputRequired = useCallback((data: any) => {
    setIsWaitingForUser(true);
    if (data.conversation_state) {
      setConversationState(data.conversation_state);
    }
  }, []);

  // 处理完成
  const handleAgentComplete = useCallback((data: any) => {
    setIsLoading(false);
    setCurrentStep('');
    setConsensusScore(null);

    if (data.data?.conversation_state) {
      setConversationState(data.data.conversation_state);
      setIsWaitingForUser(data.data.conversation_state.waiting_for_user || false);
    }
  }, []);

  // 处理错误
  const handleAgentError = useCallback((data: any) => {
    // 忽略空的错误数据（可能是 WebSocket 连接超时）
    if (!data || !data.error || data.error === '{}') {
      console.log('[AgentPanel] WebSocket connection status:', wsRef.current?.isConnected() ? 'connected' : 'disconnected');
      return;
    }
    setIsLoading(false);
    setCurrentStep('');
    push("system", "agent", `❌ Agent 错误: ${data.error || JSON.stringify(data)}`);
  }, []);

  // 连接 WebSocket
  useEffect(() => {
    const storyId = currentNovelId || 'demo-story';
    const callbacks: AgentStreamCallbacks = {
      onAgentStart: () => {}, // WebSocket 连接时不显示加载，等待用户发送消息后才显示
      onAgentMessage: handleAgentMessage,
      onProgressUpdate: handleProgressUpdate,
      onConsensusUpdate: handleConsensusUpdate,
      onUserInputRequired: handleUserInputRequired,
      onAgentComplete: handleAgentComplete,
      onAgentError: handleAgentError,
    };

    const ws = new AgentRoomWebSocket(storyId, callbacks);
    wsRef.current = ws;

    ws.connect().catch(console.error);

    return () => {
      ws.disconnect();
    };
  }, [currentNovelId, handleAgentMessage, handleProgressUpdate, handleConsensusUpdate, handleUserInputRequired, handleAgentComplete, handleAgentError]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim()) return;
    const message = inputValue.trim();
    
    // 添加字数范围信息到消息中
    const messageWithWordCount = message.startsWith('/write') || message.startsWith('/continue') || message.startsWith('/generate')
      ? `${message} [字数范围: ${selectedWordCount.min}-${selectedWordCount.max}字]`
      : message;
    
    push("User", "user", messageWithWordCount);
    setEditValue("");
    setIsLoading(true);

    const controller = new AbortController();
    let timeoutId: ReturnType<typeof setTimeout> | undefined = setTimeout(() => controller.abort(), 120000); // 120 秒超时

    try {
      const res = await fetch(apiUrl("/api/agent/chat"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          story_id: currentNovelId || "demo-story",
          story_name: currentNovelName,
          chapter_id: currentChapterId,
          chapter_name: currentChapterName,
          word_count_range: {
            min: selectedWordCount.min,
            max: selectedWordCount.max
          },
          conversation_state: conversationState
        }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      const data = (await res.json()) as ChatResponse;

      if (data.error) {
        push("system", "agent", `❌ Agent 处理失败: ${data.error}`);
        return;
      }

      // 保存对话状态
      if (data.conversation_state) {
        setConversationState(data.conversation_state);
        setIsWaitingForUser(data.conversation_state.waiting_for_user || false);
      }

      data.agent_logs?.forEach((log) => {
        const text = log.content ? `${log.message || ""}\n${String(log.content)}` : log.message || "";
        push(log.agent || "agent", "agent", text);
        
        // 如果是需要用户输入的决策点，特殊标记
        if (log.requires_user_input) {
          setIsWaitingForUser(true);
        }
        
        // 处理自动填充到 Story Bible
        if (log.auto_fill && currentNovelId) {
          const { type, content, items } = log.auto_fill;
          
          switch (type) {
            case 'worldbuilding':
              addStoryAsset('worldbuilding', {
                id: `world-${Date.now()}`,
                name: `世界观设定-${new Date().toLocaleDateString()}`,
                novelId: currentNovelId
              });
              push("system", "agent", "✅ 已自动添加到 Story Bible > World");
              break;
              
            case 'characters':
              if (items && Array.isArray(items)) {
                items.forEach((item: any, index: number) => {
                  if (typeof item === 'object' && item.name) {
                    addStoryAsset('characters', {
                      id: `char-${Date.now()}-${index}`,
                      name: item.name,
                      novelId: currentNovelId
                    });
                  }
                });
                push("system", "agent", `✅ 已自动添加 ${items.length} 个角色到 Story Bible > Characters`);
              }
              break;
              
            case 'factions':
              if (items && Array.isArray(items)) {
                (items as string[]).forEach((name: string, index: number) => {
                  addStoryAsset('factions', {
                    id: `faction-${Date.now()}-${index}`,
                    name: typeof name === 'string' ? name : `势力${index + 1}`,
                    novelId: currentNovelId
                  });
                });
                push("system", "agent", `✅ 已自动添加 ${items.length} 个势力到 Story Bible > Factions`);
              }
              break;
              
            case 'outline':
              if (content) {
                const currentNovel = novels.find(n => n.id === currentNovelId);
                const existingOutline = currentNovel?.outline || '';
                updateNovel(currentNovelId, { 
                  outline: existingOutline + '\n\n【大纲框架】\n' + content 
                });
                push("system", "agent", "✅ 已自动保存大纲到小说设定");
              }
              break;
              
            case 'timeline':
              addStoryAsset('timeline', {
                id: `timeline-${Date.now()}`,
                name: `时间线-${new Date().toLocaleDateString()}`,
                novelId: currentNovelId
              });
              push("system", "agent", "✅ 已自动添加到 Story Bible > Timeline");
              break;
              
            case 'locations':
              addStoryAsset('locations', {
                id: `location-${Date.now()}`,
                name: `场景设定-${new Date().toLocaleDateString()}`,
                novelId: currentNovelId
              });
              push("system", "agent", "✅ 已自动添加到 Story Bible > Locations");
              break;
          }
        }
      });

      if (data.context?.recent_summaries?.length) {
        push("system", "agent", `Recent Chapters:\n${data.context.recent_summaries.join("\n")}`);
      }

      if (data.world_bible) {
        setWorldBible({
          world_view: data.world_bible.world_view,
          rules: data.world_bible.rules,
          themes: data.world_bible.themes || [],
        });
      }
      if (typeof data.approved === "boolean") {
        setWorldApproved(data.approved);
      }

      // 智能识别并自动填充内容
      if (data.final_text && currentNovelId) {
        const lowerMsg = message.toLowerCase();
        
        // 1. 填充章节内容 - 包含写作相关关键词
        if (currentChapterId && 
            (lowerMsg.includes('写') || lowerMsg.includes('创作') || lowerMsg.includes('章节') || 
             lowerMsg.includes('内容') || lowerMsg.includes('draft') || lowerMsg.includes('write') ||
             lowerMsg.includes('正文') || lowerMsg.includes('段落'))) {
          // 传递 trace_data 如果存在，并确保类型匹配
          const traceData = data.trace_data?.map((item: {text?: string, source_agent?: string, revisions?: string[]}) => ({
            text: item.text || '',
            source_agent: item.source_agent || '',
            revisions: item.revisions
          }));
          updateChapterContent(currentNovelId, currentChapterId, data.final_text, traceData);
          push("system", "agent", "✅ 已自动填充到当前章节内容");
        }
        
        // 2. 更新章节标题/名称
        else if ((lowerMsg.includes('章节') || lowerMsg.includes('标题') || lowerMsg.includes('chapter')) &&
                 (lowerMsg.includes('名') || lowerMsg.includes('标题') || lowerMsg.includes('title') || lowerMsg.includes('叫'))) {
          // 尝试提取标题（取第一行或前20字）
          const title = data.final_text.split('\n')[0].slice(0, 30) || data.final_text.slice(0, 30);
          if (currentChapterId && title) {
            updateChapter(currentNovelId, currentChapterId, { title });
            push("system", "agent", `✅ 已自动更新章节标题为：${title}`);
          }
        }
        
        // 3. 更新小说名称
        else if ((lowerMsg.includes('小说') || lowerMsg.includes('书名') || lowerMsg.includes('故事')) &&
                 (lowerMsg.includes('名') || lowerMsg.includes('标题') || lowerMsg.includes('title') || lowerMsg.includes('叫'))) {
          const title = data.final_text.split('\n')[0].slice(0, 50) || data.final_text.slice(0, 50);
          if (title) {
            updateNovel(currentNovelId, { title });
            push("system", "agent", `✅ 已自动更新小说名称为：${title}`);
          }
        }
        
        // 4. 更新大纲 - 包含大纲相关关键词
        else if (lowerMsg.includes('大纲') || lowerMsg.includes('outline') || lowerMsg.includes('结构') || 
                 lowerMsg.includes('框架') || lowerMsg.includes('plot')) {
          updateNovel(currentNovelId, { outline: data.final_text });
          push("system", "agent", "✅ 已自动保存到小说大纲");
        }
        
        // 5. 更新设定/世界观 - 保存到编辑器世界观 + Story Bible > World
        else if (lowerMsg.includes('设定') || lowerMsg.includes('世界观') || lowerMsg.includes('背景') ||
                 lowerMsg.includes('world') || lowerMsg.includes('setting') || lowerMsg.includes('规则')) {
          // 保存到编辑器世界观（通过 setWorldBible 保存到 world_bibles 表）
          const currentWorldBible = {
            world_view: data.final_text,
            rules: '',
            themes: [],
          };
          setWorldBible(currentWorldBible);
          
          // 同时保存到 outline
          const currentNovel = novels.find(n => n.id === currentNovelId);
          const existingOutline = currentNovel?.outline || '';
          const worldBuildingSection = `\n\n【世界观设定】\n${data.final_text}`;
          updateNovel(currentNovelId, { 
            outline: existingOutline + worldBuildingSection 
          });
          
          // 添加到 Story Bible > World
          if (currentNovelId) {
            addStoryAsset('worldbuilding', {
              id: `world-${Date.now()}`,
              name: `世界观设定-${new Date().toLocaleDateString()}`,
              novelId: currentNovelId
            });
          }
          
          push("system", "agent", "✅ 已自动保存到编辑器世界观、小说大纲和 Story Bible > World");
        }
        
        // 6. 更新角色设定 - 保存到 Story Bible > Characters
        else if (lowerMsg.includes('角色') || lowerMsg.includes('人物') || lowerMsg.includes('character') ||
                 lowerMsg.includes('主角') || lowerMsg.includes('配角')) {
          // 解析角色列表并添加到 Story Bible
          const currentNovel = novels.find(n => n.id === currentNovelId);
          const existingOutline = currentNovel?.outline || '';
          const charactersSection = `\n\n【角色设定】\n${data.final_text}`;
          updateNovel(currentNovelId, { 
            outline: existingOutline + charactersSection 
          });
          
          // 尝试解析角色名称并添加到 Story Bible > Characters
          if (currentNovelId && data.final_text) {
            // 简单解析：查找可能的角色名（以【】或[]包裹的内容，或"角色名："格式）
            const characterMatches = data.final_text.match(/[【\[]([^【\]\[\]]+)[】\]]|([^：:\n]{2,20})[：:]/g);
            if (characterMatches && characterMatches.length > 0) {
              characterMatches.slice(0, 5).forEach((match, index) => {
                const name = match.replace(/[【\]\[】：:]/g, '').trim();
                if (name && name.length > 1 && name.length < 20) {
                  addStoryAsset('characters', {
                    id: `char-${Date.now()}-${index}`,
                    name: name,
                    novelId: currentNovelId
                  });
                }
              });
            } else {
              // 如果没有解析到角色名，添加一个整体条目
              addStoryAsset('characters', {
                id: `char-${Date.now()}`,
                name: `角色设定-${new Date().toLocaleDateString()}`,
                novelId: currentNovelId
              });
            }
          }
          
          push("system", "agent", "✅ 已自动保存到小说大纲和 Story Bible > Characters");
        }
        
        // 7. 更新简介/描述 - 保存到 outline 开头
        else if (lowerMsg.includes('简介') || lowerMsg.includes('描述') || lowerMsg.includes('description') ||
                 lowerMsg.includes('summary') || lowerMsg.includes('介绍')) {
          const currentNovel = novels.find(n => n.id === currentNovelId);
          const existingOutline = currentNovel?.outline || '';
          const summarySection = `【简介】\n${data.final_text}\n\n${existingOutline}`;
          updateNovel(currentNovelId, { outline: summarySection });
          push("system", "agent", "✅ 已自动保存到小说大纲（简介部分）");
        }
        
        // 8. 更新势力/组织 - 保存到 Story Bible > Factions
        else if (lowerMsg.includes('势力') || lowerMsg.includes('组织') || lowerMsg.includes('门派') ||
                 lowerMsg.includes('faction') || lowerMsg.includes('组织') || lowerMsg.includes('集团')) {
          const currentNovel = novels.find(n => n.id === currentNovelId);
          const existingOutline = currentNovel?.outline || '';
          const factionsSection = `\n\n【势力/组织设定】\n${data.final_text}`;
          updateNovel(currentNovelId, { 
            outline: existingOutline + factionsSection 
          });
          
          // 添加到 Story Bible > Factions
          if (currentNovelId) {
            addStoryAsset('factions', {
              id: `faction-${Date.now()}`,
              name: `势力设定-${new Date().toLocaleDateString()}`,
              novelId: currentNovelId
            });
          }
          
          push("system", "agent", "✅ 已自动保存到小说大纲和 Story Bible > Factions");
        }
        
        // 9. 更新时间线 - 保存到 Story Bible > Timeline
        else if (lowerMsg.includes('时间线') || lowerMsg.includes('timeline') || lowerMsg.includes('年表') ||
                 lowerMsg.includes('历史') || lowerMsg.includes('时间轴') || lowerMsg.includes('年代')) {
          const currentNovel = novels.find(n => n.id === currentNovelId);
          const existingOutline = currentNovel?.outline || '';
          const timelineSection = `\n\n【时间线/历史】\n${data.final_text}`;
          updateNovel(currentNovelId, { 
            outline: existingOutline + timelineSection 
          });
          
          // 添加到 Story Bible > Timeline
          if (currentNovelId) {
            addStoryAsset('timeline', {
              id: `timeline-${Date.now()}`,
              name: `时间线-${new Date().toLocaleDateString()}`,
              novelId: currentNovelId
            });
          }
          
          push("system", "agent", "✅ 已自动保存到小说大纲和 Story Bible > Timeline");
        }
        
        // 10. 更新地点/场景 - 保存到 Story Bible > Locations
        else if (lowerMsg.includes('地点') || lowerMsg.includes('场景') || lowerMsg.includes('location') ||
                 lowerMsg.includes('地图') || lowerMsg.includes('场景') || lowerMsg.includes('场所')) {
          const currentNovel = novels.find(n => n.id === currentNovelId);
          const existingOutline = currentNovel?.outline || '';
          const locationsSection = `\n\n【地点/场景设定】\n${data.final_text}`;
          updateNovel(currentNovelId, { 
            outline: existingOutline + locationsSection 
          });
          
          // 添加到 Story Bible > Locations
          if (currentNovelId) {
            addStoryAsset('locations', {
              id: `location-${Date.now()}`,
              name: `场景设定-${new Date().toLocaleDateString()}`,
              novelId: currentNovelId
            });
          }
          
          push("system", "agent", "✅ 已自动保存到小说大纲和 Story Bible > Locations");
        }
      }
    } catch (error) {
      if (timeoutId !== undefined) clearTimeout(timeoutId);
      const isAbort = error instanceof Error && error.name === "AbortError";
      const msg = error instanceof Error ? error.message : String(error);
      const isNetwork = msg.includes("fetch") || msg.includes("Failed to fetch") || msg.includes("NetworkError");
      if (isAbort) {
        push("system", "agent", "❌ 请求超时（120 秒），请稍后重试或简化请求。");
      } else {
        push("system", "agent", isNetwork
          ? `❌ 网络请求失败，请确认后端服务已启动（${apiUrl("")}）且 CORS 已配置。`
          : `Agent Room 请求失败: ${msg}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <aside className="w-96 border-l border-zinc-200 bg-zinc-50 flex flex-col h-full shrink-0 shadow-sm">
      <div className="p-4 border-b border-zinc-200 bg-white shrink-0">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-zinc-800">Agent Room</h2>
          <div className="flex items-center gap-1">
            <button
              onClick={() => {
                clearMessages?.();
                setConversationState(null);
              }}
              className="p-1.5 text-zinc-400 hover:text-red-600 hover:bg-zinc-100 rounded-lg transition-colors"
              title="清空聊天记录"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 6h18"/>
                <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
                <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
              </svg>
            </button>
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-1.5 text-zinc-400 hover:text-indigo-600 hover:bg-zinc-100 rounded-lg transition-colors"
              title="生成设置"
            >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
          </button>
          </div>
        </div>
        <p className="mt-1.5 text-[10px] text-zinc-400">找找灵感来 battle 一下吧</p>
        
        {/* 生成设置面板 */}
        {showSettings && (
          <div className="mt-3 pt-3 border-t border-zinc-200">
            <label className="block text-xs font-medium text-zinc-600 mb-2">
              每章生成字数范围
            </label>
            <select
              value={selectedWordCount.label}
              onChange={(e) => {
                const option = WORD_COUNT_OPTIONS.find(o => o.label === e.target.value);
                if (option) setSelectedWordCount(option);
              }}
              className="w-full px-3 py-2 text-sm bg-zinc-50 border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
            >
              {WORD_COUNT_OPTIONS.map((option) => (
                <option key={option.label} value={option.label}>
                  {option.label}
                </option>
              ))}
            </select>
            <p className="mt-1.5 text-[10px] text-zinc-400">
              当前选择: {selectedWordCount.min.toLocaleString()}-{selectedWordCount.max.toLocaleString()} 字
            </p>
          </div>
        )}
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}>
            <div className="flex items-center gap-2 mb-1 px-1">
              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">{msg.sender}</span>
            </div>
            <div className={`max-w-[90%] whitespace-pre-wrap p-3 rounded-2xl text-sm shadow-sm ${msg.role === "user" ? "bg-indigo-600 text-white rounded-tr-none" : "bg-white text-zinc-700 border border-zinc-100 rounded-tl-none"}`}>
              {msg.content}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex flex-col items-start">
            <div className="flex items-center gap-2 mb-1 px-1">
              <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">Agent</span>
            </div>
            <div className="max-w-[90%] p-3 rounded-2xl text-sm bg-white text-zinc-500 border border-zinc-100 rounded-tl-none flex items-center gap-2">
              <span className="inline-block w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />
              <span className="inline-block w-2 h-2 rounded-full bg-indigo-500 animate-pulse [animation-delay:0.2s]" />
              <span className="inline-block w-2 h-2 rounded-full bg-indigo-500 animate-pulse [animation-delay:0.4s]" />
              <span className="text-zinc-500">Agent 正在加载中...</span>
            </div>
          </div>
        )}
      </div>

      <div className="p-4 bg-white border-t border-zinc-200 shrink-0">
        {/* 共识度可视化 */}
        {consensusScore !== null && (
          <div className="mb-3 px-3 py-2 bg-emerald-50 border border-emerald-200 rounded-lg">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-emerald-700 font-medium">共识度</span>
              <span className="text-xs font-bold text-emerald-600">{Math.round(consensusScore * 100)}%</span>
            </div>
            <div className="w-full h-1.5 bg-emerald-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-emerald-500 transition-all duration-300"
                style={{ width: `${consensusScore * 100}%` }}
              />
            </div>
          </div>
        )}

        {/* 当前步骤显示 */}
        {isLoading && currentStep && (
          <div className="mb-3 px-3 py-2 bg-indigo-50 border border-indigo-200 rounded-lg">
            <p className="text-xs text-indigo-700 flex items-center gap-2">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
              {currentStep}
            </p>
          </div>
        )}

        {isLoading && !currentStep && (
          <div className="mb-3 px-3 py-2 bg-indigo-50 border border-indigo-200 rounded-lg">
            <p className="text-xs text-indigo-700 flex items-center gap-2">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
              Agent 正在加载中，请稍候...
            </p>
          </div>
        )}
        {isWaitingForUser && !isLoading && (
          <div className="mb-3 px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-xs text-amber-700 flex items-center gap-2">
              <span>⏸️</span>
              <span>Agent 正在等待您的决策或反馈...</span>
            </p>
          </div>
        )}
        <div className="relative">
          <textarea
            value={inputValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), handleSend())}
            placeholder={isWaitingForUser 
              ? "请输入您的决策或反馈，例如：继续 / 修改 / 确认" 
              : "直接输入内容，Agent 团队会自主讨论并执行..."}
            className={`w-full pl-3 pr-10 py-2.5 border rounded-xl text-sm resize-none h-20 ${
              isWaitingForUser 
                ? 'bg-amber-50 border-amber-300 focus:border-amber-500 focus:ring-amber-500/20' 
                : 'bg-zinc-50 border-zinc-200 focus:border-indigo-500 focus:ring-indigo-500/20'
            }`}
          />
          <button 
            onClick={handleSend} 
            className={`absolute right-2 bottom-2 w-7 h-7 text-white rounded-lg transition-colors ${
              isWaitingForUser ? 'bg-amber-600 hover:bg-amber-700' : 'bg-indigo-600 hover:bg-indigo-700'
            }`}
          >
            ↗
          </button>
        </div>
      </div>
    </aside>
  );
};
