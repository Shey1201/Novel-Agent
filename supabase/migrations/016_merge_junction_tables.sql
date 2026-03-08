-- ============================================
-- 合并关联表到主表
-- 目标：减少表数量，从 16 个表优化到 11 个表
-- ============================================

BEGIN;

-- ============================================
-- 第一阶段：备份关联表数据
-- ============================================

-- 备份 agent_skills
CREATE TABLE IF NOT EXISTS _backup_agent_skills AS SELECT * FROM agent_skills WHERE 1=0;
INSERT INTO _backup_agent_skills SELECT * FROM agent_skills;

-- 备份 asset_versions
CREATE TABLE IF NOT EXISTS _backup_asset_versions AS SELECT * FROM asset_versions WHERE 1=0;
INSERT INTO _backup_asset_versions SELECT * FROM asset_versions;

-- 备份 novel_asset_mappings
CREATE TABLE IF NOT EXISTS _backup_novel_asset_mappings AS SELECT * FROM novel_asset_mappings WHERE 1=0;
INSERT INTO _backup_novel_asset_mappings SELECT * FROM novel_asset_mappings;

-- 备份 novel_skill_mappings
CREATE TABLE IF NOT EXISTS _backup_novel_skill_mappings AS SELECT * FROM novel_skill_mappings WHERE 1=0;
INSERT INTO _backup_novel_skill_mappings SELECT * FROM novel_skill_mappings;

-- 备份 skill_constraints
CREATE TABLE IF NOT EXISTS _backup_skill_constraints AS SELECT * FROM skill_constraints WHERE 1=0;
INSERT INTO _backup_skill_constraints SELECT * FROM skill_constraints;

-- ============================================
-- 第二阶段：为主表添加新字段
-- ============================================

-- 1. agents 表添加 skill_ids 数组
ALTER TABLE agents
    ADD COLUMN IF NOT EXISTS skill_ids UUID[] DEFAULT '{}';

-- 2. assets 表添加 novel_ids 数组和 versions JSONB
ALTER TABLE assets
    ADD COLUMN IF NOT EXISTS novel_ids UUID[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS versions JSONB DEFAULT '[]';

-- 3. skills 表添加 novel_ids 数组和 constraints JSONB
ALTER TABLE skills
    ADD COLUMN IF NOT EXISTS novel_ids UUID[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS constraints JSONB DEFAULT '[]';

-- ============================================
-- 第三阶段：迁移关联数据到主表
-- ============================================

-- 1. 迁移 agent_skills 到 agents.skill_ids
UPDATE agents a
SET skill_ids = (
    SELECT ARRAY_AGG(skill_id)
    FROM agent_skills am
    WHERE am.agent_id = a.id
)
WHERE EXISTS (SELECT 1 FROM agent_skills am WHERE am.agent_id = a.id);

-- 2. 迁移 asset_versions 到 assets.versions
UPDATE assets a
SET versions = (
    SELECT JSONB_AGG(
        JSONB_BUILD_OBJECT(
            'id', id,
            'version', version,
            'content', content,
            'created_at', created_at
        ) ORDER BY created_at DESC
    )
    FROM asset_versions av
    WHERE av.asset_id = a.id
)
WHERE EXISTS (SELECT 1 FROM asset_versions av WHERE av.asset_id = a.id);

-- 3. 迁移 novel_asset_mappings 到 assets.novel_ids
UPDATE assets a
SET novel_ids = (
    SELECT ARRAY_AGG(novel_id)
    FROM novel_asset_mappings nam
    WHERE nam.asset_id = a.id
)
WHERE EXISTS (SELECT 1 FROM novel_asset_mappings nam WHERE nam.asset_id = a.id);

-- 4. 迁移 novel_skill_mappings 到 skills.novel_ids
UPDATE skills s
SET novel_ids = (
    SELECT ARRAY_AGG(novel_id)
    FROM novel_skill_mappings nsm
    WHERE nsm.skill_id = s.id
)
WHERE EXISTS (SELECT 1 FROM novel_skill_mappings nsm WHERE nsm.skill_id = s.id);

-- 5. 迁移 skill_constraints 到 skills.constraints
UPDATE skills s
SET constraints = (
    SELECT JSONB_AGG(
        JSONB_BUILD_OBJECT(
            'id', id,
            'type', type,
            'description', description,
            'priority', priority
        ) ORDER BY priority DESC
    )
    FROM skill_constraints sc
    WHERE sc.skill_id = s.id
)
WHERE EXISTS (SELECT 1 FROM skill_constraints sc WHERE sc.skill_id = s.id);

-- ============================================
-- 第四阶段：创建索引优化查询
-- ============================================

-- 为数组字段创建 GIN 索引
CREATE INDEX IF NOT EXISTS idx_agents_skill_ids ON agents USING GIN (skill_ids);
CREATE INDEX IF NOT EXISTS idx_assets_novel_ids ON assets USING GIN (novel_ids);
CREATE INDEX IF NOT EXISTS idx_skills_novel_ids ON skills USING GIN (novel_ids);

-- ============================================
-- 第五阶段：删除旧关联表
-- ============================================

DROP TABLE IF EXISTS agent_skills CASCADE;
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
