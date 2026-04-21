-- 创建系统设置表
CREATE TABLE IF NOT EXISTS system_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Token 设置
    token_enabled BOOLEAN DEFAULT FALSE,
    token_daily_limit INTEGER DEFAULT 50000,
    token_warning_threshold FLOAT DEFAULT 0.8,
    token_budget_allocation JSONB DEFAULT '{
        "planner": 0.10,
        "discussion": 0.13,
        "conflict": 0.07,
        "writing": 0.47,
        "editor": 0.13,
        "reader": 0.07,
        "summary": 0.03
    }'::jsonb,
    
    -- 讨论设置
    discussion_max_rounds INTEGER DEFAULT 2,
    discussion_max_tokens INTEGER DEFAULT 80,
    discussion_enable_short_mode BOOLEAN DEFAULT TRUE,
    discussion_min_interval INTEGER DEFAULT 3,
    
    -- 缓存设置
    cache_enable_planner BOOLEAN DEFAULT TRUE,
    cache_enable_conflict BOOLEAN DEFAULT TRUE,
    cache_enable_consistency BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建全局资产表
CREATE TABLE IF NOT EXISTS global_assets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('characters', 'worldbuilding', 'factions', 'locations', 'timeline')),
    description TEXT,
    source_novel_id TEXT NOT NULL,
    source_novel_name TEXT NOT NULL,
    color TEXT,
    is_starred BOOLEAN DEFAULT FALSE,
    active_version_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建资产版本表
CREATE TABLE IF NOT EXISTS asset_versions (
    id TEXT PRIMARY KEY,
    asset_id TEXT REFERENCES global_assets(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建小说资产映射表
CREATE TABLE IF NOT EXISTS novel_asset_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    novel_id TEXT NOT NULL,
    asset_id TEXT REFERENCES global_assets(id) ON DELETE CASCADE,
    reference_type TEXT DEFAULT 'linked', -- 'linked' | 'cloned'
    version_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建 Agent 技能表
CREATE TABLE IF NOT EXISTS agent_skills (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    asset_id TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    content TEXT NOT NULL,
    target_agents TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建小说技能映射表
CREATE TABLE IF NOT EXISTS novel_skill_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    novel_id TEXT NOT NULL,
    skill_id TEXT REFERENCES agent_skills(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 添加更新时间触发器
DROP TRIGGER IF EXISTS update_system_settings_updated_at ON system_settings;
CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON system_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_global_assets_updated_at ON global_assets;
CREATE TRIGGER update_global_assets_updated_at BEFORE UPDATE ON global_assets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_agent_skills_updated_at ON agent_skills;
CREATE TRIGGER update_agent_skills_updated_at BEFORE UPDATE ON agent_skills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 启用 RLS
ALTER TABLE system_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE global_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE asset_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE novel_asset_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE novel_skill_mappings ENABLE ROW LEVEL SECURITY;

-- 创建访问策略
DROP POLICY IF EXISTS "Allow users to manage own settings" ON system_settings;
CREATE POLICY "Allow users to manage own settings" ON system_settings
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Allow public read access" ON global_assets;
CREATE POLICY "Allow public read access" ON global_assets
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow authenticated users to modify" ON global_assets;
CREATE POLICY "Allow authenticated users to modify" ON global_assets
    FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Allow public read access" ON asset_versions;
CREATE POLICY "Allow public read access" ON asset_versions
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow authenticated users to modify" ON asset_versions;
CREATE POLICY "Allow authenticated users to modify" ON asset_versions
    FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Allow public read access" ON novel_asset_mappings;
CREATE POLICY "Allow public read access" ON novel_asset_mappings
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow authenticated users to modify" ON novel_asset_mappings;
CREATE POLICY "Allow authenticated users to modify" ON novel_asset_mappings
    FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Allow public read access" ON agent_skills;
CREATE POLICY "Allow public read access" ON agent_skills
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow authenticated users to modify" ON agent_skills;
CREATE POLICY "Allow authenticated users to modify" ON agent_skills
    FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Allow public read access" ON novel_skill_mappings;
CREATE POLICY "Allow public read access" ON novel_skill_mappings
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow authenticated users to modify" ON novel_skill_mappings;
CREATE POLICY "Allow authenticated users to modify" ON novel_skill_mappings
    FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');
