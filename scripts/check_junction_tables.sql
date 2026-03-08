-- ============================================-- 检查关联表的实际结构-- ============================================-- 1. 检查 agent_skills 表结构
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'agent_skills'
ORDER BY ordinal_position;-- 2. 检查 asset_versions 表结构
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'asset_versions'
ORDER BY ordinal_position;-- 3. 检查 novel_asset_mappings 表结构
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'novel_asset_mappings'
ORDER BY ordinal_position;-- 4. 检查 novel_skill_mappings 表结构
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'novel_skill_mappings'
ORDER BY ordinal_position;-- 5. 检查 skill_constraints 表结构
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'skill_constraints'
ORDER BY ordinal_position;