-- ============================================
-- 合并关联表到主表（修正版）
-- 注意：agent_skills 是独立表，不是关联表，保留不动
-- ============================================

BEGIN;

-- ============================================
-- 第一阶段：备份关联表数据
-- ============================================

-- 备份 asset_versions
CREATE TABLE IF NOT EXISTS _backup_asset_versions AS SELECT * FROM asset_versions WHERE 1=0;
TRUNCATE TABLE _backup_asset_versions;
INSERT INTO _backup_asset_versions SELECT * FROM asset_versions;

-- 备份 novel_asset_mappings
CREATE TABLE IF NOT EXISTS _backup_novel_asset_mappings AS SELECT * FROM novel_asset_mappings WHERE 1=0;
TRUNCATE TABLE _backup_novel_asset_mappings;
INSERT INTO _backup_novel_asset_mappings SELECT * FROM novel_asset_mappings;

-- 备份 novel_skill_mappings
CREATE TABLE IF NOT EXISTS _backup_novel_skill_mappings AS SELECT * FROM novel_skill_mappings WHERE 1=0;
TRUNCATE TABLE _backup_novel_skill_mappings;
INSERT INTO _backup_novel_skill_mappings SELECT * FROM novel_skill_mappings;

-- 备份 skill_constraints
CREATE TABLE IF NOT EXISTS _backup_skill_constraints AS SELECT * FROM skill_constraints WHERE 1=0;
TRUNCATE TABLE _backup_skill_constraints;
INSERT INTO _backup_skill_constraints SELECT * FROM skill_constraints;

-- ============================================
-- 第二阶段：为主表添加新字段
-- ============================================

-- 1. assets 表添加 novel_ids 数组和 versions JSONB
ALTER TABLE assets
    ADD COLUMN IF NOT EXISTS novel_ids UUID[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS versions JSONB DEFAULT '[]';

-- 2. skills 表添加 novel_ids 数组和 constraints JSONB
ALTER TABLE skills
    ADD COLUMN IF NOT EXISTS novel_ids UUID[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS constraints JSONB DEFAULT '[]';

-- ============================================
-- 第三阶段：迁移关联数据到主表
-- ============================================

-- 1. 迁移 asset_versions 到 assets.versions
-- asset_versions.asset_id 关联到 assets.id
UPDATE assets a
SET versions = (
    SELECT COALESCE(JSONB_AGG(
        JSONB_BUILD_OBJECT(
            'id', av.id,
            'name', av.name,
            'description', av.description,
            'data', av.data,
            'created_at', av.created_at
        ) ORDER BY av.created_at DESC
    ), '[]'::jsonb)
    FROM asset_versions av
    WHERE av.asset_id = a.id::text
)
WHERE EXISTS (SELECT 1 FROM asset_versions av WHERE av.asset_id = a.id::text);

-- 2. 迁移 novel_asset_mappings 到 assets.novel_ids
-- novel_asset_mappings.asset_id 关联到 assets.id
UPDATE assets a
SET novel_ids = (
    SELECT ARRAY_AGG(DISTINCT nam.novel_id::uuid)
    FROM novel_asset_mappings nam
    WHERE nam.asset_id = a.id::text
)
WHERE EXISTS (SELECT 1 FROM novel_asset_mappings nam WHERE nam.asset_id = a.id::text);

-- 3. 迁移 novel_skill_mappings 到 skills.novel_ids
-- novel_skill_mappings.skill_id 关联到 skills.id
UPDATE skills s
SET novel_ids = (
    SELECT ARRAY_AGG(DISTINCT nsm.novel_id::uuid)
    FROM novel_skill_mappings nsm
    WHERE nsm.skill_id = s.id::text
)
WHERE EXISTS (SELECT 1 FROM novel_skill_mappings nsm WHERE nsm.skill_id = s.id::text);

-- 4. 迁移 skill_constraints 到 skills.constraints
-- skill_constraints.skill_id 关联到 skills.id
UPDATE skills s
SET constraints = (
    SELECT COALESCE(JSONB_AGG(
        JSONB_BUILD_OBJECT(
            'id', sc.id,
            'content', sc.content,
            'priority', sc.priority,
            'enabled', sc.enabled,
            'created_at', sc.created_at
        ) ORDER BY 
            CASE sc.priority 
                WHEN 'high' THEN 1 
                WHEN 'medium' THEN 2 
                WHEN 'low' THEN 3 
                ELSE 4 
            END
    ), '[]'::jsonb)
    FROM skill_constraints sc
    WHERE sc.skill_id = s.id::text
)
WHERE EXISTS (SELECT 1 FROM skill_constraints sc WHERE sc.skill_id = s.id::text);

-- ============================================
-- 第四阶段：创建索引优化查询
-- ============================================

-- 为数组字段创建 GIN 索引
CREATE INDEX IF NOT EXISTS idx_assets_novel_ids ON assets USING GIN (novel_ids);
CREATE INDEX IF NOT EXISTS idx_skills_novel_ids ON skills USING GIN (novel_ids);

-- ============================================
-- 第五阶段：删除旧关联表
-- ============================================

DROP TABLE IF EXISTS asset_versions CASCADE;
DROP TABLE IF EXISTS novel_asset_mappings CASCADE;
DROP TABLE IF EXISTS novel_skill_mappings CASCADE;
DROP TABLE IF EXISTS skill_constraints CASCADE;

-- ============================================
-- 第六阶段：验证结果
-- ============================================

SELECT '优化后表数量' as info, COUNT(*) as table_count
FROM information_schema.tables
WHERE table_schema = 'public'
    AND table_type = 'BASE TABLE'
    AND table_name NOT LIKE '_backup%';

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
    AND table_type = 'BASE TABLE'
    AND table_name NOT LIKE '_backup%'
ORDER BY table_name;

COMMIT;
