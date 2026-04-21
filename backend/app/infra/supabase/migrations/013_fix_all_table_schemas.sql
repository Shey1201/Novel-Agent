-- 修复所有表结构问题
-- 一次性添加所有缺失的字段

-- 1. 修复 chapters 表 - 添加 status 字段
ALTER TABLE chapters ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'draft';

-- 2. 修复 categories 表 - 添加 updated_at 字段（如果还没添加）
ALTER TABLE categories ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
UPDATE categories SET updated_at = created_at WHERE updated_at IS NULL;

-- 3. 为 chapters 表添加更新时间触发器（如果还没添加）
DROP TRIGGER IF EXISTS update_chapters_updated_at ON chapters;
CREATE TRIGGER update_chapters_updated_at BEFORE UPDATE ON chapters
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 4. 确保所有表都有正确的触发器
DROP TRIGGER IF EXISTS update_categories_updated_at ON categories;
CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 5. 检查并修复 novels 表的 deleted_at 字段（软删除）
ALTER TABLE novels ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;

-- 6. 验证所有表结构
COMMENT ON TABLE novels IS '小说表 - 包含deleted_at软删除字段';
COMMENT ON TABLE chapters IS '章节表 - 包含status状态字段';
COMMENT ON TABLE categories IS '分类表 - 包含updated_at字段';
