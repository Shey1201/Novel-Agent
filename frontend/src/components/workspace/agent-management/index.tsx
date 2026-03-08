import React, { useState, useEffect, useCallback } from 'react';
import { useSupabaseStore, type Agent } from '@/store/supabaseStore';

interface EditingAgent {
  role: string;
  personality: string;
  temperature: number;
  prompt: string;
}

const AgentConfigForm: React.FC<{ 
  agent: Agent; 
  onSave: (updates: Partial<Agent>) => void;
  onChange: (hasChanges: boolean) => void;
}> = ({ agent, onSave, onChange }) => {
  const [editData, setEditData] = useState<EditingAgent>({
    role: agent.role,
    personality: agent.personality || '',
    temperature: agent.temperature,
    prompt: agent.prompt,
  });
  const [hasChanges, setHasChanges] = useState(false);

  // 检测是否有更改
  useEffect(() => {
    const changed = 
      editData.role !== agent.role ||
      editData.personality !== (agent.personality || '') ||
      editData.temperature !== agent.temperature ||
      editData.prompt !== agent.prompt;
    
    setHasChanges(changed);
    onChange(changed);
  }, [editData, agent, onChange]);

  // 当切换 agent 时重置编辑数据
  useEffect(() => {
    setEditData({
      role: agent.role,
      personality: agent.personality || '',
      temperature: agent.temperature,
      prompt: agent.prompt,
    });
    setHasChanges(false);
  }, [agent.id]);

  const handleSave = () => {
    onSave({
      role: editData.role,
      personality: editData.personality,
      temperature: editData.temperature,
      prompt: editData.prompt,
    });
    setHasChanges(false);
  };

  const handleCancel = () => {
    // 重置为原始值
    setEditData({
      role: agent.role,
      personality: agent.personality || '',
      temperature: agent.temperature,
      prompt: agent.prompt,
    });
    setHasChanges(false);
  };

  return (
    <div className="bg-white border border-zinc-200 rounded-2xl shadow-sm">
      <div className="p-4 border-b border-zinc-100 flex justify-between items-center">
        <h3 className="text-sm font-bold text-zinc-800">Agent Config: {agent.name}</h3>
        {hasChanges && (
          <span className="text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded-full">
            有未保存的更改
          </span>
        )}
      </div>
      <div className="p-6 space-y-4">
        <div>
          <label className="block text-xs font-medium text-zinc-600 mb-1">Name</label>
          <input
            value={agent.name}
            readOnly
            className="w-full p-2 text-xs border border-zinc-200 rounded-lg bg-zinc-100 text-zinc-500"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-zinc-600 mb-1">Role</label>
          <input
            value={editData.role}
            onChange={(e) => setEditData({ ...editData, role: e.target.value })}
            className="w-full p-2 text-xs border border-zinc-200 rounded-lg bg-zinc-50/50 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none transition-all"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-zinc-600 mb-1">Personality</label>
          <input
            value={editData.personality}
            onChange={(e) => setEditData({ ...editData, personality: e.target.value })}
            className="w-full p-2 text-xs border border-zinc-200 rounded-lg bg-zinc-50/50 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 outline-none transition-all"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-zinc-600 mb-1">
            Temperature: {editData.temperature.toFixed(2)}
          </label>
          <input
            type="range"
            min="0" max="1" step="0.05"
            value={editData.temperature}
            onChange={(e) => setEditData({ ...editData, temperature: parseFloat(e.target.value) })}
            className="w-full accent-indigo-600 h-1.5 bg-zinc-200 rounded-lg appearance-none cursor-pointer"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-zinc-600 mb-1">Prompt Template</label>
          <textarea
            value={editData.prompt}
            onChange={(e) => setEditData({ ...editData, prompt: e.target.value })}
            className="w-full h-48 p-3 text-xs border border-zinc-200 rounded-xl focus:ring-2 focus:ring-indigo-500/10 outline-none resize-none bg-zinc-50/50 font-mono"
          />
        </div>

        {/* 保存/取消按钮 */}
        {hasChanges && (
          <div className="flex gap-3 pt-4 border-t border-zinc-100">
            <button
              onClick={handleSave}
              className="flex-1 bg-indigo-600 text-white py-2 px-4 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors flex items-center justify-center gap-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
                <polyline points="17 21 17 13 7 13 7 21"/>
                <polyline points="7 3 7 8 15 8"/>
              </svg>
              保存更改
            </button>
            <button
              onClick={handleCancel}
              className="px-4 py-2 border border-zinc-300 text-zinc-700 rounded-lg text-sm font-medium hover:bg-zinc-50 transition-colors"
            >
              取消
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

const AgentManagement: React.FC = () => {
  const { agents, updateAgent, loadFromSupabase } = useSupabaseStore();
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  
  // 组件挂载时加载数据
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      await loadFromSupabase();
      setIsLoading(false);
    };
    loadData();
  }, [loadFromSupabase]);
  
  // 当agents数据加载完成后，设置默认选中的agent
  useEffect(() => {
    if (agents.length > 0 && !selectedAgentId) {
      setSelectedAgentId(agents[0].id);
    }
  }, [agents, selectedAgentId]);
  
  const selectedAgent = agents.find(a => a.id === selectedAgentId) || null;

  const handleSave = useCallback((updates: Partial<Agent>) => {
    if (selectedAgentId) {
      // 更新到 store（会同步到 Supabase）
      updateAgent(selectedAgentId, updates);
      setHasUnsavedChanges(false);
    }
  }, [selectedAgentId, updateAgent]);

  const handleAgentSelect = (agentId: string) => {
    // 如果当前有未保存的更改，提示用户
    if (selectedAgentId && hasUnsavedChanges) {
      const confirmSwitch = window.confirm('当前 Agent 有未保存的更改，确定要切换吗？');
      if (!confirmSwitch) return;
    }
    setSelectedAgentId(agentId);
    setHasUnsavedChanges(false);
  };

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-zinc-200">
        <h1 className="text-xl font-bold text-zinc-900">Agent Management</h1>
        <p className="text-sm text-zinc-500 mt-1">配置和管理您的 AI 创作团队</p>
      </div>
      
      <div className="flex-1 overflow-hidden flex">
        {/* 左侧 Agent 列表 */}
        <div className="w-64 border-r border-zinc-200 overflow-y-auto p-3">
          {agents.map(agent => (
            <button
              key={agent.id}
              onClick={() => handleAgentSelect(agent.id)}
              className={`w-full text-left p-3 rounded-lg transition-colors mb-2 relative ${
                selectedAgentId === agent.id
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'hover:bg-zinc-100'
              }`}>
              <div className="font-semibold text-sm flex items-center gap-2">
                {agent.name}
                {selectedAgentId === agent.id && hasUnsavedChanges && (
                  <span className="w-2 h-2 bg-amber-500 rounded-full" title="有未保存的更改" />
                )}
              </div>
              <div className="text-xs text-zinc-500 truncate">{agent.role}</div>
            </button>
          ))}
        </div>
        
        {/* 右侧配置区域 */}
        <div className="flex-1 overflow-y-auto p-6">
          {selectedAgent ? (
            <AgentConfigForm 
              agent={selectedAgent} 
              onSave={handleSave}
              onChange={setHasUnsavedChanges}
            />
          ) : (
            <div className="flex items-center justify-center h-full text-zinc-400 text-sm">
              选择一个 Agent 进行配置
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentManagement;
