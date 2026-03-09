-- ============================================
-- 创建系统设置表（包含AI配置）
-- ============================================

-- 创建系统设置表
CREATE TABLE IF NOT EXISTS system_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Token 设置
    token_enabled BOOLEAN DEFAULT FALSE,
    token_daily_limit INTEGER DEFAULT 50000,
    token_warning_threshold FLOAT DEFAULT 0.8,
    token_budget_allocation JSONB DEFAULT '{
        "planner": 0.10,
        "discussion": 0.13,
        "conflict": 0.07,
        "writing": 0.47,
        "editor": 0.13,
        "reader": 0.07,
        "summary": 0.03
    }'::jsonb,
    
    -- 讨论设置
    discussion_max_rounds INTEGER DEFAULT 2,
    discussion_max_tokens INTEGER DEFAULT 80,
    discussion_enable_short_mode BOOLEAN DEFAULT TRUE,
    discussion_min_interval INTEGER DEFAULT 3,
    
    -- 缓存设置
    cache_enable_planner BOOLEAN DEFAULT TRUE,
    cache_enable_conflict BOOLEAN DEFAULT TRUE,
    cache_enable_consistency BOOLEAN DEFAULT TRUE,
    
    -- AI 配置（新增）
    ai_chat_model TEXT,
    ai_api_key TEXT,
    ai_base_url TEXT,
    ai_is_active BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_system_settings_updated_at ON system_settings;
CREATE TRIGGER update_system_settings_updated_at 
    BEFORE UPDATE ON system_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 启用 RLS
ALTER TABLE system_settings ENABLE ROW LEVEL SECURITY;

-- 创建访问策略
DROP POLICY IF EXISTS "Allow users to manage own settings" ON system_settings;
CREATE POLICY "Allow users to manage own settings" ON system_settings
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- 添加表注释
COMMENT ON TABLE system_settings IS '系统设置表，包含Token、讨论、缓存和AI配置';
COMMENT ON COLUMN system_settings.ai_chat_model IS 'AI 模型名称';
COMMENT ON COLUMN system_settings.ai_api_key IS 'API 密钥';
COMMENT ON COLUMN system_settings.ai_base_url IS 'API 基础 URL';
COMMENT ON COLUMN system_settings.ai_is_active IS '是否激活自定义 AI 配置';

-- 验证表结构
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'system_settings' 
ORDER BY ordinal_position;
