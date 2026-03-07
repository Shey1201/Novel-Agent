import React, { useState, useEffect } from 'react';

type SettingsTab = 'account' | 'general' | 'token' | 'generation' | 'notifications' | 'storage' | 'about';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface CollapsibleSectionProps {
  title: string;
  badge?: React.ReactNode;
  subtitle?: string;
  defaultExpanded?: boolean;
  alignSubtitle?: 'left' | 'withTitle';
  children: React.ReactNode;
}

interface ToggleSwitchProps {
  leftLabel: string;
  rightLabel: string;
  defaultChecked?: boolean;
  onChange?: (checked: boolean) => void;
}

const ToggleSwitch: React.FC<ToggleSwitchProps> = ({
  leftLabel,
  rightLabel,
  defaultChecked = false,
  onChange,
}) => {
  const [isChecked, setIsChecked] = useState(defaultChecked);

  const handleToggle = () => {
    const newValue = !isChecked;
    setIsChecked(newValue);
    onChange?.(newValue);
  };

  return (
    <div
      onClick={handleToggle}
      className="relative flex items-center bg-zinc-100 rounded-full p-1 w-32 h-8 transition-colors duration-200 cursor-pointer"
      role="switch"
      aria-checked={isChecked}
    >
      {/* Left Label */}
      <span
        className={`flex-1 text-xs font-medium text-center z-10 transition-colors duration-200 ${
          !isChecked ? 'text-zinc-900' : 'text-zinc-500'
        }`}
      >
        {leftLabel}
      </span>

      {/* Right Label */}
      <span
        className={`flex-1 text-xs font-medium text-center z-10 transition-colors duration-200 ${
          isChecked ? 'text-zinc-900' : 'text-zinc-500'
        }`}
      >
        {rightLabel}
      </span>

      {/* Sliding Background */}
      <div
        className={`absolute top-1 bottom-1 w-[calc(50%-4px)] bg-white rounded-full shadow-sm transition-transform duration-200 ${
          isChecked ? 'translate-x-[calc(100%+8px)]' : 'translate-x-0'
        }`}
        style={{ left: '4px' }}
      />
    </div>
  );
};

const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
  title,
  badge,
  subtitle,
  defaultExpanded = false,
  alignSubtitle = 'left',
  children,
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className="bg-white border border-zinc-200 rounded-xl overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 flex items-center justify-between hover:bg-zinc-50 transition-colors"
      >
        <div className="flex-1 text-left">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-zinc-900">{title}</h3>
            {badge}
          </div>
          {subtitle && (
            <p className={`text-xs text-zinc-500 mt-0.5 ${alignSubtitle === 'left' ? 'pl-0' : ''}`}>
              {subtitle}
            </p>
          )}
        </div>
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
          className={`text-zinc-400 transition-transform duration-200 ${
            isExpanded ? 'rotate-180' : ''
          }`}
        >
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>
      {isExpanded && <div className="px-4 pb-4">{children}</div>}
    </div>
  );
};

// Token 设置接口
interface TokenSettings {
  enabled: boolean;
  daily_limit: number;
  warning_threshold: number;
  budget_allocation: Record<string, number>;
}

// 生成设置接口
interface GenerationSettings {
  max_rounds: number;
  max_tokens_per_response: number;
  enable_short_mode: boolean;
  paragraph_length: number;
  reader_interval: number;
  enable_streaming: boolean;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<SettingsTab>('general');
  
  // Token 设置状态
  const [tokenSettings, setTokenSettings] = useState<TokenSettings>({
    enabled: false,
    daily_limit: 50000,
    warning_threshold: 0.8,
    budget_allocation: {
      planner: 0.10,
      discussion: 0.13,
      conflict: 0.07,
      writing: 0.47,
      editor: 0.13,
      reader: 0.07,
      summary: 0.03,
    }
  });
  
  // 生成设置状态
  const [generationSettings, setGenerationSettings] = useState<GenerationSettings>({
    max_rounds: 2,
    max_tokens_per_response: 80,
    enable_short_mode: true,
    paragraph_length: 500,
    reader_interval: 3,
    enable_streaming: true,
  });
  
  // Token 使用状态
  const [tokenStatus, setTokenStatus] = useState({
    enabled: false,
    daily_limit: 50000,
    daily_used: 0,
    daily_remaining: 50000,
    usage_rate: 0
  });

  // 加载设置
  useEffect(() => {
    if (isOpen) {
      loadSettings();
    }
  }, [isOpen]);

  const loadSettings = async () => {
    try {
      // 加载 Token 设置
      const tokenRes = await fetch('/api/settings/token');
      if (tokenRes.ok) {
        const tokenData = await tokenRes.json();
        setTokenSettings(tokenData);
      }
      
      // 加载 Token 状态
      const statusRes = await fetch('/api/settings/token/status');
      if (statusRes.ok) {
        const statusData = await statusRes.json();
        setTokenStatus(statusData);
      }
      
      // 加载生成设置
      const genRes = await fetch('/api/settings/generation');
      if (genRes.ok) {
        const genData = await genRes.json();
        setGenerationSettings(prev => ({ ...prev, ...genData }));
      }
      
      // 加载讨论设置
      const discRes = await fetch('/api/settings/discussion');
      if (discRes.ok) {
        const discData = await discRes.json();
        setGenerationSettings(prev => ({ ...prev, ...discData }));
      }
    } catch (error) {
      console.error('加载设置失败:', error);
    }
  };

  // 保存 Token 设置
  const saveTokenSettings = async () => {
    try {
      await fetch('/api/settings/token', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tokenSettings)
      });
    } catch (error) {
      console.error('保存 Token 设置失败:', error);
    }
  };

  // 保存生成设置
  const saveGenerationSettings = async () => {
    try {
      await fetch('/api/settings/generation', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          paragraph_length: generationSettings.paragraph_length,
          reader_interval: generationSettings.reader_interval,
          enable_streaming: generationSettings.enable_streaming,
        })
      });
      
      await fetch('/api/settings/discussion', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          max_rounds: generationSettings.max_rounds,
          max_tokens_per_response: generationSettings.max_tokens_per_response,
          enable_short_mode: generationSettings.enable_short_mode,
        })
      });
    } catch (error) {
      console.error('保存生成设置失败:', error);
    }
  };

  // 重置每日 Token
  const resetDailyToken = async () => {
    try {
      await fetch('/api/settings/token/reset', { method: 'POST' });
      loadSettings();
    } catch (error) {
      console.error('重置 Token 失败:', error);
    }
  };

  if (!isOpen) return null;

  const tabs: Array<{ key: SettingsTab; label: string; icon: React.ReactNode }> = [
    {
      key: 'account',
      label: 'Account',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>
          <circle cx="12" cy="7" r="4"/>
        </svg>
      ),
    },
    {
      key: 'general',
      label: 'General',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="4" x2="20" y1="12" y2="12"/>
          <line x1="4" x2="20" y1="6" y2="6"/>
          <line x1="4" x2="20" y1="18" y2="18"/>
        </svg>
      ),
    },
    {
      key: 'token',
      label: 'Token Budget',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 6v6l4 2"/>
        </svg>
      ),
    },
    {
      key: 'generation',
      label: 'Generation',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 3v18"/>
          <path d="M3 12h18"/>
          <path d="m7 7 10 10"/>
          <path d="m17 7-10 10"/>
        </svg>
      ),
    },
    {
      key: 'notifications',
      label: 'Notifications',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>
          <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>
        </svg>
      ),
    },
    {
      key: 'storage',
      label: 'Storage & Data',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <ellipse cx="12" cy="5" rx="9" ry="3"/>
          <path d="M3 5V19A9 3 0 0 0 21 19V5"/>
          <path d="M3 12A9 3 0 0 0 21 12"/>
        </svg>
      ),
    },
    {
      key: 'about',
      label: 'About',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 16v-4"/>
          <path d="M12 8h.01"/>
        </svg>
      ),
    },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'account':
        return (
          <div className="space-y-6">
            <div className="bg-white border border-zinc-200 rounded-xl p-4">
              <h3 className="text-sm font-semibold text-zinc-900 mb-4">Account Information</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs text-zinc-500 mb-1">Username</label>
                  <input
                    type="text"
                    defaultValue="user@example.com"
                    className="w-full px-3 py-2 text-sm border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs text-zinc-500 mb-1">Display Name</label>
                  <input
                    type="text"
                    defaultValue="Novel Writer"
                    className="w-full px-3 py-2 text-sm border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                  />
                </div>
              </div>
            </div>
          </div>
        );
      case 'general':
        return (
          <div className="space-y-3">
            {/* AI Configuration - Collapsible */}
            <CollapsibleSection
              title="AI Configuration"
              subtitle="Configure AI Model (OpenAI Compatible)"
              defaultExpanded={true}
              alignSubtitle="left"
              badge={
                <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium text-emerald-700 bg-emerald-50 rounded-full">
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M20 6 9 17l-5-5"/>
                  </svg>
                  Built-in Key Active
                </span>
              }
            >
              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-zinc-500 mb-1">OpenAI API Key</label>
                  <input
                    type="password"
                    placeholder="sk-..."
                    className="w-full px-3 py-2 text-sm border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs text-zinc-500 mb-1">Claude API Key</label>
                  <input
                    type="password"
                    placeholder="..."
                    className="w-full px-3 py-2 text-sm border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs text-zinc-500 mb-1">DeepSeek API Key</label>
                  <input
                    type="password"
                    placeholder="..."
                    className="w-full px-3 py-2 text-sm border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                  />
                </div>
              </div>
            </CollapsibleSection>

            {/* Appearance - Collapsible */}
            <CollapsibleSection
              title="Appearance"
              defaultExpanded={false}
            >
              <div className="space-y-4">
                {/* Theme Toggle */}
                <div className="flex items-center justify-between">
                  <div>
                    <label className="block text-sm font-medium text-zinc-700">Theme</label>
                    <p className="text-xs text-zinc-500">Choose your preferred theme</p>
                  </div>
                  <ToggleSwitch leftLabel="Light" rightLabel="Dark" defaultChecked={false} />
                </div>

                {/* Font Toggle */}
                <div className="flex items-center justify-between">
                  <div>
                    <label className="block text-sm font-medium text-zinc-700">Font</label>
                    <p className="text-xs text-zinc-500">Editor font style</p>
                  </div>
                  <ToggleSwitch leftLabel="Sans" rightLabel="Serif" defaultChecked={false} />
                </div>
              </div>
            </CollapsibleSection>

            {/* Language - Single Row Card with Toggle */}
            <div className="bg-white border border-zinc-200 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-zinc-900">Language</h3>
                  <p className="text-xs text-zinc-500 mt-0.5">Display language for interface</p>
                </div>
                <ToggleSwitch leftLabel="EN" rightLabel="中文" defaultChecked={false} />
              </div>
            </div>
          </div>
        );
        
      case 'token':
        return (
          <div className="space-y-4">
            {/* Token 限制开关 */}
            <div className="bg-white border border-zinc-200 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-zinc-900">启用 Token 每日限制</h3>
                  <p className="text-xs text-zinc-500 mt-0.5">控制每日 LLM Token 消耗上限</p>
                </div>
                <ToggleSwitch 
                  leftLabel="关闭" 
                  rightLabel="开启" 
                  defaultChecked={tokenSettings.enabled}
                  onChange={(checked) => {
                    setTokenSettings(prev => ({ ...prev, enabled: checked }));
                    saveTokenSettings();
                  }}
                />
              </div>
            </div>
            
            {/* 每日限制设置 */}
            {tokenSettings.enabled && (
              <>
                <div className="bg-white border border-zinc-200 rounded-xl p-4">
                  <h3 className="text-sm font-semibold text-zinc-900 mb-4">每日 Token 限制</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-xs text-zinc-500 mb-1">
                        每日上限 (tokens) <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        inputMode="numeric"
                        pattern="[0-9]*"
                        value={tokenSettings.daily_limit === 0 ? '' : tokenSettings.daily_limit}
                        onChange={(e) => {
                          const value = e.target.value;
                          // 只允许数字输入
                          if (value === '' || /^\d+$/.test(value)) {
                            const newLimit = value === '' ? 0 : parseInt(value);
                            setTokenSettings(prev => ({ 
                              ...prev, 
                              daily_limit: newLimit
                            }));
                          }
                        }}
                        onBlur={(e) => {
                          const value = e.target.value;
                          // 如果为空或无效，恢复默认值
                          if (value === '' || parseInt(value) < 1000) {
                            alert('每日用量必须填写，且不能少于 1000 tokens');
                            setTokenSettings(prev => ({ 
                              ...prev, 
                              daily_limit: 50000
                            }));
                          }
                          saveTokenSettings();
                        }}
                        className="w-full px-3 py-2 text-sm border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                      />
                      <p className="text-xs text-zinc-400 mt-1">
                        推荐: 50,000 tokens/天 (约 ¥3-5)
                      </p>
                    </div>
                    
                    <div>
                      <label className="block text-xs text-zinc-500 mb-1">
                        警告阈值 (%)
                      </label>
                      <input
                        type="number"
                        min="50"
                        max="95"
                        value={Math.round(tokenSettings.warning_threshold * 100)}
                        onChange={(e) => {
                          setTokenSettings(prev => ({ 
                            ...prev, 
                            warning_threshold: parseInt(e.target.value) / 100 
                          }));
                        }}
                        onBlur={saveTokenSettings}
                        className="w-full px-3 py-2 text-sm border border-zinc-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                      />
                    </div>
                  </div>
                </div>
                
                {/* Token 预算分配 */}
                <CollapsibleSection
                  title="Token 预算分配"
                  subtitle="各 Agent 预算占比"
                  defaultExpanded={false}
                >
                  <div className="space-y-3">
                    {Object.entries(tokenSettings.budget_allocation).map(([agent, ratio]) => (
                      <div key={agent} className="flex items-center justify-between">
                        <span className="text-sm text-zinc-700 capitalize">
                          {agent === 'planner' && '规划 Agent'}
                          {agent === 'discussion' && '讨论 Agent'}
                          {agent === 'conflict' && '冲突 Agent'}
                          {agent === 'writing' && '写作 Agent'}
                          {agent === 'editor' && '编辑 Agent'}
                          {agent === 'reader' && '读者 Agent'}
                          {agent === 'summary' && '总结 Agent'}
                        </span>
                        <div className="flex items-center gap-2">
                          <input
                            type="range"
                            min="1"
                            max="50"
                            value={Math.round(ratio * 100)}
                            onChange={(e) => {
                              const newRatio = parseInt(e.target.value) / 100;
                              setTokenSettings(prev => ({
                                ...prev,
                                budget_allocation: {
                                  ...prev.budget_allocation,
                                  [agent]: newRatio
                                }
                              }));
                            }}
                            onBlur={saveTokenSettings}
                            className="w-24"
                          />
                          <span className="text-xs text-zinc-500 w-12 text-right">
                            {Math.round(ratio * 100)}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CollapsibleSection>
                
                {/* 今日使用情况 - 使用用户设置的 daily_limit */}
                <div className="bg-white border border-zinc-200 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-semibold text-zinc-900">今日使用情况</h3>
                    <button
                      onClick={resetDailyToken}
                      className="text-xs text-indigo-600 hover:text-indigo-700"
                    >
                      重置
                    </button>
                  </div>
                  
                  <div className="space-y-3">
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-zinc-700">已使用</span>
                        <span className="text-sm text-zinc-500">
                          {tokenStatus.daily_used.toLocaleString()} / {tokenSettings.daily_limit.toLocaleString()}
                        </span>
                      </div>
                      <div className="w-full h-2 bg-zinc-100 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full transition-all ${
                            (tokenStatus.daily_used / tokenSettings.daily_limit) > 0.9 ? 'bg-red-500' :
                            (tokenStatus.daily_used / tokenSettings.daily_limit) > 0.7 ? 'bg-amber-500' :
                            'bg-emerald-500'
                          }`}
                          style={{ width: `${Math.min((tokenStatus.daily_used / tokenSettings.daily_limit) * 100, 100)}%` }}
                        />
                      </div>
                      <p className="text-xs text-zinc-400 mt-1">
                        使用率: {((tokenStatus.daily_used / tokenSettings.daily_limit) * 100).toFixed(1)}%
                      </p>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 pt-2">
                      <div className="bg-zinc-50 rounded-lg p-3">
                        <p className="text-xs text-zinc-500">剩余 Token</p>
                        <p className="text-lg font-semibold text-zinc-900">
                          {Math.max(0, tokenSettings.daily_limit - tokenStatus.daily_used).toLocaleString()}
                        </p>
                      </div>
                      <div className="bg-zinc-50 rounded-lg p-3">
                        <p className="text-xs text-zinc-500">预计可写</p>
                        <p className="text-lg font-semibold text-zinc-900">
                          ~{Math.max(0, Math.floor((tokenSettings.daily_limit - tokenStatus.daily_used) / 15000))} 章
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        );
        
      case 'generation':
        return (
          <div className="space-y-4">
            {/* Agent 讨论设置 */}
            <CollapsibleSection
              title="Agent 讨论设置"
              subtitle="控制讨论轮次和发言长度"
              defaultExpanded={true}
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="block text-sm font-medium text-zinc-700">最大讨论轮数</label>
                    <p className="text-xs text-zinc-500">限制讨论轮次以节省 Token</p>
                  </div>
                  <select
                    value={generationSettings.max_rounds}
                    onChange={(e) => {
                      setGenerationSettings(prev => ({ 
                        ...prev, 
                        max_rounds: parseInt(e.target.value) 
                      }));
                      saveGenerationSettings();
                    }}
                    className="px-3 py-2 text-sm border border-zinc-200 rounded-lg"
                  >
                    <option value={1}>1 轮</option>
                    <option value={2}>2 轮 (推荐)</option>
                    <option value={3}>3 轮</option>
                  </select>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <label className="block text-sm font-medium text-zinc-700">短发言模式</label>
                    <p className="text-xs text-zinc-500">限制每次发言在 80 tokens 以内</p>
                  </div>
                  <ToggleSwitch 
                    leftLabel="关闭" 
                    rightLabel="开启" 
                    defaultChecked={generationSettings.enable_short_mode}
                    onChange={(checked) => {
                      setGenerationSettings(prev => ({ ...prev, enable_short_mode: checked }));
                      saveGenerationSettings();
                    }}
                  />
                </div>
                
                {generationSettings.enable_short_mode && (
                  <div>
                    <label className="block text-xs text-zinc-500 mb-1">
                      最大发言长度 (tokens)
                    </label>
                    <input
                      type="number"
                      min="50"
                      max="200"
                      value={generationSettings.max_tokens_per_response}
                      onChange={(e) => {
                        setGenerationSettings(prev => ({ 
                          ...prev, 
                          max_tokens_per_response: parseInt(e.target.value) || 80 
                        }));
                      }}
                      onBlur={saveGenerationSettings}
                      className="w-full px-3 py-2 text-sm border border-zinc-200 rounded-lg"
                    />
                  </div>
                )}
              </div>
            </CollapsibleSection>
            
            {/* 写作生成设置 */}
            <CollapsibleSection
              title="写作生成设置"
              subtitle="分段生成和流式输出"
              defaultExpanded={true}
            >
              <div className="space-y-4">
                <div>
                  <label className="block text-xs text-zinc-500 mb-1">
                    每段字数
                  </label>
                  <input
                    type="number"
                    min="300"
                    max="1000"
                    step="100"
                    value={generationSettings.paragraph_length}
                    onChange={(e) => {
                      setGenerationSettings(prev => ({ 
                        ...prev, 
                        paragraph_length: parseInt(e.target.value) || 500 
                      }));
                    }}
                    onBlur={saveGenerationSettings}
                    className="w-full px-3 py-2 text-sm border border-zinc-200 rounded-lg"
                  />
                  <p className="text-xs text-zinc-400 mt-1">
                    分段生成可更好控制 Token 使用
                  </p>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <label className="block text-sm font-medium text-zinc-700">流式生成</label>
                    <p className="text-xs text-zinc-500">实时显示生成内容</p>
                  </div>
                  <ToggleSwitch 
                    leftLabel="关闭" 
                    rightLabel="开启" 
                    defaultChecked={generationSettings.enable_streaming}
                    onChange={(checked) => {
                      setGenerationSettings(prev => ({ ...prev, enable_streaming: checked }));
                      saveGenerationSettings();
                    }}
                  />
                </div>
              </div>
            </CollapsibleSection>
            
            {/* Reader Agent 设置 */}
            <CollapsibleSection
              title="Reader Agent 设置"
              subtitle="控制读者反馈频率"
              defaultExpanded={false}
            >
              <div className="space-y-4">
                <div>
                  <label className="block text-xs text-zinc-500 mb-1">
                    调用间隔 (章数)
                  </label>
                  <select
                    value={generationSettings.reader_interval}
                    onChange={(e) => {
                      setGenerationSettings(prev => ({ 
                        ...prev, 
                        reader_interval: parseInt(e.target.value) 
                      }));
                      saveGenerationSettings();
                    }}
                    className="w-full px-3 py-2 text-sm border border-zinc-200 rounded-lg"
                  >
                    <option value={1}>每章 (最精确)</option>
                    <option value={2}>每 2 章</option>
                    <option value={3}>每 3 章 (推荐)</option>
                    <option value={5}>每 5 章 (最省 Token)</option>
                  </select>
                  <p className="text-xs text-zinc-400 mt-1">
                    Reader Agent 消耗较多 Token，建议每 3 章调用一次
                  </p>
                </div>
              </div>
            </CollapsibleSection>
            
            {/* 优化说明 */}
            <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4">
              <h4 className="text-sm font-semibold text-indigo-900 mb-2">优化效果预估</h4>
              <div className="space-y-1 text-xs text-indigo-700">
                <p>• 2轮讨论 + 短发言: 节省 40% Token</p>
                <p>• 分段生成: 失败率降低 80%</p>
                <p>• Reader 每3章: 节省 15% Token</p>
                <p>• 综合优化: 节省 50-60% Token</p>
              </div>
            </div>
          </div>
        );
        
      case 'notifications':
        return (
          <div className="space-y-4">
            <div className="bg-white border border-zinc-200 rounded-xl p-4">
              <h3 className="text-sm font-semibold text-zinc-900 mb-4">Notification Preferences</h3>
              <div className="space-y-3">
                <label className="flex items-center justify-between">
                  <span className="text-sm text-zinc-700">Email notifications</span>
                  <input type="checkbox" className="w-4 h-4 rounded border-zinc-300 text-indigo-600 focus:ring-indigo-500" />
                </label>
                <label className="flex items-center justify-between">
                  <span className="text-sm text-zinc-700">Push notifications</span>
                  <input type="checkbox" className="w-4 h-4 rounded border-zinc-300 text-indigo-600 focus:ring-indigo-500" />
                </label>
                <label className="flex items-center justify-between">
                  <span className="text-sm text-zinc-700">Agent completion alerts</span>
                  <input type="checkbox" defaultChecked className="w-4 h-4 rounded border-zinc-300 text-indigo-600 focus:ring-indigo-500" />
                </label>
                <label className="flex items-center justify-between">
                  <span className="text-sm text-zinc-700">Token usage warnings</span>
                  <input type="checkbox" defaultChecked className="w-4 h-4 rounded border-zinc-300 text-indigo-600 focus:ring-indigo-500" />
                </label>
              </div>
            </div>
          </div>
        );
      case 'storage':
        return (
          <div className="space-y-4">
            <div className="bg-white border border-zinc-200 rounded-xl p-4">
              <h3 className="text-sm font-semibold text-zinc-900 mb-4">Storage Management</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-zinc-700">Storage Used</span>
                    <span className="text-sm text-zinc-500">45MB / 100MB</span>
                  </div>
                  <div className="w-full h-2 bg-zinc-100 rounded-full overflow-hidden">
                    <div className="w-[45%] h-full bg-indigo-500 rounded-full" />
                  </div>
                </div>
                <div className="flex gap-3">
                  <button className="flex-1 px-4 py-2 text-sm font-medium text-zinc-700 bg-zinc-100 rounded-lg hover:bg-zinc-200 transition-colors">
                    Clear Cache
                  </button>
                  <button className="flex-1 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors">
                    Export Data
                  </button>
                </div>
              </div>
            </div>
            
            {/* Agent 缓存 */}
            <div className="bg-white border border-zinc-200 rounded-xl p-4">
              <h3 className="text-sm font-semibold text-zinc-900 mb-4">Agent 结果缓存</h3>
              <div className="space-y-3">
                <label className="flex items-center justify-between">
                  <span className="text-sm text-zinc-700">启用 Planner 缓存</span>
                  <input 
                    type="checkbox" 
                    defaultChecked 
                    className="w-4 h-4 rounded border-zinc-300 text-indigo-600 focus:ring-indigo-500" 
                  />
                </label>
                <label className="flex items-center justify-between">
                  <span className="text-sm text-zinc-700">启用 Conflict 缓存</span>
                  <input 
                    type="checkbox" 
                    defaultChecked 
                    className="w-4 h-4 rounded border-zinc-300 text-indigo-600 focus:ring-indigo-500" 
                  />
                </label>
                <label className="flex items-center justify-between">
                  <span className="text-sm text-zinc-700">启用 Consistency 缓存</span>
                  <input 
                    type="checkbox" 
                    defaultChecked 
                    className="w-4 h-4 rounded border-zinc-300 text-indigo-600 focus:ring-indigo-500" 
                  />
                </label>
              </div>
            </div>
          </div>
        );
      case 'about':
        return (
          <div className="space-y-4">
            <div className="bg-white border border-zinc-200 rounded-xl p-4">
              <h3 className="text-sm font-semibold text-zinc-900 mb-4">About Novel Agent Studio</h3>
              <div className="space-y-2 text-sm text-zinc-600">
                <p>Version: 3.0.0</p>
                <p>Build: 2024.03.07</p>
                <p>© 2024 Novel Agent Studio. All rights reserved.</p>
              </div>
            </div>
            
            <div className="bg-white border border-zinc-200 rounded-xl p-4">
              <h3 className="text-sm font-semibold text-zinc-900 mb-4">Token 优化功能</h3>
              <div className="space-y-2 text-xs text-zinc-600">
                <p>✓ Token Budget Manager - 预算分配和监控</p>
                <p>✓ 讨论轮次控制 - 最多2轮讨论</p>
                <p>✓ 短发言模式 - 80 tokens限制</p>
                <p>✓ 上下文压缩 - 3000→200 tokens</p>
                <p>✓ Agent 结果缓存 - 避免重复调用</p>
                <p>✓ 分段写作生成 - 500字/段</p>
                <p>✓ Reader Agent 调度 - 每3章一次</p>
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/30 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative w-full max-w-3xl h-[600px] bg-zinc-50 rounded-2xl shadow-2xl overflow-hidden flex">
        {/* Sidebar */}
        <div className="w-56 bg-zinc-50 border-r border-zinc-200 p-4">
          <h2 className="text-lg font-semibold text-zinc-900 mb-6 px-2">Settings</h2>
          <nav className="space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === tab.key
                    ? 'bg-white text-zinc-900 shadow-sm'
                    : 'text-zinc-600 hover:bg-zinc-100'
                }`}
              >
                <span className={activeTab === tab.key ? 'text-zinc-900' : 'text-zinc-400'}>
                  {tab.icon}
                </span>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 flex flex-col bg-zinc-50/50">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-200">
            <h3 className="text-lg font-semibold text-zinc-900 capitalize">{activeTab}</h3>
            <button
              onClick={onClose}
              className="p-2 text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100 rounded-lg transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
              </svg>
            </button>
          </div>

          {/* Scrollable Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {renderContent()}
          </div>
        </div>
      </div>
    </div>
  );
};

// 为了保持向后兼容，导出一个默认的包装组件
const Settings: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-zinc-900">系统设置</h1>
        <p className="text-sm text-zinc-500 mt-1">管理应用的全局参数、API密钥和外观。</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-8">
          <SettingsSection title="API Keys">
            <SettingsInput label="OpenAI API Key" type="password" placeholder="sk-..." />
            <SettingsInput label="Claude API Key" type="password" placeholder="..." />
            <SettingsInput label="DeepSeek API Key" type="password" placeholder="..." />
          </SettingsSection>

          <SettingsSection title="Appearance">
            <SettingsSelect label="Theme" defaultValue="System">
              <option>System</option>
              <option>Light</option>
              <option>Dark</option>
            </SettingsSelect>
            <SettingsInput label="Background Color" defaultValue="#F4F4F5" />
            <SettingsSelect label="Font" defaultValue="Default">
              <option>Default</option>
              <option>Serif</option>
              <option>Mono</option>
            </SettingsSelect>
          </SettingsSection>
        </div>

        <div className="space-y-8">
          <SettingsSection title="Model Defaults">
            <SettingsSelect label="Default Model" defaultValue="GPT-4o">
              <option>GPT-4o</option>
              <option>Claude 3 Sonnet</option>
              <option>DeepSeek V2</option>
            </SettingsSelect>
            <SettingsInput label="Token Limit" defaultValue="4096" />
          </SettingsSection>

          <SettingsSection title="System">
            <SettingsSelect label="Debug Mode" defaultValue="Disabled">
              <option>Disabled</option>
              <option>Enabled</option>
            </SettingsSelect>
            <button className="w-full text-center text-xs font-bold text-zinc-600 bg-zinc-100 hover:bg-zinc-200 p-2 rounded-lg transition-colors">Clear Cache</button>
            <button className="w-full text-center text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 p-2 rounded-lg transition-colors">Export Data</button>
          </SettingsSection>
        </div>
      </div>
    </div>
  );
};

const SettingsSection: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div className="bg-white border border-zinc-200 rounded-2xl shadow-sm">
    <div className="p-4 border-b border-zinc-100">
      <h3 className="text-sm font-bold text-zinc-800">{title}</h3>
    </div>
    <div className="p-6 space-y-4">
      {children}
    </div>
  </div>
);

const SettingsInput: React.FC<{ label: string; type?: string; placeholder?: string; defaultValue?: string; }> = ({ label, type = 'text', placeholder, defaultValue }) => (
  <div>
    <label className="block text-xs font-medium text-zinc-600 mb-1">{label}</label>
    <input 
      type={type} 
      placeholder={placeholder}
      defaultValue={defaultValue}
      className="w-full p-2 text-xs border border-zinc-200 rounded-lg focus:ring-2 focus:ring-indigo-500/50 outline-none bg-zinc-50/50"
    />
  </div>
);

const SettingsSelect: React.FC<{ label: string; defaultValue?: string; children: React.ReactNode }> = ({ label, defaultValue, children }) => (
  <div>
    <label className="block text-xs font-medium text-zinc-600 mb-1">{label}</label>
    <select 
      defaultValue={defaultValue}
      className="w-full p-2 text-xs border border-zinc-200 rounded-lg focus:ring-2 focus:ring-indigo-500/50 outline-none bg-zinc-50/50"
    >
      {children}
    </select>
  </div>
);

export { SettingsModal };
export default Settings;
