-- 创建卷表
CREATE TABLE IF NOT EXISTS volumes (
    id TEXT PRIMARY KEY,
    novel_id TEXT NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    "order" INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 添加更新时间触发器
DROP TRIGGER IF EXISTS update_volumes_updated_at ON volumes;
CREATE TRIGGER update_volumes_updated_at BEFORE UPDATE ON volumes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 启用 RLS
ALTER TABLE volumes ENABLE ROW LEVEL SECURITY;

-- 创建访问策略
DROP POLICY IF EXISTS "Allow public read access" ON volumes;
CREATE POLICY "Allow public read access" ON volumes
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow authenticated users to modify" ON volumes;
CREATE POLICY "Allow authenticated users to modify" ON volumes
    FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_volumes_novel_id ON volumes(novel_id);
CREATE INDEX IF NOT EXISTS idx_volumes_order ON volumes("order");

-- 为 chapters 表添加 volume_id 字段
ALTER TABLE chapters ADD COLUMN IF NOT EXISTS volume_id TEXT REFERENCES volumes(id) ON DELETE SET NULL;

-- 创建章节表的 volume_id 索引
CREATE INDEX IF NOT EXISTS idx_chapters_volume_id ON chapters(volume_id);
