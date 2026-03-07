"""
Symbolic Logic Engine - 符号逻辑约束引擎
将世界观规则转化为逻辑谓词，确保设定"绝对不崩"
"""

from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import json


class LogicOperator(Enum):
    """逻辑运算符"""
    AND = "and"
    OR = "or"
    NOT = "not"
    IMPLIES = "implies"
    EQUALS = "equals"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    IN = "in"


class RuleType(Enum):
    """规则类型"""
    MAGIC_SYSTEM = "magic_system"      # 魔法系统规则
    POWER_LEVEL = "power_level"        # 战力等级规则
    TIME_SPACE = "time_space"          # 时空规则
    SOCIAL_STRUCTURE = "social_structure"  # 社会结构规则
    PHYSICAL_LAW = "physical_law"      # 物理法则
    BIOLOGICAL = "biological"          # 生物规则


@dataclass
class LogicPredicate:
    """逻辑谓词"""
    name: str
    arguments: List[str]
    operator: Optional[LogicOperator] = None
    value: Any = None
    
    def to_string(self) -> str:
        """转换为字符串表示"""
        args_str = ", ".join(self.arguments)
        if self.operator and self.value is not None:
            return f"{self.name}({args_str}) {self.operator.value} {self.value}"
        return f"{self.name}({args_str})"


@dataclass
class WorldRule:
    """世界观规则"""
    rule_id: str
    rule_type: RuleType
    name: str
    description: str
    predicates: List[LogicPredicate]
    constraints: List[str]  # 约束条件（字符串形式）
    exceptions: List[str] = field(default_factory=list)
    priority: int = 5  # 1-10，数字越大优先级越高
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_type": self.rule_type.value,
            "name": self.name,
            "description": self.description,
            "predicates": [p.to_string() for p in self.predicates],
            "constraints": self.constraints,
            "priority": self.priority,
            "enabled": self.enabled
        }


@dataclass
class LogicViolation:
    """逻辑违规"""
    violation_id: str
    rule_id: str
    rule_name: str
    violated_predicate: LogicPredicate
    actual_value: Any
    expected_value: Any
    severity: float  # 0-1
    chapter_location: str
    suggested_fix: str
    auto_fixable: bool = False


@dataclass
class FactAssertion:
    """事实断言"""
    fact_id: str
    predicate: LogicPredicate
    source: str  # 来源（章节/设定等）
    confidence: float = 1.0  # 置信度
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class SymbolicLogicEngine:
    """
    符号逻辑引擎
    
    核心功能：
    1. 将世界观规则转化为逻辑谓词
    2. 实时验证剧情是否符合逻辑约束
    3. 发现违规时直接拦截并报错
    4. 提供自动修复建议
    """
    
    def __init__(self):
        self.rules: Dict[str, WorldRule] = {}
        self.facts: Dict[str, FactAssertion] = {}
        self.violations: List[LogicViolation] = []
        
        # 规则索引
        self.rules_by_type: Dict[RuleType, List[str]] = {
            rt: [] for rt in RuleType
        }
        
        # 谓词求值器
        self.evaluators: Dict[str, Callable] = {
            "power_level": self._eval_power_level,
            "magic_capability": self._eval_magic_capability,
            "time_consistency": self._eval_time_consistency,
            "spatial_consistency": self._eval_spatial_consistency,
            "social_status": self._eval_social_status
        }
    
    def add_rule(self, rule: WorldRule) -> str:
        """添加世界观规则"""
        self.rules[rule.rule_id] = rule
        self.rules_by_type[rule.rule_type].append(rule.rule_id)
        return rule.rule_id
    
    def create_magic_system_rule(
        self,
        rule_id: str,
        name: str,
        description: str,
        magic_levels: List[str],
        level_requirements: Dict[str, Any]
    ) -> WorldRule:
        """
        创建魔法系统规则
        
        示例：
        - 魔法等级：学徒 < 法师 < 大法师 < 传奇法师
        - 施法需要消耗魔力
        - 高级魔法需要相应等级
        """
        predicates = [
            LogicPredicate(
                name="magic_level",
                arguments=["character", "level"],
                operator=LogicOperator.IN,
                value=magic_levels
            ),
            LogicPredicate(
                name="mana_cost",
                arguments=["spell", "cost"],
                operator=LogicOperator.LESS_THAN,
                value="max_mana"
            )
        ]
        
        constraints = [
            f"magic_level(X, L) and spell_level(S, LS) implies L >= LS",
            f"mana_cost(S, C) and current_mana(X, M) implies M >= C"
        ]
        
        return WorldRule(
            rule_id=rule_id,
            rule_type=RuleType.MAGIC_SYSTEM,
            name=name,
            description=description,
            predicates=predicates,
            constraints=constraints,
            priority=9
        )
    
    def create_power_level_rule(
        self,
        rule_id: str,
        name: str,
        description: str,
        power_tiers: List[Dict[str, Any]]
    ) -> WorldRule:
        """
        创建战力等级规则
        
        示例：
        - 等级体系：青铜 < 白银 < 黄金 < 钻石
        - 高等级对低等级有压制
        - 等级差距过大无法越级挑战
        """
        predicates = [
            LogicPredicate(
                name="power_level",
                arguments=["character", "level"],
                operator=LogicOperator.IN,
                value=[t["name"] for t in power_tiers]
            ),
            LogicPredicate(
                name="combat_power",
                arguments=["character", "power"],
                operator=LogicOperator.GREATER_THAN,
                value=0
            )
        ]
        
        constraints = [
            f"power_level(X, L1) and power_level(Y, L2) and tier_gap(L1, L2, G) implies "
            f"(G > 3 implies cannot_defeat(X, Y))"
        ]
        
        return WorldRule(
            rule_id=rule_id,
            rule_type=RuleType.POWER_LEVEL,
            name=name,
            description=description,
            predicates=predicates,
            constraints=constraints,
            priority=10
        )
    
    def assert_fact(self, fact: FactAssertion) -> bool:
        """
        断言事实
        
        在添加事实前验证是否符合所有规则
        """
        # 验证事实
        violations = self._validate_fact(fact)
        
        if violations:
            # 发现违规，不添加事实
            self.violations.extend(violations)
            return False
        
        # 添加事实
        self.facts[fact.fact_id] = fact
        return True
    
    def _validate_fact(self, fact: FactAssertion) -> List[LogicViolation]:
        """验证事实是否符合规则"""
        violations = []
        
        # 获取相关规则
        predicate_name = fact.predicate.name
        
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            # 检查规则是否适用于此谓词
            relevant_predicates = [
                p for p in rule.predicates
                if p.name == predicate_name
            ]
            
            for rule_predicate in relevant_predicates:
                # 评估约束
                violation = self._check_constraint(
                    fact, rule, rule_predicate
                )
                
                if violation:
                    violations.append(violation)
        
        return violations
    
    def _check_constraint(
        self,
        fact: FactAssertion,
        rule: WorldRule,
        rule_predicate: LogicPredicate
    ) -> Optional[LogicViolation]:
        """检查具体约束"""
        # 获取求值器
        evaluator = self.evaluators.get(fact.predicate.name)
        
        if evaluator:
            result = evaluator(fact, rule_predicate)
            if not result["valid"]:
                return LogicViolation(
                    violation_id=f"viol_{datetime.now().timestamp()}",
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    violated_predicate=rule_predicate,
                    actual_value=fact.predicate.value,
                    expected_value=result.get("expected"),
                    severity=result.get("severity", 0.8),
                    chapter_location=fact.source,
                    suggested_fix=result.get("suggestion", "请检查设定一致性"),
                    auto_fixable=result.get("auto_fixable", False)
                )
        
        return None
    
    def _eval_power_level(self, fact: FactAssertion, rule_predicate: LogicPredicate) -> Dict[str, Any]:
        """评估战力等级约束"""
        # 简化的战力等级评估
        power_levels = ["青铜", "白银", "黄金", "铂金", "钻石", "星耀", "王者"]
        
        if fact.predicate.name == "power_level":
            level = fact.predicate.arguments[1] if len(fact.predicate.arguments) > 1 else None
            
            if level and level not in power_levels:
                return {
                    "valid": False,
                    "expected": f"等级应在 {power_levels} 中",
                    "severity": 0.9,
                    "suggestion": f"请将等级修改为有效的等级之一",
                    "auto_fixable": False
                }
        
        return {"valid": True}
    
    def _eval_magic_capability(self, fact: FactAssertion, rule_predicate: LogicPredicate) -> Dict[str, Any]:
        """评估魔法能力约束"""
        # 检查魔法等级与施法能力的匹配
        if fact.predicate.name == "cast_spell":
            character = fact.predicate.arguments[0] if fact.predicate.arguments else None
            spell = fact.predicate.arguments[1] if len(fact.predicate.arguments) > 1 else None
            
            # 查找角色的魔法等级
            char_magic_level = None
            for f in self.facts.values():
                if f.predicate.name == "magic_level" and f.predicate.arguments[0] == character:
                    char_magic_level = f.predicate.arguments[1] if len(f.predicate.arguments) > 1 else None
                    break
            
            if char_magic_level and spell:
                # 简化的魔法等级检查
                magic_tiers = ["学徒", "法师", "大法师", "传奇法师"]
                spell_tiers = ["初级", "中级", "高级", "禁咒"]
                
                char_tier = magic_tiers.index(char_magic_level) if char_magic_level in magic_tiers else -1
                
                # 检查法术等级是否超过角色能力
                if "禁咒" in spell and char_tier < 3:
                    return {
                        "valid": False,
                        "expected": f"角色 {character} 的魔法等级为 {char_magic_level}，无法施放禁咒",
                        "severity": 1.0,
                        "suggestion": f"请将法术改为 {character} 能力范围内的法术，或提升角色等级",
                        "auto_fixable": False
                    }
        
        return {"valid": True}
    
    def _eval_time_consistency(self, fact: FactAssertion, rule_predicate: LogicPredicate) -> Dict[str, Any]:
        """评估时间一致性"""
        if fact.predicate.name == "event_time":
            event = fact.predicate.arguments[0] if fact.predicate.arguments else None
            time_str = fact.predicate.arguments[1] if len(fact.predicate.arguments) > 1 else None
            
            # 检查时间线冲突
            for f in self.facts.values():
                if f.predicate.name == "event_time" and f.predicate.arguments[0] == event:
                    existing_time = f.predicate.arguments[1] if len(f.predicate.arguments) > 1 else None
                    if existing_time and existing_time != time_str:
                        return {
                            "valid": False,
                            "expected": f"事件 {event} 的时间应为 {existing_time}",
                            "severity": 0.95,
                            "suggestion": f"请统一事件 {event} 的时间设定",
                            "auto_fixable": True
                        }
        
        return {"valid": True}
    
    def _eval_spatial_consistency(self, fact: FactAssertion, rule_predicate: LogicPredicate) -> Dict[str, Any]:
        """评估空间一致性"""
        if fact.predicate.name == "character_location":
            character = fact.predicate.arguments[0] if fact.predicate.arguments else None
            location = fact.predicate.arguments[1] if len(fact.predicate.arguments) > 1 else None
            
            # 检查角色是否能在该位置
            # 查找角色的移动能力
            can_teleport = any(
                f.predicate.name == "has_ability" and 
                f.predicate.arguments[0] == character and
                "teleport" in str(f.predicate.arguments[1])
                for f in self.facts.values()
            )
            
            # 查找角色之前的位置
            prev_location = None
            for f in self.facts.values():
                if f.predicate.name == "character_location" and f.predicate.arguments[0] == character:
                    prev_location = f.predicate.arguments[1] if len(f.predicate.arguments) > 1 else None
            
            # 简化的距离检查（实际应该使用地图数据）
            if prev_location and location and prev_location != location and not can_teleport:
                # 假设位置变化需要合理时间
                return {
                    "valid": True,  # 暂时允许，但记录警告
                    "warning": f"角色 {character} 从 {prev_location} 移动到 {location}，请确保移动合理"
                }
        
        return {"valid": True}
    
    def _eval_social_status(self, fact: FactAssertion, rule_predicate: LogicPredicate) -> Dict[str, Any]:
        """评估社会地位一致性"""
        if fact.predicate.name == "social_interaction":
            character1 = fact.predicate.arguments[0] if fact.predicate.arguments else None
            character2 = fact.predicate.arguments[1] if len(fact.predicate.arguments) > 1 else None
            interaction = fact.predicate.arguments[2] if len(fact.predicate.arguments) > 2 else None
            
            # 查找社会地位
            status1 = None
            status2 = None
            
            for f in self.facts.values():
                if f.predicate.name == "social_status":
                    if f.predicate.arguments[0] == character1:
                        status1 = f.predicate.arguments[1] if len(f.predicate.arguments) > 1 else None
                    if f.predicate.arguments[0] == character2:
                        status2 = f.predicate.arguments[1] if len(f.predicate.arguments) > 1 else None
            
            # 检查尊卑礼仪
            if status1 and status2 and interaction:
                hierarchy = ["平民", "贵族", "王族", "皇帝"]
                idx1 = hierarchy.index(status1) if status1 in hierarchy else -1
                idx2 = hierarchy.index(status2) if status2 in hierarchy else -1
                
                if idx1 < idx2 and interaction in ["命令", "呵斥", "威胁"]:
                    return {
                        "valid": False,
                        "expected": f"{status1} 不应该对 {status2} 使用 {interaction}",
                        "severity": 0.7,
                        "suggestion": f"请调整 {character1} 对 {character2} 的态度，符合社会等级规范",
                        "auto_fixable": False
                    }
        
        return {"valid": True}
    
    def validate_chapter_content(
        self,
        chapter_content: str,
        chapter_id: str
    ) -> Dict[str, Any]:
        """
        验证章节内容
        
        解析章节中的事实断言并验证
        """
        # 解析内容中的事实（简化版本）
        extracted_facts = self._extract_facts_from_text(chapter_content, chapter_id)
        
        violations = []
        accepted_facts = []
        
        for fact in extracted_facts:
            if self.assert_fact(fact):
                accepted_facts.append(fact)
            else:
                # 获取本次断言产生的违规
                new_violations = [v for v in self.violations if v.chapter_location == chapter_id]
                violations.extend(new_violations)
        
        return {
            "chapter_id": chapter_id,
            "extracted_facts": len(extracted_facts),
            "accepted_facts": len(accepted_facts),
            "violations": [self._violation_to_dict(v) for v in violations],
            "is_valid": len(violations) == 0,
            "severity_score": max([v.severity for v in violations]) if violations else 0
        }
    
    def _extract_facts_from_text(
        self,
        text: str,
        chapter_id: str
    ) -> List[FactAssertion]:
        """从文本中提取事实（简化版本）"""
        facts = []
        
        # 简单的模式匹配提取事实
        # 角色等级变化
        level_patterns = [
            r'([\u4e00-\u9fa5]{2,4})[^。]*突破[^。]*到[^。]*([\u4e00-\u9fa5]+)',
            r'([\u4e00-\u9fa5]{2,4})[^。]*晋升[^。]*为[^。]*([\u4e00-\u9fa5]+)',
        ]
        
        for pattern in level_patterns:
            for match in re.finditer(pattern, text):
                character = match.group(1)
                new_level = match.group(2)
                
                fact = FactAssertion(
                    fact_id=f"fact_{datetime.now().timestamp()}_{len(facts)}",
                    predicate=LogicPredicate(
                        name="power_level",
                        arguments=[character, new_level]
                    ),
                    source=chapter_id
                )
                facts.append(fact)
        
        # 施法行为
        spell_pattern = r'([\u4e00-\u9fa5]{2,4})[^。]*施展[^。]*([\u4e00-\u9fa5]+)'
        for match in re.finditer(spell_pattern, text):
            character = match.group(1)
            spell = match.group(2)
            
            fact = FactAssertion(
                fact_id=f"fact_{datetime.now().timestamp()}_{len(facts)}",
                predicate=LogicPredicate(
                    name="cast_spell",
                    arguments=[character, spell]
                ),
                source=chapter_id
            )
            facts.append(fact)
        
        return facts
    
    def _violation_to_dict(self, violation: LogicViolation) -> Dict[str, Any]:
        """将违规转换为字典"""
        return {
            "violation_id": violation.violation_id,
            "rule_name": violation.rule_name,
            "predicate": violation.violated_predicate.to_string(),
            "actual_value": violation.actual_value,
            "expected_value": violation.expected_value,
            "severity": violation.severity,
            "suggested_fix": violation.suggested_fix,
            "auto_fixable": violation.auto_fixable
        }
    
    def get_world_consistency_report(self) -> Dict[str, Any]:
        """获取世界观一致性报告"""
        return {
            "total_rules": len(self.rules),
            "enabled_rules": sum(1 for r in self.rules.values() if r.enabled),
            "total_facts": len(self.facts),
            "total_violations": len(self.violations),
            "unresolved_violations": len([v for v in self.violations]),
            "rules_by_type": {
                rt.value: len(ids) for rt, ids in self.rules_by_type.items()
            },
            "recent_violations": [
                self._violation_to_dict(v)
                for v in self.violations[-10:]  # 最近10个
            ]
        }


# 全局实例
_logic_engine: Optional[SymbolicLogicEngine] = None


def get_symbolic_logic_engine() -> SymbolicLogicEngine:
    """获取符号逻辑引擎实例"""
    global _logic_engine
    if _logic_engine is None:
        _logic_engine = SymbolicLogicEngine()
    return _logic_engine
