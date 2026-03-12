/**
 * API 配置
 * 根据环境自动选择 API 基础 URL
 * 线上部署时必须在构建前设置 NEXT_PUBLIC_API_URL 为实际后端地址，否则会请求到 localhost 导致 Failed to fetch / ERR_CONNECTION_CLOSED
 */

// API 基础 URL - 从环境变量读取，本地开发默认连后端 8000 端口
export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

// 运行时检测：线上环境若仍为 localhost，提示配置错误（仅浏览器环境）
if (typeof window !== 'undefined' && API_BASE.includes('127.0.0.1') && !window.location.hostname.includes('localhost')) {
  console.warn(
    '[API] 当前为线上环境但 API 指向 127.0.0.1，请求会失败。请在构建时设置环境变量 NEXT_PUBLIC_API_URL 为后端实际地址。'
  );
}

// 构建完整 API URL
export function apiUrl(path: string): string {
  // 如果 path 已经以 http 开头，直接返回
  if (path.startsWith('http')) {
    return path;
  }
  // 如果 path 不以 / 开头，添加 /
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE}${normalizedPath}`;
}

// WebSocket URL
export function wsUrl(path: string): string {
  if (path.startsWith('ws')) {
    return path;
  }
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  // 将 http 替换为 ws
  const wsBase = API_BASE.replace('https://', 'wss://').replace('http://', 'ws://') || 'ws://localhost:8000';
  return `${wsBase}${normalizedPath}`;
}

// ==================== Agent Room WebSocket 客户端 ====================
export type AgentMessageHandler = (data: any) => void;
export type AgentStreamCallbacks = {
  onAgentStart?: AgentMessageHandler;
  onAgentMessage?: AgentMessageHandler;
  onAgentComplete?: AgentMessageHandler;
  onAgentError?: AgentMessageHandler;
  onConsensusUpdate?: AgentMessageHandler;
  onProgressUpdate?: AgentMessageHandler;
  onUserInputRequired?: AgentMessageHandler;
};

export class AgentRoomWebSocket {
  private ws: WebSocket | null = null;
  private storyId: string;
  private callbacks: AgentStreamCallbacks;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 2000;

  constructor(storyId: string, callbacks: AgentStreamCallbacks) {
    this.storyId = storyId;
    this.callbacks = callbacks;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const url = wsUrl(`/api/agent/ws/${this.storyId}`);

      try {
        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
          console.log('[AgentRoomWebSocket] Connected to', url);
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (e) {
            console.error('[AgentRoomWebSocket] Failed to parse message:', e);
          }
        };

        this.ws.onerror = (error) => {
          // WebSocket 错误可能是由于连接关闭或其他原因，不一定影响功能
          // 只在连接未建立时记录错误
          if (this.ws?.readyState !== WebSocket.OPEN) {
            console.log('[AgentRoomWebSocket] Connection not established, will retry');
          }
        };

        this.ws.onclose = () => {
          console.log('[AgentRoomWebSocket] Disconnected');
          this.attemptReconnect();
        };
      } catch (e) {
        reject(e);
      }
    });
  }

  private handleMessage(message: any) {
    const { type, data } = message;

    switch (type) {
      case 'connected':
        this.callbacks.onAgentStart?.(data);
        break;
      case 'agent_message':
        this.callbacks.onAgentMessage?.(data);
        break;
      case 'agent_start':
        this.callbacks.onAgentStart?.(data);
        break;
      case 'agent_complete':
        this.callbacks.onAgentComplete?.(data);
        break;
      case 'agent_error':
        this.callbacks.onAgentError?.(data);
        break;
      case 'consensus_update':
        this.callbacks.onConsensusUpdate?.(data);
        break;
      case 'progress_update':
        this.callbacks.onProgressUpdate?.(data);
        break;
      case 'user_input_required':
        this.callbacks.onUserInputRequired?.(data);
        break;
      default:
        console.log('[AgentRoomWebSocket] Unknown message type:', type);
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('[AgentRoomWebSocket] Max reconnect attempts reached');
      return;
    }

    this.reconnectAttempts++;
    console.log(`[AgentRoomWebSocket] Reconnecting... Attempt ${this.reconnectAttempts}`);

    setTimeout(() => {
      this.connect().catch(console.error);
    }, this.reconnectDelay);
  }

  sendMessage(message: string, options?: {
    chapter_id?: string;
    story_name?: string;
    word_count_range?: { min: number; max: number };
    conversation_state?: any;
  }) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'send_message',
        message,
        ...options
      }));
    } else {
      console.error('[AgentRoomWebSocket] WebSocket not connected');
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// ==================== SSE 流式请求 ====================
export async function fetchAgentChatStream(
  payload: {
    message: string;
    story_id?: string;
    story_name?: string;
    chapter_id?: string;
    word_count_range?: { min: number; max: number };
    conversation_state?: any;
  },
  callbacks: AgentStreamCallbacks
): Promise<void> {
  const response = await fetch(apiUrl('/api/agent/chat/stream'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: payload.message,
      story_id: payload.story_id || 'demo-story',
      story_name: payload.story_name,
      chapter_id: payload.chapter_id,
      word_count_range: payload.word_count_range,
      conversation_state: payload.conversation_state
    })
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    callbacks.onAgentError?.({ error: error.detail || 'Request failed' });
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    callbacks.onAgentError?.({ error: 'No response body' });
    return;
  }

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.agent_logs && data.agent_logs.length > 0) {
              callbacks.onAgentMessage?.({ log: data.agent_logs[data.agent_logs.length - 1], data });
            }
            if (data.final_text !== undefined) {
              callbacks.onAgentComplete?.({ data });
            }
          } catch (e) {
            console.error('[fetchAgentChatStream] Parse error:', e);
          }
        }
      }
    }
  } catch (e) {
    callbacks.onAgentError?.({ error: String(e) });
  }
}
