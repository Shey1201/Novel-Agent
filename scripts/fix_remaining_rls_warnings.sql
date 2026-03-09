-- ============================================
-- 修复剩余的 RLS 警告
-- ============================================

-- 先查看这些表的实际结构
SELECT '检查表结构' as step;

-- chapters 表
SELECT 'chapters' as table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'chapters' AND column_name IN ('id', 'novel_id', 'user_id');

-- novels 表
SELECT 'novels' as table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'novels' AND column_name IN ('id', 'user_id');

-- users 表
SELECT 'users' as table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users' AND column_name IN ('id', 'user_id');

-- world_bibles 表
SELECT 'world_bibles' as table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'world_bibles' AND column_name IN ('id', 'novel_id', 'user_id');

-- ============================================
-- 查看当前的 Policy
-- ============================================

SELECT tablename, policyname, permissive, roles, cmd, qual, with_check
FROM pg_policies
WHERE schemaname = 'public'
AND tablename IN ('chapters', 'novels', 'users', 'world_bibles')
ORDER BY tablename, policyname;

-- ============================================
-- 修复 chapters 表 - 通过 novel_id 关联到 novels.user_id
-- ============================================

DROP POLICY IF EXISTS "Allow authenticated users to modify" ON chapters;

CREATE POLICY "Allow authenticated users to modify" ON chapters
    FOR ALL 
    USING (
        EXISTS (
            SELECT 1 FROM novels 
            WHERE novels.id = chapters.novel_id 
            AND novels.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM novels 
            WHERE novels.id = chapters.novel_id 
            AND novels.user_id = auth.uid()
        )
    );

-- ============================================
-- 修复 novels 表 - 直接使用 user_id
-- ============================================

DROP POLICY IF EXISTS "Allow authenticated users to modify" ON novels;

CREATE POLICY "Allow authenticated users to modify" ON novels
    FOR ALL 
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- ============================================
-- 修复 users 表 - 使用 id 字段
-- ============================================

DROP POLICY IF EXISTS "Allow authenticated users to modify" ON users;

CREATE POLICY "Allow authenticated users to modify" ON users
    FOR ALL 
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid());

-- ============================================
-- 修复 world_bibles 表 - 通过 novel_id 关联到 novels.user_id
-- ============================================

DROP POLICY IF EXISTS "Allow authenticated users to modify" ON world_bibles;

CREATE POLICY "Allow authenticated users to modify" ON world_bibles
    FOR ALL 
    USING (
        EXISTS (
            SELECT 1 FROM novels 
            WHERE novels.id = world_bibles.novel_id 
            AND novels.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM novels 
            WHERE novels.id = world_bibles.novel_id 
            AND novels.user_id = auth.uid()
        )
    );

-- ============================================
-- 验证修复结果
-- ============================================

SELECT '修复后的 Policy' as step;

SELECT tablename, policyname, permissive, roles, cmd, 
       LEFT(qual::text, 50) as qual_preview,
       LEFT(with_check::text, 50) as with_check_preview
FROM pg_policies
WHERE schemaname = 'public'
AND tablename IN ('chapters', 'novels', 'users', 'world_bibles')
ORDER BY tablename, policyname;
