-- 创建资产挂载记录表
CREATE TABLE IF NOT EXISTS asset_mounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    novel_id UUID NOT NULL REFERENCES novels(id) ON DELETE CASCADE,
    reference_type VARCHAR(50) DEFAULT 'linked',
    version_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(asset_id, novel_id)
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_asset_mounts_asset_id ON asset_mounts(asset_id);
CREATE INDEX IF NOT EXISTS idx_asset_mounts_novel_id ON asset_mounts(novel_id);

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_asset_mounts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS asset_mounts_updated_at_trigger ON asset_mounts;
CREATE TRIGGER asset_mounts_updated_at_trigger
    BEFORE UPDATE ON asset_mounts
    FOR EACH ROW
    EXECUTE FUNCTION update_asset_mounts_updated_at();

-- 为现有数据创建挂载记录（迁移数据）
INSERT INTO asset_mounts (asset_id, novel_id, reference_type, created_at, updated_at)
SELECT 
    id as asset_id,
    novel_id,
    'linked' as reference_type,
    created_at,
    updated_at
FROM assets
WHERE novel_id IS NOT NULL
ON CONFLICT (asset_id, novel_id) DO NOTHING;