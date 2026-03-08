"""
分类管理 API 路由
提供小说分类的 CRUD 操作
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.memory.category_memory import category_memory

router = APIRouter(prefix="/api/categories", tags=["categories"])


# ========== 数据模型 ==========

class CategoryCreateRequest(BaseModel):
    name: str
    color: str


class CategoryUpdateRequest(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None


class CategoryResponse(BaseModel):
    id: str
    name: str
    color: str
    user_id: Optional[str]
    created_at: str
    updated_at: str


# ========== 分类 API ==========

@router.get("", response_model=List[CategoryResponse])
async def get_categories():
    """获取所有分类"""
    try:
        categories = supabase_memory.get_all_categories()
        return [
            CategoryResponse(
                id=cat.id,
                name=cat.name,
                color=cat.color,
                user_id=cat.user_id,
                created_at=cat.created_at,
                updated_at=cat.updated_at
            )
            for cat in categories
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")


@router.post("", response_model=CategoryResponse)
async def create_category(request: CategoryCreateRequest):
    """创建新分类"""
    try:
        category = supabase_memory.create_category(
            name=request.name,
            color=request.color
        )
        if not category:
            raise HTTPException(status_code=500, detail="Failed to create category")
        return CategoryResponse(
            id=category.id,
            name=category.name,
            color=category.color,
            user_id=category.user_id,
            created_at=category.created_at,
            updated_at=category.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create category: {str(e)}")


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: str, request: CategoryUpdateRequest):
    """更新分类"""
    try:
        updates = {k: v for k, v in request.model_dump().items() if v is not None}
        category = supabase_memory.update_category(category_id, **updates)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        return CategoryResponse(
            id=category.id,
            name=category.name,
            color=category.color,
            user_id=category.user_id,
            created_at=category.created_at,
            updated_at=category.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update category: {str(e)}")


@router.delete("/{category_id}")
async def delete_category(category_id: str):
    """删除分类"""
    try:
        success = supabase_memory.delete_category(category_id)
        if not success:
            raise HTTPException(status_code=404, detail="Category not found")
        return {"message": "Category deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete category: {str(e)}")
