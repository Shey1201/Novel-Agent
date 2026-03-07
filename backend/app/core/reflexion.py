"""
Reflexion System - 反思回滚机制
提供内容质量评估、问题识别和自动重写功能
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


class IssueSeverity(Enum):
    """问题严重程度"""
    CRITICAL = "critical"      # 严重问题，必须重写
    MAJOR = "major"            # 主要问题，建议重写
    MINOR = "minor"            # 轻微问题，可以局部修改
    TRIVIAL = "trivial"        # 微不足道，可忽略


class IssueType(Enum):
    """问题类型"""
    CHARACTER_INCONSISTENCY = "character_inconsistency"
    WORLD_INCONSISTENCY = "world_inconsistency"
    PLOT_LOGIC_ERROR = "plot_logic_error"
    TENSION_WEAK = "tension_weak"
    PROSE_QUALITY = "prose_quality"
    PACING_ISSUE = "pacing_issue"
    DIALOGUE_ISSUE = "dialogue_issue"
    CONTINUITY_ERROR = "continuity_error"


@dataclass
class Issue:
    """问题定义"""
    type: IssueType
    severity: IssueSeverity
    description: str
    location: Optional[str] = None  # 问题位置（段落/句子）
    suggestion: str = ""
    affected_sections: List[int] = field(default_factory=list)


@dataclass
class ReflexionResult:
    """反思结果"""
    original_text: str
    issues: List[Issue]
    needs_rewrite: bool
    rewrite_type: str  # "full", "partial", "none"
    rewritten_text: Optional[str] = None
    improvement_summary: str = ""


class IssueIdentifier:
    """
    问题识别器
    
    识别文本中的各种问题
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.1)
    
    async def identify_issues(
        self,
        text: str,
        context: Dict[str, Any],
        story_bible: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """
        识别文本中的问题
        
        Args:
            text: 待检查的文本
            context: 上下文信息（前文摘要、角色状态等）
            story_bible: Story Bible 设定
            
        Returns:
            问题列表
        """
        issues = []
        
        # 1. 使用 LLM 进行深度分析
        llm_issues = await self._llm_issue_analysis(text, context, story_bible)
        issues.extend(llm_issues)
        
        # 2. 规则基础检查
        rule_issues = self._rule_based_checks(text, context, story_bible)
        issues.extend(rule_issues)
        
        # 3. 排序：严重问题在前
        severity_order = {
            IssueSeverity.CRITICAL: 0,
            IssueSeverity.MAJOR: 1,
            IssueSeverity.MINOR: 2,
            IssueSeverity.TRIVIAL: 3
        }
        issues.sort(key=lambda x: severity_order.get(x.severity, 99))
        
        return issues
    
    async def _llm_issue_analysis(
        self,
        text: str,
        context: Dict[str, Any],
        story_bible: Optional[Dict[str, Any]]
    ) -> List[Issue]:
        """使用 LLM 分析问题"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位专业的小说编辑，负责检查文本质量。
请仔细分析提供的文本，识别以下类型的问题：

1. **角色设定不一致** - 角色行为与设定不符
2. **世界观冲突** - 违反已建立的规则
3. **情节逻辑错误** - 时间线、因果关系问题
4. **冲突张力不足** - 缺乏戏剧冲突
5. **文笔质量问题** - 表达不清、重复、单调
6. **节奏问题** - 过快、过慢、跳跃
7. **对话问题** - 不符合角色性格、过于直白
8. **连续性错误** - 与前文矛盾

对每个发现的问题，请提供：
- 问题类型
- 严重程度 (critical/major/minor/trivial)
- 具体描述
- 建议修改方案

以 JSON 格式返回结果。"""),
            ("human", """【Story Bible】
{story_bible}

【前文上下文】
{context}

【待检查文本】
{text}

请分析问题并以 JSON 格式返回：
{{
    "issues": [
        {{
            "type": "问题类型",
            "severity": "严重程度",
            "description": "具体描述",
            "location": "位置（如可能）",
            "suggestion": "修改建议"
        }}
    ]
}}""")
        ])
        
        chain = prompt | self.llm
        
        try:
            response = await chain.ainvoke({
                "text": text[:5000],  # 限制长度
                "context": json.dumps(context, ensure_ascii=False)[:2000],
                "story_bible": json.dumps(story_bible, ensure_ascii=False)[:2000] if story_bible else "无"
            })
            
            # 解析 JSON 响应
            content = response.content
            # 提取 JSON 部分
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content.strip())
            
            issues = []
            for issue_data in result.get("issues", []):
                try:
                    issue = Issue(
                        type=IssueType(issue_data.get("type", "prose_quality")),
                        severity=IssueSeverity(issue_data.get("severity", "minor")),
                        description=issue_data.get("description", ""),
                        location=issue_data.get("location"),
                        suggestion=issue_data.get("suggestion", "")
                    )
                    issues.append(issue)
                except (ValueError, KeyError):
                    continue
            
            return issues
        except Exception as e:
            print(f"LLM issue analysis error: {e}")
            return []
    
    def _rule_based_checks(
        self,
        text: str,
        context: Dict[str, Any],
        story_bible: Optional[Dict[str, Any]]
    ) -> List[Issue]:
        """基于规则的检查"""
        issues = []
        
        # 检查文本长度
        if len(text) < 100:
            issues.append(Issue(
                type=IssueType.PACING_ISSUE,
                severity=IssueSeverity.MINOR,
                description="文本过短，可能需要扩展",
                suggestion="增加细节描写或对话"
            ))
        
        # 检查重复词汇
        words = text.split()
        if len(words) > 50:
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1
            
            repeated = [w for w, c in word_counts.items() if c > len(words) * 0.1]
            if len(repeated) > 3:
                issues.append(Issue(
                    type=IssueType.PROSE_QUALITY,
                    severity=IssueSeverity.MINOR,
                    description=f"检测到过多重复词汇: {', '.join(repeated[:3])}",
                    suggestion="使用同义词替换，增加词汇多样性"
                ))
        
        # 检查对话比例
        dialogue_count = text.count('"') + text.count('"') + text.count('"')
        if len(text) > 200 and dialogue_count < 2:
            issues.append(Issue(
                type=IssueType.DIALOGUE_ISSUE,
                severity=IssueSeverity.TRIVIAL,
                description="对话较少，可能影响节奏",
                suggestion="适当添加对话来展现角色性格"
            ))
        
        return issues


class ReflexionEngine:
    """
    反思引擎
    
    执行重写逻辑
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.7)
        self.issue_identifier = IssueIdentifier()
    
    async def evaluate_and_rewrite(
        self,
        text: str,
        context: Dict[str, Any],
        story_bible: Optional[Dict[str, Any]] = None,
        auto_rewrite: bool = True
    ) -> ReflexionResult:
        """
        评估并重写文本
        
        Args:
            text: 原始文本
            context: 上下文
            story_bible: Story Bible
            auto_rewrite: 是否自动重写
            
        Returns:
            反思结果
        """
        # 1. 识别问题
        issues = await self.issue_identifier.identify_issues(
            text, context, story_bible
        )
        
        # 2. 决定重写策略
        rewrite_type = self._determine_rewrite_strategy(issues)
        needs_rewrite = rewrite_type != "none"
        
        # 3. 执行重写
        rewritten_text = None
        improvement_summary = ""
        
        if needs_rewrite and auto_rewrite:
            if rewrite_type == "full":
                rewritten_text = await self._full_rewrite(
                    text, issues, context, story_bible
                )
            elif rewrite_type == "partial":
                rewritten_text = await self._partial_rewrite(
                    text, issues, context, story_bible
                )
            
            improvement_summary = self._generate_improvement_summary(issues)
        
        return ReflexionResult(
            original_text=text,
            issues=issues,
            needs_rewrite=needs_rewrite,
            rewrite_type=rewrite_type,
            rewritten_text=rewritten_text,
            improvement_summary=improvement_summary
        )
    
    def _determine_rewrite_strategy(self, issues: List[Issue]) -> str:
        """决定重写策略"""
        if not issues:
            return "none"
        
        # 检查是否有严重问题
        critical_count = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        major_count = sum(1 for i in issues if i.severity == IssueSeverity.MAJOR)
        
        if critical_count > 0:
            return "full"
        elif major_count > 2:
            return "full"
        elif major_count > 0 or len(issues) > 3:
            return "partial"
        else:
            return "minor"
    
    async def _full_rewrite(
        self,
        text: str,
        issues: List[Issue],
        context: Dict[str, Any],
        story_bible: Optional[Dict[str, Any]]
    ) -> str:
        """完全重写"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位专业的小说作家。请基于反馈完全重写这段文本。
保持原文的核心情节和意图，但解决所有指出的问题。"""),
            ("human", """【Story Bible】
{story_bible}

【前文上下文】
{context}

【需要解决的问题】
{issues}

【原文】
{text}

请重写这段文本，解决上述所有问题。保持情节连贯，增强表现力。""")
        ])
        
        chain = prompt | self.llm
        
        response = await chain.ainvoke({
            "text": text,
            "context": json.dumps(context, ensure_ascii=False),
            "story_bible": json.dumps(story_bible, ensure_ascii=False) if story_bible else "无",
            "issues": "\n".join([f"- {i.description} ({i.severity.value})" for i in issues])
        })
        
        return response.content
    
    async def _partial_rewrite(
        self,
        text: str,
        issues: List[Issue],
        context: Dict[str, Any],
        story_bible: Optional[Dict[str, Any]]
    ) -> str:
        """局部重写"""
        # 只处理主要问题
        major_issues = [i for i in issues if i.severity in (IssueSeverity.CRITICAL, IssueSeverity.MAJOR)]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位专业的小说编辑。请修改文本中的问题部分。
尽量保持原文不变，只修改有问题的段落或句子。"""),
            ("human", """【Story Bible】
{story_bible}

【需要解决的主要问题】
{issues}

【原文】
{text}

请修改文本，解决上述问题。只修改必要的部分，保持其他内容不变。""")
        ])
        
        chain = prompt | self.llm
        
        response = await chain.ainvoke({
            "text": text,
            "story_bible": json.dumps(story_bible, ensure_ascii=False) if story_bible else "无",
            "issues": "\n".join([f"- {i.description}" for i in major_issues])
        })
        
        return response.content
    
    def _generate_improvement_summary(self, issues: List[Issue]) -> str:
        """生成改进摘要"""
        if not issues:
            return "文本质量良好，无需修改。"
        
        critical = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        major = sum(1 for i in issues if i.severity == IssueSeverity.MAJOR)
        minor = sum(1 for i in issues if i.severity == IssueSeverity.MINOR)
        
        summary_parts = []
        if critical > 0:
            summary_parts.append(f"修复了 {critical} 个严重问题")
        if major > 0:
            summary_parts.append(f"改进了 {major} 个主要问题")
        if minor > 0:
            summary_parts.append(f"优化了 {minor} 个细节")
        
        return "。".join(summary_parts)


class QualityEvaluator:
    """
    质量评估器
    
    多维度评估文本质量
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0.1)
    
    async def evaluate(
        self,
        text: str,
        context: Dict[str, Any],
        story_bible: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        多维度质量评估
        
        Returns:
            {
                "total_score": float,
                "breakdown": {
                    "logic_consistency": float,
                    "plot_tension": float,
                    "prose_quality": float,
                    "character_voice": float,
                    "world_consistency": float
                },
                "feedback": str,
                "rewrite_needed": bool
            }
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一位专业的小说评论家。请对这段文本进行多维度评分。

评分维度（0-1分）：
1. **逻辑一致性** (logic_consistency): 情节逻辑是否通顺
2. **冲突张力** (plot_tension): 是否有足够的戏剧冲突
3. **文笔质量** (prose_quality): 语言表达是否流畅优美
4. **角色声音** (character_voice): 角色是否有独特个性
5. **世界观一致性** (world_consistency): 是否符合设定

以 JSON 格式返回评分和反馈。"""),
            ("human", """【Story Bible】
{story_bible}

【前文上下文】
{context}

【待评估文本】
{text}

请进行评分（0-1分）并提供反馈。""")
        ])
        
        chain = prompt | self.llm
        
        try:
            response = await chain.ainvoke({
                "text": text[:4000],
                "context": json.dumps(context, ensure_ascii=False)[:1500],
                "story_bible": json.dumps(story_bible, ensure_ascii=False)[:1500] if story_bible else "无"
            })
            
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content.strip())
            
            # 计算总分
            breakdown = result.get("breakdown", {})
            weights = {
                "logic_consistency": 0.3,
                "plot_tension": 0.25,
                "prose_quality": 0.2,
                "character_voice": 0.15,
                "world_consistency": 0.1
            }
            
            total_score = sum(
                breakdown.get(k, 0.5) * w for k, w in weights.items()
            )
            
            return {
                "total_score": round(total_score, 2),
                "breakdown": {k: round(v, 2) for k, v in breakdown.items()},
                "feedback": result.get("feedback", ""),
                "rewrite_needed": total_score < 0.6
            }
        except Exception as e:
            print(f"Quality evaluation error: {e}")
            return {
                "total_score": 0.5,
                "breakdown": {},
                "feedback": "评估失败",
                "rewrite_needed": False
            }


# 便捷函数
_reflexion_engine: Optional[ReflexionEngine] = None


def get_reflexion_engine() -> ReflexionEngine:
    """获取反思引擎实例"""
    global _reflexion_engine
    if _reflexion_engine is None:
        _reflexion_engine = ReflexionEngine()
    return _reflexion_engine


async def evaluate_text(
    text: str,
    context: Dict[str, Any],
    story_bible: Optional[Dict[str, Any]] = None
) -> ReflexionResult:
    """评估文本"""
    engine = get_reflexion_engine()
    return await engine.evaluate_and_rewrite(text, context, story_bible)


async def quick_evaluate(text: str) -> Dict[str, Any]:
    """快速评估"""
    evaluator = QualityEvaluator()
    return await evaluator.evaluate(text, {})
