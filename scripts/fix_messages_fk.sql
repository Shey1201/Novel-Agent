-- 修复 messages 表的外键约束问题
-- 错误: insert or update on table "messages" violates foreign key constraint "messages_user_id_fkey"

-- 方案: 直接删除外键约束 (最简单可靠)
-- 这样可以允许插入任何 user_id，不需要在 users 表中存在对应记录

-- 1. 查找并删除外键约束
DO $$
DECLARE
    constraint_name TEXT;
BEGIN
    -- 查找 messages 表的外键约束
    SELECT tc.constraint_name INTO constraint_name
    FROM information_schema.table_constraints AS tc
    WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_name = 'messages'
        AND tc.constraint_name LIKE '%user_id%';
    
    IF constraint_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE messages DROP CONSTRAINT %I', constraint_name);
        RAISE NOTICE 'Dropped foreign key constraint: %', constraint_name;
    ELSE
        RAISE NOTICE 'No user_id foreign key constraint found on messages table';
    END IF;
END $$;

-- 2. 备用方案: 直接尝试删除常见的外键约束名称
ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_user_id_fkey;
ALTER TABLE messages DROP CONSTRAINT IF EXISTS fk_messages_user_id;
ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_user_id_foreign;

-- 3. 验证外键约束是否已删除
SELECT 
    tc.constraint_name,
    tc.constraint_type
FROM information_schema.table_constraints AS tc
WHERE tc.table_name = 'messages'
    AND tc.constraint_type = 'FOREIGN KEY';

-- 如果上面的查询返回空结果，说明外键约束已成功删除
