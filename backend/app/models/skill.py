"""
Skill 数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class SkillConstraint(BaseModel):
    """技能约束条目"""
    id: str
    content: str
    priority: Literal["high", "medium", "low"] = "medium"
    enabled: bool = True


class SkillCategory(BaseModel):
    """技能分类"""
    id: str
    name: str
    type: Literal["system", "writing", "domain", "auditing"]
    parent_id: Optional[str] = None
    color: str = "#6366f1"
    icon: Optional[str] = None
    is_system: bool = False
    description: Optional[str] = None
    default_agents: List[str] = Field(default_factory=list)
    order: int = 0


class Skill(BaseModel):
    """技能定义"""
    id: str
    name: str
    description: str = ""
    category_id: str
    constraints: List[SkillConstraint] = Field(default_factory=list)
    target_agents: List[str] = Field(default_factory=lambda: ["writer"])
    version: str = "1.0.0"
    is_active: bool = True
    is_system: bool = False
    linked_assets: List[str] = Field(default_factory=list)
    applicable_novels: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    author: Optional[str] = None
    test_example: Optional[str] = None


class SkillTestResult(BaseModel):
    """技能测试结果"""
    passed: bool
    violations: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class SkillCreateRequest(BaseModel):
    """创建技能请求"""
    name: str
    description: str = ""
    category_id: str
    constraints: List[SkillConstraint] = Field(default_factory=list)
    target_agents: List[str] = Field(default_factory=lambda: ["writer"])
    is_active: bool = True
    linked_assets: List[str] = Field(default_factory=list)


class SkillUpdateRequest(BaseModel):
    """更新技能请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    constraints: Optional[List[SkillConstraint]] = None
    target_agents: Optional[List[str]] = None
    is_active: Optional[bool] = None
    linked_assets: Optional[List[str]] = None
    version: Optional[str] = None


class CategoryCreateRequest(BaseModel):
    """创建分类请求"""
    name: str
    type: Literal["system", "writing", "domain", "auditing"]
    parent_id: Optional[str] = None
    color: str = "#6366f1"
    is_system: bool = False
    description: Optional[str] = None
    default_agents: List[str] = Field(default_factory=list)
    order: int = 0


class CategoryUpdateRequest(BaseModel):
    """更新分类请求"""
    name: Optional[str] = None
    type: Optional[Literal["system", "writing", "domain", "auditing"]] = None
    parent_id: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None
    default_agents: Optional[List[str]] = None
    order: Optional[int] = None


class SkillTestRequest(BaseModel):
    """技能测试请求"""
    text: str
