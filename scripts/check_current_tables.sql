-- ============================================-- 检查当前数据库表结构-- ============================================-- 1. 列出所有用户表（不包括备份表）
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    AND table_name NOT LIKE '_backup%'
ORDER BY table_name;-- 2. 检查关键表是否存在
SELECT 
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'agents') THEN '✅ agents'
         ELSE '❌ agents' END as agents,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'assets') THEN '✅ assets'
         ELSE '❌ assets' END as assets,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'settings') THEN '✅ settings'
         ELSE '❌ settings' END as settings,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'agent_configs') THEN '⚠️ agent_configs (旧)'
         ELSE '✅ agent_configs 已删除' END as agent_configs_old,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'story_assets') THEN '⚠️ story_assets (旧)'
         ELSE '✅ story_assets 已删除' END as story_assets_old,
    CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'global_assets') THEN '⚠️ global_assets (旧)'
         ELSE '✅ global_assets 已删除' END as global_assets_old;-- 3. 检查 agents 表结构
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'agents'
ORDER BY ordinal_position;-- 4. 检查 assets 表结构
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'assets'
ORDER BY ordinal_position;