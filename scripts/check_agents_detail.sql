-- 查看当前 agents 的详细内容
SELECT 
    agent_id,
    name,
    role,
    prompt,
    temperature,
    personality,
    description,
    enabled
FROM agents 
WHERE deleted_at IS NULL
ORDER BY agent_id;
