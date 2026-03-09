-- ============================================
-- 删除过于宽松的 RLS Policy
-- ============================================

-- 删除 chapters 表的宽松 policy
DROP POLICY IF EXISTS "Allow public access" ON chapters;

-- 删除 novels 表的宽松 policy  
DROP POLICY IF EXISTS "Allow public access" ON novels;

-- 删除 users 表的宽松 policy
DROP POLICY IF EXISTS "Allow all" ON users;

-- 删除 world_bibles 表的宽松 policy
DROP POLICY IF EXISTS "Allow public access" ON world_bibles;

-- ============================================
-- 验证删除结果
-- ============================================

SELECT tablename, policyname, permissive, roles, cmd, 
       LEFT(qual::text, 50) as qual_preview
FROM pg_policies
WHERE schemaname = 'public'
AND tablename IN ('chapters', 'novels', 'users', 'world_bibles')
ORDER BY tablename, policyname;
