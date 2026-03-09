-- ============================================
-- 创建 AI 配置表
-- ============================================

-- 创建用户 AI 配置表
CREATE TABLE IF NOT EXISTS user_ai_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    chat_model TEXT NOT NULL DEFAULT 'gpt-4o-mini',
    api_key TEXT NOT NULL,
    base_url TEXT NOT NULL DEFAULT 'https://api.openai.com/v1',
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_user_ai_configs_updated_at ON user_ai_configs;
CREATE TRIGGER update_user_ai_configs_updated_at
    BEFORE UPDATE ON user_ai_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 启用 RLS
ALTER TABLE user_ai_configs ENABLE ROW LEVEL SECURITY;

-- 创建访问策略
DROP POLICY IF EXISTS "Allow users to manage own config" ON user_ai_configs;
CREATE POLICY "Allow users to manage own config" ON user_ai_configs
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- 添加表注释
COMMENT ON TABLE user_ai_configs IS '用户自定义 AI 配置表';
COMMENT ON COLUMN user_ai_configs.chat_model IS 'AI 模型名称';
COMMENT ON COLUMN user_ai_configs.api_key IS 'API 密钥（加密存储）';
COMMENT ON COLUMN user_ai_configs.base_url IS 'API 基础 URL';
COMMENT ON COLUMN user_ai_configs.is_active IS '是否激活使用';

-- 验证表结构
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'user_ai_configs' 
ORDER BY ordinal_position;
