import { create } from 'zustand';

export type AssetType = 'characters' | 'worldbuilding' | 'factions' | 'locations' | 'timeline';

export type AgentType = 'writer' | 'editor' | 'planner' | 'conflict' | 'reader' | 'summary';

export interface AssetVersion {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  data: Record<string, any>;
}

export interface GlobalAsset {
  id: string;
  name: string;
  type: AssetType;
  description?: string;
  source_novel_id: string;
  source_novel_name: string;
  color?: string;
  is_starred: boolean;
  mount_count: number;
  created_at: string;
  updated_at: string;
  version_count: number;
  versions?: AssetVersion[];
  active_version_id?: string | null;
}

export interface MountInfo {
  reference_type: 'linked' | 'cloned';
  version_id?: string | null;
}

export interface AgentSkill {
  id: string;
  name: string;
  description: string;
  asset_id: string;
  asset_type: AssetType;
  target_agents: AgentType[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface AssetState {
  // 资产数据
  assets: GlobalAsset[];
  isLoading: boolean;
  error: string | null;

  // 当前选中的资产
  selectedAssetId: string | null;

  // 当前小说的挂载资产
  mountedAssets: Record<string, string[]>; // novelId -> assetIds
  mountInfos: Record<string, MountInfo>; // assetId -> mountInfo

  // Agent技能数据
  agentSkills: AgentSkill[];
  assetSkills: Record<string, string[]>; // assetId -> skillIds

  // Actions
  setAssets: (assets: GlobalAsset[]) => void;
  setSelectedAsset: (assetId: string | null) => void;
  addAsset: (asset: GlobalAsset) => void;
  updateAsset: (assetId: string, updates: Partial<GlobalAsset>) => void;
  deleteAsset: (assetId: string) => void;

  // API Actions
  fetchAllAssets: () => Promise<void>;
  fetchAssetsByType: (type: AssetType) => Promise<void>;
  fetchAssetsByNovel: (novelId: string) => Promise<void>;
  fetchMountedAssets: (novelId: string) => Promise<void>;
  createAsset: (asset: Omit<GlobalAsset, 'mount_count' | 'created_at' | 'updated_at' | 'version_count'>) => Promise<GlobalAsset | null>;
  mountAssetToNovel: (assetId: string, novelId: string, referenceType?: 'linked' | 'cloned', versionId?: string) => Promise<boolean>;
  unmountAssetFromNovel: (assetId: string, novelId: string) => Promise<boolean>;
  toggleStarAsset: (assetId: string) => Promise<boolean>;
  searchAssets: (query: string) => Promise<void>;

  // Agent Skill Actions
  fetchSkillsByAsset: (assetId: string) => Promise<void>;
  createSkillFromAsset: (assetId: string, skillName: string, description: string, targetAgents: AgentType[], novelId?: string) => Promise<AgentSkill | null>;
  toggleSkillActive: (skillId: string) => Promise<boolean>;
  deleteSkill: (skillId: string) => Promise<boolean>;

  // Getters
  getAssetById: (assetId: string) => GlobalAsset | undefined;
  getAssetsByType: (type: AssetType) => GlobalAsset[];
  getStarredAssets: () => GlobalAsset[];
  isAssetMounted: (assetId: string, novelId: string) => boolean;
  getSkillsByAssetId: (assetId: string) => AgentSkill[];
}

const API_BASE = 'http://localhost:8000';

export const useAssetStore = create<AssetState>((set, get) => ({
  assets: [],
  isLoading: false,
  error: null,
  selectedAssetId: null,
  mountedAssets: {},
  mountInfos: {},
  agentSkills: [],
  assetSkills: {},

  setAssets: (assets) => set({ assets }),
  
  setSelectedAsset: (assetId) => set({ selectedAssetId: assetId }),
  
  addAsset: (asset) => set((state) => ({ 
    assets: [...state.assets, asset] 
  })),
  
  updateAsset: (assetId, updates) => set((state) => ({
    assets: state.assets.map(a => 
      a.id === assetId ? { ...a, ...updates } : a
    )
  })),
  
  deleteAsset: (assetId) => set((state) => ({
    assets: state.assets.filter(a => a.id !== assetId)
  })),

  // ==================== API Actions ====================
  
  fetchAllAssets: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/api/assets/all`);
      if (!response.ok) throw new Error('Failed to fetch assets');
      const data = await response.json();
      set({ assets: data, isLoading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Unknown error', isLoading: false });
    }
  },

  fetchAssetsByType: async (type: AssetType) => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/api/assets/by-type/${type}`);
      if (!response.ok) throw new Error('Failed to fetch assets');
      const data = await response.json();
      set({ assets: data, isLoading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Unknown error', isLoading: false });
    }
  },

  fetchAssetsByNovel: async (novelId: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/api/assets/by-novel/${novelId}`);
      if (!response.ok) throw new Error('Failed to fetch assets');
      const data = await response.json();
      set({ assets: data, isLoading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Unknown error', isLoading: false });
    }
  },

  fetchMountedAssets: async (novelId: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/api/assets/novel/${novelId}/mounted`);
      if (!response.ok) throw new Error('Failed to fetch mounted assets');
      const data = await response.json();
      
      // 更新挂载状态
      const assetIds = data.map((a: GlobalAsset) => a.id);
      set((state) => ({
        mountedAssets: { ...state.mountedAssets, [novelId]: assetIds },
        isLoading: false
      }));
      
      // 获取每个资产的挂载信息
      for (const asset of data) {
        const mountResponse = await fetch(
          `${API_BASE}/api/assets/${asset.id}/mount-status?novel_id=${novelId}`
        );
        if (mountResponse.ok) {
          const mountData = await mountResponse.json();
          if (mountData.mount_info) {
            set((state) => ({
              mountInfos: {
                ...state.mountInfos,
                [`${novelId}:${asset.id}`]: mountData.mount_info
              }
            }));
          }
        }
      }
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Unknown error', isLoading: false });
    }
  },

  createAsset: async (asset) => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/api/assets/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(asset)
      });
      if (!response.ok) throw new Error('Failed to create asset');
      const data = await response.json();
      set((state) => ({ 
        assets: [...state.assets, data],
        isLoading: false 
      }));
      return data;
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Unknown error', isLoading: false });
      return null;
    }
  },

  mountAssetToNovel: async (assetId, novelId, referenceType = 'linked', versionId) => {
    try {
      const response = await fetch(`${API_BASE}/api/assets/mount`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          asset_id: assetId,
          novel_id: novelId,
          reference_type: referenceType,
          version_id: versionId
        })
      });
      if (!response.ok) return false;
      
      // 更新本地状态
      set((state) => ({
        mountedAssets: {
          ...state.mountedAssets,
          [novelId]: [...(state.mountedAssets[novelId] || []), assetId]
        },
        mountInfos: {
          ...state.mountInfos,
          [`${novelId}:${assetId}`]: { reference_type: referenceType, version_id: versionId }
        }
      }));
      
      // 更新资产的mount_count
      const asset = get().assets.find(a => a.id === assetId);
      if (asset) {
        get().updateAsset(assetId, { mount_count: (asset.mount_count || 0) + 1 });
      }
      
      return true;
    } catch {
      return false;
    }
  },

  unmountAssetFromNovel: async (assetId, novelId) => {
    try {
      const response = await fetch(`${API_BASE}/api/assets/unmount?asset_id=${assetId}&novel_id=${novelId}`, {
        method: 'POST'
      });
      if (!response.ok) return false;
      
      // 更新本地状态
      set((state) => ({
        mountedAssets: {
          ...state.mountedAssets,
          [novelId]: (state.mountedAssets[novelId] || []).filter(id => id !== assetId)
        }
      }));
      
      // 更新资产的mount_count
      const asset = get().assets.find(a => a.id === assetId);
      if (asset && asset.mount_count > 0) {
        get().updateAsset(assetId, { mount_count: asset.mount_count - 1 });
      }
      
      return true;
    } catch {
      return false;
    }
  },

  toggleStarAsset: async (assetId) => {
    try {
      const response = await fetch(`${API_BASE}/api/assets/${assetId}/toggle-star`, {
        method: 'POST'
      });
      if (!response.ok) return false;
      const data = await response.json();
      
      // 更新本地状态
      get().updateAsset(assetId, { is_starred: data.is_starred });
      return data.is_starred;
    } catch {
      return false;
    }
  },

  searchAssets: async (query) => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/api/assets/search?query=${encodeURIComponent(query)}`);
      if (!response.ok) throw new Error('Failed to search assets');
      const data = await response.json();
      set({ assets: data, isLoading: false });
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Unknown error', isLoading: false });
    }
  },

  // ==================== Getters ====================
  
  getAssetById: (assetId) => {
    return get().assets.find(a => a.id === assetId);
  },

  getAssetsByType: (type) => {
    return get().assets.filter(a => a.type === type);
  },

  getStarredAssets: () => {
    return get().assets.filter(a => a.is_starred);
  },

  isAssetMounted: (assetId, novelId) => {
    return get().mountedAssets[novelId]?.includes(assetId) || false;
  },

  // ==================== Agent Skill Actions ====================

  fetchSkillsByAsset: async (assetId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/assets/${assetId}/skills`);
      if (!response.ok) throw new Error('Failed to fetch skills');
      const data = await response.json();

      set((state) => ({
        agentSkills: [...state.agentSkills.filter(s => s.asset_id !== assetId), ...data],
        assetSkills: {
          ...state.assetSkills,
          [assetId]: data.map((s: AgentSkill) => s.id)
        }
      }));
    } catch (err) {
      console.error('Failed to fetch skills:', err);
    }
  },

  createSkillFromAsset: async (assetId, skillName, description, targetAgents, novelId) => {
    const asset = get().getAssetById(assetId);
    if (!asset) return null;

    try {
      const response = await fetch(`${API_BASE}/api/assets/skills/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          skill_id: `skill-${Date.now()}`,
          skill_name: skillName,
          description,
          asset_id: assetId,
          asset_type: asset.type,
          asset_content: asset.description || '',
          target_agents: targetAgents,
          novel_id: novelId
        })
      });

      if (!response.ok) throw new Error('Failed to create skill');
      const data = await response.json();

      set((state) => ({
        agentSkills: [...state.agentSkills, data],
        assetSkills: {
          ...state.assetSkills,
          [assetId]: [...(state.assetSkills[assetId] || []), data.id]
        }
      }));

      return data;
    } catch (err) {
      console.error('Failed to create skill:', err);
      return null;
    }
  },

  toggleSkillActive: async (skillId) => {
    try {
      const response = await fetch(`${API_BASE}/api/assets/skills/${skillId}/toggle`, {
        method: 'POST'
      });
      if (!response.ok) return false;
      const data = await response.json();

      set((state) => ({
        agentSkills: state.agentSkills.map(s =>
          s.id === skillId ? { ...s, is_active: data.is_active } : s
        )
      }));

      return data.is_active;
    } catch {
      return false;
    }
  },

  deleteSkill: async (skillId) => {
    try {
      const response = await fetch(`${API_BASE}/api/assets/skills/${skillId}`, {
        method: 'DELETE'
      });
      if (!response.ok) return false;

      set((state) => ({
        agentSkills: state.agentSkills.filter(s => s.id !== skillId),
        assetSkills: Object.fromEntries(
          Object.entries(state.assetSkills).map(([assetId, skillIds]) => [
            assetId,
            skillIds.filter(id => id !== skillId)
          ])
        )
      }));

      return true;
    } catch {
      return false;
    }
  },

  getSkillsByAssetId: (assetId) => {
    return get().agentSkills.filter(s => s.asset_id === assetId);
  }
}));
