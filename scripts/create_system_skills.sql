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
    ARRAY['critic', 'editor'],
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
-- 使用Agent：critic（主）、editor（辅）
INSERT INTO skills (
    id, name, description, category_id, constraints, target_agents, 
    version, is_active, is_system, linked_assets, applicable_novels, 
    author, test_example, created_at, updated_at
) VALUES (
    'skill-content-safety',
    '内容安全审查',
    '在小说生成或修改过程中，检测文本是否包含违规、敏感或不适宜内容，保证生成文本安全合规。',
    'cat-system-safety',
    '[{"id":"constraint-content-safety","content":"你的任务是进行内容安全审查。<br><br>请检查以下文本是否包含：<br>1. 政治敏感内容<br>2. 仇恨、歧视或攻击性言论<br>3. 色情或低俗描写<br>4. 过度血腥或极端暴力<br>5. 侵犯版权或隐私内容<br><br>审查要求：<br>- 不改变文本内容<br>- 仅进行检测与标注<br>- 如果存在问题，请指出具体段落<br><br>输出格式：<br>安全检测结果：<br>是否存在问题：是 / 否<br><br>若存在问题：<br>问题类型：<br>问题段落：<br>建议处理方式：","priority":"high","enabled":true}]'::jsonb,
    ARRAY['critic', 'editor'],
    '1.0.0',
    true,
    true,
    ARRAY[]::text[],
    ARRAY[]::text[],
    'system',
    '安全检测结果：<br>是否存在问题：是<br><br>若存在问题：<br>问题类型：政治敏感内容<br>问题段落：第三章涉及敏感政治话题<br>建议处理方式：建议修改或删除该段落',
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
-- 使用Agent：consistency（主）、critic（辅）
INSERT INTO skills (
    id, name, description, category_id, constraints, target_agents, 
    version, is_active, is_system, linked_assets, applicable_novels, 
    author, test_example, created_at, updated_at
) VALUES (
    'skill-consistency-check',
    '连贯性检测',
    '检测小说剧情中的时间线、事件因果关系和叙事逻辑是否一致。',
    'cat-system-logic',
    '[{"id":"constraint-consistency-check","content":"你的任务是进行剧情连贯性检测。<br><br>请检查文本中的：<br>1. 时间顺序是否合理<br>2. 事件是否存在因果关系<br>3. 剧情是否出现逻辑跳跃<br>4. 角色行为是否突然改变<br><br>不要修改文本，只进行分析。<br><br>输出格式：<br>连贯性检查结果：<br><br>问题段落：<br>问题类型：（时间线/因果逻辑/剧情跳跃）<br><br>问题说明：<br><br>修改建议：","priority":"high","enabled":true}]'::jsonb,
    ARRAY['consistency', 'critic'],
    '1.0.0',
    true,
    true,
    ARRAY[]::text[],
    ARRAY[]::text[],
    'system',
    '连贯性检查结果：<br><br>问题段落：第5章主角突然出现在另一个城市<br>问题类型：时间线<br><br>问题说明：第4章结尾主角还在家中，第5章开头已到达千里之外的城市，缺少行程交代<br><br>修改建议：在第5章开头加入主角赶路的情节，或说明时间跨度',
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
-- 使用Agent：consistency（主）
INSERT INTO skills (
    id, name, description, category_id, constraints, target_agents, 
    version, is_active, is_system, linked_assets, applicable_novels, 
    author, test_example, created_at, updated_at
) VALUES (
    'skill-character-consistency',
    '角色一致性',
    '检查人物设定、性格、行为是否在故事中保持一致。',
    'cat-system-logic',
    '[{"id":"constraint-character-consistency","content":"你的任务是检查角色一致性。<br><br>请分析以下内容：<br>1. 角色性格是否前后一致<br>2. 角色行为是否符合设定<br>3. 角色背景是否发生冲突<br><br>若发现问题，请指出：<br><br>角色名称：<br>问题段落：<br>问题类型（性格 / 背景 / 行为）：<br><br>建议修改方式：","priority":"high","enabled":true}]'::jsonb,
    ARRAY['consistency'],
    '1.0.0',
    true,
    true,
    ARRAY[]::text[],
    ARRAY[]::text[],
    'system',
    '角色名称：李明<br>问题段落：第3章<br>问题类型（性格 / 背景 / 行为）：性格<br><br>建议修改方式：前文设定李明性格内向不善言辞，此处却突然主动发表长篇演讲，建议增加内心挣扎描写或改为简短回应',
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
SELECT id, name, category_id, target_agents, is_system FROM skills WHERE is_system = true ORDER BY name;
