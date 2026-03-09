-- ============================================
-- 重置 agents 数据为正确的默认值
-- ============================================

-- 先查看当前数据
SELECT '当前agents数据' as status;
SELECT agent_id, name, role, temperature, personality, enabled 
FROM agents 
WHERE deleted_at IS NULL
ORDER BY agent_id;

-- ============================================
-- 清空并重新插入正确的 agents 数据
-- ============================================

-- 先清空当前数据
DELETE FROM agents WHERE deleted_at IS NULL;

-- 插入正确的默认 agents 数据
INSERT INTO agents (
    id, user_id, agent_id, name, role, prompt, 
    temperature, enabled, personality, avatar_url, 
    description, created_at, updated_at
) VALUES 
(
    gen_random_uuid(),
    NULL,
    'writer',
    'Writer',
    '故事撰写者',
    '撰写故事内容，创作精彩情节',
    0.5,
    TRUE,
    'creative',
    '',
    '负责撰写小说内容',
    NOW(),
    NOW()
),
(
    gen_random_uuid(),
    NULL,
    'editor',
    'Editor',
    '内容编辑',
    '编辑和改进内容质量',
    0.3,
    TRUE,
    'logic',
    '',
    '负责编辑和改进内容',
    NOW(),
    NOW()
),
(
    gen_random_uuid(),
    NULL,
    'planner',
    'Planner',
    '规划师',
    '规划故事大纲和章节结构',
    0.4,
    TRUE,
    'logic',
    '',
    '负责规划故事结构',
    NOW(),
    NOW()
),
(
    gen_random_uuid(),
    NULL,
    'conflict',
    'Conflict',
    '冲突设计师',
    '设计和优化故事冲突',
    0.5,
    TRUE,
    'creative',
    '',
    '负责设计故事冲突',
    NOW(),
    NOW()
),
(
    gen_random_uuid(),
    NULL,
    'reader',
    'Reader',
    '读者代表',
    '从读者角度提供反馈',
    0.4,
    TRUE,
    'logic',
    '',
    '代表读者提供反馈',
    NOW(),
    NOW()
),
(
    gen_random_uuid(),
    NULL,
    'critic',
    'Critic',
    '评论家',
    '批判性分析内容质量',
    0.3,
    TRUE,
    'logic',
    '',
    '批判性分析内容',
    NOW(),
    NOW()
),
(
    gen_random_uuid(),
    NULL,
    'summary',
    'Summary',
    '总结者',
    '总结和提炼关键信息',
    0.4,
    TRUE,
    'logic',
    '',
    '负责总结内容',
    NOW(),
    NOW()
),
(
    gen_random_uuid(),
    NULL,
    'facilitator',
    'Facilitator',
    '主持人',
    '协调讨论流程',
    0.5,
    TRUE,
    'creative',
    '',
    '协调讨论流程',
    NOW(),
    NOW()
)
ON CONFLICT (user_id, agent_id) DO UPDATE SET
    name = EXCLUDED.name,
    role = EXCLUDED.role,
    prompt = EXCLUDED.prompt,
    temperature = EXCLUDED.temperature,
    personality = EXCLUDED.personality,
    updated_at = NOW();

-- ============================================
-- 验证结果
-- ============================================

SELECT '重置后的agents数据' as status;
SELECT 
    agent_id, 
    name, 
    role, 
    temperature,
    personality,
    enabled
FROM agents 
WHERE deleted_at IS NULL
ORDER BY agent_id;

SELECT COUNT(*) as total_agents FROM agents WHERE deleted_at IS NULL;
