-- ============================================-- 全面分析所有表结构-- ============================================-- 1. 列出所有表及其记录数
SELECT 
    t.table_name,
    (SELECT COUNT(*) FROM information_schema.columns c WHERE c.table_name = t.table_name AND c.table_schema = 'public') as column_count,
    pg_catalog.obj_description(pg_catalog.pg_class.oid, 'pg_class') as description
FROM information_schema.tables t
LEFT JOIN pg_catalog.pg_class ON pg_catalog.pg_class.relname = t.table_name
WHERE t.table_schema = 'public' 
    AND t.table_type = 'BASE TABLE'
    AND t.table_name NOT LIKE '_backup%'
ORDER BY t.table_name;-- 2. 找出关联表（mappings/junction tables）
SELECT 
    table_name,
    '关联表' as table_type,
    '可能可以优化合并' as suggestion
FROM information_schema.tables
WHERE table_schema = 'public'
    AND table_type = 'BASE TABLE'
    AND (table_name LIKE '%mappings%' OR table_name LIKE '%junction%' OR table_name LIKE '%relation%')
    AND table_name NOT LIKE '_backup%';-- 3. 检查是否有重复功能的表
SELECT 
    table_name,
    string_agg(column_name, ', ') as columns
FROM information_schema.columns
WHERE table_schema = 'public'
    AND column_name IN ('novel_id', 'asset_id', 'skill_id', 'user_id')
GROUP BY table_name
HAVING COUNT(*) >= 2
ORDER BY table_name;