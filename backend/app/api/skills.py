"""
Skill API 路由
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime

from app.models.skill import (
    Skill, SkillCategory, SkillConstraint, SkillTestResult,
    SkillCreateRequest, SkillUpdateRequest,
    CategoryCreateRequest, CategoryUpdateRequest,
    SkillTestRequest
)
from app.memory.skill_memory import skill_memory

router = APIRouter(prefix="/api/skills", tags=["skills"])


# ========== 分类 API ==========

@router.get("/categories", response_model=List[SkillCategory])
async def get_categories():
    """获取所有技能分类"""
    return skill_memory.get_all_categories()


@router.post("/categories", response_model=SkillCategory)
async def create_category(request: CategoryCreateRequest):
    """创建新分类"""
    import uuid
    category = SkillCategory(
        id=f"cat-{uuid.uuid4().hex[:8]}",
        name=request.name,
        type=request.type,
        parent_id=request.parent_id,
        color=request.color,
        is_system=request.is_system,
        description=request.description,
        default_agents=request.default_agents,
        order=request.order
    )
    return skill_memory.create_category(category)


@router.get("/categories/{category_id}", response_model=SkillCategory)
async def get_category(category_id: str):
    """获取单个分类"""
    category = skill_memory.get_category_by_id(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    return category


@router.put("/categories/{category_id}", response_model=SkillCategory)
async def update_category(category_id: str, request: CategoryUpdateRequest):
    """更新分类"""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    category = skill_memory.update_category(category_id, updates)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    return category


@router.delete("/categories/{category_id}")
async def delete_category(category_id: str):
    """删除分类"""
    # 检查是否是系统分类
    category = skill_memory.get_category_by_id(category_id)
    if category and category.is_system:
        raise HTTPException(status_code=403, detail="不能删除系统分类")
    
    success = skill_memory.delete_category(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="分类不存在")
    return {"message": "分类已删除"}


@router.post("/categories/{category_id}/move")
async def move_category(category_id: str, parent_id: Optional[str] = None, order: int = 0):
    """移动分类"""
    success = skill_memory.move_category(category_id, parent_id, order)
    if not success:
        raise HTTPException(status_code=404, detail="分类不存在")
    return {"message": "分类已移动"}


# ========== 技能 API ==========

@router.get("", response_model=List[Skill])
async def get_skills(category_id: Optional[str] = None):
    """获取所有技能"""
    if category_id:
        return skill_memory.get_skills_by_category(category_id)
    return skill_memory.get_all_skills()


@router.post("", response_model=Skill)
async def create_skill(request: SkillCreateRequest):
    """创建新技能"""
    import uuid
    skill = Skill(
        id=f"skill-{uuid.uuid4().hex[:8]}",
        name=request.name,
        description=request.description,
        category_id=request.category_id,
        constraints=request.constraints,
        target_agents=request.target_agents,
        is_active=request.is_active,
        is_system=False,
        linked_assets=request.linked_assets,
        applicable_novels=[],
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
    return skill_memory.create_skill(skill)


@router.get("/{skill_id}", response_model=Skill)
async def get_skill(skill_id: str):
    """获取单个技能"""
    skill = skill_memory.get_skill_by_id(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="技能不存在")
    return skill


@router.put("/{skill_id}", response_model=Skill)
async def update_skill(skill_id: str, request: SkillUpdateRequest):
    """更新技能"""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    skill = skill_memory.update_skill(skill_id, updates)
    if not skill:
        raise HTTPException(status_code=404, detail="技能不存在")
    return skill


@router.delete("/{skill_id}")
async def delete_skill(skill_id: str):
    """删除技能"""
    # 检查是否是系统技能
    skill = skill_memory.get_skill_by_id(skill_id)
    if skill and skill.is_system:
        raise HTTPException(status_code=403, detail="不能删除系统技能")
    
    success = skill_memory.delete_skill(skill_id)
    if not success:
        raise HTTPException(status_code=404, detail="技能不存在")
    return {"message": "技能已删除"}


@router.post("/{skill_id}/link-asset")
async def link_asset(skill_id: str, asset_id: str):
    """关联资产到技能"""
    success = skill_memory.link_asset_to_skill(skill_id, asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="技能不存在")
    return {"message": "资产已关联"}


@router.post("/{skill_id}/unlink-asset")
async def unlink_asset(skill_id: str, asset_id: str):
    """取消资产关联"""
    success = skill_memory.unlink_asset_from_skill(skill_id, asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="技能不存在")
    return {"message": "资产关联已取消"}


@router.post("/{skill_id}/mount")
async def mount_to_novel(skill_id: str, novel_id: str):
    """挂载技能到小说"""
    success = skill_memory.mount_skill_to_novel(skill_id, novel_id)
    if not success:
        raise HTTPException(status_code=404, detail="技能不存在")
    return {"message": "技能已挂载"}


@router.post("/{skill_id}/unmount")
async def unmount_from_novel(skill_id: str, novel_id: str):
    """从小说卸载技能"""
    success = skill_memory.unmount_skill_from_novel(skill_id, novel_id)
    if not success:
        raise HTTPException(status_code=404, detail="技能不存在")
    return {"message": "技能已卸载"}


@router.post("/{skill_id}/test", response_model=SkillTestResult)
async def test_skill(skill_id: str, request: SkillTestRequest):
    """测试技能约束"""
    result = skill_memory.test_skill(skill_id, request.text)
    return result


@router.get("/novel/{novel_id}", response_model=List[Skill])
async def get_novel_skills(novel_id: str):
    """获取小说的所有技能"""
    return skill_memory.get_active_skills_for_novel(novel_id)


@router.get("/system/default", response_model=List[Skill])
async def get_system_skills():
    """获取系统默认技能"""
    return skill_memory.get_system_skills()
