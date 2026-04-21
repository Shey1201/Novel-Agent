-- 为 novels 表添加 deleted_at 字段用于软删除
ALTER TABLE novels ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;

-- 创建索引提高查询性能
CREATE INDEX IF NOT EXISTS idx_novels_deleted_at ON novels(deleted_at);

-- 确认字段添加
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'novels' AND column_name = 'deleted_at';
