-- 为 chapters 表添加卷信息字段
-- 使用 volume_name 和 volume_order 来标识卷，不需要单独的表

-- 添加卷名字段
ALTER TABLE chapters ADD COLUMN IF NOT EXISTS volume_name TEXT DEFAULT '未分卷';

-- 添加卷顺序字段（用于排序卷）
ALTER TABLE chapters ADD COLUMN IF NOT EXISTS volume_order INTEGER DEFAULT 0;

-- 创建索引优化查询
CREATE INDEX IF NOT EXISTS idx_chapters_volume_name ON chapters(volume_name);
CREATE INDEX IF NOT EXISTS idx_chapters_volume_order ON chapters(volume_order);
CREATE INDEX IF NOT EXISTS idx_chapters_novel_volume ON chapters(novel_id, volume_order, order_index);

-- 更新现有数据：如果没有卷信息，设置为默认卷
UPDATE chapters SET volume_name = '未分卷', volume_order = 0 WHERE volume_name IS NULL;
