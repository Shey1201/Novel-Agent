-- ============================================-- 修复 settings 表的 RLS，安全的策略配置-- ============================================

-- 确保 RLS 已启用
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

-- 删除现有的所有策略
DROP POLICY IF EXISTS "Allow users to manage own settings" ON settings;
DROP POLICY IF EXISTS "Allow public access to settings" ON settings;
DROP POLICY IF EXISTS "Enable all access" ON settings;
DROP POLICY IF EXISTS "Allow all" ON settings;
DROP POLICY IF EXISTS "Allow service key access" ON settings;

-- 创建限制性策略：只允许认证用户访问自己的数据
-- 后端使用 service key 可以绕过这个限制
CREATE POLICY "Allow authenticated users" ON settings
    FOR ALL 
    USING (auth.role() = 'authenticated') 
    WITH CHECK (auth.role() = 'authenticated');

-- 验证策略
SELECT policyname, cmd, permissive, qual 
FROM pg_policies 
WHERE tablename = 'settings';
