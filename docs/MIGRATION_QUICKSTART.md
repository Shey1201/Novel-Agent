# 数据库迁移快速开始指南

## 🚀 一键迁移（推荐）

```bash
cd scripts
python execute_migration.py
```

按照提示操作即可完成完整迁移。

---

## 📋 手动迁移步骤

### 1. 备份数据
```bash
cd scripts
python backup_database.py
```

### 2. 执行 SQL 迁移
在 Supabase SQL Editor 中执行：
```sql
-- 复制 supabase/migrations/015_optimize_database_schema.sql 的全部内容
```

### 3. 验证迁移
```bash
python -c "from scripts.execute_migration import verify_migration; verify_migration()"
```

### 4. 部署代码
```bash
# 后端
cd backend
git push origin master

# 前端
cd frontend
git push origin master
vercel --prod
```

---

## ✅ 迁移检查清单

- [ ] 数据已备份
- [ ] SQL 迁移已执行
- [ ] `agents` 表可访问
- [ ] `assets` 表可访问
- [ ] `settings` 表可访问
- [ ] 后端代码已部署
- [ ] 前端代码已部署
- [ ] Agent 配置功能正常
- [ ] 资产管理功能正常
- [ ] 用户设置功能正常

---

## 🔄 回滚方案

如果迁移后出现问题：

```bash
cd scripts
python restore_database.py
```

---

## 📊 迁移前后对比

| 项目 | 迁移前 | 迁移后 |
|------|--------|--------|
| 表数量 | 17 个 | 13 个 |
| Agent 表 | agent_configs | agents |
| 资产表 | story_assets + global_assets | assets |
| 设置表 | user_settings + system_settings | settings |
| 软删除 | 部分支持 | 全部支持 |

---

## ⚠️ 常见问题

### Q: 迁移后数据丢失怎么办？
A: 使用 `restore_database.py` 恢复备份数据。

### Q: 新表结构不兼容旧代码？
A: 确保前后端代码都已更新并部署。

### Q: 软删除如何工作？
A: 删除操作会设置 `deleted_at` 字段，查询时自动过滤。

---

## 📞 支持

遇到问题请检查：
1. 环境变量是否正确设置
2. Supabase 连接是否正常
3. 迁移 SQL 是否完整执行
4. 代码是否已更新到最新版本
