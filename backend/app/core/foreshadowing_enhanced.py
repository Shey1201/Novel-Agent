"""
Enhanced Foreshadowing System - 增强版伏笔系统
结合事件因果图实现逻辑闭环检查
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import re

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


class EventType(Enum):
    """事件类型"""
    CAUSE = "cause"           # 原因事件
    EFFECT = "effect"         # 结果事件
    FORESHADOW = "foreshadow" # 伏笔事件
    RESOLUTION = "resolution" # 解决事件


class LogicStatus(Enum):
    """逻辑状态"""
    VALID = "valid"           # 逻辑有效
    INVALID = "invalid"       # 逻辑无效
    INCOMPLETE = "incomplete" # 逻辑不完整
    CONTRADICTORY = "contradictory"  # 逻辑矛盾


@dataclass
class CausalEvent:
    """因果事件节点"""
    id: str
    event: str                    # 事件描述
    event_type: EventType
    chapter: int                  # 发生章节
    related_clue_id: Optional[str] = None  # 关联伏笔ID
    causes: List[str] = field(default_factory=list)    # 原因事件ID列表
    effects: List[str] = field(default_factory=list)   # 结果事件ID列表
    characters_involved: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "event": self.event,
            "event_type": self.event_type.value,
            "chapter": self.chapter,
            "related_clue_id": self.related_clue_id,
            "causes": self.causes,
            "effects": self.effects,
            "characters_involved": self.characters_involved,
            "properties": self.properties
        }


@dataclass
class LogicChain:
    """逻辑链"""
    id: str
    start_event_id: str
    end_event_id: str
    events: List[str]  # 事件ID序列
    is_closed: bool    # 是否闭环
    coherence_score: float  # 连贯性评分 0-1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "start_event_id": self.start_event_id,
            "end_event_id": self.end_event_id,
            "events": self.events,
            "is_closed": self.is_closed,
            "coherence_score": self.coherence_score
        }


@dataclass
class ForeshadowingCheckResult:
    """伏笔检查结果"""
    clue_id: str
    clue_text: str
    status: LogicStatus
    causal_chain: Optional[LogicChain]
    issues: List[str]
    suggestions: List[str]
    expected_chapter: Optional[int]  # 预期解决章节


class CausalGraph:
    """
    事件因果图
    
    管理事件之间的因果关系，实现逻辑闭环检查
    """
    
    def __init__(self):
        self.events: Dict[str, CausalEvent] = {}
        self.chains: Dict[str, LogicChain] = {}
        self.clue_to_event: Dict[str, str] = {}  # 伏笔ID -> 事件ID
    
    def add_event(self, event: CausalEvent) -> str:
        """添加事件到因果图"""
        self.events[event.id] = event
        if event.related_clue_id:
            self.clue_to_event[event.related_clue_id] = event.id
        return event.id
    
    def link_cause_effect(self, cause_id: str, effect_id: str):
        """建立因果关系"""
        if cause_id in self.events and effect_id in self.events:
            cause = self.events[cause_id]
            effect = self.events[effect_id]
            
            if effect_id not in cause.effects:
                cause.effects.append(effect_id)
            if cause_id not in effect.causes:
                effect.causes.append(cause_id)
    
    def find_logic_chains(self, start_event_id: str) -> List[LogicChain]:
        """
        查找从起始事件开始的逻辑链
        
        使用DFS遍历找到所有可能的因果链
        """
        chains = []
        visited = set()
        
        def dfs(current_id: str, path: List[str]):
            if current_id in visited:
                return
            
            visited.add(current_id)
            path.append(current_id)
            
            event = self.events.get(current_id)
            if not event:
                return
            
            # 如果是结果事件或没有后续效果，形成一条链
            if event.event_type == EventType.RESOLUTION or not event.effects:
                chain = LogicChain(
                    id=f"chain_{start_event_id}_{current_id}",
                    start_event_id=start_event_id,
                    end_event_id=current_id,
                    events=path.copy(),
                    is_closed=event.event_type == EventType.RESOLUTION,
                    coherence_score=self._calculate_coherence(path)
                )
                chains.append(chain)
            
            # 继续遍历效果
            for effect_id in event.effects:
                dfs(effect_id, path)
            
            path.pop()
            visited.remove(current_id)
        
        dfs(start_event_id, [])
        return chains
    
    def _calculate_coherence(self, event_ids: List[str]) -> float:
        """计算逻辑链的连贯性评分"""
        if len(event_ids) < 2:
            return 1.0
        
        scores = []
        for i in range(len(event_ids) - 1):
            current = self.events.get(event_ids[i])
            next_event = self.events.get(event_ids[i + 1])
            
            if current and next_event:
                # 检查章节顺序
                chapter_gap = abs(next_event.chapter - current.chapter)
                chapter_score = max(0, 1 - chapter_gap / 10)  # 章节差距越大分数越低
                
                # 检查角色连续性
                common_chars = set(current.characters_involved) & set(next_event.characters_involved)
                char_score = len(common_chars) / max(len(current.characters_involved), 1)
                
                scores.append((chapter_score + char_score) / 2)
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def check_clue_closure(self, clue_id: str) -> ForeshadowingCheckResult:
        """
        检查伏笔的逻辑闭环
        
        验证伏笔是否有合理的因果链，是否形成闭环
        """
        event_id = self.clue_to_event.get(clue_id)
        if not event_id:
            return ForeshadowingCheckResult(
                clue_id=clue_id,
                clue_text="",
                status=LogicStatus.INCOMPLETE,
                causal_chain=None,
                issues=["未找到关联事件"],
                suggestions=["需要为伏笔创建因果事件"],
                expected_chapter=None
            )
        
        event = self.events.get(event_id)
        if not event:
            return ForeshadowingCheckResult(
                clue_id=clue_id,
                clue_text="",
                status=LogicStatus.INVALID,
                causal_chain=None,
                issues=["关联事件不存在"],
                suggestions=["检查伏笔与事件的关联"],
                expected_chapter=None
            )
        
        # 查找所有逻辑链
        chains = self.find_logic_chains(event_id)
        
        if not chains:
            return ForeshadowingCheckResult(
                clue_id=clue_id,
                clue_text=event.event,
                status=LogicStatus.INCOMPLETE,
                causal_chain=None,
                issues=["伏笔没有后续因果链"],
                suggestions=["为伏笔添加结果事件或解决方案"],
                expected_chapter=event.chapter + 5
            )
        
        # 找到最佳闭环链
        closed_chains = [c for c in chains if c.is_closed]
        
        if closed_chains:
            best_chain = max(closed_chains, key=lambda c: c.coherence_score)
            return ForeshadowingCheckResult(
                clue_id=clue_id,
                clue_text=event.event,
                status=LogicStatus.VALID,
                causal_chain=best_chain,
                issues=[],
                suggestions=["逻辑闭环完整"],
                expected_chapter=None
            )
        else:
            # 找到最长的未闭环链
            best_chain = max(chains, key=lambda c: len(c.events))
            last_event = self.events.get(best_chain.end_event_id)
            
            return ForeshadowingCheckResult(
                clue_id=clue_id,
                clue_text=event.event,
                status=LogicStatus.INCOMPLETE,
                causal_chain=best_chain,
                issues=[f"伏笔在第{last_event.chapter}章后未解决"],
                suggestions=[
                    f"建议在第{last_event.chapter + 3}章前添加解决方案",
                    "确保伏笔与主线剧情的关联性"
                ],
                expected_chapter=last_event.chapter + 3
            )
    
    def get_unresolved_clues(self, current_chapter: int) -> List[Dict[str, Any]]:
        """获取未解决的伏笔列表"""
        unresolved = []
        
        for clue_id, event_id in self.clue_to_event.items():
            result = self.check_clue_closure(clue_id)
            
            if result.status in [LogicStatus.INCOMPLETE, LogicStatus.INVALID]:
                event = self.events.get(event_id)
                if event and current_chapter - event.chapter >= 3:
                    unresolved.append({
                        "clue_id": clue_id,
                        "clue_text": result.clue_text,
                        "created_chapter": event.chapter,
                        "chapters_pending": current_chapter - event.chapter,
                        "issues": result.issues,
                        "suggestions": result.suggestions,
                        "expected_chapter": result.expected_chapter
                    })
        
        return sorted(unresolved, key=lambda x: x["chapters_pending"], reverse=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "events": {k: v.to_dict() for k, v in self.events.items()},
            "chains": {k: v.to_dict() for k, v in self.chains.items()},
            "clue_to_event": self.clue_to_event
        }


class EnhancedForeshadowingTracker:
    """
    增强版伏笔跟踪器
    
    结合因果图实现逻辑闭环检查
    """
    
    def __init__(self):
        from app.core.foreshadowing import ForeshadowingTracker
        self.base_tracker = ForeshadowingTracker()
        self.causal_graph = CausalGraph()
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    
    async def extract_events_from_chapter(
        self,
        chapter_content: str,
        chapter_number: int
    ) -> List[CausalEvent]:
        """从章节中提取因果事件"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的小说情节分析专家。请从以下章节内容中提取关键事件，并分析它们之间的因果关系。

请提取：
1. 伏笔事件（暗示未来发展的线索）
2. 原因事件（推动情节发展的关键动作）
3. 结果事件（原因导致的后果）
4. 解决事件（伏笔的回收或问题的解决）

对于每个事件，请提供：
- 事件描述（简洁的一句话）
- 事件类型（foreshadow/cause/effect/resolution）
- 涉及的角色
- 如果是伏笔，预期的解决方式

请以JSON格式输出：
{{
    "events": [
        {{
            "event": "事件描述",
            "event_type": "foreshadow",
            "characters_involved": ["角色1", "角色2"],
            "expected_resolution": "预期解决方式（可选）"
        }}
    ]
}}"""),
            ("human", "章节内容：\n{content}\n\n章节号：{chapter}")
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "content": chapter_content[:3000],
            "chapter": chapter_number
        })
        
        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content.strip())
            events = []
            
            for i, event_data in enumerate(data.get("events", [])):
                event = CausalEvent(
                    id=f"event_{chapter_number}_{i}_{datetime.now().timestamp()}",
                    event=event_data["event"],
                    event_type=EventType(event_data["event_type"]),
                    chapter=chapter_number,
                    characters_involved=event_data.get("characters_involved", []),
                    properties={"expected_resolution": event_data.get("expected_resolution")}
                )
                events.append(event)
            
            return events
        except Exception as e:
            print(f"Failed to extract events: {e}")
            return []
    
    async def analyze_causal_relations(
        self,
        events: List[CausalEvent],
        chapter_content: str
    ) -> List[Tuple[str, str]]:
        """分析事件间的因果关系"""
        if len(events) < 2:
            return []
        
        events_text = "\n".join([
            f"{i+1}. [{e.event_type.value}] {e.event}"
            for i, e in enumerate(events)
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """分析以下事件之间的因果关系。请指出哪些事件是其他事件的原因或结果。

请以JSON格式输出因果关系列表：
{{
    "relations": [
        {{"cause": "原因事件编号", "effect": "结果事件编号"}}
    ]
}}"""),
            ("human", "事件列表：\n{events}\n\n章节内容摘要：\n{content}")
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "events": events_text,
            "content": chapter_content[:1000]
        })
        
        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content.strip())
            relations = []
            
            for rel in data.get("relations", []):
                cause_idx = int(rel["cause"]) - 1
                effect_idx = int(rel["effect"]) - 1
                
                if 0 <= cause_idx < len(events) and 0 <= effect_idx < len(events):
                    relations.append((events[cause_idx].id, events[effect_idx].id))
            
            return relations
        except Exception as e:
            print(f"Failed to analyze causal relations: {e}")
            return []
    
    async def process_chapter(
        self,
        chapter_content: str,
        chapter_number: int
    ) -> Dict[str, Any]:
        """
        处理章节 - 提取伏笔和事件，建立因果链
        
        Returns:
            处理结果，包含提取的伏笔和事件
        """
        # 1. 使用基础跟踪器提取伏笔
        from app.core.foreshadowing import extract_clues_from_chapter
        clue_result = await extract_clues_from_chapter(
            chapter_content=chapter_content,
            chapter_summary="",  # 可以传入章节摘要
            chapter_number=chapter_number
        )
        
        # 2. 提取因果事件
        events = await self.extract_events_from_chapter(
            chapter_content=chapter_content,
            chapter_number=chapter_number
        )
        
        # 3. 将伏笔与事件关联
        for clue in clue_result.clues:
            # 找到最匹配的事件
            for event in events:
                if event.event_type == EventType.FORESHADOW:
                    if clue.clue in event.event or event.event in clue.clue:
                        event.related_clue_id = clue.id
                        break
        
        # 4. 添加事件到因果图
        for event in events:
            self.causal_graph.add_event(event)
        
        # 5. 分析因果关系
        relations = await self.analyze_causal_relations(events, chapter_content)
        for cause_id, effect_id in relations:
            self.causal_graph.link_cause_effect(cause_id, effect_id)
        
        # 6. 检查未解决伏笔
        unresolved = self.causal_graph.get_unresolved_clues(chapter_number)
        
        return {
            "chapter_number": chapter_number,
            "clues_extracted": len(clue_result.clues),
            "events_extracted": len(events),
            "causal_relations": len(relations),
            "unresolved_clues": unresolved,
            "closure_warnings": [
                f"伏笔 '{u['clue_text'][:30]}...' 已悬而未决 {u['chapters_pending']} 章"
                for u in unresolved[:3]
            ]
        }
    
    def get_writing_guidance(self, current_chapter: int) -> Dict[str, Any]:
        """
        获取写作指导 - 提示未解决伏笔
        
        在生成新章节时调用，确保伏笔合理衔接
        """
        unresolved = self.causal_graph.get_unresolved_clues(current_chapter)
        
        # 按优先级排序
        high_priority = [u for u in unresolved if u["chapters_pending"] >= 5]
        medium_priority = [u for u in unresolved if 3 <= u["chapters_pending"] < 5]
        
        guidance = {
            "current_chapter": current_chapter,
            "total_unresolved": len(unresolved),
            "high_priority_clues": high_priority,
            "medium_priority_clues": medium_priority,
            "suggestions": []
        }
        
        # 生成写作建议
        if high_priority:
            guidance["suggestions"].append(
                f"⚠️ 有 {len(high_priority)} 个关键伏笔已悬而未决超过5章，建议在本章解决"
            )
            for clue in high_priority[:2]:
                guidance["suggestions"].append(
                    f"  - '{clue['clue_text'][:40]}...' ({clue['suggestions'][0] if clue['suggestions'] else '需解决'})"
                )
        
        if medium_priority:
            guidance["suggestions"].append(
                f"💡 有 {len(medium_priority)} 个伏笔可以开始铺垫解决方案"
            )
        
        if not unresolved:
            guidance["suggestions"].append("✅ 所有伏笔已解决，可以开始新的情节线")
        
        return guidance


# 全局实例
_enhanced_tracker: Optional[EnhancedForeshadowingTracker] = None


def get_enhanced_foreshadowing_tracker() -> EnhancedForeshadowingTracker:
    """获取增强版伏笔跟踪器实例"""
    global _enhanced_tracker
    if _enhanced_tracker is None:
        _enhanced_tracker = EnhancedForeshadowingTracker()
    return _enhanced_tracker
