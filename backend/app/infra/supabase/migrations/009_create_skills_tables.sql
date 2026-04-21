-- 创建技能分类表
CREATE TABLE IF NOT EXISTS skill_categories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('system', 'writing', 'domain', 'auditing')),
    parent_id TEXT REFERENCES skill_categories(id) ON DELETE SET NULL,
    color TEXT DEFAULT '#6366f1',
    icon TEXT,
    is_system BOOLEAN DEFAULT FALSE,
    description TEXT,
    default_agents TEXT[] DEFAULT '{}',
    "order" INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建技能表
CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    category_id TEXT REFERENCES skill_categories(id) ON DELETE SET NULL,
    target_agents TEXT[] DEFAULT '{}',
    version TEXT DEFAULT '1.0.0',
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT FALSE,
    linked_assets TEXT[] DEFAULT '{}',
    applicable_novels TEXT[] DEFAULT '{}',
    author TEXT,
    test_example TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建技能约束表
CREATE TABLE IF NOT EXISTS skill_constraints (
    id TEXT PRIMARY KEY,
    skill_id TEXT REFERENCES skills(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('high', 'medium', 'low')),
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 添加更新时间触发器
DROP TRIGGER IF EXISTS update_skill_categories_updated_at ON skill_categories;
CREATE TRIGGER update_skill_categories_updated_at BEFORE UPDATE ON skill_categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_skills_updated_at ON skills;
CREATE TRIGGER update_skills_updated_at BEFORE UPDATE ON skills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 启用 RLS
ALTER TABLE skill_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_constraints ENABLE ROW LEVEL SECURITY;

-- 创建访问策略（允许所有人读取，只有认证用户可以修改）
DROP POLICY IF EXISTS "Allow public read access" ON skill_categories;
CREATE POLICY "Allow public read access" ON skill_categories
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow authenticated users to modify" ON skill_categories;
CREATE POLICY "Allow authenticated users to modify" ON skill_categories
    FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Allow public read access" ON skills;
CREATE POLICY "Allow public read access" ON skills
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow authenticated users to modify" ON skills;
CREATE POLICY "Allow authenticated users to modify" ON skills
    FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');

DROP POLICY IF EXISTS "Allow public read access" ON skill_constraints;
CREATE POLICY "Allow public read access" ON skill_constraints
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow authenticated users to modify" ON skill_constraints;
CREATE POLICY "Allow authenticated users to modify" ON skill_constraints
    FOR ALL USING (auth.role() = 'authenticated') WITH CHECK (auth.role() = 'authenticated');

-- 插入默认分类数据
INSERT INTO skill_categories (id, name, type, parent_id, color, is_system, description, default_agents, "order") VALUES
    ('cat-system-root', '系统内置', 'system', NULL, '#ef4444', true, '系统默认启用的基础约束，不可删除', ARRAY['writer', 'editor'], 0),
    ('cat-safety', '安全合规', 'system', 'cat-system-root', '#dc2626', true, '禁止血腥、暴力、色情等硬性约束', ARRAY['writer', 'editor'], 0),
    ('cat-logic', '基础逻辑', 'system', 'cat-system-root', '#ea580c', true, '常识一致性、时空因果律等底层规则', ARRAY['writer', 'editor', 'planner'], 1),
    ('cat-writing-root', '创作文风', 'writing', NULL, '#3b82f6', true, '管理写作风格和文风的技能分类', ARRAY['writer'], 1),
    ('cat-light-novel', '轻小说类', 'writing', 'cat-writing-root', '#60a5fa', false, '日式轻小说风格', ARRAY['writer'], 0),
    ('cat-hard-sf', '硬核科幻', 'writing', 'cat-writing-root', '#818cf8', false, '硬科幻文学风格', ARRAY['writer'], 1),
    ('cat-classical', '古典文学', 'writing', 'cat-writing-root', '#a78bfa', false, '古典文学风格', ARRAY['writer'], 2),
    ('cat-domain-root', '领域知识', 'domain', NULL, '#10b981', true, '管理专业领域知识的技能分类', ARRAY['writer', 'editor'], 2),
    ('cat-medical', '医学知识', 'domain', 'cat-domain-root', '#34d399', false, '医学专业领域知识', ARRAY['writer', 'editor'], 0),
    ('cat-martial', '武术体系', 'domain', 'cat-domain-root', '#2dd4bf', false, '武术、战斗系统知识', ARRAY['writer'], 1),
    ('cat-space', '星际航行', 'domain', 'cat-domain-root', '#5eead4', false, '科幻星际航行相关知识', ARRAY['writer'], 2),
    ('cat-auditing-root', '质量审计', 'auditing', NULL, '#f59e0b', true, '管理质量检查和审计的技能分类', ARRAY['editor'], 3),
    ('cat-balance', '战力平衡', 'auditing', 'cat-auditing-root', '#fbbf24', false, '战力数值平衡检查', ARRAY['editor'], 0),
    ('cat-consistency', '人设一致', 'auditing', 'cat-auditing-root', '#fcd34d', false, '角色设定一致性检查', ARRAY['editor', 'reader'], 1)
ON CONFLICT (id) DO NOTHING;

-- 插入默认技能数据
INSERT INTO skills (id, name, description, category_id, target_agents, version, is_active, is_system, linked_assets, applicable_novels) VALUES
    ('skill-no-violence', '禁止暴力描写', '禁止过度详细的暴力场景描写', 'cat-safety', ARRAY['writer', 'editor'], '1.0.0', true, true, ARRAY[]::TEXT[], ARRAY[]::TEXT[]),
    ('skill-no-adult', '禁止色情内容', '禁止任何形式的色情、性暗示内容', 'cat-safety', ARRAY['writer', 'editor'], '1.0.0', true, true, ARRAY[]::TEXT[], ARRAY[]::TEXT[]),
    ('skill-causality', '因果一致性', '确保故事情节符合因果逻辑', 'cat-logic', ARRAY['writer', 'editor', 'planner'], '1.0.0', true, true, ARRAY[]::TEXT[], ARRAY[]::TEXT[])
ON CONFLICT (id) DO NOTHING;

-- 插入默认技能约束
INSERT INTO skill_constraints (id, skill_id, content, priority, enabled) VALUES
    ('constraint-1', 'skill-no-violence', '不得详细描写血腥、残忍的暴力场景', 'high', true),
    ('constraint-2', 'skill-no-violence', '战斗场景应保持适度，避免过度渲染', 'medium', true),
    ('constraint-3', 'skill-no-adult', '禁止露骨的性描写', 'high', true),
    ('constraint-4', 'skill-no-adult', '避免过度的性暗示', 'high', true),
    ('constraint-5', 'skill-causality', '事件发展应符合前因后果', 'high', true),
    ('constraint-6', 'skill-causality', '避免逻辑漏洞和矛盾', 'high', true)
ON CONFLICT (id) DO NOTHING;
