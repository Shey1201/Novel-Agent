# 数据库结构优化迁移指南

## 概述

本次迁移将优化数据库结构，减少冗余表，统一命名规范，提高查询性能。

## 主要变更

### 1. 表合并

| 旧表 | 新表 | 说明 |
|------|------|------|
| `agent_configs` | `agents` | 重命名并优化结构 |
| `story_assets` + `global_assets` | `assets` | 合并为统一资产表 |
| `system_settings` + `user_settings` | `settings` | 合并为统一设置表 |

### 2. 新增字段

**novels 表：**
- `outline` - 小说大纲
- `word_count` - 总字数
- `status` - 状态 (draft/writing/completed/archived)

**chapters 表：**
- `word_count` - 章节字数
- `summary` - 章节摘要
- `volume_name` - 卷名称
- `volume_order` - 卷顺序

**所有表：**
- `deleted_at` - 软删除时间戳

### 3. 索引优化

为所有表添加了适当的索引，提高查询性能。

## 迁移步骤

### 步骤 1：备份数据（自动）

迁移脚本会自动创建备份表：
- `_backup_novels`
- `_backup_chapters`
- `_backup_categories`
- ...等等

### 步骤 2：执行迁移

在 Supabase SQL Editor 中执行：

```sql
\i supabase/migrations/015_optimize_database_schema.sql
```

或者复制粘贴文件内容执行。

### 步骤 3：验证数据

迁移完成后，检查数据完整性：

```sql
-- 检查行数
SELECT 'novels' as table_name, COUNT(*) as count FROM novels
UNION ALL
SELECT 'chapters', COUNT(*) FROM chapters
UNION ALL
SELECT 'agents', COUNT(*) FROM agents
UNION ALL
SELECT 'assets', COUNT(*) FROM assets
UNION ALL
SELECT 'settings', COUNT(*) FROM settings;
```

### 步骤 4：更新后端代码

需要更新的文件：

1. **agent_memory.py**
   - 表名：`agent_configs` → `agents`
   - 添加 `deleted_at` 过滤

2. **novel_memory.py**
   - 已兼容，无需修改

3. **assetStore / global_asset_manager.py**
   - 表名：`story_assets` / `global_assets` → `assets`
   - 字段调整：`category` → `type`
   - 添加 `is_global` 字段处理

4. **system_settings.py**
   - 表名：`system_settings` → `settings`
   - 合并 `user_settings` 的字段

### 步骤 5：清理旧表（可选）

确认新表正常工作后，执行清理：

```sql
-- 删除旧表
DROP TABLE IF EXISTS agent_configs;
DROP TABLE IF EXISTS story_assets;
DROP TABLE IF EXISTS global_assets;
DROP TABLE IF EXISTS system_settings;
DROP TABLE IF EXISTS user_settings;

-- 删除备份表
DROP TABLE IF EXISTS _backup_novels;
DROP TABLE IF EXISTS _backup_chapters;
-- ... 等等
```

## 回滚方案

如果迁移出现问题，可以从备份表恢复：

```sql
-- 恢复 novels 表
TRUNCATE novels;
INSERT INTO novels SELECT * FROM _backup_novels;

-- 恢复其他表类似...
```

## 注意事项

1. **执行前务必备份**：虽然迁移脚本会自动备份，但建议额外手动备份
2. **在低峰期执行**：迁移过程可能会锁定表
3. **测试环境先行**：先在测试环境验证无误后再在生产环境执行
4. **保留备份表**：建议保留备份表至少一周，确认无误后再清理

## 后端代码更新示例

### Agent Memory 更新

```python
# 旧代码
response = self.supabase.table("agent_configs").select("*").execute()

# 新代码
response = self.supabase.table("agents").select("*").is_("deleted_at", "null").execute()
```

### Asset Manager 更新

```python
# 旧代码 - story_assets
response = self.supabase.table("story_assets").select("*").eq("novel_id", novel_id).execute()

# 新代码 - assets
response = self.supabase.table("assets").select("*").eq("novel_id", novel_id).is_("deleted_at", "null").execute()

# 旧代码 - global_assets
response = self.supabase.table("global_assets").select("*").eq("is_starred", True).execute()

# 新代码 - assets
response = self.supabase.table("assets").select("*").eq("is_global", True).eq("is_starred", True).is_("deleted_at", "null").execute()
```

### Settings 更新

```python
# 旧代码 - system_settings
response = self.supabase.table("system_settings").select("*").execute()

# 新代码 - settings
response = self.supabase.table("settings").select("*").is_("deleted_at", "null").execute()
```

## 性能优化

迁移后数据库性能提升：

1. **减少表数量**：从 17 个表减少到 13 个表
2. **统一索引策略**：所有表都有适当的索引
3. **软删除统一**：所有表都支持软删除，便于数据恢复
4. **查询优化**：合并后的表减少了 JOIN 操作

## 联系支持

如有问题，请检查：
1. Supabase 日志
2. 后端应用日志
3. 备份表数据完整性
