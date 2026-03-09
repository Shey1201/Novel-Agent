-- ============================================
-- 从备份表恢复 agents 数据
-- ============================================

-- 先检查备份表是否存在以及数据情况
SELECT '备份表检查' as step;

-- 检查 _backup_agent_configs 表是否存在
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '_backup_agent_configs') 
        THEN '备份表 _backup_agent_configs 存在'
        ELSE '备份表 _backup_agent_configs 不存在'
    END as backup_table_status;

-- 检查备份表中的数据量
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '_backup_agent_configs') 
        THEN (SELECT COUNT(*)::text FROM _backup_agent_configs)
        ELSE '0'
    END as backup_record_count;

-- 检查当前 agents 表的数据量
SELECT COUNT(*) as current_agents_count FROM agents WHERE deleted_at IS NULL;

-- ============================================
-- 恢复数据（仅在备份表存在且有数据时执行）
-- ============================================

DO $$
DECLARE
    backup_exists BOOLEAN;
    backup_count INTEGER;
BEGIN
    -- 检查备份表是否存在
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = '_backup_agent_configs'
    ) INTO backup_exists;
    
    IF backup_exists THEN
        -- 检查备份表是否有数据
        SELECT COUNT(*) INTO backup_count FROM _backup_agent_configs;
        
        IF backup_count > 0 THEN
            -- 清空当前 agents 表
            DELETE FROM agents WHERE deleted_at IS NULL;
            
            -- 从备份表恢复数据
            INSERT INTO agents (
                id, user_id, agent_id, name, role, prompt, 
                temperature, enabled, personality, avatar_url, 
                description, created_at, updated_at
            )
            SELECT 
                id, user_id, agent_id, name, role, prompt,
                temperature, enabled, personality, avatar_url,
                description, created_at, updated_at
            FROM _backup_agent_configs
            WHERE deleted_at IS NULL;
            
            RAISE NOTICE '已从备份表恢复 % 条 agents 记录', backup_count;
        ELSE
            RAISE NOTICE '备份表存在但没有数据';
        END IF;
    ELSE
        RAISE NOTICE '备份表不存在，无法恢复';
    END IF;
END $$;

-- ============================================
-- 验证恢复结果
-- ============================================

-- 检查恢复后的数据
SELECT '恢复后数据' as step;
SELECT COUNT(*) as restored_agents_count FROM agents WHERE deleted_at IS NULL;

-- 显示恢复的数据
SELECT 
    agent_id, 
    name, 
    role, 
    temperature,
    personality,
    enabled
FROM agents 
WHERE deleted_at IS NULL
ORDER BY agent_id;
