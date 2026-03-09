-- ============================================
-- 修正 agents 的 role 字段
-- ============================================

-- role 应该是英文描述（Role下面一行的内容）

UPDATE agents SET
    role = '负责多Agent之间的协调与任务调度，主持讨论并推动决策达成。'
WHERE agent_id = 'facilitator';

UPDATE agents SET
    role = '负责故事结构设计和剧情规划。'
WHERE agent_id = 'planner';

UPDATE agents SET
    role = '负责将剧情规划转化为完整小说章节。'
WHERE agent_id = 'writer';

UPDATE agents SET
    role = '负责优化小说语言与叙事质量。'
WHERE agent_id = 'editor';

UPDATE agents SET
    role = '负责设计剧情冲突与戏剧张力。'
WHERE agent_id = 'conflict';

UPDATE agents SET
    role = '模拟真实读者的阅读体验。'
WHERE agent_id = 'reader';

UPDATE agents SET
    role = '检查小说设定一致性。'
WHERE agent_id = 'consistency';

UPDATE agents SET
    role = '对章节进行严格质量评估。'
WHERE agent_id = 'critic';

UPDATE agents SET
    role = '总结讨论与剧情进展。'
WHERE agent_id = 'summary';

-- 验证结果
SELECT agent_id, name, role
FROM agents 
WHERE deleted_at IS NULL
ORDER BY agent_id;
