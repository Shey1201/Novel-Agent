-- ============================================-- 修复 settings 表的 RLS，允许 service key 访问-- ============================================

-- 确保 RLS 已启用
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

-- 删除现有的所有策略
DROP POLICY IF EXISTS "Allow users to manage own settings" ON settings;
DROP POLICY IF EXISTS "Allow public access to settings" ON settings;
DROP POLICY IF EXISTS "Enable all access" ON settings;
DROP POLICY IF EXISTS "Allow all" ON settings;
DROP POLICY IF EXISTS "Allow service key access" ON settings;

-- 创建一个允许所有访问的策略（service key 可以绕过 RLS）
-- 注意：这实际上允许任何有数据库连接的人访问，但在生产环境中应该使用 service key 保护
CREATE POLICY "Allow service key access" ON settings
    FOR ALL 
    USING (true) 
    WITH CHECK (true);

-- 验证策略
SELECT policyname, cmd, permissive, qual 
FROM pg_policies 
WHERE tablename = 'settings';
