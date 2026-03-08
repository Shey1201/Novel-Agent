-- 为 categories 表添加 updated_at 字段
ALTER TABLE categories ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- 更新现有记录的 updated_at 字段
UPDATE categories SET updated_at = created_at WHERE updated_at IS NULL;
