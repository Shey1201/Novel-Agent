-- ============================================-- 在现有 settings 表中添加 AI 配置字段-- ============================================

-- 查看现有表结构SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'settings' ORDER BY ordinal_position;

-- 添加 AI 配置字段（如果不存在）DO $$BEGIN    -- 检查并添加 ai_chat_model 字段    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'settings' AND column_name = 'ai_chat_model') THEN        ALTER TABLE settings ADD COLUMN ai_chat_model TEXT;    END IF;
    
    -- 检查并添加 ai_api_key 字段    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'settings' AND column_name = 'ai_api_key') THEN        ALTER TABLE settings ADD COLUMN ai_api_key TEXT;    END IF;
    
    -- 检查并添加 ai_base_url 字段    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'settings' AND column_name = 'ai_base_url') THEN        ALTER TABLE settings ADD COLUMN ai_base_url TEXT;    END IF;
    
    -- 检查并添加 ai_is_active 字段    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'settings' AND column_name = 'ai_is_active') THEN        ALTER TABLE settings ADD COLUMN ai_is_active BOOLEAN DEFAULT FALSE;    END IF;END $$;

-- 添加字段注释COMMENT ON COLUMN settings.ai_chat_model IS 'AI 模型名称';COMMENT ON COLUMN settings.ai_api_key IS 'API 密钥';COMMENT ON COLUMN settings.ai_base_url IS 'API 基础 URL';COMMENT ON COLUMN settings.ai_is_active IS '是否激活自定义 AI 配置';

-- 验证字段添加成功SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'settings' AND column_name LIKE 'ai_%' ORDER BY ordinal_position;