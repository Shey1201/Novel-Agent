-- ============================================
-- 查看并修复 categories 表的 RLS Policy
-- ============================================

-- 查看当前的 Policy
SELECT tablename, policyname, permissive, roles, cmd, 
       qual::text as qual,
       with_check::text as with_check
FROM pg_policies
WHERE schemaname = 'public'
AND tablename = 'categories';

-- 删除宽松的 Policy
DROP POLICY IF EXISTS "Allow public access" ON categories;
DROP POLICY IF EXISTS "Allow authenticated users full access" ON categories;

-- 创建正确的 Policy
DROP POLICY IF EXISTS "Allow public read access" ON categories;
DROP POLICY IF EXISTS "Allow authenticated users to modify" ON categories;

-- 查询策略 - 允许所有人读取
CREATE POLICY "Allow public read access" ON categories
    FOR SELECT USING (true);

-- 修改策略 - 只允许认证用户修改自己的数据
CREATE POLICY "Allow authenticated users to modify" ON categories
    FOR ALL 
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- 验证修复结果
SELECT tablename, policyname, permissive, roles, cmd, 
       LEFT(qual::text, 50) as qual_preview
FROM pg_policies
WHERE schemaname = 'public'
AND tablename = 'categories';
