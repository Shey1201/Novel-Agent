-- 创建资产分类表
-- 用于存储用户自定义的资产分类

-- 1. 创建资产分类表
CREATE TABLE IF NOT EXISTS asset_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    name TEXT NOT NULL,
    color TEXT DEFAULT '#6366f1',
    "order" INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 为 assets 表添加 category_id 字段
ALTER TABLE assets 
ADD COLUMN IF NOT EXISTS category_id UUID REFERENCES asset_categories(id) ON DELETE SET NULL;

-- 3. 创建索引
CREATE INDEX IF NOT EXISTS idx_asset_categories_user_id ON asset_categories(user_id);
CREATE INDEX IF NOT EXISTS idx_assets_category_id ON assets(category_id);

-- 4. 添加表注释
COMMENT ON TABLE asset_categories IS '资产自定义分类表';
COMMENT ON COLUMN asset_categories.name IS '分类名称';
COMMENT ON COLUMN asset_categories.color IS '分类颜色';
COMMENT ON COLUMN assets.category_id IS '所属分类ID';

-- 5. 检查表结构
SELECT 'asset_categories' as table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'asset_categories' 
ORDER BY ordinal_position;

-- 6. 检查 assets 表新字段
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'assets' AND column_name = 'category_id';
