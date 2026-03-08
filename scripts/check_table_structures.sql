-- ============================================
-- 查看所有关联表的结构
-- ============================================

-- 查看所有表的结构信息
SELECT 
    table_name,
    string_agg(column_name || ' (' || data_type || ')', ', ' ORDER BY ordinal_position) as columns
FROM information_schema.columns
WHERE table_schema = 'public'
    AND table_name IN ('agent_skills', 'asset_versions', 'novel_asset_mappings', 
                       'novel_skill_mappings', 'skill_constraints', 'agents', 'assets', 'skills')
GROUP BY table_name
ORDER BY table_name;

-- 查看每个关联表的样本数据
SELECT '--- agent_skills ---' as info;
SELECT * FROM agent_skills LIMIT 2;

SELECT '--- asset_versions ---' as info;
SELECT * FROM asset_versions LIMIT 2;

SELECT '--- novel_asset_mappings ---' as info;
SELECT * FROM novel_asset_mappings LIMIT 2;

SELECT '--- novel_skill_mappings ---' as info;
SELECT * FROM novel_skill_mappings LIMIT 2;

SELECT '--- skill_constraints ---' as info;
SELECT * FROM skill_constraints LIMIT 2;
