import React, { useState } from 'react';

type SettingsTab = 'account' | 'general' | 'notifications' | 'storage' | 'about';

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
  alignSubtitle = 'withTitle',
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

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<SettingsTab>('general');

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
          </div>
        );
      case 'about':
        return (
          <div className="space-y-4">
            <div className="bg-white border border-zinc-200 rounded-xl p-4">
              <h3 className="text-sm font-semibold text-zinc-900 mb-4">About Novel Agent Studio</h3>
              <div className="space-y-2 text-sm text-zinc-600">
                <p>Version: 1.0.0</p>
                <p>Build: 2024.03.07</p>
                <p>© 2024 Novel Agent Studio. All rights reserved.</p>
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
