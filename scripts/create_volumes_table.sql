-- 创建 volumes 表用于存储小说分卷信息
-- 这样可以保存空卷（没有章节的分卷）

-- 创建 volumes 表
CREATE TABLE IF NOT EXISTS volumes (
    id TEXT PRIMARY KEY,
    novel_id UUID NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    name TEXT NOT NULL DEFAULT '未命名卷',
    "order" INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_volumes_novel_id ON volumes(novel_id);
CREATE INDEX IF NOT EXISTS idx_volumes_order ON volumes("order");

-- 添加表注释
COMMENT ON TABLE volumes IS '小说分卷表';
COMMENT ON COLUMN volumes.id IS '卷ID，格式: vol-{order}-{name}';
COMMENT ON COLUMN volumes.novel_id IS '所属小说ID';
COMMENT ON COLUMN volumes.name IS '卷名称';
COMMENT ON COLUMN volumes.order IS '卷顺序';

-- 检查表结构
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'volumes' 
ORDER BY ordinal_position;
