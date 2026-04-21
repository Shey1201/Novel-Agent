-- 禁用 agent_configs 表的 RLS
ALTER TABLE agent_configs DISABLE ROW LEVEL SECURITY;

-- 清空现有数据
DELETE FROM agent_configs;

-- 插入默认 Agent 配置（不需要 user_id）
INSERT INTO agent_configs (agent_id, name, role, prompt, temperature, enabled, personality) VALUES
    ('facilitator', 'Facilitator', '调度协调', '负责Agent调度和讨论主持', 0.5, true, 'structure'),
    ('planner', 'Planner', '规划架构', '负责章节规划和剧情架构', 0.7, true, 'structure'),
    ('writer', 'Writer', '章节写作', '负责具体章节写作', 0.9, true, 'literary'),
    ('editor', 'Editor', '润色修订', '负责文本润色和结构优化', 0.4, true, 'logic'),
    ('conflict', 'Conflict', '冲突设计', '负责冲突设计和戏剧性增强', 0.8, true, 'drama'),
    ('reader', 'Reader', '读者评估', '负责读者视角评估', 0.6, true, 'reader'),
    ('consistency', 'Consistency', '一致性检查', '负责逻辑一致性检查', 0.3, true, 'logic'),
    ('critic', 'Critic', '批判评估', '负责批判性评估和改进建议', 0.5, true, 'logic'),
    ('summary', 'Summary', '摘要总结', '负责内容摘要和总结', 0.4, true, 'structure');

-- 确认数据
SELECT agent_id, name, temperature FROM agent_configs;
