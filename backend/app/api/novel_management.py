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
    order: int = 0
    status: str = "draft"


class ChapterUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    order: Optional[int] = None
    status: Optional[str] = None


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
    order: int
    status: str
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
    novels = novel_memory.get_all_novels()
    print(f"[API] Retrieved {len(novels)} novels from memory")
    result = []
    
    for novel in novels:
        chapters = novel_memory.get_chapters_by_novel(novel.id)
        result.append(NovelWithChaptersResponse(
            id=novel.id,
            title=novel.title,
            outline="",
            locked=novel.locked,
            category_id=novel.category_id,
            created_at=novel.created_at,
            updated_at=novel.updated_at,
            chapters=[
                ChapterResponse(
                    id=c.id,
                    novel_id=c.novel_id,
                    title=c.title,
                    content=c.content,
                    order=c.order,
                    status=c.status,
                    created_at=c.created_at,
                    updated_at=c.updated_at
                )
                for c in chapters
            ]
        ))
    
    return result


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
            order=c.order,
            status=c.status,
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
            order=request.order,
            status=request.status
        )
        return ChapterResponse(
            id=chapter.id,
            novel_id=chapter.novel_id,
            title=chapter.title,
            content=chapter.content,
            order=chapter.order,
            status=chapter.status,
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
        order=chapter.order,
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
        if request.order is not None:
            updates["order"] = request.order
        if request.status is not None:
            updates["status"] = request.status
        
        chapter = novel_memory.update_chapter(chapter_id, **updates)
        return ChapterResponse(
            id=chapter.id,
            novel_id=chapter.novel_id,
            title=chapter.title,
            content=chapter.content,
            order=chapter.order,
            status=chapter.status,
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
