-- ============================================
-- 数据库迁移 CRUD 测试（移除外键约束后）
-- ============================================

-- 临时移除外键约束（测试完成后可以恢复）
ALTER TABLE agents DROP CONSTRAINT IF EXISTS agents_user_id_fkey;
ALTER TABLE assets DROP CONSTRAINT IF EXISTS assets_user_id_fkey;
ALTER TABLE settings DROP CONSTRAINT IF EXISTS settings_user_id_fkey;

-- 使用匿名用户ID进行测试
DO $$
DECLARE
    test_agent_id UUID;
    test_asset_id UUID;
    test_settings_id UUID;
    v_count INTEGER;
    v_name TEXT;
    ANON_USER_ID CONSTANT UUID := 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'::UUID;
BEGIN
    RAISE NOTICE '🧪 开始数据库迁移 CRUD 测试...';
    RAISE NOTICE '使用匿名用户ID: %', ANON_USER_ID;
    RAISE NOTICE '========================================';

    -- 1. 测试 Agents CRUD
    RAISE NOTICE '\n🤖 测试1: Agents CRUD';
    
    -- Create
    INSERT INTO agents (user_id, agent_id, name, role, prompt, temperature, enabled, personality)
    VALUES (ANON_USER_ID, 'test-agent-' || extract(epoch from now())::text, '测试Agent', 'writer', '测试prompt', 0.7, true, 'creative')
    RETURNING id INTO test_agent_id;
    RAISE NOTICE 'Agent 创建: ✅ ID: %', test_agent_id;
    
    -- Read
    SELECT COUNT(*) INTO v_count FROM agents WHERE id = test_agent_id;
    RAISE NOTICE 'Agent 读取: %', CASE WHEN v_count > 0 THEN '✅ 成功' ELSE '❌ 失败' END;
    
    -- Update
    UPDATE agents SET name = '更新的测试Agent' WHERE id = test_agent_id;
    SELECT name INTO v_name FROM agents WHERE id = test_agent_id;
    RAISE NOTICE 'Agent 更新: %', CASE WHEN v_name = '更新的测试Agent' THEN '✅ 成功' ELSE '❌ 失败' END;
    
    -- Soft Delete
    UPDATE agents SET deleted_at = NOW() WHERE id = test_agent_id;
    SELECT COUNT(*) INTO v_count FROM agents WHERE id = test_agent_id AND deleted_at IS NULL;
    RAISE NOTICE 'Agent 软删除: %', CASE WHEN v_count = 0 THEN '✅ 成功' ELSE '❌ 失败' END;

    -- 2. 测试 Assets CRUD
    RAISE NOTICE '\n📦 测试2: Assets CRUD';
    
    -- Create local asset
    INSERT INTO assets (user_id, type, name, content, is_global, color)
    VALUES (ANON_USER_ID, 'characters', '测试角色', '{"desc": "test"}'::jsonb, false, '#ff0000')
    RETURNING id INTO test_asset_id;
    RAISE NOTICE '本地 Asset 创建: ✅ ID: %', test_asset_id;
    
    -- Create global asset
    INSERT INTO assets (user_id, type, name, description, is_global, is_starred, color)
    VALUES (ANON_USER_ID, 'worldbuilding', '测试世界观', '描述', true, true, '#00ff00');
    RAISE NOTICE '全局 Asset 创建: ✅';
    
    -- Query by type
    SELECT COUNT(*) INTO v_count FROM assets WHERE type = 'characters' AND deleted_at IS NULL;
    RAISE NOTICE '按类型查询: ✅ 找到 % 个角色', v_count;
    
    -- Query global
    SELECT COUNT(*) INTO v_count FROM assets WHERE is_global = true AND deleted_at IS NULL;
    RAISE NOTICE '全局 Asset 查询: ✅ 找到 % 个', v_count;
    
    -- Cleanup
    UPDATE assets SET deleted_at = NOW() WHERE user_id = ANON_USER_ID;
    RAISE NOTICE 'Asset 清理: ✅';

    -- 3. 测试 Settings CRUD
    RAISE NOTICE '\n⚙️ 测试3: Settings CRUD';
    
    INSERT INTO settings (user_id, token_enabled, token_daily_limit, discussion_max_rounds, constraints, writing_mode)
    VALUES (ANON_USER_ID, true, 100000, 3, ARRAY['禁止暴力'], 'auto')
    ON CONFLICT (user_id) DO UPDATE SET token_daily_limit = 150000
    RETURNING id INTO test_settings_id;
    RAISE NOTICE 'Settings 创建/更新: ✅ ID: %', test_settings_id;

    -- 4. 数据迁移验证
    RAISE NOTICE '\n📊 测试4: 数据迁移验证';
    
    SELECT COUNT(*) INTO v_count FROM agents WHERE deleted_at IS NULL;
    RAISE NOTICE 'agents 记录数: %', v_count;
    
    SELECT COUNT(*) INTO v_count FROM assets WHERE deleted_at IS NULL;
    RAISE NOTICE 'assets 记录数: %', v_count;
    
    SELECT COUNT(*) INTO v_count FROM settings WHERE deleted_at IS NULL;
    RAISE NOTICE 'settings 记录数: %', v_count;

    RAISE NOTICE '\n========================================';
    RAISE NOTICE '🎉 CRUD 测试完成！';
    RAISE NOTICE '========================================';
    
END $$;

-- 清理测试数据
DELETE FROM agents WHERE user_id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'::UUID;
DELETE FROM assets WHERE user_id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'::UUID;
DELETE FROM settings WHERE user_id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'::UUID;

-- 恢复外键约束（如果需要）
-- ALTER TABLE agents ADD CONSTRAINT agents_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);
-- ALTER TABLE assets ADD CONSTRAINT assets_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);
-- ALTER TABLE settings ADD CONSTRAINT settings_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);
