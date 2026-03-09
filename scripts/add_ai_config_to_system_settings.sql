-- ============================================
-- 在 system_settings 表中添加 AI 配置字段
-- ============================================

-- 添加 AI 配置字段（无默认值，初始为空）
ALTER TABLE system_settings
ADD COLUMN IF NOT EXISTS ai_chat_model TEXT,
ADD COLUMN IF NOT EXISTS ai_api_key TEXT,
ADD COLUMN IF NOT EXISTS ai_base_url TEXT,
ADD COLUMN IF NOT EXISTS ai_is_active BOOLEAN DEFAULT FALSE;

-- 添加字段注释
COMMENT ON COLUMN system_settings.ai_chat_model IS 'AI 模型名称';
COMMENT ON COLUMN system_settings.ai_api_key IS 'API 密钥';
COMMENT ON COLUMN system_settings.ai_base_url IS 'API 基础 URL';
COMMENT ON COLUMN system_settings.ai_is_active IS '是否激活自定义 AI 配置';

-- 验证字段添加成功
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns 
WHERE table_name = 'system_settings' 
AND column_name LIKE 'ai_%'
ORDER BY ordinal_position;
