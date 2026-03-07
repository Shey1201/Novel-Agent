"""
Foreshadowing System - 伏笔系统
提供伏笔提取、跟踪和提醒功能
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import re

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


class ClueStatus(Enum):
    """伏笔状态"""
    UNRESOLVED = "unresolved"      # 未解决
    RESOLVED = "resolved"          # 已解决
    ABANDONED = "abandoned"        # 已放弃
    FORGOTTEN = "forgotten"        # 被遗忘（长期未解决）


class CluePriority(Enum):
    """伏笔优先级"""
    CRITICAL = 10      # 关键主线伏笔
    HIGH = 7           # 重要伏笔
    MEDIUM = 5         # 普通伏笔
    LOW = 3            # 细节伏笔
    HINT = 1           # 暗示/彩蛋


@dataclass
class ForeshadowingClue:
    """伏笔线索"""
    id: str
    clue: str                          # 伏笔描述
    chapter_created: int               # 创建章节
    chapter_resolved: Optional[int] = None  # 解决章节
    status: ClueStatus = ClueStatus.UNRESOLVED
    priority: CluePriority = CluePriority.MEDIUM
    expected_resolution: Optional[str] = None  # 预期解决方式
    related_characters: List[str] = field(default_factory=list)
    related_plotlines: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    notes: str = ""                    # 备注
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "clue": self.clue,
            "chapter_created": self.chapter_created,
            "chapter_resolved": self.chapter_resolved,
            "status": self.status.value,
            "priority": self.priority.value,
            "expected_resolution": self.expected_resolution,
            "related_characters": self.related_characters,
            "related_plotlines": self.related_plotlines,
            "tags": self.tags,
            "notes": self.notes,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ForeshadowingClue':
        """从字典创建"""
        return cls(
            id=data["id"],
            clue=data["clue"],
            chapter_created=data["chapter_created"],
            chapter_resolved=data.get("chapter_resolved"),
            status=ClueStatus(data.get("status", "unresolved")),
            priority=CluePriority(data.get("priority", 5)),
            expected_resolution=data.get("expected_resolution"),
            related_characters=data.get("related_characters", []),
            related_plotlines=data.get("related_plotlines", []),
            tags=data.get("tags", []),
            notes=data.get("notes", ""),
            created_at=data.get("created_at", datetime.now().isoformat())
        )


@dataclass
class ClueExtractionResult:
    """伏笔提取结果"""
    clues: List[ForeshadowingClue]
    chapter_number: int
    extraction_time: str = field(default_factory=lambda: datetime.now().isoformat())


class ClueExtractor:
    """
    伏笔提取器
    
    从章节内容中提取伏笔线索
    """
    
    # 伏笔关键词模式
    CLUE_PATTERNS = [
        r"(.{2,10})(?:似乎|好像|仿佛).{0,5}(?:隐藏着|暗示着|预示着)",
        r"(?:注意|留意|记住)(.{2,10})",
        r"(.{2,10})(?:后来|之后|将来).{0,5}(?:会|将)",
        r"(?:伏笔|暗示|线索)(.{2,10})",
        r"(.{2,10})(?:秘密|真相|谜团)",
    ]
    
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.3)
    
    async def extract_from_chapter(
        self,
        chapter_content: str,
        chapter_summary: str,
        chapter_number: int,
        existing_clues: Optional[List[ForeshadowingClue]] = None
    ) -> ClueExtractionResult:
        """
        从章节中提取伏笔
        
        Args:
            chapter_content: 章节内容
            chapter_summary: 章节摘要
            chapter_number: 章节号
            existing_clues: 已有的伏笔列表（用于检查解决状态）
            
        Returns:
            提取结果
        """
        clues = []
        
        # 1. 使用 LLM 提取新伏笔
        llm_clues = await self._llm_extract_clues(
            chapter_content, chapter_summary, chapter_number
        )
        clues.extend(llm_clues)
        
        # 2. 规则提取
        rule_clues = self._rule_extract_clues(
            chapter_content, chapter_number
        )
        clues.extend(rule_clues)
        
        # 3. 检查已有伏笔是否被解决
        if existing_clues:
            resolved_clues = await self._check_resolved_clues(
                chapter_content, chapter_summary, existing_clues, chapter_number
            )
            # 更新已解决的伏笔
            for resolved in resolved_clues:
                for clue in clues:
                    if clue.id == resolved.id:
                        clue.status = ClueStatus.RESOLVED
                        clue.chapter_resolved = chapter_number
        
        # 去重
        unique_clues = self._deduplicate_clues(clues)
        
        return ClueExtractionResult(
            clues=unique_clues,
            chapter_number=chapter_number
        )
    
    async def _llm_extract_clues(
        self,
        chapter_content: str,
        chapter_summary: str,
        chapter_number: int
    ) -> List[ForeshadowingClue]:
        """使用 LLM 提取伏笔"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位专业的小说分析师，擅长识别故事中的伏笔和线索。

请分析提供的章节内容，识别以下类型的伏笔：

1. **物品伏笔** - 提到的物品将在后续发挥重要作用
2. **对话伏笔** - 对话中隐藏的暗示或预言
3. **事件伏笔** - 发生的事件将在后续产生影响
4. **角色伏笔** - 角色的行为、特征暗示后续发展
5. **设定伏笔** - 世界观设定中埋下的线索

对每个发现的伏笔，请提供：
- 伏笔描述（简洁明了）
- 优先级（1-10，10为最关键）
- 预期解决方式（可选）
- 相关角色
- 相关剧情线

以 JSON 格式返回结果。"""),
            ("human", """【章节号】第 {chapter_number} 章

【章节摘要】
{summary}

【章节内容】
{content}

请分析并提取伏笔，以 JSON 格式返回：
{{
    "clues": [
        {{
            "clue": "伏笔描述",
            "priority": 优先级数字,
            "expected_resolution": "预期解决方式",
            "related_characters": ["角色1", "角色2"],
            "related_plotlines": ["剧情线1"],
            "tags": ["物品伏笔"]
        }}
    ]
}}""")
        ])
        
        chain = prompt | self.llm
        
        try:
            response = await chain.ainvoke({
                "chapter_number": chapter_number,
                "summary": chapter_summary[:1000],
                "content": chapter_content[:3000]
            })
            
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content.strip())
            
            clues = []
            for i, clue_data in enumerate(result.get("clues", [])):
                clue = ForeshadowingClue(
                    id=f"clue_{chapter_number}_{i}_{datetime.now().timestamp()}",
                    clue=clue_data.get("clue", ""),
                    chapter_created=chapter_number,
                    priority=CluePriority(clue_data.get("priority", 5)),
                    expected_resolution=clue_data.get("expected_resolution"),
                    related_characters=clue_data.get("related_characters", []),
                    related_plotlines=clue_data.get("related_plotlines", []),
                    tags=clue_data.get("tags", [])
                )
                clues.append(clue)
            
            return clues
        except Exception as e:
            print(f"LLM clue extraction error: {e}")
            return []
    
    def _rule_extract_clues(
        self,
        chapter_content: str,
        chapter_number: int
    ) -> List[ForeshadowingClue]:
        """基于规则提取伏笔"""
        clues = []
        
        for pattern in self.CLUE_PATTERNS:
            matches = re.finditer(pattern, chapter_content)
            for i, match in enumerate(matches):
                clue_text = match.group(1).strip()
                if len(clue_text) > 5:
                    clue = ForeshadowingClue(
                        id=f"rule_clue_{chapter_number}_{i}",
                        clue=f"文中暗示: {clue_text}",
                        chapter_created=chapter_number,
                        priority=CluePriority.LOW,
                        tags=["规则提取"]
                    )
                    clues.append(clue)
        
        return clues
    
    async def _check_resolved_clues(
        self,
        chapter_content: str,
        chapter_summary: str,
        existing_clues: List[ForeshadowingClue],
        chapter_number: int
    ) -> List[ForeshadowingClue]:
        """检查哪些伏笔在本章被解决"""
        unresolved = [c for c in existing_clues if c.status == ClueStatus.UNRESOLVED]
        
        if not unresolved:
            return []
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位小说分析师。请检查本章内容是否解决了以下伏笔。

对于每个伏笔，判断：
- "resolved": 本章明确解决了这个伏笔
- "referenced": 提到了但未解决
- "unresolved": 未提及

以 JSON 格式返回结果。"""),
            ("human", """【章节摘要】
{summary}

【章节内容片段】
{content}

【待检查伏笔】
{clues}

请判断每个伏笔的状态，以 JSON 格式返回：
{{
    "results": [
        {{
            "clue_id": "伏笔ID",
            "status": "resolved/referenced/unresolved",
            "resolution": "如何解决（如果resolved）"
        }}
    ]
}}""")
        ])
        
        chain = prompt | self.llm
        
        try:
            clues_text = "\n".join([
                f"- ID: {c.id}, 内容: {c.clue}" for c in unresolved[:10]
            ])
            
            response = await chain.ainvoke({
                "summary": chapter_summary[:800],
                "content": chapter_content[:2000],
                "clues": clues_text
            })
            
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content.strip())
            
            resolved = []
            for item in result.get("results", []):
                if item.get("status") == "resolved":
                    clue_id = item.get("clue_id")
                    for clue in unresolved:
                        if clue.id == clue_id:
                            clue.status = ClueStatus.RESOLVED
                            clue.chapter_resolved = chapter_number
                            clue.notes = item.get("resolution", "")
                            resolved.append(clue)
                            break
            
            return resolved
        except Exception as e:
            print(f"Check resolved clues error: {e}")
            return []
    
    def _deduplicate_clues(self, clues: List[ForeshadowingClue]) -> List[ForeshadowingClue]:
        """去重"""
        seen = set()
        unique = []
        for clue in clues:
            # 基于内容相似度去重
            key = clue.clue[:20]  # 取前20字符作为键
            if key not in seen:
                seen.add(key)
                unique.append(clue)
        return unique


class ForeshadowingTracker:
    """
    伏笔跟踪器
    
    管理伏笔的生命周期
    """
    
    def __init__(self):
        self.clues: Dict[str, ForeshadowingClue] = {}
        self.extractor = ClueExtractor()
    
    def add_clue(self, clue: ForeshadowingClue):
        """添加伏笔"""
        self.clues[clue.id] = clue
    
    def get_clue(self, clue_id: str) -> Optional[ForeshadowingClue]:
        """获取伏笔"""
        return self.clues.get(clue_id)
    
    def get_active_clues(
        self,
        current_chapter: int,
        min_priority: int = 5,
        max_age: int = 10
    ) -> List[ForeshadowingClue]:
        """
        获取需要处理的活跃伏笔
        
        Args:
            current_chapter: 当前章节
            min_priority: 最小优先级
            max_age: 最大年龄（章节数）
            
        Returns:
            活跃伏笔列表
        """
        active = []
        
        for clue in self.clues.values():
            # 只考虑未解决的
            if clue.status != ClueStatus.UNRESOLVED:
                continue
            
            # 检查优先级
            if clue.priority.value < min_priority:
                continue
            
            # 检查年龄
            age = current_chapter - clue.chapter_created
            if age > max_age:
                # 标记为被遗忘
                clue.status = ClueStatus.FORGOTTEN
                continue
            
            # 5章前的伏笔需要处理
            if age >= 5:
                active.append(clue)
        
        # 按优先级排序
        active.sort(key=lambda x: x.priority.value, reverse=True)
        
        return active
    
    def get_clues_by_status(self, status: ClueStatus) -> List[ForeshadowingClue]:
        """按状态获取伏笔"""
        return [c for c in self.clues.values() if c.status == status]
    
    def get_clues_by_character(self, character: str) -> List[ForeshadowingClue]:
        """按角色获取伏笔"""
        return [
            c for c in self.clues.values()
            if character in c.related_characters
        ]
    
    def resolve_clue(
        self,
        clue_id: str,
        chapter_number: int,
        resolution_notes: str = ""
    ):
        """解决伏笔"""
        clue = self.clues.get(clue_id)
        if clue:
            clue.status = ClueStatus.RESOLVED
            clue.chapter_resolved = chapter_number
            clue.notes = resolution_notes
    
    def abandon_clue(self, clue_id: str, reason: str = ""):
        """放弃伏笔"""
        clue = self.clues.get(clue_id)
        if clue:
            clue.status = ClueStatus.ABANDONED
            clue.notes = reason
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self.clues)
        resolved = len(self.get_clues_by_status(ClueStatus.RESOLVED))
        unresolved = len(self.get_clues_by_status(ClueStatus.UNRESOLVED))
        abandoned = len(self.get_clues_by_status(ClueStatus.ABANDONED))
        forgotten = len(self.get_clues_by_status(ClueStatus.FORGOTTEN))
        
        return {
            "total": total,
            "resolved": resolved,
            "unresolved": unresolved,
            "abandoned": abandoned,
            "forgotten": forgotten,
            "resolution_rate": resolved / total if total > 0 else 0
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "clues": {k: v.to_dict() for k, v in self.clues.items()},
            "statistics": self.get_statistics()
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """从字典加载"""
        clues_data = data.get("clues", {})
        self.clues = {
            k: ForeshadowingClue.from_dict(v) for k, v in clues_data.items()
        }


class ForeshadowingReminder:
    """
    伏笔提醒器
    
    在写作时提醒作者处理伏笔
    """
    
    def __init__(self, tracker: ForeshadowingTracker):
        self.tracker = tracker
    
    def get_reminders_for_chapter(
        self,
        chapter_number: int,
        current_plot: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取本章的伏笔提醒
        
        Args:
            chapter_number: 当前章节
            current_plot: 当前剧情概要
            
        Returns:
            提醒列表
        """
        reminders = []
        
        # 获取活跃伏笔
        active_clues = self.tracker.get_active_clues(chapter_number)
        
        for clue in active_clues:
            age = chapter_number - clue.chapter_created
            
            reminder = {
                "clue_id": clue.id,
                "clue": clue.clue,
                "priority": clue.priority.value,
                "priority_label": clue.priority.name,
                "age": age,
                "created_chapter": clue.chapter_created,
                "expected_resolution": clue.expected_resolution,
                "related_characters": clue.related_characters,
                "urgency": self._calculate_urgency(clue, age),
                "suggestion": self._generate_suggestion(clue, current_plot)
            }
            
            reminders.append(reminder)
        
        # 按紧急程度排序
        reminders.sort(key=lambda x: x["urgency"], reverse=True)
        
        return reminders
    
    def _calculate_urgency(self, clue: ForeshadowingClue, age: int) -> float:
        """计算紧急程度"""
        # 基于优先级和年龄的紧急度计算
        priority_weight = clue.priority.value / 10
        age_weight = min(age / 10, 1.0)  # 最多10章后达到最大
        
        return priority_weight * 0.6 + age_weight * 0.4
    
    def _generate_suggestion(
        self,
        clue: ForeshadowingClue,
        current_plot: Optional[str]
    ) -> str:
        """生成建议"""
        suggestions = []
        
        if clue.expected_resolution:
            suggestions.append(f"预期解决: {clue.expected_resolution}")
        
        if clue.related_characters:
            chars = ", ".join(clue.related_characters)
            suggestions.append(f"涉及角色: {chars}")
        
        age = datetime.now().timestamp()  # 简化计算
        if clue.priority.value >= 7:
            suggestions.append("⚠️ 这是关键伏笔，建议在本章或下章解决")
        
        return "; ".join(suggestions) if suggestions else "考虑适时回收此伏笔"
    
    def check_clue_consistency(
        self,
        new_content: str,
        active_clues: List[ForeshadowingClue]
    ) -> List[Dict[str, Any]]:
        """
        检查新内容是否与伏笔冲突
        
        Args:
            new_content: 新内容
            active_clues: 活跃伏笔
            
        Returns:
            冲突列表
        """
        conflicts = []
        
        for clue in active_clues:
            # 简单检查：如果伏笔内容与新内容矛盾
            # 实际应该使用更复杂的逻辑或 LLM 检查
            if clue.clue in new_content:
                conflicts.append({
                    "clue_id": clue.id,
                    "clue": clue.clue,
                    "type": "potential_contradiction",
                    "message": f"新内容可能影响了伏笔: {clue.clue[:50]}..."
                })
        
        return conflicts


# 便捷函数
_foreshadowing_tracker: Optional[ForeshadowingTracker] = None


def get_foreshadowing_tracker() -> ForeshadowingTracker:
    """获取伏笔跟踪器实例"""
    global _foreshadowing_tracker
    if _foreshadowing_tracker is None:
        _foreshadowing_tracker = ForeshadowingTracker()
    return _foreshadowing_tracker


async def extract_clues_from_chapter(
    chapter_content: str,
    chapter_summary: str,
    chapter_number: int
) -> ClueExtractionResult:
    """从章节提取伏笔"""
    extractor = ClueExtractor()
    tracker = get_foreshadowing_tracker()
    
    result = await extractor.extract_from_chapter(
        chapter_content,
        chapter_summary,
        chapter_number,
        list(tracker.clues.values())
    )
    
    # 添加到跟踪器
    for clue in result.clues:
        if clue.status == ClueStatus.UNRESOLVED:
            tracker.add_clue(clue)
    
    return result


def get_active_clues_for_chapter(chapter_number: int) -> List[Dict[str, Any]]:
    """获取章节的活跃伏笔提醒"""
    tracker = get_foreshadowing_tracker()
    reminder = ForeshadowingReminder(tracker)
    return reminder.get_reminders_for_chapter(chapter_number)
