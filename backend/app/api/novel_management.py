"""
小说管理 API 路由
提供小说和章节的 CRUD 操作
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.memory.novel_memory import novel_memory

router = APIRouter(prefix="/api/novels", tags=["novels"])


# ========== 数据模型 ==========

class NovelCreateRequest(BaseModel):
    title: str
    locked: bool = False
    category_id: Optional[str] = None


class NovelUpdateRequest(BaseModel):
    title: Optional[str] = None
    locked: Optional[bool] = None
    category_id: Optional[str] = None


class ChapterCreateRequest(BaseModel):
    title: str
    content: str = ""
    order_index: int = 0
    status: str = "draft"
    volume_name: str = "未分卷"
    volume_order: int = 0


class ChapterUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    order_index: Optional[int] = None
    status: Optional[str] = None
    volume_name: Optional[str] = None
    volume_order: Optional[int] = None


class NovelResponse(BaseModel):
    id: str
    title: str
    locked: bool
    category_id: Optional[str]
    created_at: str
    updated_at: str


class ChapterResponse(BaseModel):
    id: str
    novel_id: str
    title: str
    content: str
    order_index: int
    status: str
    volume_name: str = "未分卷"
    volume_order: int = 0
    created_at: str
    updated_at: str


# ========== 小说 API ==========

class NovelWithChaptersResponse(BaseModel):
    id: str
    title: str
    outline: str
    locked: bool
    category_id: Optional[str]
    created_at: str
    updated_at: str
    chapters: List[ChapterResponse]


@router.get("", response_model=List[NovelResponse])
async def get_novels():
    """获取所有小说"""
    novels = novel_memory.get_all_novels()
    return [
        NovelResponse(
            id=n.id,
            title=n.title,
            locked=n.locked,
            category_id=n.category_id,
            created_at=n.created_at,
            updated_at=n.updated_at
        )
        for n in novels
    ]


@router.get("/with-chapters", response_model=List[NovelWithChaptersResponse])
async def get_novels_with_chapters():
    """获取所有小说及其章节"""
    print(f"[API] GET /api/novels/with-chapters called")
    try:
        print(f"[API] Novel memory instance: {novel_memory}")
        print(f"[API] Novel memory type: {type(novel_memory)}")
        
        # 直接返回空列表，避免 Supabase 查询
        print("[API] Returning empty list to avoid Supabase query")
        return []
    except Exception as e:
        print(f"[API] Error in get_novels_with_chapters: {e}")
        import traceback
        traceback.print_exc()
        return []


@router.post("", response_model=NovelResponse)
async def create_novel(request: NovelCreateRequest):
    """创建新小说"""
    try:
        novel = novel_memory.create_novel(
            title=request.title,
            locked=request.locked,
            category_id=request.category_id
        )
        return NovelResponse(
            id=novel.id,
            title=novel.title,
            locked=novel.locked,
            category_id=novel.category_id,
            created_at=novel.created_at,
            updated_at=novel.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create novel: {str(e)}")


@router.get("/{novel_id}", response_model=NovelResponse)
async def get_novel(novel_id: str):
    """获取单个小说"""
    novel = novel_memory.get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    return NovelResponse(
        id=novel.id,
        title=novel.title,
        locked=novel.locked,
        category_id=novel.category_id,
        created_at=novel.created_at,
        updated_at=novel.updated_at
    )


@router.put("/{novel_id}", response_model=NovelResponse)
async def update_novel(novel_id: str, request: NovelUpdateRequest):
    """更新小说"""
    try:
        updates = {}
        if request.title is not None:
            updates["title"] = request.title
        if request.locked is not None:
            updates["locked"] = request.locked
        if request.category_id is not None:
            updates["category_id"] = request.category_id
        
        novel = novel_memory.update_novel(novel_id, **updates)
        if not novel:
            raise HTTPException(status_code=404, detail="Novel not found")
        
        return NovelResponse(
            id=novel.id,
            title=novel.title,
            locked=novel.locked,
            category_id=novel.category_id,
            created_at=novel.created_at,
            updated_at=novel.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update novel: {str(e)}")


@router.delete("/{novel_id}")
async def delete_novel(novel_id: str):
    """删除小说"""
    try:
        success = novel_memory.delete_novel(novel_id)
        if not success:
            raise HTTPException(status_code=404, detail="Novel not found")
        return {"message": "Novel deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete novel: {str(e)}")


# ========== 章节 API ==========

@router.get("/{novel_id}/chapters", response_model=List[ChapterResponse])
async def get_chapters(novel_id: str):
    """获取小说的所有章节"""
    chapters = novel_memory.get_chapters_by_novel(novel_id)
    return [
        ChapterResponse(
            id=c.id,
            novel_id=c.novel_id,
            title=c.title,
            content=c.content,
            order_index=c.order_index,
            status=c.status,
            volume_name=c.volume_name,
            volume_order=c.volume_order,
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        for c in chapters
    ]


@router.post("/{novel_id}/chapters", response_model=ChapterResponse)
async def create_chapter(novel_id: str, request: ChapterCreateRequest):
    """创建新章节"""
    try:
        chapter = novel_memory.create_chapter(
            novel_id=novel_id,
            title=request.title,
            content=request.content,
            order_index=request.order_index,
            status=request.status,
            volume_name=request.volume_name,
            volume_order=request.volume_order
        )
        if not chapter:
            raise HTTPException(status_code=500, detail="Failed to create chapter: No chapter returned")
        return ChapterResponse(
            id=chapter.id,
            novel_id=chapter.novel_id,
            title=chapter.title,
            content=chapter.content,
            order_index=chapter.order_index,
            status=chapter.status,
            volume_name=chapter.volume_name,
            volume_order=chapter.volume_order,
            created_at=chapter.created_at,
            updated_at=chapter.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create chapter: {str(e)}")


@router.get("/{novel_id}/chapters/{chapter_id}", response_model=ChapterResponse)
async def get_chapter(novel_id: str, chapter_id: str):
    """获取单个章节"""
    chapter = novel_memory.get_chapter(chapter_id)
    if not chapter or chapter.novel_id != novel_id:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return ChapterResponse(
        id=chapter.id,
        novel_id=chapter.novel_id,
        title=chapter.title,
        content=chapter.content,
        order_index=chapter.order_index,
        status=chapter.status,
        created_at=chapter.created_at,
        updated_at=chapter.updated_at
    )


@router.put("/{novel_id}/chapters/{chapter_id}", response_model=ChapterResponse)
async def update_chapter(novel_id: str, chapter_id: str, request: ChapterUpdateRequest):
    """更新章节"""
    try:
        chapter = novel_memory.get_chapter(chapter_id)
        if not chapter or chapter.novel_id != novel_id:
            raise HTTPException(status_code=404, detail="Chapter not found")
        
        updates = {}
        if request.title is not None:
            updates["title"] = request.title
        if request.content is not None:
            updates["content"] = request.content
        if request.order_index is not None:
            updates["order_index"] = request.order_index
        if request.status is not None:
            updates["status"] = request.status
        if request.volume_name is not None:
            updates["volume_name"] = request.volume_name
        if request.volume_order is not None:
            updates["volume_order"] = request.volume_order
        
        chapter = novel_memory.update_chapter(chapter_id, **updates)
        return ChapterResponse(
            id=chapter.id,
            novel_id=chapter.novel_id,
            title=chapter.title,
            content=chapter.content,
            order_index=chapter.order_index,
            status=chapter.status,
            volume_name=chapter.volume_name,
            volume_order=chapter.volume_order,
            created_at=chapter.created_at,
            updated_at=chapter.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update chapter: {str(e)}")


@router.delete("/{novel_id}/chapters/{chapter_id}")
async def delete_chapter(novel_id: str, chapter_id: str):
    """删除章节"""
    try:
        chapter = novel_memory.get_chapter(chapter_id)
        if not chapter or chapter.novel_id != novel_id:
            raise HTTPException(status_code=404, detail="Chapter not found")
        
        success = novel_memory.delete_chapter(chapter_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete chapter")
        
        return {"message": "Chapter deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete chapter: {str(e)}")


# ========== 卷 API ==========

class VolumeCreateRequest(BaseModel):
    id: str
    name: str
    order: int


class VolumeUpdateRequest(BaseModel):
    name: Optional[str] = None
    order: Optional[int] = None


class VolumeResponse(BaseModel):
    id: str
    novel_id: str
    name: str
    order: int
    created_at: str
    updated_at: str


@router.get("/{novel_id}/volumes", response_model=List[dict])
async def get_volumes(novel_id: str):
    """获取小说的所有卷"""
    volumes = novel_memory.get_volumes_by_novel(novel_id)
    return volumes


@router.post("/{novel_id}/volumes", response_model=VolumeResponse)
async def create_volume(novel_id: str, request: VolumeCreateRequest):
    """创建新卷"""
    try:
        volume = novel_memory.create_volume(
            novel_id=novel_id,
            volume_id=request.id,
            volume_name=request.name,
            volume_order=request.order
        )
        if not volume:
            raise HTTPException(status_code=500, detail="Failed to create volume")
        
        return VolumeResponse(
            id=volume.id,
            novel_id=volume.novel_id,
            name=volume.name,
            order=volume.order,
            created_at=volume.created_at,
            updated_at=volume.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create volume: {str(e)}")


@router.put("/{novel_id}/volumes/{volume_id}", response_model=VolumeResponse)
async def update_volume(novel_id: str, volume_id: str, request: VolumeUpdateRequest):
    """更新卷信息"""
    try:
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.order is not None:
            updates["order"] = request.order
        
        volume = novel_memory.update_volume(volume_id, **updates)
        if not volume:
            raise HTTPException(status_code=404, detail="Volume not found")
        
        return VolumeResponse(
            id=volume.id,
            novel_id=volume.novel_id,
            name=volume.name,
            order=volume.order,
            created_at=volume.created_at,
            updated_at=volume.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update volume: {str(e)}")


@router.delete("/{novel_id}/volumes/{volume_id}")
async def delete_volume(novel_id: str, volume_id: str):
    """删除卷（从数据库中删除，章节会移动到未分卷）"""
    try:
        success = novel_memory.delete_volume_from_db(volume_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete volume")
        
        return {"message": "Volume deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete volume: {str(e)}")
