-- ============================================
-- 数据库迁移简单测试（检查表结构和基本功能）
-- ============================================

-- 测试1: 检查表是否存在
SELECT 'agents' as table_name, COUNT(*) as record_count FROM agents WHERE deleted_at IS NULL
UNION ALL
SELECT 'assets', COUNT(*) FROM assets WHERE deleted_at IS NULL
UNION ALL
SELECT 'settings', COUNT(*) FROM settings WHERE deleted_at IS NULL
UNION ALL
SELECT 'messages', COUNT(*) FROM messages WHERE deleted_at IS NULL;

-- 测试2: 检查软删除字段
SELECT 
    table_name,
    column_name,
    data_type
FROM information_schema.columns 
WHERE table_schema = 'public' 
    AND table_name IN ('agents', 'assets', 'settings', 'messages')
    AND column_name = 'deleted_at';

-- 测试3: 检查关键字段
SELECT 
    table_name,
    string_agg(column_name, ', ' ORDER BY ordinal_position) as columns
FROM information_schema.columns 
WHERE table_schema = 'public' 
    AND table_name IN ('agents', 'assets', 'settings')
GROUP BY table_name;

-- 测试4: 简单查询测试（不使用外键）
-- 查询 agents 表结构
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'public' AND table_name = 'agents'
ORDER BY ordinal_position;

-- 测试5: 检查索引
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
    AND tablename IN ('agents', 'assets', 'settings', 'messages')
ORDER BY tablename, indexname;
