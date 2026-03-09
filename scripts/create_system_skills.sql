-- 创建系统内置 Skill 和分类
-- 这些 Skill 是系统必需的，用户无法修改

-- 分类 1: 系统内置-安全与合规
INSERT INTO skill_categories (id, name, type, parent_id, color, icon, is_system, description, default_agents, "order")
VALUES (
    'cat-system-safety',
    '系统内置-安全与合规',
    'system',
    NULL,
    '#ef4444',
    'shield',
    true,
    '系统安全审查和合规检测，确保生成内容符合规范',
    ARRAY['consistency', 'critic'],
    0
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    type = EXCLUDED.type,
    is_system = EXCLUDED.is_system,
    description = EXCLUDED.description,
    default_agents = EXCLUDED.default_agents,
    "order" = EXCLUDED."order";

-- 分类 2: 系统内置-基础逻辑
INSERT INTO skill_categories (id, name, type, parent_id, color, icon, is_system, description, default_agents, "order")
VALUES (
    'cat-system-logic',
    '系统内置-基础逻辑',
    'system',
    NULL,
    '#3b82f6',
    'check-circle',
    true,
    '系统逻辑检测和一致性审查，保证故事逻辑合理',
    ARRAY['consistency', 'critic'],
    1
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    type = EXCLUDED.type,
    is_system = EXCLUDED.is_system,
    description = EXCLUDED.description,
    default_agents = EXCLUDED.default_agents,
    "order" = EXCLUDED."order";

-- Skill 1: 内容安全审查 (属于 系统内置-安全与合规)
INSERT INTO skills (
    id, name, description, category_id, constraints, target_agents, 
    version, is_active, is_system, linked_assets, applicable_novels, 
    author, test_example, created_at, updated_at
) VALUES (
    'skill-content-safety',
    '内容安全审查',
    '保证生成内容不含违法、敏感或低俗信息。',
    'cat-system-safety',
    '[{"id":"constraint-content-safety","content":"在生成文本前，请严格检查内容：<br>1. 避免政治敏感、仇恨、歧视性或暴力语言<br>2. 禁止色情、低俗、血腥描写<br>3. 避免侵犯版权、隐私或使用未授权信息<br>如果发现违规内容，立即停止生成，并输出：<br>- 检测结果：违规类型<br>- 建议处理：阻止/替换内容<br>请保持输出格式整洁。","priority":"high","enabled":true}]'::jsonb,
    ARRAY['writer', 'critic'],
    '1.0.0',
    true,
    true,
    ARRAY[]::text[],
    ARRAY[]::text[],
    'system',
    '检测结果：政治敏感内容<br>建议处理：阻止生成，建议修改涉及敏感政治的段落',
    NOW(),
    NOW()
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    category_id = EXCLUDED.category_id,
    constraints = EXCLUDED.constraints,
    target_agents = EXCLUDED.target_agents,
    is_active = EXCLUDED.is_active,
    is_system = EXCLUDED.is_system,
    test_example = EXCLUDED.test_example,
    updated_at = NOW();

-- Skill 2: 连贯性检测 (属于 系统内置-基础逻辑)
INSERT INTO skills (
    id, name, description, category_id, constraints, target_agents, 
    version, is_active, is_system, linked_assets, applicable_novels, 
    author, test_example, created_at, updated_at
) VALUES (
    'skill-consistency-check',
    '连贯性检测',
    '确保故事事件顺序合理、前后逻辑一致。',
    'cat-system-logic',
    '[{"id":"constraint-consistency-check","content":"分析以下文本的事件逻辑：<br>1. 检查事件时间顺序是否合理<br>2. 检查因果关系是否清晰<br>3. 标记逻辑冲突段落并提供修改建议<br><br>输出格式：<br>- 冲突段落：<br>- 问题描述：<br>- 建议修改：<br>确保输出简明，便于直接修正文稿。","priority":"high","enabled":true}]'::jsonb,
    ARRAY['critic', 'consistency'],
    '1.0.0',
    true,
    true,
    ARRAY[]::text[],
    ARRAY[]::text[],
    'system',
    '- 冲突段落：第3章主角先与敌人和解，第5章又在未知原因下攻击敌人<br>- 问题描述：行为前后矛盾，缺少动机说明<br>- 建议修改：在第5章开头加入主角发现敌人背叛的情节',
    NOW(),
    NOW()
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    category_id = EXCLUDED.category_id,
    constraints = EXCLUDED.constraints,
    target_agents = EXCLUDED.target_agents,
    is_active = EXCLUDED.is_active,
    is_system = EXCLUDED.is_system,
    test_example = EXCLUDED.test_example,
    updated_at = NOW();

-- Skill 3: 角色一致性 (属于 系统内置-基础逻辑)
INSERT INTO skills (
    id, name, description, category_id, constraints, target_agents, 
    version, is_active, is_system, linked_assets, applicable_novels, 
    author, test_example, created_at, updated_at
) VALUES (
    'skill-character-consistency',
    '角色一致性',
    '保证人物性格、背景和行为在全篇故事中一致。',
    'cat-system-logic',
    '[{"id":"constraint-character-consistency","content":"对文本中的每个角色进行一致性检查：<br>1. 性格特征是否前后一致<br>2. 背景经历是否与设定匹配<br>3. 行为是否符合角色逻辑<br><br>输出格式：<br>- 冲突段落：<br>- 冲突类型（性格/背景/行为）：<br>- 修改建议：<br>确保输出详细且可直接应用修改。","priority":"high","enabled":true}]'::jsonb,
    ARRAY['consistency', 'critic'],
    '1.0.0',
    true,
    true,
    ARRAY[]::text[],
    ARRAY[]::text[],
    'system',
    '- 冲突段落：第2章主角性格内向害羞，第4章却在陌生人面前侃侃而谈<br>- 冲突类型（性格/背景/行为）：性格<br>- 修改建议：在第4章加入主角内心挣扎的描写，或修改为在熟悉环境下才主动交流',
    NOW(),
    NOW()
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    category_id = EXCLUDED.category_id,
    constraints = EXCLUDED.constraints,
    target_agents = EXCLUDED.target_agents,
    is_active = EXCLUDED.is_active,
    is_system = EXCLUDED.is_system,
    test_example = EXCLUDED.test_example,
    updated_at = NOW();

-- 输出结果
SELECT '系统 Skill 和分类创建完成' as result;
SELECT id, name, is_system FROM skill_categories WHERE is_system = true ORDER BY "order";
SELECT id, name, category_id, is_system FROM skills WHERE is_system = true ORDER BY name;
