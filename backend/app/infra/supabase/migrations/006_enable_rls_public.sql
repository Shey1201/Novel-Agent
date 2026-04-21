-- 启用 RLS，但允许所有用户访问（包括匿名用户）
ALTER TABLE agent_configs ENABLE ROW LEVEL SECURITY;

-- 删除旧策略
DROP POLICY IF EXISTS "Users can only access their own agent configs" ON agent_configs;
DROP POLICY IF EXISTS "Allow public access" ON agent_configs;

-- 创建允许所有用户访问的策略
CREATE POLICY "Allow public access" ON agent_configs
    FOR ALL USING (true) WITH CHECK (true);
