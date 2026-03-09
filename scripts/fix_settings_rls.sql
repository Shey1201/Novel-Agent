-- ============================================-- 修复 settings 表的 RLS 策略-- ============================================

-- 确保 RLS 已启用
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

-- 删除现有的所有策略
DROP POLICY IF EXISTS "Allow users to manage own settings" ON settings;
DROP POLICY IF EXISTS "Allow public access to settings" ON settings;
DROP POLICY IF EXISTS "Enable all access" ON settings;
DROP POLICY IF EXISTS "Allow all" ON settings;

-- 创建新的策略：允许认证用户管理自己的设置
CREATE POLICY "Allow users to manage own settings" ON settings
    FOR ALL 
    USING (auth.uid() = user_id) 
    WITH CHECK (auth.uid() = user_id);

-- 验证策略
SELECT policyname, cmd, permissive 
FROM pg_policies 
WHERE tablename = 'settings';
