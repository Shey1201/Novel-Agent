-- 修复 assets 表的 RLS 权限
-- 错误: new row violates row-level security policy for table "assets"

-- 1. 启用 RLS (如果还没启用)
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;

-- 2. 删除已存在的策略 (避免冲突)
DROP POLICY IF EXISTS "Allow all operations on assets" ON assets;
DROP POLICY IF EXISTS "Allow anonymous insert on assets" ON assets;
DROP POLICY IF EXISTS "Allow anonymous select on assets" ON assets;
DROP POLICY IF EXISTS "Allow anonymous update on assets" ON assets;
DROP POLICY IF EXISTS "Allow anonymous delete on assets" ON assets;

-- 3. 创建允许所有操作的策略 (针对匿名用户)
CREATE POLICY "Allow all operations on assets" 
ON assets 
FOR ALL 
TO anon, authenticated 
USING (true) 
WITH CHECK (true);

-- 4. 验证权限
SELECT * FROM pg_policies WHERE tablename = 'assets';
