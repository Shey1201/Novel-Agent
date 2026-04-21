-- ============================================
-- 数据库结构优化迁移
-- 目标：减少冗余、统一规范、提高性能
-- 注意：此迁移会保留所有数据
-- ============================================

-- 开始事务
BEGIN;

-- ============================================
-- 第一阶段：备份现有数据
-- ============================================

-- 创建备份表（仅结构，数据在迁移过程中保留）
CREATE TABLE IF NOT EXISTS _backup_novels AS SELECT * FROM novels WHERE 1=0;
CREATE TABLE IF NOT EXISTS _backup_chapters AS SELECT * FROM chapters WHERE 1=0;
CREATE TABLE IF NOT EXISTS _backup_categories AS SELECT * FROM categories WHERE 1=0;
CREATE TABLE IF NOT EXISTS _backup_agent_configs AS SELECT * FROM agent_configs WHERE 1=0;
CREATE TABLE IF NOT EXISTS _backup_story_assets AS SELECT * FROM story_assets WHERE 1=0;
CREATE TABLE IF NOT EXISTS _backup_global_assets AS SELECT * FROM global_assets WHERE 1=0;
CREATE TABLE IF NOT EXISTS _backup_world_bibles AS SELECT * FROM world_bibles WHERE 1=0;
CREATE TABLE IF NOT EXISTS _backup_skills AS SELECT * FROM skills WHERE 1=0;
CREATE TABLE IF NOT EXISTS _backup_skill_categories AS SELECT * FROM skill_categories WHERE 1=0;
CREATE TABLE IF NOT EXISTS _backup_skill_constraints AS SELECT * FROM skill_constraints WHERE 1=0;
CREATE TABLE IF NOT EXISTS _backup_system_settings AS SELECT * FROM system_settings WHERE 1=0;
CREATE TABLE IF NOT EXISTS _backup_user_settings AS SELECT * FROM user_settings WHERE 1=0;
CREATE TABLE IF NOT EXISTS _backup_messages AS SELECT * FROM messages WHERE 1=0;

-- 备份数据
INSERT INTO _backup_novels SELECT * FROM novels;
INSERT INTO _backup_chapters SELECT * FROM chapters;
INSERT INTO _backup_categories SELECT * FROM categories;
INSERT INTO _backup_agent_configs SELECT * FROM agent_configs;
INSERT INTO _backup_story_assets SELECT * FROM story_assets;
INSERT INTO _backup_global_assets SELECT * FROM global_assets;
INSERT INTO _backup_world_bibles SELECT * FROM world_bibles;
INSERT INTO _backup_skills SELECT * FROM skills;
INSERT INTO _backup_skill_categories SELECT * FROM skill_categories;
INSERT INTO _backup_skill_constraints SELECT * FROM skill_constraints;
INSERT INTO _backup_system_settings SELECT * FROM system_settings;
INSERT INTO _backup_user_settings SELECT * FROM user_settings;
INSERT INTO _backup_messages SELECT * FROM messages;

-- ============================================
-- 第二阶段：优化现有表
-- ============================================

-- 1. 优化 novels 表
-- 添加缺失的字段和索引
ALTER TABLE novels 
    ADD COLUMN IF NOT EXISTS outline TEXT DEFAULT '',
    ADD COLUMN IF NOT EXISTS word_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'writing', 'completed', 'archived'));

-- 2. 优化 chapters 表（已完成大部分优化）
-- 确保所有字段都存在
ALTER TABLE chapters
    ADD COLUMN IF NOT EXISTS word_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS summary TEXT DEFAULT '';

-- 3. 优化 categories 表
-- 添加软删除支持
ALTER TABLE categories
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS "order" INTEGER DEFAULT 0;

-- 4. 优化 agent_configs 表 - 重命名为 agents 并优化结构
-- 先创建新表
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    agent_id TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    prompt TEXT DEFAULT '',
    temperature FLOAT DEFAULT 0.5,
    enabled BOOLEAN DEFAULT TRUE,
    personality TEXT DEFAULT 'logic',
    avatar_url TEXT DEFAULT '',
    description TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    UNIQUE(user_id, agent_id)
);

-- 迁移数据
INSERT INTO agents (
    id, user_id, agent_id, name, role, prompt, temperature, 
    enabled, personality, created_at, updated_at
)
SELECT 
    id, user_id, agent_id, name, role, prompt, temperature,
    enabled, personality, created_at, updated_at
FROM agent_configs
ON CONFLICT (id) DO NOTHING;

-- 5. 合并 story_assets 和 global_assets 为统一的 assets 表
CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    novel_id UUID REFERENCES novels(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('characters', 'worldbuilding', 'factions', 'locations', 'timeline')),
    name TEXT NOT NULL,
    content JSONB DEFAULT '{}',
    description TEXT DEFAULT '',
    is_global BOOLEAN DEFAULT FALSE,
    is_starred BOOLEAN DEFAULT FALSE,
    source_novel_id UUID REFERENCES novels(id) ON DELETE SET NULL,
    color TEXT DEFAULT '#6366f1',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL
);

-- 从 story_assets 迁移数据
INSERT INTO assets (
    id, user_id, novel_id, type, name, content, 
    created_at, updated_at
)
SELECT 
    id, user_id, novel_id, category, name, content,
    created_at, updated_at
FROM story_assets
ON CONFLICT (id) DO NOTHING;

-- 从 global_assets 迁移数据
INSERT INTO assets (
    id, user_id, type, name, description, is_global, 
    is_starred, source_novel_id, color, created_at, updated_at
)
SELECT 
    gen_random_uuid(),  -- 生成新的UUID
    NULL,  -- global_assets 可能没有 user_id
    type, name, description, TRUE, 
    is_starred, source_novel_id::UUID, color, created_at, updated_at
FROM global_assets
ON CONFLICT DO NOTHING;

-- 6. 优化 world_bibles 表
ALTER TABLE world_bibles
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;

-- 7. 优化 skills 相关表
-- skills 表添加软删除
ALTER TABLE skills
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;

-- skill_categories 表添加软删除
ALTER TABLE skill_categories
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;

-- 8. 合并设置表
CREATE TABLE IF NOT EXISTS settings (
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
    
    -- 用户偏好设置（来自 user_settings）
    constraints TEXT[] DEFAULT ARRAY['禁止血腥', '禁止 OOC', '避免翻译腔'],
    writing_mode TEXT DEFAULT 'manual',
    agent_config JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    
    UNIQUE(user_id)
);

-- 从 system_settings 迁移数据
INSERT INTO settings (
    id, user_id, token_enabled, token_daily_limit, token_warning_threshold,
    token_budget_allocation, discussion_max_rounds, discussion_max_tokens,
    discussion_enable_short_mode, discussion_min_interval,
    cache_enable_planner, cache_enable_conflict, cache_enable_consistency,
    created_at, updated_at
)
SELECT 
    id, user_id, token_enabled, token_daily_limit, token_warning_threshold,
    token_budget_allocation, discussion_max_rounds, discussion_max_tokens,
    discussion_enable_short_mode, discussion_min_interval,
    cache_enable_planner, cache_enable_conflict, cache_enable_consistency,
    created_at, updated_at
FROM system_settings
ON CONFLICT (id) DO NOTHING;

-- 从 user_settings 迁移数据
INSERT INTO settings (
    user_id, constraints, writing_mode, agent_config, created_at, updated_at
)
SELECT 
    user_id, constraints, writing_mode, agent_config, created_at, updated_at
FROM user_settings
ON CONFLICT (user_id) DO UPDATE SET
    constraints = EXCLUDED.constraints,
    writing_mode = EXCLUDED.writing_mode,
    agent_config = EXCLUDED.agent_config;

-- 9. 优化 messages 表
ALTER TABLE messages
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS session_id TEXT DEFAULT '';

-- ============================================
-- 第三阶段：创建优化后的索引
-- ============================================

-- novels 表索引
CREATE INDEX IF NOT EXISTS idx_novels_user_id ON novels(user_id);
CREATE INDEX IF NOT EXISTS idx_novels_category_id ON novels(category_id);
CREATE INDEX IF NOT EXISTS idx_novels_deleted_at ON novels(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_novels_status ON novels(status);

-- chapters 表索引
CREATE INDEX IF NOT EXISTS idx_chapters_novel_id ON chapters(novel_id);
CREATE INDEX IF NOT EXISTS idx_chapters_novel_order ON chapters(novel_id, volume_order, order_index);
CREATE INDEX IF NOT EXISTS idx_chapters_status ON chapters(status);

-- categories 表索引
CREATE INDEX IF NOT EXISTS idx_categories_user_id ON categories(user_id);
CREATE INDEX IF NOT EXISTS idx_categories_deleted_at ON categories(deleted_at) WHERE deleted_at IS NULL;

-- agents 表索引
CREATE INDEX IF NOT EXISTS idx_agents_user_id ON agents(user_id);
CREATE INDEX IF NOT EXISTS idx_agents_agent_id ON agents(user_id, agent_id);
CREATE INDEX IF NOT EXISTS idx_agents_deleted_at ON agents(deleted_at) WHERE deleted_at IS NULL;

-- assets 表索引
CREATE INDEX IF NOT EXISTS idx_assets_user_id ON assets(user_id);
CREATE INDEX IF NOT EXISTS idx_assets_novel_id ON assets(novel_id);
CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(type);
CREATE INDEX IF NOT EXISTS idx_assets_is_global ON assets(is_global) WHERE is_global = TRUE;
CREATE INDEX IF NOT EXISTS idx_assets_deleted_at ON assets(deleted_at) WHERE deleted_at IS NULL;

-- skills 表索引
CREATE INDEX IF NOT EXISTS idx_skills_category_id ON skills(category_id);
CREATE INDEX IF NOT EXISTS idx_skills_deleted_at ON skills(deleted_at) WHERE deleted_at IS NULL;

-- settings 表索引
CREATE INDEX IF NOT EXISTS idx_settings_user_id ON settings(user_id);

-- messages 表索引
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);

-- ============================================
-- 第四阶段：更新触发器
-- ============================================

-- 确保 update_updated_at_column 函数存在
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql' SET search_path = public;

-- 为所有表添加/更新触发器
DROP TRIGGER IF EXISTS update_agents_updated_at ON agents;
CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_assets_updated_at ON assets;
CREATE TRIGGER update_assets_updated_at BEFORE UPDATE ON assets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_settings_updated_at ON settings;
CREATE TRIGGER update_settings_updated_at BEFORE UPDATE ON settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 第五阶段：启用 RLS 和创建策略
-- ============================================

-- 为新表启用 RLS
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

-- 创建通用策略函数
CREATE OR REPLACE FUNCTION get_current_user_id()
RETURNS UUID AS $$
BEGIN
    RETURN auth.uid();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- agents 表策略
DROP POLICY IF EXISTS "agents_select_policy" ON agents;
CREATE POLICY "agents_select_policy" ON agents
    FOR SELECT USING (user_id = get_current_user_id() OR user_id IS NULL);

DROP POLICY IF EXISTS "agents_modify_policy" ON agents;
CREATE POLICY "agents_modify_policy" ON agents
    FOR ALL USING (user_id = get_current_user_id()) WITH CHECK (user_id = get_current_user_id());

-- assets 表策略
DROP POLICY IF EXISTS "assets_select_policy" ON assets;
CREATE POLICY "assets_select_policy" ON assets
    FOR SELECT USING (
        user_id = get_current_user_id() 
        OR is_global = TRUE 
        OR user_id IS NULL
    );

DROP POLICY IF EXISTS "assets_modify_policy" ON assets;
CREATE POLICY "assets_modify_policy" ON assets
    FOR ALL USING (user_id = get_current_user_id()) WITH CHECK (user_id = get_current_user_id());

-- settings 表策略
DROP POLICY IF EXISTS "settings_select_policy" ON settings;
CREATE POLICY "settings_select_policy" ON settings
    FOR SELECT USING (user_id = get_current_user_id());

DROP POLICY IF EXISTS "settings_modify_policy" ON settings;
CREATE POLICY "settings_modify_policy" ON settings
    FOR ALL USING (user_id = get_current_user_id()) WITH CHECK (user_id = get_current_user_id());

-- ============================================
-- 第六阶段：添加表注释
-- ============================================

COMMENT ON TABLE novels IS '小说主表';
COMMENT ON TABLE chapters IS '章节表，支持卷(volume)功能';
COMMENT ON TABLE categories IS '小说分类表';
COMMENT ON TABLE agents IS 'AI Agent配置表（替代agent_configs）';
COMMENT ON TABLE assets IS '统一资产表（合并story_assets和global_assets）';
COMMENT ON TABLE world_bibles IS '世界观设定表';
COMMENT ON TABLE skills IS '技能表';
COMMENT ON TABLE skill_categories IS '技能分类表';
COMMENT ON TABLE skill_constraints IS '技能约束表';
COMMENT ON TABLE settings IS '统一设置表（合并system_settings和user_settings）';
COMMENT ON TABLE messages IS '消息记录表';

-- ============================================
-- 第七阶段：验证数据完整性
-- ============================================

-- 检查迁移后的数据行数
DO $$
DECLARE
    v_novels_count INTEGER;
    v_chapters_count INTEGER;
    v_agents_count INTEGER;
    v_assets_count INTEGER;
    v_settings_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_novels_count FROM novels;
    SELECT COUNT(*) INTO v_chapters_count FROM chapters;
    SELECT COUNT(*) INTO v_agents_count FROM agents;
    SELECT COUNT(*) INTO v_assets_count FROM assets;
    SELECT COUNT(*) INTO v_settings_count FROM settings;
    
    RAISE NOTICE '迁移完成统计：';
    RAISE NOTICE '- novels: % 条', v_novels_count;
    RAISE NOTICE '- chapters: % 条', v_chapters_count;
    RAISE NOTICE '- agents: % 条', v_agents_count;
    RAISE NOTICE '- assets: % 条', v_assets_count;
    RAISE NOTICE '- settings: % 条', v_settings_count;
END $$;

-- 提交事务
COMMIT;

-- ============================================
-- 第八阶段：清理（可选，确认无误后执行）
-- ============================================
-- 注意：以下命令用于删除旧表，请在确认新表正常工作后再执行

/*
-- 删除旧表（确认无误后取消注释执行）
DROP TABLE IF EXISTS agent_configs;
DROP TABLE IF EXISTS story_assets;
DROP TABLE IF EXISTS global_assets;
DROP TABLE IF EXISTS system_settings;
DROP TABLE IF EXISTS user_settings;
DROP TABLE IF EXISTS novel_asset_mappings;
DROP TABLE IF EXISTS agent_skills;
DROP TABLE IF EXISTS novel_skill_mappings;

-- 删除备份表
DROP TABLE IF EXISTS _backup_novels;
DROP TABLE IF EXISTS _backup_chapters;
DROP TABLE IF EXISTS _backup_categories;
DROP TABLE IF EXISTS _backup_agent_configs;
DROP TABLE IF EXISTS _backup_story_assets;
DROP TABLE IF EXISTS _backup_global_assets;
DROP TABLE IF EXISTS _backup_world_bibles;
DROP TABLE IF EXISTS _backup_skills;
DROP TABLE IF EXISTS _backup_skill_categories;
DROP TABLE IF EXISTS _backup_skill_constraints;
DROP TABLE IF EXISTS _backup_system_settings;
DROP TABLE IF EXISTS _backup_user_settings;
DROP TABLE IF EXISTS _backup_messages;
*/
