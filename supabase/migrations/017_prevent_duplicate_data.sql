-- ============================================
-- 防止重复数据插入的迁移
-- 添加唯一约束和清理逻辑
-- ============================================

-- ============================================
-- 第一步：确保 agents 表有正确的唯一约束
-- ============================================

-- 添加唯一约束（如果不存在）
DO $$
BEGIN
    -- 检查是否已存在唯一约束
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'agents_user_agent_unique'
    ) THEN
        -- 先删除重复数据（保留最新的）
        DELETE FROM agents a
        WHERE a.ctid NOT IN (
            SELECT ctid FROM (
                SELECT DISTINCT ON (user_id, agent_id) ctid
                FROM agents
                WHERE deleted_at IS NULL
                ORDER BY user_id, agent_id, updated_at DESC
            ) sub
        );
        
        -- 创建唯一索引
        CREATE UNIQUE INDEX agents_user_agent_unique 
        ON agents(user_id, agent_id) 
        WHERE deleted_at IS NULL;
    END IF;
END $$;

-- ============================================
-- 第二步：清理备份表
-- ============================================

-- 删除所有备份表
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
-- 第三步：清理旧表
-- ============================================

DROP TABLE IF EXISTS agent_configs;
DROP TABLE IF EXISTS story_assets;
DROP TABLE IF EXISTS global_assets;

-- ============================================
-- 第四步：为其他表添加唯一约束
-- ============================================

-- categories 表
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'categories_user_name_unique'
    ) THEN
        DELETE FROM categories c
        WHERE c.ctid NOT IN (
            SELECT ctid FROM (
                SELECT DISTINCT ON (user_id, name) ctid
                FROM categories
                WHERE deleted_at IS NULL
                ORDER BY user_id, name, updated_at DESC
            ) sub
        );
        
        CREATE UNIQUE INDEX categories_user_name_unique 
        ON categories(user_id, name) 
        WHERE deleted_at IS NULL;
    END IF;
END $$;

-- skills 表 (skills表没有user_id和deleted_at字段，使用id作为主键)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'skills_name_unique'
    ) THEN
        -- 删除重复的技能（保留最新的）
        DELETE FROM skills s
        WHERE s.ctid NOT IN (
            SELECT ctid FROM (
                SELECT DISTINCT ON (name) ctid
                FROM skills
                ORDER BY name, updated_at DESC
            ) sub
        );
        
        -- 创建唯一索引
        CREATE UNIQUE INDEX skills_name_unique 
        ON skills(name);
    END IF;
END $$;

-- asset_categories 表 (没有deleted_at字段)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'asset_categories_user_name_unique'
    ) THEN
        -- 删除重复的分类（保留最新的）
        DELETE FROM asset_categories ac
        WHERE ac.ctid NOT IN (
            SELECT ctid FROM (
                SELECT DISTINCT ON (user_id, name) ctid
                FROM asset_categories
                ORDER BY user_id, name, updated_at DESC
            ) sub
        );
        
        -- 创建唯一索引
        CREATE UNIQUE INDEX asset_categories_user_name_unique 
        ON asset_categories(user_id, name);
    END IF;
END $$;

-- ============================================
-- 第五步：验证结果
-- ============================================

-- 检查是否还有重复数据
SELECT 'agents' as table_name, COUNT(*) as duplicates
FROM agents 
WHERE deleted_at IS NULL
GROUP BY user_id, agent_id 
HAVING COUNT(*) > 1

UNION ALL

SELECT 'categories' as table_name, COUNT(*) as duplicates
FROM categories 
WHERE deleted_at IS NULL
GROUP BY user_id, name 
HAVING COUNT(*) > 1

UNION ALL

SELECT 'skills' as table_name, COUNT(*) as duplicates
FROM skills 
GROUP BY name 
HAVING COUNT(*) > 1

UNION ALL

SELECT 'asset_categories' as table_name, COUNT(*) as duplicates
FROM asset_categories 
GROUP BY user_id, name 
HAVING COUNT(*) > 1;
