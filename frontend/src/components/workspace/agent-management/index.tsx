import React, { useState } from 'react';
import { useNovelStore, type Agent } from '@/store/novelStore';

const AgentConfigForm: React.FC<{ agent: Agent }> = ({ agent }) => {
  const { updateAgent } = useNovelStore();

  // A simple mock for personality, as it's not in the store yet
  const [personality, setPersonality] = useState('Strategic / Analytical / Long-term thinker');

  return (
    <div className="bg-white border border-zinc-200 rounded-2xl shadow-sm">
      <div className="p-4 border-b border-zinc-100">
        <h3 className="text-sm font-bold text-zinc-800">Agent Config: {agent.name}</h3>
      </div>
      <div className="p-6 space-y-4">
        <div>
          <label className="block text-xs font-medium text-zinc-600 mb-1">Name</label>
          <input
            value={agent.name}
            // We might not want to change the name (ID) itself, so this is read-only for now
            readOnly
            className="w-full p-2 text-xs border border-zinc-200 rounded-lg bg-zinc-100 text-zinc-500"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-zinc-600 mb-1">Role</label>
          <input
            value={agent.role}
            onChange={(e) => updateAgent(agent.id, { role: e.target.value })}
            className="w-full p-2 text-xs border border-zinc-200 rounded-lg bg-zinc-50/50"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-zinc-600 mb-1">Personality</label>
          <input
            value={personality}
            onChange={(e) => setPersonality(e.target.value)}
            className="w-full p-2 text-xs border border-zinc-200 rounded-lg bg-zinc-50/50"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-zinc-600 mb-1">Temperature: {agent.temperature}</label>
          <input
            type="range"
            min="0" max="1" step="0.1"
            value={agent.temperature}
            onChange={(e) => updateAgent(agent.id, { temperature: parseFloat(e.target.value) })}
            className="w-full accent-indigo-600 h-1.5 bg-zinc-200 rounded-lg appearance-none cursor-pointer"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-zinc-600 mb-1">Prompt Template</label>
          <textarea
            value={agent.prompt}
            onChange={(e) => updateAgent(agent.id, { prompt: e.target.value })}
            className="w-full h-48 p-3 text-xs border border-zinc-200 rounded-xl focus:ring-2 focus:ring-indigo-500/10 outline-none resize-none bg-zinc-50/50 font-mono"
          />
        </div>
      </div>
    </div>
  );
};

const AgentManagement: React.FC = () => {
  const { agents } = useNovelStore();
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(agents[0]?.id || null);
  const selectedAgent = agents.find(a => a.id === selectedAgentId) || null;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-zinc-900">Agent Management</h1>
        <p className="text-sm text-zinc-500 mt-1">配置和管理您的 AI 创作团队中的每个角色。</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="md:col-span-1 space-y-2">
          {agents.map(agent => (
            <button
              key={agent.id}
              onClick={() => setSelectedAgentId(agent.id)}
              className={`w-full text-left p-3 rounded-lg transition-colors ${
                selectedAgentId === agent.id
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'hover:bg-zinc-100'
              }`}>
              <div className="font-semibold text-sm">{agent.name}</div>
              <div className="text-xs text-zinc-500 truncate">{agent.role}</div>
            </button>
          ))}
        </div>
        <div className="md:col-span-3">
          {selectedAgent ? (
            <AgentConfigForm agent={selectedAgent} />
          ) : (
            <div className="flex items-center justify-center h-full text-zinc-400 text-sm">
              Select an agent to configure.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentManagement;
