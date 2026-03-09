-- ============================================-- 删除 settings 表中重复的 AI 配置字段-- ============================================

-- 删除不带 ai_ 前缀的重复字段
ALTER TABLE settings
    DROP COLUMN IF EXISTS chat_model,
    DROP COLUMN IF EXISTS api_key,
    DROP COLUMN IF EXISTS base_url,
    DROP COLUMN IF EXISTS is_active;

-- 验证字段已删除
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'settings' 
AND column_name IN ('chat_model', 'api_key', 'base_url', 'is_active', 'ai_chat_model', 'ai_api_key', 'ai_base_url', 'ai_is_active')
ORDER BY column_name;
