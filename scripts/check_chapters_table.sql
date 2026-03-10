-- 检查 chapters 表是否存在
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name = 'chapters';

-- 如果存在，查看表结构
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'chapters'
ORDER BY ordinal_position;