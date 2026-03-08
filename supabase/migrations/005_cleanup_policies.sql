-- 删除 agent_configs 表的 RLS 策略
DROP POLICY IF EXISTS "Users can only access their own agent configs" ON agent_configs;

-- 确认 RLS 已禁用且没有策略
SELECT 
    schemaname,
    tablename,
    rowsecurity,
    (SELECT COUNT(*) FROM pg_policies WHERE tablename = 'agent_configs') as policy_count
FROM pg_tables 
WHERE tablename = 'agent_configs';
