-- 创建系统内置 Skill
-- 这些 Skill 是系统必需的，用户无法修改

-- 首先确保系统分类存在
INSERT INTO skill_categories (id, name, type, parent_id, color, icon, is_system, description, default_agents, "order")
VALUES (
    'cat-system-auditing',
    '系统审计',
    'auditing',
    NULL,
    '#ef4444',
    'shield',
    true,
    '系统自动审计和检测技能，确保生成内容的质量和合规性',
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

-- Skill 1: 内容安全审查
INSERT INTO skills (
    id, name, description, category_id, constraints, target_agents, 
    version, is_active, is_system, linked_assets, applicable_novels, 
    author, test_example, created_at, updated_at
) VALUES (
    'skill-content-safety',
    '内容安全审查',
    '自动检测生成文本是否含有违规、敏感或不适宜内容，保证生成内容合规安全。',
    'cat-system-auditing',
    '[
        {
            "id": "constraint-content-safety",
            "content": "在生成故事文本前，请严格检查内容：<br>- 识别并标记政治敏感、暴力、仇恨或歧视性语言<br>- 识别色情或低俗描写，含过度血腥场景需阻止<br>- 检查是否涉及版权或隐私侵权<br>如果发现违规内容，停止生成，并返回"违规提示+违规类型"。",
            "priority": "high",
            "enabled": true
        }
    ]'::jsonb,
    ARRAY['consistency', 'critic'],
    '1.0.0',
    true,
    true,
    ARRAY[]::text[],
    ARRAY[]::text[],
    'system',
    '违规检测结果：文本涉及政治敏感内容，生成被阻止。',
    NOW(),
    NOW()
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    constraints = EXCLUDED.constraints,
    target_agents = EXCLUDED.target_agents,
    is_active = EXCLUDED.is_active,
    is_system = EXCLUDED.is_system,
    test_example = EXCLUDED.test_example,
    updated_at = NOW();

-- Skill 2: 连贯性检测
INSERT INTO skills (
    id, name, description, category_id, constraints, target_agents, 
    version, is_active, is_system, linked_assets, applicable_novels, 
    author, test_example, created_at, updated_at
) VALUES (
    'skill-consistency-check',
    '连贯性检测',
    '保证故事事件、时间线、逻辑前后一致，避免读者产生理解困扰。',
    'cat-system-auditing',
    '[
        {
            "id": "constraint-consistency-check",
            "content": "分析故事文本：<br>1. 检查事件时间顺序是否合理<br>2. 检查因果关系是否正确<br>3. 标记逻辑冲突的段落，并提出修改建议<br><br>输出格式：<br>- 冲突段落：<br>- 问题描述：<br>- 建议修改：",
            "priority": "high",
            "enabled": true
        }
    ]'::jsonb,
    ARRAY['consistency', 'critic'],
    '1.0.0',
    true,
    true,
    ARRAY[]::text[],
    ARRAY[]::text[],
    'system',
    '冲突段落：第3章主角先与敌人和解，第5章又在未知原因下攻击敌人<br>问题描述：行为前后矛盾<br>建议修改：在第5章加入原因说明，保证行为逻辑一致',
    NOW(),
    NOW()
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    constraints = EXCLUDED.constraints,
    target_agents = EXCLUDED.target_agents,
    is_active = EXCLUDED.is_active,
    is_system = EXCLUDED.is_system,
    test_example = EXCLUDED.test_example,
    updated_at = NOW();

-- Skill 3: 角色一致性
INSERT INTO skills (
    id, name, description, category_id, constraints, target_agents, 
    version, is_active, is_system, linked_assets, applicable_novels, 
    author, test_example, created_at, updated_at
) VALUES (
    'skill-character-consistency',
    '角色一致性',
    '确保角色性格、背景、行为在全篇故事中一致，防止角色塑造出现逻辑错位。',
    'cat-system-auditing',
    '[
        {
            "id": "constraint-character-consistency",
            "content": "对每个角色进行一致性检查：<br>1. 性格是否前后一致<br>2. 背景设定是否被破坏<br>3. 行为是否符合性格逻辑<br><br>输出格式：<br>- 冲突段落：<br>- 问题描述：<br>- 建议修改：",
            "priority": "high",
            "enabled": true
        }
    ]'::jsonb,
    ARRAY['consistency', 'critic'],
    '1.0.0',
    true,
    true,
    ARRAY[]::text[],
    ARRAY[]::text[],
    'system',
    '冲突段落：第2章主角性格内向害羞，第4章却在陌生人面前侃侃而谈<br>问题描述：性格设定前后不一致<br>建议修改：在第4章加入内心挣扎描写，或修改场景使其符合内向性格',
    NOW(),
    NOW()
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    constraints = EXCLUDED.constraints,
    target_agents = EXCLUDED.target_agents,
    is_active = EXCLUDED.is_active,
    is_system = EXCLUDED.is_system,
    test_example = EXCLUDED.test_example,
    updated_at = NOW();

-- 输出结果
SELECT '系统 Skill 创建完成' as result;
SELECT id, name, is_system, is_active FROM skills WHERE is_system = true;
