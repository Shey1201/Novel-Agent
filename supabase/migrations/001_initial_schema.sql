-- 创建小说表
CREATE TABLE IF NOT EXISTS novels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'Untitled Story',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    locked BOOLEAN DEFAULT FALSE,
    category_id TEXT,
    mounted_skills TEXT[] DEFAULT '{}'
);

-- 创建章节表
CREATE TABLE IF NOT EXISTS chapters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    novel_id UUID REFERENCES novels(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT '章节',
    content TEXT DEFAULT '',
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建 Agent 配置表
CREATE TABLE IF NOT EXISTS agent_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    agent_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    prompt TEXT DEFAULT '',
    temperature FLOAT DEFAULT 0.5,
    enabled BOOLEAN DEFAULT TRUE,
    personality TEXT DEFAULT 'logic',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建故事资源表
CREATE TABLE IF NOT EXISTS story_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    novel_id UUID REFERENCES novels(id) ON DELETE CASCADE,
    category TEXT NOT NULL CHECK (category IN ('characters', 'worldbuilding', 'factions', 'locations', 'timeline')),
    name TEXT NOT NULL,
    content JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建世界设定表
CREATE TABLE IF NOT EXISTS world_bibles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    novel_id UUID REFERENCES novels(id) ON DELETE CASCADE,
    world_view TEXT DEFAULT '',
    rules TEXT DEFAULT '',
    themes TEXT[] DEFAULT '{}',
    approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建分类表
CREATE TABLE IF NOT EXISTS categories (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    color TEXT DEFAULT '#6366f1',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建用户设置表
CREATE TABLE IF NOT EXISTS user_settings (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    constraints TEXT[] DEFAULT ARRAY['禁止血腥', '禁止 OOC', '避免翻译腔'],
    writing_mode TEXT DEFAULT 'manual',
    agent_config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为所有表添加更新时间触发器（使用 DROP IF EXISTS + CREATE）
DROP TRIGGER IF EXISTS update_novels_updated_at ON novels;
CREATE TRIGGER update_novels_updated_at BEFORE UPDATE ON novels
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_chapters_updated_at ON chapters;
CREATE TRIGGER update_chapters_updated_at BEFORE UPDATE ON chapters
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_agent_configs_updated_at ON agent_configs;
CREATE TRIGGER update_agent_configs_updated_at BEFORE UPDATE ON agent_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_story_assets_updated_at ON story_assets;
CREATE TRIGGER update_story_assets_updated_at BEFORE UPDATE ON story_assets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_world_bibles_updated_at ON world_bibles;
CREATE TRIGGER update_world_bibles_updated_at BEFORE UPDATE ON world_bibles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_settings_updated_at ON user_settings;
CREATE TRIGGER update_user_settings_updated_at BEFORE UPDATE ON user_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 启用 RLS (行级安全)
ALTER TABLE novels ENABLE ROW LEVEL SECURITY;
ALTER TABLE chapters ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE story_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE world_bibles ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;

-- 创建 RLS 策略（使用 DROP IF EXISTS + CREATE）
DROP POLICY IF EXISTS "Users can only access their own novels" ON novels;
CREATE POLICY "Users can only access their own novels" ON novels
    FOR ALL USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can only access their own chapters" ON chapters;
CREATE POLICY "Users can only access their own chapters" ON chapters
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM novels WHERE novels.id = chapters.novel_id AND novels.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can only access their own agent configs" ON agent_configs;
CREATE POLICY "Users can only access their own agent configs" ON agent_configs
    FOR ALL USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can only access their own story assets" ON story_assets;
CREATE POLICY "Users can only access their own story assets" ON story_assets
    FOR ALL USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can only access their own world bibles" ON world_bibles;
CREATE POLICY "Users can only access their own world bibles" ON world_bibles
    FOR ALL USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can only access their own categories" ON categories;
CREATE POLICY "Users can only access their own categories" ON categories
    FOR ALL USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can only access their own settings" ON user_settings;
CREATE POLICY "Users can only access their own settings" ON user_settings
    FOR ALL USING (auth.uid() = user_id);

-- 插入默认 Agent 配置
INSERT INTO agent_configs (agent_id, name, role, prompt, temperature, enabled, personality) VALUES
    ('facilitator', 'Facilitator', '调度协调', '负责Agent调度和讨论主持', 0.5, true, 'structure'),
    ('planner', 'Planner', '规划架构', '负责章节规划和剧情架构', 0.7, true, 'structure'),
    ('writer', 'Writer', '章节写作', '负责具体章节写作', 0.9, true, 'literary'),
    ('editor', 'Editor', '润色修订', '负责文本润色和结构优化', 0.4, true, 'logic'),
    ('conflict', 'Conflict', '冲突设计', '负责冲突设计和戏剧性增强', 0.8, true, 'drama'),
    ('reader', 'Reader', '读者评估', '负责读者视角评估', 0.6, true, 'reader'),
    ('consistency', 'Consistency', '一致性检查', '负责逻辑一致性检查', 0.3, true, 'logic'),
    ('critic', 'Critic', '批判评估', '负责批判性评估和改进建议', 0.5, true, 'logic'),
    ('summary', 'Summary', '摘要总结', '负责内容摘要和总结', 0.4, true, 'structure')
ON CONFLICT (agent_id) DO NOTHING;
