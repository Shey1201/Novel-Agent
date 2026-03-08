"""
统一的错误处理工具
提供更好的错误信息和调试支持
"""
import functools
import traceback
from typing import Callable, Any, Optional
from fastapi import HTTPException

class DatabaseError(Exception):
    """数据库操作错误"""
    def __init__(self, message: str, table: str = None, column: str = None):
        self.table = table
        self.column = column
        super().__init__(message)

class ModelValidationError(Exception):
    """模型验证错误"""
    def __init__(self, message: str, model: str = None, field: str = None):
        self.model = model
        self.field = field
        super().__init__(message)

def handle_db_error(func: Callable) -> Callable:
    """
    数据库操作错误处理装饰器
    自动识别常见错误并提供友好的错误信息
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            
            # 识别常见的数据库错误
            if "Could not find" in error_msg and "column" in error_msg:
                # 字段缺失错误
                import re
                match = re.search(r"'([^']+)' column of '([^']+)'", error_msg)
                if match:
                    column, table = match.groups()
                    raise DatabaseError(
                        f"数据库表 '{table}' 缺少字段 '{column}'，请运行迁移脚本添加",
                        table=table,
                        column=column
                    )
            
            elif "relation" in error_msg and "does not exist" in error_msg:
                # 表不存在错误
                import re
                match = re.search(r"relation \"([^\"]+)\"", error_msg)
                if match:
                    table = match.group(1)
                    raise DatabaseError(
                        f"数据库表 '{table}' 不存在，请检查迁移脚本",
                        table=table
                    )
            
            elif "violates foreign key constraint" in error_msg:
                # 外键约束错误
                raise DatabaseError("数据关联错误：引用的记录不存在")
            
            elif "violates unique constraint" in error_msg:
                # 唯一约束错误
                raise DatabaseError("数据重复：该记录已存在")
            
            # 重新抛出原始错误
            raise
    
    return wrapper

def handle_api_error(func: Callable) -> Callable:
    """
    API 错误处理装饰器
    将内部错误转换为 HTTPException
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except DatabaseError as e:
            print(f"[DatabaseError] {e}")
            if e.table and e.column:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "数据库结构错误",
                        "message": str(e),
                        "table": e.table,
                        "column": e.column,
                        "fix": f"请运行: ALTER TABLE {e.table} ADD COLUMN {e.column} ..."
                    }
                )
            else:
                raise HTTPException(status_code=500, detail=str(e))
        except ModelValidationError as e:
            print(f"[ModelValidationError] {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            print(f"[UnexpectedError] {type(e).__name__}: {e}")
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "服务器内部错误",
                    "message": str(e),
                    "type": type(e).__name__
                }
            )
    
    return wrapper

def safe_model_init(model_class: type, data: dict) -> Optional[Any]:
    """
    安全地初始化模型实例
    处理字段不匹配的情况
    """
    try:
        # 获取模型期望的字段
        if hasattr(model_class, '__dataclass_fields__'):
            expected_fields = set(model_class.__dataclass_fields__.keys())
        elif hasattr(model_class, '__fields__'):  # Pydantic
            expected_fields = set(model_class.__fields__.keys())
        else:
            expected_fields = None
        
        if expected_fields:
            # 过滤掉模型不需要的字段
            filtered_data = {k: v for k, v in data.items() if k in expected_fields}
            
            # 检查缺少的字段
            missing_fields = expected_fields - set(data.keys())
            if missing_fields:
                print(f"[safe_model_init] 警告: {model_class.__name__} 缺少字段: {missing_fields}")
                # 为缺少的字段设置默认值
                for field in missing_fields:
                    filtered_data[field] = None
            
            return model_class(**filtered_data)
        else:
            return model_class(**data)
            
    except Exception as e:
        print(f"[safe_model_init] 错误: 无法创建 {model_class.__name__}: {e}")
        print(f"  数据: {data}")
        return None
