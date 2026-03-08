-- ============================================-- 删除旧表（数据已迁移到新表）-- ============================================-- 注意：确保数据已成功迁移到新表后再执行！-- 删除旧的 agent_configs 表（数据已迁移到 agents）
DROP TABLE IF EXISTS agent_configs CASCADE;-- 删除旧的 story_assets 表（数据已迁移到 assets）
DROP TABLE IF EXISTS story_assets CASCADE;-- 删除旧的 global_assets 表（数据已迁移到 assets）
DROP TABLE IF EXISTS global_assets CASCADE;-- 删除旧的 system_settings 表（数据已迁移到 settings）
DROP TABLE IF EXISTS system_settings CASCADE;-- 删除旧的 user_settings 表（数据已迁移到 settings）
DROP TABLE IF EXISTS user_settings CASCADE;-- 验证删除结果
SELECT 'Remaining tables after cleanup:' as info;

SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    AND table_name NOT LIKE '_backup%'
ORDER BY table_name;