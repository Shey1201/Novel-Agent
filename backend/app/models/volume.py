"""
Volume 数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Volume(BaseModel):
    """卷定义"""
    id: str
    novel_id: str
    name: str
    order: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class VolumeCreateRequest(BaseModel):
    """创建卷请求"""
    name: str
    order: int = 0


class VolumeUpdateRequest(BaseModel):
    """更新卷请求"""
    name: Optional[str] = None
    order: Optional[int] = None
