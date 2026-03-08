-- 为所有表启用公开访问（无需登录）

-- Novels
ALTER TABLE novels ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can only access their own novels" ON novels;
DROP POLICY IF EXISTS "Allow public access" ON novels;
CREATE POLICY "Allow public access" ON novels FOR ALL USING (true) WITH CHECK (true);

-- Chapters
ALTER TABLE chapters ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can only access their own chapters" ON chapters;
DROP POLICY IF EXISTS "Allow public access" ON chapters;
CREATE POLICY "Allow public access" ON chapters FOR ALL USING (true) WITH CHECK (true);

-- Agent Configs
ALTER TABLE agent_configs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can only access their own agent configs" ON agent_configs;
DROP POLICY IF EXISTS "Allow public access" ON agent_configs;
CREATE POLICY "Allow public access" ON agent_configs FOR ALL USING (true) WITH CHECK (true);

-- Story Assets
ALTER TABLE story_assets ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can only access their own story assets" ON story_assets;
DROP POLICY IF EXISTS "Allow public access" ON story_assets;
CREATE POLICY "Allow public access" ON story_assets FOR ALL USING (true) WITH CHECK (true);

-- World Bibles
ALTER TABLE world_bibles ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can only access their own world bibles" ON world_bibles;
DROP POLICY IF EXISTS "Allow public access" ON world_bibles;
CREATE POLICY "Allow public access" ON world_bibles FOR ALL USING (true) WITH CHECK (true);

-- Categories
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can only access their own categories" ON categories;
DROP POLICY IF EXISTS "Allow public access" ON categories;
CREATE POLICY "Allow public access" ON categories FOR ALL USING (true) WITH CHECK (true);

-- User Settings
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can only access their own settings" ON user_settings;
DROP POLICY IF EXISTS "Allow public access" ON user_settings;
CREATE POLICY "Allow public access" ON user_settings FOR ALL USING (true) WITH CHECK (true);

-- 确认配置
SELECT tablename, rowsecurity FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('novels', 'chapters', 'agent_configs', 'story_assets', 'world_bibles', 'categories', 'user_settings');
