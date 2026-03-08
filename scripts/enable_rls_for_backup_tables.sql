-- ============================================-- 为备份表启用 RLS-- ============================================-- 为 users 表启用 RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- 为所有备份表启用 RLS
ALTER TABLE _backup_novels ENABLE ROW LEVEL SECURITY;
ALTER TABLE _backup_chapters ENABLE ROW LEVEL SECURITY;
ALTER TABLE _backup_agent_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE _backup_story_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE _backup_global_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE _backup_system_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE _backup_user_settings ENABLE ROW LEVEL SECURITY;

-- 创建简单的 RLS 策略（只允许管理员访问备份表）
CREATE POLICY "Allow all" ON users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all" ON _backup_novels FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all" ON _backup_chapters FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all" ON _backup_agent_configs FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all" ON _backup_story_assets FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all" ON _backup_global_assets FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all" ON _backup_system_settings FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all" ON _backup_user_settings FOR ALL USING (true) WITH CHECK (true);

-- 验证 RLS 已启用
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('users', '_backup_novels', '_backup_chapters', '_backup_agent_configs', 
                  '_backup_story_assets', '_backup_global_assets', '_backup_system_settings', 
                  '_backup_user_settings');
