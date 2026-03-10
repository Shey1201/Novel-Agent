"""
Asset API Routes: 资产管理API (适配优化后的数据库结构)
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# 使用新的 asset_manager（合并后的统一资产表）
from app.memory.asset_manager import (
    asset_manager, Asset, AssetVersion
)
from app.memory.skill_memory import skill_memory
from app.models.skill import Skill

router = APIRouter(prefix="/api/assets", tags=["assets"])


# ==================== 请求/响应模型 ====================

class CreateAssetRequest(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    source_novel_id: str
    source_novel_name: str
    color: Optional[str] = None


class UpdateAssetRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    is_starred: Optional[bool] = None


class MountAssetRequest(BaseModel):
    asset_id: str
    novel_id: str
    reference_type: str = "linked"  # "linked" | "cloned"
    version_id: Optional[str] = None


class CreateVersionRequest(BaseModel):
    version_id: str
    name: str
    description: Optional[str] = None
    data: dict = {}


class AssetResponse(BaseModel):
    id: str
    name: str
    type: str
    description: Optional[str]
    source_novel_id: str
    source_novel_name: str
    color: Optional[str]
    is_starred: bool
    mount_count: int
    created_at: str
    updated_at: str
    version_count: int


# ==================== API端点 ====================

@router.get("/all", response_model=List[AssetResponse])
async def get_all_assets():
    """获取所有全局资产"""
    assets = asset_manager.get_global_assets()
    return [
        AssetResponse(
            id=a.id,
            name=a.name,
            type=a.type,
            description=a.description,
            source_novel_id=a.source_novel_id,
            source_novel_name=a.source_novel_name,
            color=a.color,
            is_starred=a.is_starred,
            mount_count=asset_manager.get_asset_mount_count(a.id),
            created_at=a.created_at,
            updated_at=a.updated_at,
            version_count=len(a.versions)
        ) for a in assets
    ]


@router.get("/by-type/{asset_type}", response_model=List[AssetResponse])
async def get_assets_by_type(asset_type: str):
    """按类型获取资产"""
    assets = asset_manager.get_assets_by_type(asset_type)
    return [
        AssetResponse(
            id=a.id,
            name=a.name,
            type=a.type,
            description=a.description,
            source_novel_id=a.source_novel_id,
            source_novel_name=a.source_novel_name,
            color=a.color,
            is_starred=a.is_starred,
            mount_count=asset_manager.get_asset_mount_count(a.id),
            created_at=a.created_at,
            updated_at=a.updated_at,
            version_count=len(a.versions)
        ) for a in assets
    ]


@router.get("/by-novel/{novel_id}", response_model=List[AssetResponse])
async def get_assets_by_novel(novel_id: str):
    """按原生小说获取资产"""
    assets = asset_manager.get_assets_by_novel(novel_id)
    return [
        AssetResponse(
            id=a.id,
            name=a.name,
            type=a.type,
            description=a.description,
            source_novel_id=a.source_novel_id,
            source_novel_name=a.source_novel_name,
            color=a.color,
            is_starred=a.is_starred,
            mount_count=asset_manager.get_asset_mount_count(a.id),
            created_at=a.created_at,
            updated_at=a.updated_at,
            version_count=len(a.versions)
        ) for a in assets
    ]


@router.get("/novel/{novel_id}/mounted", response_model=List[AssetResponse])
async def get_novel_mounted_assets(novel_id: str):
    """获取小说已挂载的资产"""
    assets = asset_manager.get_novel_assets(novel_id)
    return [
        AssetResponse(
            id=a.id,
            name=a.name,
            type=a.type,
            description=a.description,
            source_novel_id=a.source_novel_id,
            source_novel_name=a.source_novel_name,
            color=a.color,
            is_starred=a.is_starred,
            mount_count=asset_manager.get_asset_mount_count(a.id),
            created_at=a.created_at,
            updated_at=a.updated_at,
            version_count=len(a.versions)
        ) for a in assets
    ]


@router.post("/create", response_model=AssetResponse)
async def create_asset(request: CreateAssetRequest):
    """创建新资产"""
    import uuid
    asset = Asset(
        id=str(uuid.uuid4()),
        name=request.name,
        type=request.type,
        description=request.description or "",
        source_novel_id=request.source_novel_id,
        is_global=True,
        is_starred=False,
        color=request.color or "#6366f1",
        content={},
        novel_id=None,
        user_id=None
    )
    created = asset_manager.create_asset(asset)
    if not created:
        raise HTTPException(status_code=500, detail="Failed to create asset")
    return AssetResponse(
        id=created.id,
        name=created.name,
        type=created.type,
        description=created.description,
        source_novel_id=created.source_novel_id or "",
        source_novel_name=request.source_novel_name,
        color=created.color,
        is_starred=created.is_starred,
        mount_count=0,
        created_at=created.created_at,
        updated_at=created.updated_at,
        version_count=0
    )


@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(asset_id: str, request: UpdateAssetRequest):
    """更新资产"""
    updates = request.model_dump(exclude_unset=True)
    updated = asset_manager.update_asset(asset_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return AssetResponse(
        id=updated.id,
        name=updated.name,
        type=updated.type,
        description=updated.description,
        source_novel_id=updated.source_novel_id,
        source_novel_name=updated.source_novel_name,
        color=updated.color,
        is_starred=updated.is_starred,
        mount_count=asset_manager.get_asset_mount_count(updated.id),
        created_at=updated.created_at,
        updated_at=updated.updated_at,
        version_count=len(updated.versions)
    )


@router.delete("/{asset_id}")
async def delete_asset(asset_id: str):
    """删除资产"""
    success = asset_manager.delete_asset(asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"message": "Asset deleted successfully"}


@router.post("/mount")
async def mount_asset(request: MountAssetRequest):
    """挂载资产到小说"""
    success = asset_manager.mount_asset_to_novel(
        request.asset_id,
        request.novel_id,
        request.reference_type,
        request.version_id
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to mount asset")
    return {"message": "Asset mounted successfully"}


@router.post("/unmount")
async def unmount_asset(asset_id: str, novel_id: str):
    """从小说卸载资产"""
    success = asset_manager.unmount_asset_from_novel(asset_id, novel_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to unmount asset")
    return {"message": "Asset unmounted successfully"}


@router.get("/{asset_id}/mount-status")
async def get_mount_status(asset_id: str, novel_id: str):
    """获取资产在小说中的挂载状态"""
    is_mounted = asset_manager.is_asset_mounted_to_novel(asset_id, novel_id)
    mount_info = asset_manager.get_mount_info(asset_id, novel_id)
    return {
        "is_mounted": is_mounted,
        "mount_info": mount_info
    }


@router.get("/search")
async def search_assets(query: str):
    """搜索资产"""
    assets = asset_manager.search_assets(query)
    return [
        AssetResponse(
            id=a.id,
            name=a.name,
            type=a.type,
            description=a.description,
            source_novel_id=a.source_novel_id,
            source_novel_name=a.source_novel_name,
            color=a.color,
            is_starred=a.is_starred,
            mount_count=asset_manager.get_asset_mount_count(a.id),
            created_at=a.created_at,
            updated_at=a.updated_at,
            version_count=len(a.versions)
        ) for a in assets
    ]


@router.get("/starred", response_model=List[AssetResponse])
async def get_starred_assets():
    """获取收藏的资产"""
    assets = asset_manager.get_starred_assets()
    return [
        AssetResponse(
            id=a.id,
            name=a.name,
            type=a.type,
            description=a.description,
            source_novel_id=a.source_novel_id,
            source_novel_name=a.source_novel_name,
            color=a.color,
            is_starred=a.is_starred,
            mount_count=asset_manager.get_asset_mount_count(a.id),
            created_at=a.created_at,
            updated_at=a.updated_at,
            version_count=len(a.versions)
        ) for a in assets
    ]


@router.post("/{asset_id}/toggle-star")
async def toggle_star_asset(asset_id: str):
    """切换资产收藏状态"""
    result = asset_manager.toggle_star_asset(asset_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"is_starred": result}


# ==================== 版本管理 ====================

@router.post("/{asset_id}/versions")
async def create_asset_version(asset_id: str, request: CreateVersionRequest):
    """为资产创建新版本"""
    version = AssetVersion(
        id=request.version_id,
        name=request.name,
        description=request.description,
        data=request.data
    )
    created = asset_manager.create_asset_version(asset_id, version)
    if not created:
        raise HTTPException(status_code=404, detail="Asset not found")
    return created


@router.put("/{asset_id}/active-version")
async def set_active_version(asset_id: str, version_id: Optional[str] = None):
    """设置资产的激活版本"""
    success = asset_manager.set_active_version(asset_id, version_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to set active version")
    return {"message": "Active version updated"}


# ==================== Agent技能联动 ====================

class CreateSkillRequest(BaseModel):
    skill_id: str
    skill_name: str
    description: str
    asset_id: str
    asset_type: str
    asset_content: str
    target_agents: List[str]
    novel_id: Optional[str] = None


class SkillResponse(BaseModel):
    id: str
    name: str
    description: str
    asset_id: str
    asset_type: str
    target_agents: List[str]
    is_active: bool
    created_at: str
    updated_at: str


@router.post("/skills/create", response_model=SkillResponse)
async def create_skill_from_asset(request: CreateSkillRequest):
    """从资产创建Agent技能"""
    skill = skill_memory.create_skill_from_asset(
        skill_id=request.skill_id,
        skill_name=request.skill_name,
        description=request.description,
        asset_id=request.asset_id,
        asset_type=request.asset_type,
        asset_content=request.asset_content,
        target_agents=request.target_agents,
        novel_id=request.novel_id
    )
    return SkillResponse(
        id=skill.id,
        name=skill.name,
        description=skill.description,
        asset_id=request.asset_id,
        asset_type=request.asset_type,
        target_agents=skill.target_agents,
        is_active=skill.is_active,
        created_at=skill.created_at,
        updated_at=skill.updated_at
    )


@router.get("/skills/all", response_model=List[SkillResponse])
async def get_all_skills():
    """获取所有Agent技能"""
    skills = skill_memory.get_all_skills()
    return [
        SkillResponse(
            id=s.id,
            name=s.name,
            description=s.description,
            asset_id=s.linked_assets[0] if s.linked_assets else "",
            asset_type="",
            target_agents=s.target_agents,
            is_active=s.is_active,
            created_at=s.created_at,
            updated_at=s.updated_at
        ) for s in skills
    ]


@router.get("/{asset_id}/skills", response_model=List[SkillResponse])
async def get_skills_by_asset(asset_id: str):
    """获取资产关联的所有技能"""
    skills = skill_memory.get_skills_by_asset(asset_id)
    return [
        SkillResponse(
            id=s.id,
            name=s.name,
            description=s.description,
            asset_id=asset_id,
            asset_type="",
            target_agents=s.target_agents,
            is_active=s.is_active,
            created_at=s.created_at,
            updated_at=s.updated_at
        ) for s in skills
    ]


@router.get("/novel/{novel_id}/skills", response_model=List[SkillResponse])
async def get_skills_by_novel(novel_id: str):
    """获取小说的所有Agent技能"""
    skills = skill_memory.get_active_skills_for_novel(novel_id)
    return [
        SkillResponse(
            id=s.id,
            name=s.name,
            description=s.description,
            asset_id=s.linked_assets[0] if s.linked_assets else "",
            asset_type="",
            target_agents=s.target_agents,
            is_active=s.is_active,
            created_at=s.created_at,
            updated_at=s.updated_at
        ) for s in skills
    ]


@router.post("/skills/{skill_id}/toggle")
async def toggle_skill_active(skill_id: str):
    """切换技能激活状态"""
    result = skill_memory.toggle_skill_active(skill_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"is_active": result}


@router.delete("/skills/{skill_id}")
async def delete_skill(skill_id: str):
    """删除技能"""
    success = skill_memory.delete_skill(skill_id)
    if not success:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"message": "Skill deleted successfully"}


@router.post("/skills/{skill_id}/add-to-novel")
async def add_skill_to_novel(skill_id: str, novel_id: str):
    """将技能添加到小说"""
    success = skill_memory.mount_skill_to_novel(skill_id, novel_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add skill to novel")
    return {"message": "Skill added to novel successfully"}


@router.post("/skills/{skill_id}/remove-from-novel")
async def remove_skill_from_novel(skill_id: str, novel_id: str):
    """从小说移除技能"""
    success = skill_memory.unmount_skill_from_novel(skill_id, novel_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to remove skill from novel")
    return {"message": "Skill removed from novel successfully"}


# ==================== 资产分类管理 ====================

class CreateCategoryRequest(BaseModel):
    name: str
    color: str = "#6366f1"
    order: int = 0


class CategoryResponse(BaseModel):
    id: str
    name: str
    color: str
    order: int
    created_at: str
    updated_at: str


@router.get("/categories/all", response_model=List[CategoryResponse])
async def get_asset_categories():
    """获取所有资产分类"""
    categories = asset_manager.get_asset_categories()
    return [
        CategoryResponse(
            id=c["id"],
            name=c["name"],
            color=c["color"],
            order=c.get("order", 0),
            created_at=c["created_at"],
            updated_at=c["updated_at"]
        ) for c in categories
    ]


@router.post("/categories/create", response_model=CategoryResponse)
async def create_asset_category(request: CreateCategoryRequest):
    """创建资产分类"""
    category = asset_manager.create_asset_category(
        name=request.name,
        color=request.color,
        order=request.order
    )
    if not category:
        raise HTTPException(status_code=500, detail="Failed to create category")
    return CategoryResponse(
        id=category["id"],
        name=category["name"],
        color=category["color"],
        order=category.get("order", 0),
        created_at=category["created_at"],
        updated_at=category["updated_at"]
    )


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_asset_category(category_id: str, request: CreateCategoryRequest):
    """更新资产分类"""
    updates = request.model_dump()
    category = asset_manager.update_asset_category(category_id, updates)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return CategoryResponse(
        id=category["id"],
        name=category["name"],
        color=category["color"],
        order=category.get("order", 0),
        created_at=category["created_at"],
        updated_at=category["updated_at"]
    )


@router.delete("/categories/{category_id}")
async def delete_asset_category(category_id: str):
    """删除资产分类"""
    success = asset_manager.delete_asset_category(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}


@router.post("/{asset_id}/set-category")
async def set_asset_category(asset_id: str, category_id: Optional[str] = None):
    """设置资产分类"""
    success = asset_manager.set_asset_category(asset_id, category_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to set asset category")
    return {"message": "Asset category updated"}


@router.get("/by-category/{category_id}", response_model=List[AssetResponse])
async def get_assets_by_category(category_id: str):
    """获取指定分类下的所有资产"""
    assets = asset_manager.get_assets_by_category(category_id)
    return [
        AssetResponse(
            id=a.id,
            name=a.name,
            type=a.type,
            description=a.description,
            source_novel_id=a.source_novel_id,
            source_novel_name=a.source_novel_name,
            color=a.color,
            is_starred=a.is_starred,
            mount_count=asset_manager.get_asset_mount_count(a.id),
            created_at=a.created_at,
            updated_at=a.updated_at,
            version_count=len(a.versions)
        ) for a in assets
    ]
