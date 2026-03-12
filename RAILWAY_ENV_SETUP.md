# Railway 环境变量配置

> ⚠️ **重要**：Railway 部署时必须在 Variables 中设置 `PORT = 8000`（否则后端会默认监听 8000 端口，但 Railway 无法正确路由外部请求）。

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

---

## 线上不显示数据 / Failed to fetch / ERR_CONNECTION_CLOSED

**现象**：Vercel 前端打开后「暂无 Agent 数据」、控制台报 `TypeError: Failed to fetch` 或 `net::ERR_CONNECTION_CLOSED`。

**排查步骤**：

1. **Vercel 环境变量**  
   在 Vercel 项目 → Settings → Environment Variables 中必须设置：
   - `NEXT_PUBLIC_API_URL` = 你的 Railway 后端地址（如 `https://xxx.up.railway.app`）  
   修改后需重新部署（Redeploy）一次。

2. **Railway 环境变量**  
   在 Railway 服务 → Variables 中确认：
   - `SUPABASE_URL`、`SUPABASE_SERVICE_KEY` 已正确填写  
   否则后端连不上 Supabase，接口会返回空数据或 500。

3. **Railway 服务是否正常**  
   - 浏览器直接访问：`https://你的Railway域名/api/health`，应返回 `{"status":"ok"}`。  
   - 若打不开或超时，说明后端未启动、崩溃或冷启动中；可查看 Railway 的 Deployments / Logs 排查。

4. **冷启动**  
   Railway 免费档在闲置一段时间后会休眠，首次请求可能超时。前端已对首屏请求做多次自动重试；若仍失败，可等待 10～30 秒后刷新页面再试。

5. **ERR_CONNECTION_CLOSED 但请求地址正确**  
   若控制台里请求已发往正确的 Railway 地址（如 `https://xxx.cn.railway.app`）仍报 `ERR_CONNECTION_CLOSED`，说明后端未响应。请：
   - 浏览器直接打开：`https://你的Railway域名/api/health`，看是否返回 `{"status":"ok"}`；
   - 在 Railway Dashboard 查看该服务的 **Deployments / Logs**，确认无启动报错、无崩溃；
   - 若使用 `cn.railway.app`，确认该区域服务可被你的网络访问（如无防火墙/策略拦截）。
