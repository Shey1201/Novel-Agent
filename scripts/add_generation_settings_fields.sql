-- ============================================-- 添加生成设置字段到 settings 表-- ============================================

-- 添加生成设置相关字段
ALTER TABLE settings
    ADD COLUMN IF NOT EXISTS paragraph_length INTEGER DEFAULT 500,
    ADD COLUMN IF NOT EXISTS reader_interval INTEGER DEFAULT 3,
    ADD COLUMN IF NOT EXISTS enable_streaming BOOLEAN DEFAULT TRUE;

-- 添加 AI 配置相关字段
ALTER TABLE settings
    ADD COLUMN IF NOT EXISTS chat_model TEXT DEFAULT '',
    ADD COLUMN IF NOT EXISTS api_key TEXT DEFAULT '',
    ADD COLUMN IF NOT EXISTS base_url TEXT DEFAULT '',
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT FALSE;

-- 验证字段已添加
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'settings'
ORDER BY ordinal_position;
