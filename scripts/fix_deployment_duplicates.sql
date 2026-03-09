-- ============================================
-- 修复部署时的重复数据问题
-- 此脚本用于清理重复数据并防止未来重复插入
-- ============================================

-- ============================================
-- 第一步：清理 agents 表中的重复数据
-- ============================================

-- 删除 agents 表中重复的 agent_id（保留最新的一条）
DELETE FROM agents a
WHERE a.id NOT IN (
    SELECT id FROM (
        SELECT DISTINCT ON (user_id, agent_id) id
        FROM agents
        WHERE deleted_at IS NULL
        ORDER BY user_id, agent_id, updated_at DESC
    ) sub
);

-- ============================================
-- 第二步：清理备份表（如果存在）
-- ============================================

-- 删除所有备份表（这些表在每次部署时都会重新创建并累积数据）
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
DROP TABLE IF EXISTS _backup_novel_asset_m;
DROP TABLE IF EXISTS _backup_novel_skill_m;

-- ============================================
-- 第三步：清理旧的迁移表（如果存在）
-- ============================================

-- 删除可能存在的旧表
DROP TABLE IF EXISTS agent_configs;
DROP TABLE IF EXISTS story_assets;
DROP TABLE IF EXISTS global_assets;
DROP TABLE IF EXISTS system_settings;
DROP TABLE IF EXISTS user_settings;

-- ============================================
-- 第四步：验证清理结果
-- ============================================

-- 检查 agents 表中的唯一性
SELECT 
    agent_id, 
    COUNT(*) as count,
    STRING_AGG(name, ', ') as names
FROM agents 
WHERE deleted_at IS NULL
GROUP BY agent_id 
HAVING COUNT(*) > 1;

-- 检查 agents 表总数
SELECT COUNT(*) as total_agents FROM agents WHERE deleted_at IS NULL;

-- 检查备份表是否已删除
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE '_backup_%';
