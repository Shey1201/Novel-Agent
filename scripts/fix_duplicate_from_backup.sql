-- ============================================
-- 从备份表恢复数据（清理重复数据）
-- ============================================

-- 1. 清理 agents 表，从备份恢复
-- 先清空 agents 表
TRUNCATE TABLE agents;

-- 从备份表恢复数据（只恢复一次）
INSERT INTO agents (
    id, user_id, agent_id, name, role, prompt, temperature, 
    enabled, personality, created_at, updated_at
)
SELECT DISTINCT ON (user_id, agent_id)
    id, user_id, agent_id, name, role, prompt, temperature,
    enabled, personality, created_at, updated_at
FROM _backup_agent_configs
ORDER BY user_id, agent_id, updated_at DESC;

-- 2. 清理 assets 表，从备份恢复
TRUNCATE TABLE assets;

-- 从 story_assets 备份恢复
INSERT INTO assets (
    id, user_id, novel_id, type, name, content, 
    created_at, updated_at
)
SELECT DISTINCT ON (id)
    id, user_id, novel_id, category, name, content,
    created_at, updated_at
FROM _backup_story_assets
ORDER BY id, updated_at DESC;

-- 从 global_assets 备份恢复
INSERT INTO assets (
    id, user_id, type, name, description, is_global, 
    is_starred, source_novel_id, color, created_at, updated_at
)
SELECT DISTINCT ON (id)
    gen_random_uuid(),
    NULL,
    type, name, description, TRUE, 
    is_starred, source_novel_id::UUID, color, created_at, updated_at
FROM _backup_global_assets
ORDER BY id, updated_at DESC;

-- 3. 清理 settings 表，从备份恢复
TRUNCATE TABLE settings;

-- 从 system_settings 备份恢复
INSERT INTO settings (
    id, user_id, token_enabled, token_daily_limit, token_warning_threshold,
    token_budget_allocation, discussion_max_rounds, discussion_max_tokens,
    discussion_enable_short_mode, discussion_min_interval,
    cache_enable_planner, cache_enable_conflict, cache_enable_consistency,
    created_at, updated_at
)
SELECT DISTINCT ON (id)
    id, user_id, token_enabled, token_daily_limit, token_warning_threshold,
    token_budget_allocation, discussion_max_rounds, discussion_max_tokens,
    discussion_enable_short_mode, discussion_min_interval,
    cache_enable_planner, cache_enable_conflict, cache_enable_consistency,
    created_at, updated_at
FROM _backup_system_settings
ORDER BY id, updated_at DESC;

-- 4. 验证恢复结果
SELECT 'agents' as table_name, COUNT(*) as total
FROM agents WHERE deleted_at IS NULL
UNION ALL
SELECT 'assets', COUNT(*)
FROM assets WHERE deleted_at IS NULL
UNION ALL
SELECT 'settings', COUNT(*)
FROM settings WHERE deleted_at IS NULL;
