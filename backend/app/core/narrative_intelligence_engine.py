"""
Narrative Intelligence Engine - 叙事智能引擎
剧情结构分析、伏笔系统、Plot Graph
"""

from typing import Dict, Any, Optional, List, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import json


class ForeshadowingStatus(Enum):
    """伏笔状态"""
    PLANTED = "planted"         # 已埋下
    HINTED = "hinted"           # 已暗示
    RESOLVED = "resolved"       # 已解决
    ABANDONED = "abandoned"     # 已废弃


class PlotNodeType(Enum):
    """剧情节点类型"""
    CHARACTER = "character"     # 角色
    EVENT = "event"            # 事件
    LOCATION = "location"      # 地点
    ITEM = "item"              # 物品
    FORESHADOWING = "foreshadowing"  # 伏笔
    CONFLICT = "conflict"      # 冲突
    THEME = "theme"            # 主题


class PlotEdgeType(Enum):
    """剧情边类型"""
    CAUSAL = "causal"          # 因果
    TEMPORAL = "temporal"      # 时间先后
    SPATIAL = "spatial"        # 空间关系
    RELATIONAL = "relational"  # 人物关系
    THEMATIC = "thematic"      # 主题关联
    FORESHADOWS = "foreshadows"  # 伏笔指向


@dataclass
class Foreshadowing:
    """伏笔"""
    id: str
    clue: str
    chapter_planted: str
    chapter_resolved: Optional[str] = None
    status: ForeshadowingStatus = ForeshadowingStatus.PLANTED
    priority: str = "medium"  # low/medium/high/critical
    related_characters: List[str] = field(default_factory=list)
    expected_resolution: str = ""
    actual_resolution: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "clue": self.clue,
            "chapter_planted": self.chapter_planted,
            "chapter_resolved": self.chapter_resolved,
            "status": self.status.value,
            "priority": self.priority,
            "related_characters": self.related_characters,
            "is_resolved": self.status == ForeshadowingStatus.RESOLVED
        }


@dataclass
class PlotNode:
    """剧情节点"""
    id: str
    node_type: PlotNodeType
    name: str
    description: str
    chapter_introduced: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.node_type.value,
            "name": self.name,
            "description": self.description,
            "chapter_introduced": self.chapter_introduced
        }


@dataclass
class PlotEdge:
    """剧情边"""
    source: str
    target: str
    edge_type: PlotEdgeType
    weight: float = 1.0
    description: str = ""
    chapter_formed: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "type": self.edge_type.value,
            "weight": self.weight,
            "description": self.description
        }


@dataclass
class ChapterStructure:
    """章节结构"""
    chapter_id: str
    chapter_number: int
    
    # 结构元素
    hook: Optional[str] = None           # 钩子
    inciting_incident: Optional[str] = None  # 触发事件
    rising_action: List[str] = field(default_factory=list)  # 上升动作
    climax: Optional[str] = None         # 高潮
    falling_action: List[str] = field(default_factory=list)  # 下降动作
    resolution: Optional[str] = None     # 结局
    
    # 统计
    word_count: int = 0
    scene_count: int = 0
    character_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chapter_id": self.chapter_id,
            "chapter_number": self.chapter_number,
            "structure": {
                "hook": self.hook,
                "inciting_incident": self.inciting_incident,
                "rising_action_count": len(self.rising_action),
                "climax": self.climax,
                "falling_action_count": len(self.falling_action),
                "resolution": self.resolution
            },
            "stats": {
                "word_count": self.word_count,
                "scene_count": self.scene_count,
                "character_count": self.character_count
            }
        }


class PlotGraph:
    """
    剧情图
    
    构建角色、事件、伏笔、冲突之间的关系图
    """
    
    def __init__(self, novel_id: str):
        self.novel_id = novel_id
        self.nodes: Dict[str, PlotNode] = {}
        self.edges: List[PlotEdge] = []
        self.adjacency_list: Dict[str, List[str]] = defaultdict(list)
        
        # 索引
        self.nodes_by_type: Dict[PlotNodeType, List[str]] = defaultdict(list)
        self.nodes_by_chapter: Dict[str, List[str]] = defaultdict(list)
    
    def add_node(self, node: PlotNode) -> str:
        """添加节点"""
        self.nodes[node.id] = node
        self.nodes_by_type[node.node_type].append(node.id)
        self.nodes_by_chapter[node.chapter_introduced].append(node.id)
        return node.id
    
    def add_edge(self, edge: PlotEdge) -> bool:
        """添加边"""
        if edge.source not in self.nodes or edge.target not in self.nodes:
            return False
        
        self.edges.append(edge)
        self.adjacency_list[edge.source].append(edge.target)
        return True
    
    def get_character_arc(self, character_id: str) -> List[Dict[str, Any]]:
        """获取角色弧线"""
        arc = []
        
        # 找到角色的所有相关事件
        character_events = []
        for edge in self.edges:
            if edge.edge_type == PlotEdgeType.RELATIONAL:
                if edge.source == character_id:
                    character_events.append(edge.target)
                elif edge.target == character_id:
                    character_events.append(edge.source)
        
        # 按章节排序
        for event_id in character_events:
            event_node = self.nodes.get(event_id)
            if event_node and event_node.node_type == PlotNodeType.EVENT:
                arc.append({
                    "chapter": event_node.chapter_introduced,
                    "event": event_node.name,
                    "description": event_node.description
                })
        
        arc.sort(key=lambda x: x["chapter"])
        return arc
    
    def find_plot_holes(self) -> List[Dict[str, Any]]:
        """发现剧情断裂"""
        holes = []
        
        # 检查因果关系断裂
        causal_edges = [e for e in self.edges if e.edge_type == PlotEdgeType.CAUSAL]
        
        for edge in causal_edges:
            source_node = self.nodes.get(edge.source)
            target_node = self.nodes.get(edge.target)
            
            if source_node and target_node:
                # 检查是否有合理的因果链
                if not self._has_reasonable_connection(edge.source, edge.target):
                    holes.append({
                        "type": "causal_gap",
                        "source": source_node.name,
                        "target": target_node.name,
                        "description": f"从'{source_node.name}'到'{target_node.name}'的因果关系不够清晰"
                    })
        
        # 检查孤立节点
        for node_id, node in self.nodes.items():
            if node_id not in self.adjacency_list and not any(
                e.target == node_id for e in self.edges
            ):
                holes.append({
                    "type": "isolated_node",
                    "node": node.name,
                    "description": f"'{node.name}'与其他剧情元素缺乏关联"
                })
        
        return holes
    
    def _has_reasonable_connection(self, source: str, target: str) -> bool:
        """检查是否有合理的连接"""
        # 简化实现：检查是否有路径
        visited = set()
        queue = [source]
        
        while queue:
            current = queue.pop(0)
            if current == target:
                return True
            
            if current not in visited:
                visited.add(current)
                queue.extend(self.adjacency_list.get(current, []))
        
        return False
    
    def get_plot_summary(self) -> Dict[str, Any]:
        """获取剧情摘要"""
        return {
            "novel_id": self.novel_id,
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_breakdown": {
                node_type.value: len(ids)
                for node_type, ids in self.nodes_by_type.items()
            },
            "plot_holes": self.find_plot_holes(),
            "main_characters": [
                self.nodes[char_id].name
                for char_id in self.nodes_by_type.get(PlotNodeType.CHARACTER, [])
            ][:5]  # 前5个角色
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "novel_id": self.novel_id,
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges]
        }


class ForeshadowingEngine:
    """
    伏笔引擎
    
    自动识别、跟踪和管理伏笔
    """
    
    def __init__(self):
        self.foreshadowings: Dict[str, Foreshadowing] = {}
        self.novel_foreshadowings: Dict[str, List[str]] = defaultdict(list)
        
        # 伏笔模式识别
        self.foreshadowing_patterns = [
            r"([\u4e00-\u9fa5]{2,10})[^。]*似乎[^。]*不寻常",
            r"([\u4e00-\u9fa5]{2,10})[^。]*隐隐[^。]*感觉",
            r"([\u4e00-\u9fa5]{2,10})[^。]*后来[^。]*才明白",
            r"([\u4e00-\u9fa5]{2,10})[^。]*伏笔",
            r"([\u4e00-\u9fa5]{2,10})[^。]*暗示",
        ]
    
    def plant_foreshadowing(
        self,
        novel_id: str,
        clue: str,
        chapter: str,
        priority: str = "medium",
        related_characters: List[str] = None,
        expected_resolution: str = ""
    ) -> str:
        """埋下伏笔"""
        fs_id = f"fs_{novel_id}_{chapter}_{hash(clue) % 10000}"
        
        foreshadowing = Foreshadowing(
            id=fs_id,
            clue=clue,
            chapter_planted=chapter,
            priority=priority,
            related_characters=related_characters or [],
            expected_resolution=expected_resolution
        )
        
        self.foreshadowings[fs_id] = foreshadowing
        self.novel_foreshadowings[novel_id].append(fs_id)
        
        return fs_id
    
    def resolve_foreshadowing(
        self,
        fs_id: str,
        chapter: str,
        resolution: str
    ) -> bool:
        """解决伏笔"""
        fs = self.foreshadowings.get(fs_id)
        if not fs:
            return False
        
        fs.status = ForeshadowingStatus.RESOLVED
        fs.chapter_resolved = chapter
        fs.actual_resolution = resolution
        
        return True
    
    def extract_foreshadowings_from_text(
        self,
        novel_id: str,
        text: str,
        chapter: str
    ) -> List[str]:
        """从文本中提取伏笔"""
        import re
        
        found_ids = []
        
        for pattern in self.foreshadowing_patterns:
            for match in re.finditer(pattern, text):
                clue = match.group(0)
                fs_id = self.plant_foreshadowing(
                    novel_id=novel_id,
                    clue=clue,
                    chapter=chapter,
                    priority="medium"
                )
                found_ids.append(fs_id)
        
        return found_ids
    
    def get_unresolved_foreshadowings(
        self,
        novel_id: str,
        min_priority: str = "medium"
    ) -> List[Dict[str, Any]]:
        """获取未解决的伏笔"""
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        min_priority_level = priority_order.get(min_priority, 2)
        
        unresolved = []
        for fs_id in self.novel_foreshadowings.get(novel_id, []):
            fs = self.foreshadowings.get(fs_id)
            if fs and fs.status != ForeshadowingStatus.RESOLVED:
                fs_priority_level = priority_order.get(fs.priority, 2)
                if fs_priority_level <= min_priority_level:
                    unresolved.append(fs.to_dict())
        
        # 按优先级排序
        unresolved.sort(key=lambda x: priority_order.get(x["priority"], 2))
        
        return unresolved
    
    def get_foreshadowing_report(self, novel_id: str) -> Dict[str, Any]:
        """获取伏笔报告"""
        all_fs = [
            self.foreshadowings[fs_id]
            for fs_id in self.novel_foreshadowings.get(novel_id, [])
        ]
        
        total = len(all_fs)
        resolved = sum(1 for fs in all_fs if fs.status == ForeshadowingStatus.RESOLVED)
        unresolved = total - resolved
        
        # 按优先级统计
        by_priority = defaultdict(int)
        for fs in all_fs:
            by_priority[fs.priority] += 1
        
        # 长期未解决的伏笔
        stale_foreshadowings = [
            fs.to_dict() for fs in all_fs
            if fs.status != ForeshadowingStatus.RESOLVED
            and self._is_stale(fs.chapter_planted, "current")
        ]
        
        return {
            "total_foreshadowings": total,
            "resolved": resolved,
            "unresolved": unresolved,
            "resolution_rate": round(resolved / total, 2) if total > 0 else 0,
            "by_priority": dict(by_priority),
            "stale_foreshadowings": stale_foreshadowings,
            "suggestions": self._generate_suggestions(unresolved, stale_foreshadowings)
        }
    
    def _is_stale(self, chapter_planted: str, current_chapter: str) -> bool:
        """检查伏笔是否过期"""
        # 简化实现：如果超过5章未解决，认为过期
        try:
            planted_num = int(chapter_planted.split("_")[-1])
            current_num = int(current_chapter.split("_")[-1]) if "_" in current_chapter else 999
            return current_num - planted_num > 5
        except:
            return False
    
    def _generate_suggestions(
        self,
        unresolved_count: int,
        stale_foreshadowings: List[Dict]
    ) -> List[str]:
        """生成建议"""
        suggestions = []
        
        if unresolved_count > 5:
            suggestions.append(f"有{unresolved_count}个未解决的伏笔，建议尽快安排回收")
        
        if stale_foreshadowings:
            suggestions.append(f"有{len(stale_foreshadowings)}个伏笔长期未解决，读者可能会遗忘")
        
        if not suggestions:
            suggestions.append("伏笔管理良好")
        
        return suggestions


class NarrativeIntelligenceEngine:
    """
    叙事智能引擎
    
    整合剧情图、伏笔系统和章节结构分析
    """
    
    def __init__(self):
        self.plot_graphs: Dict[str, PlotGraph] = {}
        self.foreshadowing_engine = ForeshadowingEngine()
        self.chapter_structures: Dict[str, ChapterStructure] = {}
    
    def get_or_create_plot_graph(self, novel_id: str) -> PlotGraph:
        """获取或创建剧情图"""
        if novel_id not in self.plot_graphs:
            self.plot_graphs[novel_id] = PlotGraph(novel_id)
        return self.plot_graphs[novel_id]
    
    def analyze_chapter_structure(
        self,
        chapter_id: str,
        chapter_number: int,
        content: str
    ) -> ChapterStructure:
        """分析章节结构"""
        structure = ChapterStructure(
            chapter_id=chapter_id,
            chapter_number=chapter_number
        )
        
        # 分析字数
        structure.word_count = len(content)
        
        # 分析场景数（按空行分割）
        scenes = [s for s in content.split("\n\n") if s.strip()]
        structure.scene_count = len(scenes)
        
        # 识别结构元素（简化实现）
        if scenes:
            structure.hook = scenes[0][:100] if len(scenes[0]) > 100 else scenes[0]
        
        if len(scenes) >= 2:
            structure.inciting_incident = scenes[1][:100]
        
        # 中间部分作为上升动作
        if len(scenes) >= 4:
            structure.rising_action = [s[:50] for s in scenes[2:-2]]
        
        # 倒数第二部分作为高潮
        if len(scenes) >= 3:
            structure.climax = scenes[-2][:100]
        
        # 最后部分作为结局
        if len(scenes) >= 2:
            structure.resolution = scenes[-1][:100]
        
        self.chapter_structures[chapter_id] = structure
        
        return structure
    
    def get_narrative_report(self, novel_id: str) -> Dict[str, Any]:
        """获取叙事报告"""
        plot_graph = self.plot_graphs.get(novel_id)
        foreshadowing_report = self.foreshadowing_engine.get_foreshadowing_report(novel_id)
        
        # 收集章节结构
        chapter_structures = [
            structure.to_dict()
            for ch_id, structure in self.chapter_structures.items()
            if ch_id.startswith(novel_id)
        ]
        
        return {
            "novel_id": novel_id,
            "plot_graph": plot_graph.get_plot_summary() if plot_graph else None,
            "foreshadowing": foreshadowing_report,
            "chapter_structures": sorted(
                chapter_structures,
                key=lambda x: x["chapter_number"]
            ),
            "overall_assessment": self._generate_overall_assessment(
                plot_graph, foreshadowing_report, chapter_structures
            )
        }
    
    def _generate_overall_assessment(
        self,
        plot_graph: Optional[PlotGraph],
        foreshadowing_report: Dict[str, Any],
        chapter_structures: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成整体评估"""
        assessment = {
            "plot_integrity": "good",
            "structure_balance": "good",
            "foreshadowing_management": "good",
            "suggestions": []
        }
        
        # 评估剧情完整性
        if plot_graph:
            holes = plot_graph.find_plot_holes()
            if len(holes) > 3:
                assessment["plot_integrity"] = "needs_improvement"
                assessment["suggestions"].append(f"发现{len(holes)}处剧情断裂，建议修复")
        
        # 评估伏笔管理
        unresolved = foreshadowing_report.get("unresolved", 0)
        if unresolved > 5:
            assessment["foreshadowing_management"] = "attention_needed"
            assessment["suggestions"].append(f"有{unresolved}个未解决伏笔")
        
        # 评估结构平衡
        if chapter_structures:
            word_counts = [s["stats"]["word_count"] for s in chapter_structures]
            if word_counts:
                avg_words = sum(word_counts) / len(word_counts)
                variance = sum((w - avg_words) ** 2 for w in word_counts) / len(word_counts)
                if variance > (avg_words * 0.3) ** 2:
                    assessment["structure_balance"] = "uneven"
                    assessment["suggestions"].append("各章节字数差异较大，建议平衡")
        
        return assessment


# 全局实例
_narrative_engine: Optional[NarrativeIntelligenceEngine] = None


def get_narrative_intelligence_engine() -> NarrativeIntelligenceEngine:
    """获取叙事智能引擎实例"""
    global _narrative_engine
    if _narrative_engine is None:
        _narrative_engine = NarrativeIntelligenceEngine()
    return _narrative_engine
