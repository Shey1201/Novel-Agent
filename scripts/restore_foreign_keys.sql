-- ============================================
-- 恢复外键约束
-- ============================================

-- 先创建 users 表（如果不存在）
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建默认匿名用户（如果不存在）
INSERT INTO users (id, email, created_at, updated_at)
VALUES ('a1b2c3d4-e5f6-7890-abcd-ef1234567890'::UUID, 'anonymous@example.com', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 恢复外键约束
ALTER TABLE agents 
    DROP CONSTRAINT IF EXISTS agents_user_id_fkey,
    ADD CONSTRAINT agents_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE assets 
    DROP CONSTRAINT IF EXISTS assets_user_id_fkey,
    ADD CONSTRAINT assets_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE settings 
    DROP CONSTRAINT IF EXISTS settings_user_id_fkey,
    ADD CONSTRAINT settings_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- 验证外键约束
SELECT 
    tc.table_name, 
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name IN ('agents', 'assets', 'settings');
