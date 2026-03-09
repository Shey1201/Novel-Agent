-- 修复 messages 表的 RLS 权限
-- 错误: new row violates row-level security policy for table "messages"

-- 1. 启用 RLS (如果还没启用)
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- 2. 删除已存在的策略 (避免冲突)
DROP POLICY IF EXISTS "Allow all operations on messages" ON messages;
DROP POLICY IF EXISTS "Allow anonymous insert" ON messages;
DROP POLICY IF EXISTS "Allow anonymous select" ON messages;
DROP POLICY IF EXISTS "Allow anonymous delete" ON messages;

-- 3. 创建允许所有操作的策略 (针对匿名用户)
CREATE POLICY "Allow all operations on messages" 
ON messages 
FOR ALL 
TO anon, authenticated 
USING (true) 
WITH CHECK (true);

-- 4. 或者创建更细粒度的策略
-- 允许插入
CREATE POLICY "Allow insert on messages" 
ON messages 
FOR INSERT 
TO anon, authenticated 
WITH CHECK (true);

-- 允许查询
CREATE POLICY "Allow select on messages" 
ON messages 
FOR SELECT 
TO anon, authenticated 
USING (true);

-- 允许更新
CREATE POLICY "Allow update on messages" 
ON messages 
FOR UPDATE 
TO anon, authenticated 
USING (true) 
WITH CHECK (true);

-- 允许删除
CREATE POLICY "Allow delete on messages" 
ON messages 
FOR DELETE 
TO anon, authenticated 
USING (true);

-- 5. 授予表权限
GRANT ALL ON messages TO anon;
GRANT ALL ON messages TO authenticated;

-- 6. 查看当前策略
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
WHERE tablename = 'messages';
