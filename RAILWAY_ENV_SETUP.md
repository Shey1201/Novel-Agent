# Railway 环境变量配置

后端需要以下环境变量才能连接 Supabase 数据库：

## 必需的环境变量

```bash
# Supabase 连接配置
SUPABASE_URL=https://wzlzjhclzkrcosvkxsoa.supabase.co
SUPABASE_SERVICE_KEY=your_service_key_here

# 或者使用 Anon Key（权限较低）
# SUPABASE_ANON_KEY=your_anon_key_here
```

## 如何获取 Service Key

1. 登录 Supabase Dashboard: https://app.supabase.com
2. 进入你的项目
3. 点击左侧 "Project Settings" → "API"
4. 在 "Project API keys" 部分找到 `service_role` key（注意：这个 key 有完全访问权限，不要泄露）

## 在 Railway 中设置

1. 进入 Railway Dashboard
2. 选择你的后端服务
3. 点击 "Variables" 标签
4. 添加以下变量：
   - `SUPABASE_URL` = `https://wzlzjhclzkrcosvkxsoa.supabase.co`
   - `SUPABASE_SERVICE_KEY` = 你的 service_role key

## 验证连接

部署后查看 Railway 日志，应该能看到：
```
[NovelMemory] Connected to Supabase successfully
```

如果没有看到这条日志，说明连接失败，数据无法加载。
