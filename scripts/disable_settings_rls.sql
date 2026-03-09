-- 禁用 settings 表的 RLS，允许通过 service key 访问
ALTER TABLE settings DISABLE ROW LEVEL SECURITY;

-- 验证 RLS 已禁用
SELECT relname, relrowsecurity, relforcerowsecurity 
FROM pg_class 
WHERE relname = 'settings';
