-- 插入初始 Agent 配置（使用当前认证用户）
-- 注意：需要在已登录状态下执行
-- 此迁移仅在 agents 表为空时执行

DO $$
BEGIN
    -- 检查 agents 表是否已有数据
    IF NOT EXISTS (SELECT 1 FROM agents WHERE deleted_at IS NULL LIMIT 1) THEN
        INSERT INTO agents (user_id, agent_id, name, role, prompt, temperature, personality, enabled)
        SELECT 
            auth.uid(),
            agent.agent_id,
            agent.name,
            agent.role,
            agent.prompt,
            agent.temperature,
            agent.personality,
            TRUE
        FROM (VALUES
            ('writer', 'Writer', '故事撰写者', '撰写故事内容，创作精彩情节', 0.5, 'creative'),
            ('editor', 'Editor', '内容编辑', '编辑和改进内容质量', 0.3, 'logic'),
            ('reviewer', 'Reviewer', '质量审核', '审核内容质量和一致性', 0.4, 'logic'),
            ('world-builder', 'World Builder', '世界构建师', '构建小说世界观和背景设定', 0.6, 'creative'),
            ('character-designer', 'Character Designer', '角色设计师', '设计角色性格和背景故事', 0.5, 'creative')
        ) AS agent(agent_id, name, role, prompt, temperature, personality)
        WHERE auth.uid() IS NOT NULL
        ON CONFLICT (user_id, agent_id) DO UPDATE SET
            name = EXCLUDED.name,
            role = EXCLUDED.role,
            prompt = EXCLUDED.prompt,
            temperature = EXCLUDED.temperature,
            personality = EXCLUDED.personality,
            updated_at = NOW();
    END IF;
END $$;
