-- 创建消息表
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    agent_id TEXT,
    agent_name TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 添加更新时间触发器
DROP TRIGGER IF EXISTS update_messages_updated_at ON messages;

-- 启用 RLS
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- 创建访问策略
DROP POLICY IF EXISTS "Allow public read access" ON messages;
CREATE POLICY "Allow public read access" ON messages
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow authenticated users to modify" ON messages;
CREATE POLICY "Allow authenticated users to modify" ON messages
    FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');
