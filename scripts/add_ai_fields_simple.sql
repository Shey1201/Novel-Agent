-- 直接添加 AI 配置字段（不使用 IF EXISTS 检查）
ALTER TABLE settings
ADD COLUMN ai_chat_model TEXT,
ADD COLUMN ai_api_key TEXT,
ADD COLUMN ai_base_url TEXT,
ADD COLUMN ai_is_active BOOLEAN DEFAULT FALSE;

-- 验证字段添加成功
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'settings' 
AND column_name LIKE 'ai_%'
ORDER BY ordinal_position;
