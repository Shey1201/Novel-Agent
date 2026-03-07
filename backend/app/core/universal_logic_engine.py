"""
Universal Logic Engine - 通用符号逻辑引擎
支持所有类型文章的逻辑约束验证
"""

from typing import Dict, Any, Optional, List, Tuple, Callable, Union
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
    EXISTS = "exists"
    FORALL = "forall"


class RuleCategory(Enum):
    """规则类别 - 通用分类"""
    CHARACTER = "character"           # 角色规则
    RELATIONSHIP = "relationship"     # 关系规则
    TIMELINE = "timeline"             # 时间线规则
    CAUSALITY = "causality"           # 因果规则
    SETTING = "setting"               # 设定规则
    PLOT_STRUCTURE = "plot_structure" # 剧情结构规则
    THEME = "theme"                   # 主题规则


class GenreType(Enum):
    """小说类型"""
    FANTASY = "fantasy"               # 奇幻
    SCI_FI = "sci_fi"                # 科幻
    MYSTERY = "mystery"              # 悬疑
    ROMANCE = "romance"              # 言情
    HISTORICAL = "historical"        # 历史
    MODERN = "modern"                # 现代
    WUXIA = "wuxia"                  # 武侠
    HORROR = "horror"                # 恐怖
    GENERAL = "general"              # 通用


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
class UniversalRule:
    """通用规则"""
    rule_id: str
    category: RuleCategory
    genre: GenreType
    name: str
    description: str
    predicates: List[LogicPredicate]
    constraints: List[str]
    applicable_genres: List[GenreType] = field(default_factory=list)
    exceptions: List[str] = field(default_factory=list)
    priority: int = 5
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "category": self.category.value,
            "genre": self.genre.value,
            "name": self.name,
            "description": self.description,
            "predicates": [p.to_string() for p in self.predicates],
            "constraints": self.constraints,
            "applicable_genres": [g.value for g in self.applicable_genres],
            "priority": self.priority,
            "enabled": self.enabled
        }


@dataclass
class LogicViolation:
    """逻辑违规"""
    violation_id: str
    rule_id: str
    rule_name: str
    category: RuleCategory
    violated_predicate: LogicPredicate
    actual_value: Any
    expected_value: Any
    severity: float
    chapter_location: str
    suggested_fix: str
    auto_fixable: bool = False


@dataclass
class FactAssertion:
    """事实断言"""
    fact_id: str
    predicate: LogicPredicate
    source: str
    confidence: float = 1.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class RuleTemplateLibrary:
    """
    规则模板库
    
    提供各种类型小说的通用规则模板
    """
    
    @staticmethod
    def create_character_consistency_rule() -> UniversalRule:
        """角色一致性规则 - 适用于所有类型"""
        return UniversalRule(
            rule_id="rule_character_consistency",
            category=RuleCategory.CHARACTER,
            genre=GenreType.GENERAL,
            name="角色属性一致性",
            description="角色的基本属性（姓名、年龄、身份）在整部作品中应保持一致",
            predicates=[
                LogicPredicate(
                    name="character_attribute",
                    arguments=["character_id", "attribute_name", "value"]
                )
            ],
            constraints=[
                "forall C, A, V1, V2: character_attribute(C, A, V1) and character_attribute(C, A, V2) implies V1 = V2"
            ],
            applicable_genres=[GenreType.GENERAL],
            priority=10
        )
    
    @staticmethod
    def create_timeline_consistency_rule() -> UniversalRule:
        """时间线一致性规则 - 适用于所有类型"""
        return UniversalRule(
            rule_id="rule_timeline_consistency",
            category=RuleCategory.TIMELINE,
            genre=GenreType.GENERAL,
            name="时间线一致性",
            description="事件的时间顺序应合理，不能出现时间倒流",
            predicates=[
                LogicPredicate(
                    name="event_time",
                    arguments=["event_id", "timestamp"]
                ),
                LogicPredicate(
                    name="event_order",
                    arguments=["event1", "event2"]
                )
            ],
            constraints=[
                "event_time(E1, T1) and event_time(E2, T2) and event_order(E1, E2) implies T1 < T2",
                "event_time(E1, T1) and event_time(E2, T2) and causal_link(E1, E2) implies T1 < T2"
            ],
            applicable_genres=[GenreType.GENERAL],
            priority=10
        )
    
    @staticmethod
    def create_causality_rule() -> UniversalRule:
        """因果一致性规则 - 适用于所有类型"""
        return UniversalRule(
            rule_id="rule_causality",
            category=RuleCategory.CAUSALITY,
            genre=GenreType.GENERAL,
            name="因果逻辑一致性",
            description="原因必须在结果之前，结果必须由原因导致",
            predicates=[
                LogicPredicate(
                    name="causal_link",
                    arguments=["cause_event", "effect_event"]
                ),
                LogicPredicate(
                    name="event_status",
                    arguments=["event_id", "status"]
                )
            ],
            constraints=[
                "causal_link(C, E) implies event_status(C, 'completed') before event_status(E, 'completed')",
                "event_status(E, 'completed') and causal_link(C, E) implies event_status(C, 'completed')"
            ],
            applicable_genres=[GenreType.GENERAL],
            priority=9
        )
    
    @staticmethod
    def create_relationship_consistency_rule() -> UniversalRule:
        """关系一致性规则 - 适用于所有类型"""
        return UniversalRule(
            rule_id="rule_relationship_consistency",
            category=RuleCategory.RELATIONSHIP,
            genre=GenreType.GENERAL,
            name="人物关系一致性",
            description="人物之间的关系应保持逻辑一致",
            predicates=[
                LogicPredicate(
                    name="relationship",
                    arguments=["character1", "character2", "relation_type"]
                )
            ],
            constraints=[
                "relationship(A, B, 'parent') implies relationship(B, A, 'child')",
                "relationship(A, B, 'enemy') and relationship(B, C, 'enemy') does_not_imply relationship(A, C, 'friend')",
                "relationship(A, B, 'married') implies relationship(B, A, 'married')"
            ],
            applicable_genres=[GenreType.GENERAL],
            priority=8
        )
    
    @staticmethod
    def create_setting_consistency_rule(genre: GenreType) -> UniversalRule:
        """设定一致性规则 - 根据类型定制"""
        
        genre_specific_constraints = {
            GenreType.FANTASY: [
                "magic_system_defined implies consistent_magic_rules",
                "power_level_system implies no_sudden_unexplained_powerups"
            ],
            GenreType.SCI_FI: [
                "technology_level implies consistent_tech_capabilities",
                "physical_laws implies no_violation_without_explanation"
            ],
            GenreType.MYSTERY: [
                "clue_placement implies fair_play_rules",
                "revelation implies prior_foreshadowing"
            ],
            GenreType.ROMANCE: [
                "relationship_development implies consistent_emotional_arc",
                "character_growth implies gradual_change"
            ],
            GenreType.HISTORICAL: [
                "historical_events implies accuracy_to_recorded_history",
                "social_customs implies period_authenticity"
            ],
            GenreType.GENERAL: [
                "world_rules_defined implies consistent_application",
                "social_structure implies logical_behavior"
            ]
        }
        
        constraints = genre_specific_constraints.get(genre, genre_specific_constraints[GenreType.GENERAL])
        
        return UniversalRule(
            rule_id=f"rule_setting_consistency_{genre.value}",
            category=RuleCategory.SETTING,
            genre=genre,
            name=f"{genre.value}设定一致性",
            description=f"确保{genre.value}类型小说的设定在整部作品中保持一致",
            predicates=[
                LogicPredicate(
                    name="setting_attribute",
                    arguments=["attribute_name", "value"]
                )
            ],
            constraints=constraints,
            applicable_genres=[genre, GenreType.GENERAL],
            priority=9
        )
    
    @staticmethod
    def create_plot_structure_rule() -> UniversalRule:
        """剧情结构规则 - 适用于所有类型"""
        return UniversalRule(
            rule_id="rule_plot_structure",
            category=RuleCategory.PLOT_STRUCTURE,
            genre=GenreType.GENERAL,
            name="剧情结构合理性",
            description="剧情发展应符合基本叙事结构",
            predicates=[
                LogicPredicate(
                    name="plot_point",
                    arguments=["point_id", "type", "chapter"]
                ),
                LogicPredicate(
                    name="plot_arc",
                    arguments=["arc_id", "status"]
                )
            ],
            constraints=[
                "plot_point(P, 'inciting_incident', C) implies C > 0",
                "plot_point(P, 'climax', C1) and plot_point(Q, 'resolution', C2) implies C1 < C2",
                "foreshadowing(F, C1) and payoff(F, C2) implies C1 < C2"
            ],
            applicable_genres=[GenreType.GENERAL],
            priority=7
        )
    
    @staticmethod
    def create_theme_consistency_rule() -> UniversalRule:
        """主题一致性规则 - 适用于所有类型"""
        return UniversalRule(
            rule_id="rule_theme_consistency",
            category=RuleCategory.THEME,
            genre=GenreType.GENERAL,
            name="主题一致性",
            description="作品主题应在整部作品中保持一致，避免主题混乱",
            predicates=[
                LogicPredicate(
                    name="theme_element",
                    arguments=["theme_name", "chapter", "manifestation"]
                )
            ],
            constraints=[
                "theme_element(T, C1, M1) and theme_element(T, C2, M2) implies consistent_manifestation(M1, M2)",
                "central_theme(T) implies exists C: theme_element(T, C, _)"
            ],
            applicable_genres=[GenreType.GENERAL],
            priority=6
        )


class UniversalLogicEngine:
    """
    通用符号逻辑引擎
    
    支持所有类型小说的逻辑约束验证
    """
    
    def __init__(self, genre: GenreType = GenreType.GENERAL):
        self.genre = genre
        self.rules: Dict[str, UniversalRule] = {}
        self.facts: Dict[str, FactAssertion] = {}
        self.violations: List[LogicViolation] = []
        
        # 规则索引
        self.rules_by_category: Dict[RuleCategory, List[str]] = {
            cat: [] for cat in RuleCategory
        }
        
        # 初始化通用规则
        self._initialize_universal_rules()
        
        # 谓词求值器
        self.evaluators: Dict[str, Callable] = self._initialize_evaluators()
    
    def _initialize_universal_rules(self):
        """初始化通用规则"""
        library = RuleTemplateLibrary()
        
        # 添加所有通用规则
        universal_rules = [
            library.create_character_consistency_rule(),
            library.create_timeline_consistency_rule(),
            library.create_causality_rule(),
            library.create_relationship_consistency_rule(),
            library.create_setting_consistency_rule(self.genre),
            library.create_plot_structure_rule(),
            library.create_theme_consistency_rule()
        ]
        
        for rule in universal_rules:
            self.add_rule(rule)
    
    def _initialize_evaluators(self) -> Dict[str, Callable]:
        """初始化谓词求值器"""
        return {
            "character_attribute": self._eval_character_attribute,
            "event_time": self._eval_event_time,
            "causal_link": self._eval_causal_link,
            "relationship": self._eval_relationship,
            "setting_attribute": self._eval_setting_attribute,
            "plot_point": self._eval_plot_point,
            "theme_element": self._eval_theme_element
        }
    
    def add_rule(self, rule: UniversalRule) -> str:
        """添加规则"""
        self.rules[rule.rule_id] = rule
        self.rules_by_category[rule.category].append(rule.rule_id)
        return rule.rule_id
    
    def assert_fact(self, fact: FactAssertion) -> Tuple[bool, List[LogicViolation]]:
        """
        断言事实
        
        Returns:
            (是否成功, 违规列表)
        """
        violations = self._validate_fact(fact)
        
        if violations and any(v.severity > 0.8 for v in violations):
            # 严重违规，拒绝添加
            return False, violations
        
        # 添加事实
        self.facts[fact.fact_id] = fact
        
        return True, violations
    
    def _validate_fact(self, fact: FactAssertion) -> List[LogicViolation]:
        """验证事实"""
        violations = []
        
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
                violation = self._check_constraint(fact, rule, rule_predicate)
                if violation:
                    violations.append(violation)
        
        return violations
    
    def _check_constraint(
        self,
        fact: FactAssertion,
        rule: UniversalRule,
        rule_predicate: LogicPredicate
    ) -> Optional[LogicViolation]:
        """检查约束"""
        evaluator = self.evaluators.get(fact.predicate.name)
        
        if evaluator:
            result = evaluator(fact, rule_predicate, rule)
            if not result.get("valid", True):
                return LogicViolation(
                    violation_id=f"viol_{datetime.now().timestamp()}",
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    category=rule.category,
                    violated_predicate=rule_predicate,
                    actual_value=fact.predicate.value,
                    expected_value=result.get("expected"),
                    severity=result.get("severity", 0.5),
                    chapter_location=fact.source,
                    suggested_fix=result.get("suggestion", "请检查逻辑一致性"),
                    auto_fixable=result.get("auto_fixable", False)
                )
        
        return None
    
    def _eval_character_attribute(
        self,
        fact: FactAssertion,
        rule_predicate: LogicPredicate,
        rule: UniversalRule
    ) -> Dict[str, Any]:
        """评估角色属性"""
        character_id = fact.predicate.arguments[0] if fact.predicate.arguments else None
        attribute_name = fact.predicate.arguments[1] if len(fact.predicate.arguments) > 1 else None
        new_value = fact.predicate.arguments[2] if len(fact.predicate.arguments) > 2 else None
        
        # 检查是否已有该属性的记录
        for fact_id, existing_fact in self.facts.items():
            if (existing_fact.predicate.name == "character_attribute" and
                existing_fact.predicate.arguments[0] == character_id and
                existing_fact.predicate.arguments[1] == attribute_name):
                
                old_value = existing_fact.predicate.arguments[2] if len(existing_fact.predicate.arguments) > 2 else None
                
                if old_value != new_value:
                    return {
                        "valid": False,
                        "expected": f"{attribute_name}应保持为'{old_value}'",
                        "severity": 0.9,
                        "suggestion": f"角色{character_id}的{attribute_name}从'{old_value}'变为'{new_value}'，请确认是否为剧情需要的变化",
                        "auto_fixable": False
                    }
        
        return {"valid": True}
    
    def _eval_event_time(
        self,
        fact: FactAssertion,
        rule_predicate: LogicPredicate,
        rule: UniversalRule
    ) -> Dict[str, Any]:
        """评估事件时间"""
        event_id = fact.predicate.arguments[0] if fact.predicate.arguments else None
        new_time = fact.predicate.arguments[1] if len(fact.predicate.arguments) > 1 else None
        
        # 检查时间冲突
        for fact_id, existing_fact in self.facts.items():
            if (existing_fact.predicate.name == "event_time" and
                existing_fact.predicate.arguments[0] == event_id):
                
                old_time = existing_fact.predicate.arguments[1] if len(existing_fact.predicate.arguments) > 1 else None
                
                if old_time != new_time:
                    return {
                        "valid": False,
                        "expected": f"事件时间应为'{old_time}'",
                        "severity": 0.95,
                        "suggestion": f"事件'{event_id}'的时间从'{old_time}'变为'{new_time}'，请统一时间设定",
                        "auto_fixable": True
                    }
        
        return {"valid": True}
    
    def _eval_causal_link(
        self,
        fact: FactAssertion,
        rule_predicate: LogicPredicate,
        rule: UniversalRule
    ) -> Dict[str, Any]:
        """评估因果链接"""
        cause_event = fact.predicate.arguments[0] if fact.predicate.arguments else None
        effect_event = fact.predicate.arguments[1] if len(fact.predicate.arguments) > 1 else None
        
        # 检查原因和结果的时间顺序
        cause_time = None
        effect_time = None
        
        for fact_id, existing_fact in self.facts.items():
            if existing_fact.predicate.name == "event_time":
                if existing_fact.predicate.arguments[0] == cause_event:
                    cause_time = existing_fact.predicate.arguments[1] if len(existing_fact.predicate.arguments) > 1 else None
                if existing_fact.predicate.arguments[0] == effect_event:
                    effect_time = existing_fact.predicate.arguments[1] if len(existing_fact.predicate.arguments) > 1 else None
        
        if cause_time and effect_time:
            # 简化的字符串比较（实际应该解析时间）
            if str(cause_time) > str(effect_time):
                return {
                    "valid": False,
                    "expected": f"原因'{cause_event}'应在结果'{effect_event}'之前",
                    "severity": 1.0,
                    "suggestion": f"因果逻辑错误：'{effect_event}'发生在'{cause_event}'之前，请调整时间顺序",
                    "auto_fixable": False
                }
        
        return {"valid": True}
    
    def _eval_relationship(
        self,
        fact: FactAssertion,
        rule_predicate: LogicPredicate,
        rule: UniversalRule
    ) -> Dict[str, Any]:
        """评估关系"""
        char1 = fact.predicate.arguments[0] if fact.predicate.arguments else None
        char2 = fact.predicate.arguments[1] if len(fact.predicate.arguments) > 1 else None
        relation = fact.predicate.arguments[2] if len(fact.predicate.arguments) > 2 else None
        
        # 检查关系对称性
        if relation in ["married", "sibling", "friend", "enemy"]:
            # 这些关系应该是对称的
            for fact_id, existing_fact in self.facts.items():
                if (existing_fact.predicate.name == "relationship" and
                    existing_fact.predicate.arguments[0] == char2 and
                    existing_fact.predicate.arguments[1] == char1):
                    
                    existing_relation = existing_fact.predicate.arguments[2] if len(existing_fact.predicate.arguments) > 2 else None
                    
                    # 检查关系是否一致
                    relation_pairs = {
                        "parent": "child",
                        "child": "parent",
                        "teacher": "student",
                        "student": "teacher"
                    }
                    
                    if relation != existing_relation:
                        if relation not in relation_pairs or relation_pairs[relation] != existing_relation:
                            return {
                                "valid": False,
                                "expected": f"{char2}对{char1}的关系应为'{relation}'",
                                "severity": 0.7,
                                "suggestion": f"关系不一致：{char1}视{char2}为'{relation}'，但{char2}视{char1}为'{existing_relation}'",
                                "auto_fixable": False
                            }
        
        return {"valid": True}
    
    def _eval_setting_attribute(
        self,
        fact: FactAssertion,
        rule_predicate: LogicPredicate,
        rule: UniversalRule
    ) -> Dict[str, Any]:
        """评估设定属性"""
        attribute = fact.predicate.arguments[0] if fact.predicate.arguments else None
        new_value = fact.predicate.arguments[1] if len(fact.predicate.arguments) > 1 else None
        
        # 检查设定一致性
        for fact_id, existing_fact in self.facts.items():
            if (existing_fact.predicate.name == "setting_attribute" and
                existing_fact.predicate.arguments[0] == attribute):
                
                old_value = existing_fact.predicate.arguments[1] if len(existing_fact.predicate.arguments) > 1 else None
                
                if old_value != new_value:
                    return {
                        "valid": False,
                        "expected": f"设定'{attribute}'应保持为'{old_value}'",
                        "severity": 0.85,
                        "suggestion": f"世界设定'{attribute}'从'{old_value}'变为'{new_value}'，请确认是否为剧情需要的变化",
                        "auto_fixable": False
                    }
        
        return {"valid": True}
    
    def _eval_plot_point(
        self,
        fact: FactAssertion,
        rule_predicate: LogicPredicate,
        rule: UniversalRule
    ) -> Dict[str, Any]:
        """评估情节点"""
        point_type = fact.predicate.arguments[1] if len(fact.predicate.arguments) > 1 else None
        chapter = fact.predicate.arguments[2] if len(fact.predicate.arguments) > 2 else None
        
        # 检查剧情结构顺序
        plot_order = ["inciting_incident", "rising_action", "climax", "falling_action", "resolution"]
        
        if point_type in plot_order:
            point_index = plot_order.index(point_type)
            
            # 检查之前的剧情点是否已出现
            for prev_type in plot_order[:point_index]:
                found = any(
                    f.predicate.name == "plot_point" and
                    f.predicate.arguments[1] == prev_type
                    for f in self.facts.values()
                )
                
                if not found:
                    return {
                        "valid": True,  # 只是警告
                        "warning": f"在'{point_type}'之前应该有'{prev_type}'",
                        "suggestion": f"建议先安排'{prev_type}'，再安排'{point_type}'"
                    }
        
        return {"valid": True}
    
    def _eval_theme_element(
        self,
        fact: FactAssertion,
        rule_predicate: LogicPredicate,
        rule: UniversalRule
    ) -> Dict[str, Any]:
        """评估主题元素"""
        theme = fact.predicate.arguments[0] if fact.predicate.arguments else None
        manifestation = fact.predicate.arguments[2] if len(fact.predicate.arguments) > 2 else None
        
        # 检查主题一致性
        for fact_id, existing_fact in self.facts.items():
            if (existing_fact.predicate.name == "theme_element" and
                existing_fact.predicate.arguments[0] == theme):
                
                existing_manifestation = existing_fact.predicate.arguments[2] if len(existing_fact.predicate.arguments) > 2 else None
                
                # 检查主题表现是否矛盾
                contradictory_pairs = [
                    ("love", "hate"),
                    ("justice", "injustice"),
                    ("hope", "despair")
                ]
                
                for pos, neg in contradictory_pairs:
                    if (pos in str(existing_manifestation).lower() and neg in str(manifestation).lower()) or \
                       (neg in str(existing_manifestation).lower() and pos in str(manifestation).lower()):
                        return {
                            "valid": False,
                            "expected": f"主题'{theme}'的表现应一致",
                            "severity": 0.6,
                            "suggestion": f"主题表现矛盾：之前是'{existing_manifestation}'，现在是'{manifestation}'",
                            "auto_fixable": False
                        }
        
        return {"valid": True}
    
    def validate_content(
        self,
        content: str,
        content_id: str,
        extract_facts: bool = True
    ) -> Dict[str, Any]:
        """验证内容"""
        if extract_facts:
            extracted_facts = self._extract_facts_from_content(content, content_id)
        else:
            extracted_facts = []
        
        violations = []
        accepted_facts = []
        
        for fact in extracted_facts:
            success, fact_violations = self.assert_fact(fact)
            if success:
                accepted_facts.append(fact)
            violations.extend(fact_violations)
        
        return {
            "content_id": content_id,
            "extracted_facts": len(extracted_facts),
            "accepted_facts": len(accepted_facts),
            "violations": [self._violation_to_dict(v) for v in violations],
            "is_valid": len([v for v in violations if v.severity > 0.8]) == 0,
            "severity_score": max([v.severity for v in violations]) if violations else 0
        }
    
    def _extract_facts_from_content(
        self,
        content: str,
        content_id: str
    ) -> List[FactAssertion]:
        """从内容中提取事实"""
        facts = []
        
        # 角色属性变化
        patterns = [
            (r'([\u4e00-\u9fa5]{2,4})[^。]*年龄[^。]*([0-9]+)', "character_attribute", [1, "年龄", 2]),
            (r'([\u4e00-\u9fa5]{2,4})[^。]*身份[^。]*是[^。]*([\u4e00-\u9fa5]+)', "character_attribute", [1, "身份", 2]),
            (r'([\u4e00-\u9fa5]{2,4})[^。]*职业[^。]*是[^。]*([\u4e00-\u9fa5]+)', "character_attribute", [1, "职业", 2]),
        ]
        
        for pattern, pred_name, arg_indices in patterns:
            for match in re.finditer(pattern, content):
                args = [match.group(i) for i in arg_indices]
                
                fact = FactAssertion(
                    fact_id=f"fact_{datetime.now().timestamp()}_{len(facts)}",
                    predicate=LogicPredicate(
                        name=pred_name,
                        arguments=args
                    ),
                    source=content_id
                )
                facts.append(fact)
        
        return facts
    
    def _violation_to_dict(self, violation: LogicViolation) -> Dict[str, Any]:
        """转换违规为字典"""
        return {
            "violation_id": violation.violation_id,
            "rule_name": violation.rule_name,
            "category": violation.category.value,
            "predicate": violation.violated_predicate.to_string(),
            "actual_value": violation.actual_value,
            "expected_value": violation.expected_value,
            "severity": violation.severity,
            "suggested_fix": violation.suggested_fix,
            "auto_fixable": violation.auto_fixable
        }
    
    def get_consistency_report(self) -> Dict[str, Any]:
        """获取一致性报告"""
        return {
            "genre": self.genre.value,
            "total_rules": len(self.rules),
            "enabled_rules": sum(1 for r in self.rules.values() if r.enabled),
            "total_facts": len(self.facts),
            "total_violations": len(self.violations),
            "rules_by_category": {
                cat.value: len(ids) for cat, ids in self.rules_by_category.items()
            },
            "recent_violations": [
                self._violation_to_dict(v)
                for v in self.violations[-10:]
            ]
        }


# 全局实例
_logic_engines: Dict[GenreType, UniversalLogicEngine] = {}


def get_universal_logic_engine(genre: GenreType = GenreType.GENERAL) -> UniversalLogicEngine:
    """获取通用逻辑引擎实例"""
    global _logic_engines
    if genre not in _logic_engines:
        _logic_engines[genre] = UniversalLogicEngine(genre)
    return _logic_engines[genre]
