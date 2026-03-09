-- 修复 messages 表结构
-- 添加所有缺失的列

-- 检查并添加 agent_id 列
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'messages' 
        AND column_name = 'agent_id'
    ) THEN
        ALTER TABLE messages ADD COLUMN agent_id UUID;
        RAISE NOTICE 'Added agent_id column to messages table';
    ELSE
        RAISE NOTICE 'agent_id column already exists';
    END IF;
END $$;

-- 检查并添加 agent_name 列
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'messages' 
        AND column_name = 'agent_name'
    ) THEN
        ALTER TABLE messages ADD COLUMN agent_name TEXT;
        RAISE NOTICE 'Added agent_name column to messages table';
    ELSE
        RAISE NOTICE 'agent_name column already exists';
    END IF;
END $$;

-- 检查并添加 timestamp 列
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'messages' 
        AND column_name = 'timestamp'
    ) THEN
        ALTER TABLE messages ADD COLUMN timestamp TIMESTAMPTZ DEFAULT NOW();
        RAISE NOTICE 'Added timestamp column to messages table';
    ELSE
        RAISE NOTICE 'timestamp column already exists';
    END IF;
END $$;

-- 检查并添加 role 列（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'messages' 
        AND column_name = 'role'
    ) THEN
        ALTER TABLE messages ADD COLUMN role TEXT;
        RAISE NOTICE 'Added role column to messages table';
    ELSE
        RAISE NOTICE 'role column already exists';
    END IF;
END $$;

-- 检查并添加 content 列（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'messages' 
        AND column_name = 'content'
    ) THEN
        ALTER TABLE messages ADD COLUMN content TEXT;
        RAISE NOTICE 'Added content column to messages table';
    ELSE
        RAISE NOTICE 'content column already exists';
    END IF;
END $$;

-- 检查并添加 user_id 列（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'messages' 
        AND column_name = 'user_id'
    ) THEN
        ALTER TABLE messages ADD COLUMN user_id UUID;
        RAISE NOTICE 'Added user_id column to messages table';
    ELSE
        RAISE NOTICE 'user_id column already exists';
    END IF;
END $$;

-- 查看 messages 表完整结构
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'messages'
ORDER BY ordinal_position;
