-- ============================================
-- 检查所有关联表的实际结构
-- ============================================

-- 1. 检查 agent_skills 表结构
SELECT 'agent_skills' as table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name = 'agent_skills'
ORDER BY ordinal_position;

-- 2. 检查 asset_versions 表结构
SELECT 'asset_versions' as table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name = 'asset_versions'
ORDER BY ordinal_position;

-- 3. 检查 novel_asset_mappings 表结构
SELECT 'novel_asset_mappings' as table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name = 'novel_asset_mappings'
ORDER BY ordinal_position;

-- 4. 检查 novel_skill_mappings 表结构
SELECT 'novel_skill_mappings' as table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name = 'novel_skill_mappings'
ORDER BY ordinal_position;

-- 5. 检查 skill_constraints 表结构
SELECT 'skill_constraints' as table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name = 'skill_constraints'
ORDER BY ordinal_position;

-- 6. 查看每个表的数据样本
SELECT 'agent_skills sample' as info, * FROM agent_skills LIMIT 2;
SELECT 'asset_versions sample' as info, * FROM asset_versions LIMIT 2;
SELECT 'novel_asset_mappings sample' as info, * FROM novel_asset_mappings LIMIT 2;
SELECT 'novel_skill_mappings sample' as info, * FROM novel_skill_mappings LIMIT 2;
SELECT 'skill_constraints sample' as info, * FROM skill_constraints LIMIT 2;
