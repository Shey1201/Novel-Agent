"""
Volume API 路由
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime

from app.models.volume import Volume, VolumeCreateRequest, VolumeUpdateRequest
from app.memory.volume_memory import volume_memory

router = APIRouter(prefix="/api/volumes", tags=["volumes"])


@router.get("/novel/{novel_id}", response_model=List[Volume])
async def get_volumes_by_novel(novel_id: str):
    """获取小说的所有卷"""
    return volume_memory.get_volumes_by_novel(novel_id)


@router.post("/novel/{novel_id}", response_model=Volume)
async def create_volume(novel_id: str, request: VolumeCreateRequest):
    """创建新卷"""
    import uuid
    volume = Volume(
        id=f"vol-{uuid.uuid4().hex[:8]}",
        novel_id=novel_id,
        name=request.name,
        order=request.order
    )
    result = volume_memory.create_volume(volume)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create volume")
    return result


@router.get("/{volume_id}", response_model=Volume)
async def get_volume(volume_id: str):
    """获取单个卷"""
    volume = volume_memory.get_volume_by_id(volume_id)
    if not volume:
        raise HTTPException(status_code=404, detail="卷不存在")
    return volume


@router.put("/{volume_id}", response_model=Volume)
async def update_volume(volume_id: str, request: VolumeUpdateRequest):
    """更新卷"""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    volume = volume_memory.update_volume(volume_id, updates)
    if not volume:
        raise HTTPException(status_code=404, detail="卷不存在")
    return volume


@router.delete("/{volume_id}")
async def delete_volume(volume_id: str):
    """删除卷"""
    success = volume_memory.delete_volume(volume_id)
    if not success:
        raise HTTPException(status_code=404, detail="卷不存在或删除失败")
    return {"message": "卷已删除"}


@router.post("/{volume_id}/chapters/{chapter_id}")
async def move_chapter_to_volume(volume_id: str, chapter_id: str):
    """将章节移动到指定卷"""
    success = volume_memory.move_chapter_to_volume(chapter_id, volume_id)
    if not success:
        raise HTTPException(status_code=500, detail="移动章节失败")
    return {"message": "章节已移动"}


@router.post("/chapters/{chapter_id}/remove")
async def remove_chapter_from_volume(chapter_id: str):
    """将章节从卷中移除（移动到未分卷）"""
    success = volume_memory.move_chapter_to_volume(chapter_id, None)
    if not success:
        raise HTTPException(status_code=500, detail="移除章节失败")
    return {"message": "章节已移除"}
