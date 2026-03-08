-- ============================================
-- 检查和修复重复数据
-- ============================================

-- 1. 检查 agents 表重复数据
SELECT 'agents' as table_name, agent_id, user_id, COUNT(*) as count
FROM agents
WHERE deleted_at IS NULL
GROUP BY agent_id, user_id
HAVING COUNT(*) > 1;

-- 2. 检查 assets 表重复数据
SELECT 'assets' as table_name, name, novel_id, type, COUNT(*) as count
FROM assets
WHERE deleted_at IS NULL
GROUP BY name, novel_id, type
HAVING COUNT(*) > 1;

-- 3. 检查 settings 表重复数据
SELECT 'settings' as table_name, user_id, COUNT(*) as count
FROM settings
WHERE deleted_at IS NULL
GROUP BY user_id
HAVING COUNT(*) > 1;

-- 4. 检查 novels 表重复数据
SELECT 'novels' as table_name, title, user_id, COUNT(*) as count
FROM novels
WHERE deleted_at IS NULL
GROUP BY title, user_id
HAVING COUNT(*) > 1;

-- 5. 检查 chapters 表重复数据
SELECT 'chapters' as table_name, title, novel_id, COUNT(*) as count
FROM chapters
WHERE deleted_at IS NULL
GROUP BY title, novel_id
HAVING COUNT(*) > 1;
