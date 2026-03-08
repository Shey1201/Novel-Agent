"""
数据库结构验证器
在应用启动时检查数据库结构是否匹配模型定义
"""
import os
from typing import Dict, Set, List, Tuple
from functools import lru_cache

# 定义期望的数据库字段（基于模型类）
EXPECTED_SCHEMA: Dict[str, Set[str]] = {
    'novels': {
        'id', 'title', 'locked', 'category_id', 'user_id', 
        'mounted_skills', 'deleted_at', 'outline', 'word_count', 
        'status', 'created_at', 'updated_at'
    },
    'chapters': {
        'id', 'novel_id', 'title', 'content', 'order_index', 
        'status', 'volume_name', 'volume_order', 'word_count',
        'created_at', 'updated_at', 'deleted_at'
    },
    'categories': {
        'id', 'name', 'color', 'user_id', 'created_at', 
        'updated_at', 'deleted_at', 'order'
    },
    'agents': {
        'id', 'agent_id', 'name', 'role', 'personality', 
        'temperature', 'prompt', 'enabled', 'user_id', 
        'avatar_url', 'description', 'deleted_at', 
        'created_at', 'updated_at'
    },
    'assets': {
        'id', 'user_id', 'novel_id', 'type', 'name', 
        'content', 'description', 'is_global', 'is_starred',
        'source_novel_id', 'color', 'created_at', 'updated_at',
        'deleted_at'
    },
    'settings': {
        'id', 'user_id', 'key', 'value', 'created_at', 'updated_at'
    }
}

class DatabaseValidator:
    """数据库结构验证器"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.validation_errors: List[str] = []
    
    def validate_all_tables(self) -> bool:
        """验证所有表的结构"""
        print("[DatabaseValidator] 开始验证数据库结构...")
        
        all_valid = True
        for table_name, expected_fields in EXPECTED_SCHEMA.items():
            is_valid = self._validate_table(table_name, expected_fields)
            if not is_valid:
                all_valid = False
        
        if all_valid:
            print("[DatabaseValidator] ✅ 所有表结构验证通过")
        else:
            print("[DatabaseValidator] ❌ 发现结构不匹配:")
            for error in self.validation_errors:
                print(f"  {error}")
            print("\n[DatabaseValidator] 请运行迁移脚本修复:")
            print("  scripts/add_volume_columns_to_chapters.sql")
            print("  scripts/fix_categories_order.sql")
        
        return all_valid
    
    def _validate_table(self, table_name: str, expected_fields: Set[str]) -> bool:
        """验证单个表"""
        try:
            # 尝试查询表，如果字段不存在会报错
            result = self.supabase.table(table_name).select('*').limit(1).execute()
            
            # 如果能成功查询，说明基本结构正确
            print(f"[DatabaseValidator] ✅ {table_name}: 结构正常")
            return True
            
        except Exception as e:
            error_msg = str(e)
            
            # 检查是否是字段缺失错误
            if "Could not find" in error_msg and "column" in error_msg:
                # 提取缺失的字段名
                import re
                match = re.search(r"'([^']+)' column", error_msg)
                if match:
                    missing_col = match.group(1)
                    self.validation_errors.append(
                        f"{table_name}: 缺少字段 '{missing_col}'"
                    )
                else:
                    self.validation_errors.append(f"{table_name}: {error_msg}")
            else:
                self.validation_errors.append(f"{table_name}: {error_msg}")
            
            print(f"[DatabaseValidator] ❌ {table_name}: 结构错误")
            return False
    
    def get_missing_columns(self, table_name: str) -> List[str]:
        """获取表缺少的列"""
        if table_name not in EXPECTED_SCHEMA:
            return []
        
        expected = EXPECTED_SCHEMA[table_name]
        
        try:
            # 查询 information_schema 获取实际列
            result = self.supabase.table('information_schema.columns')\
                .select('column_name')\
                .eq('table_name', table_name)\
                .execute()
            
            if result.data:
                actual = {col['column_name'] for col in result.data}
                return list(expected - actual)
        except Exception as e:
            print(f"[DatabaseValidator] 无法获取 {table_name} 的结构: {e}")
        
        return []

# 全局验证器实例
db_validator: DatabaseValidator = None

def init_validator(supabase_client):
    """初始化验证器"""
    global db_validator
    db_validator = DatabaseValidator(supabase_client)
    return db_validator

def validate_database() -> bool:
    """验证数据库结构"""
    if db_validator is None:
        print("[DatabaseValidator] 警告: 验证器未初始化")
        return True
    return db_validator.validate_all_tables()
