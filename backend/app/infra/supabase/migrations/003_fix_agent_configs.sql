-- 删除没有 user_id 的 agent_configs 记录
-- 这样应用会自动为登录用户创建新的记录

DELETE FROM agent_configs WHERE user_id IS NULL;

-- 确认删除后的数据
SELECT agent_id, name, user_id, temperature FROM agent_configs;
