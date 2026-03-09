-- ============================================
-- 修复数据库安全问题
-- ============================================

-- ============================================
-- 1. 为 asset_categories 表启用 RLS
-- ============================================

-- 启用 RLS
ALTER TABLE asset_categories ENABLE ROW LEVEL SECURITY;

-- 删除已存在的策略（避免冲突）
DROP POLICY IF EXISTS "Allow public read access" ON asset_categories;
DROP POLICY IF EXISTS "Allow authenticated users to modify" ON asset_categories;

-- 创建查询策略 - 允许所有人读取
CREATE POLICY "Allow public read access" ON asset_categories
    FOR SELECT USING (true);

-- 创建修改策略 - 只允许认证用户修改自己的数据
CREATE POLICY "Allow authenticated users to modify" ON asset_categories
    FOR ALL 
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- ============================================
-- 2. 修复 volumes 表 - 添加 RLS Policy
-- ============================================

-- 删除已存在的宽松策略
DROP POLICY IF EXISTS "Allow public read access" ON volumes;
DROP POLICY IF EXISTS "Allow authenticated users full access" ON volumes;

-- 创建查询策略 - 允许所有人读取
CREATE POLICY "Allow public read access" ON volumes
    FOR SELECT USING (true);

-- 创建修改策略 - 需要更严格的控制
-- 注意：volumes 表没有 user_id 字段，通过 novel_id 关联到 novels 表
CREATE POLICY "Allow authenticated users to modify" ON volumes
    FOR ALL 
    USING (
        EXISTS (
            SELECT 1 FROM novels 
            WHERE novels.id = volumes.novel_id 
            AND novels.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM novels 
            WHERE novels.id = volumes.novel_id 
            AND novels.user_id = auth.uid()
        )
    );

-- ============================================
-- 3. 修复其他表的宽松 RLS Policy
-- ============================================

-- 修复 categories 表
DROP POLICY IF EXISTS "Allow public read access" ON categories;
DROP POLICY IF EXISTS "Allow authenticated users full access" ON categories;

CREATE POLICY "Allow public read access" ON categories
    FOR SELECT USING (true);

CREATE POLICY "Allow authenticated users to modify" ON categories
    FOR ALL 
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- 修复 chapters 表
DROP POLICY IF EXISTS "Allow public read access" ON chapters;
DROP POLICY IF EXISTS "Allow authenticated users full access" ON chapters;

CREATE POLICY "Allow public read access" ON chapters
    FOR SELECT USING (true);

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

-- 修复 novels 表
DROP POLICY IF EXISTS "Allow public read access" ON novels;
DROP POLICY IF EXISTS "Allow authenticated users full access" ON novels;

CREATE POLICY "Allow public read access" ON novels
    FOR SELECT USING (true);

CREATE POLICY "Allow authenticated users to modify" ON novels
    FOR ALL 
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- 修复 users 表
DROP POLICY IF EXISTS "Allow public read access" ON users;
DROP POLICY IF EXISTS "Allow authenticated users full access" ON users;

CREATE POLICY "Allow public read access" ON users
    FOR SELECT USING (true);

CREATE POLICY "Allow authenticated users to modify" ON users
    FOR ALL 
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- 修复 world_bibles 表
DROP POLICY IF EXISTS "Allow public read access" ON world_bibles;
DROP POLICY IF EXISTS "Allow authenticated users full access" ON world_bibles;

CREATE POLICY "Allow public read access" ON world_bibles
    FOR SELECT USING (true);

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
-- 4. 验证修复结果
-- ============================================

-- 检查 RLS 启用状态
SELECT 
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('asset_categories', 'volumes', 'categories', 'chapters', 'novels', 'users', 'world_bibles')
ORDER BY tablename;

-- 检查 RLS Policy
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;
