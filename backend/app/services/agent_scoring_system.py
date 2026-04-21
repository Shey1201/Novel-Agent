"""
Agent 评分系统 - 参考 ColumnWriter 的评分机制

功能：
- 多维度评分（内容质量、结构逻辑、语言表达、格式规范）
- 评分阈值控制，低于阈值自动触发修改
- 支持多轮评审直到达标
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class Grade(Enum):
    """评分等级"""
    EXCELLENT = "A"
    GOOD = "B" 
    PASS = "C"
    FAIL = "D"


@dataclass
class ReviewScore:
    """评审分数"""
    total_score: int  # 总分 0-100
    grade: str  # 等级 A/B/C/D
    
    # 各维度分数
    content_quality: int  # 内容质量 0-40
    structure_logic: int  # 结构逻辑 0-30
    language_expression: int  # 语言表达 0-20
    format_norm: int  # 格式规范 0-10
    
    # 评审详情
    strengths: List[str]  # 优点
    weaknesses: List[str]  # 缺点
    suggestions: List[str]  # 改进建议
    
    # 判断
    needs_revision: bool  # 是否需要修改
    needs_rewrite: bool  # 是否需要重写


class AgentScoringSystem:
    """
    Agent 评分系统
    
    评分维度（参考 ColumnWriter）：
    - 内容质量: 40分 (内容准确性、完整性、深度)
    - 结构逻辑: 30分 (逻辑清晰、层次分明)
    - 语言表达: 20分 (表达流畅、风格一致)
    - 格式规范: 10分 (格式正确、标点规范)
    
    评分等级：
    - A (90-100): 优秀，无需修改
    - B (75-89): 良好，小修小补
    - C (60-74): 及格，需要修改
    - D (0-59): 不及格，需要重写
    """
    
    # 评分阈值配置
    APPROVAL_THRESHOLD = 75  # 通过阈值
    REVISION_THRESHOLD = 60  # 需要重写的阈值
    MAX_REVISIONS = 3  # 最大修改轮数
    
    # 各维度满分
    MAX_CONTENT_QUALITY = 40
    MAX_STRUCTURE_LOGIC = 30
    MAX_LANGUAGE_EXPRESSION = 20
    MAX_FORMAT_NORM = 10
    
    def __init__(self, llm=None):
        self.llm = llm
    
    def calculate_grade(self, score: int) -> str:
        """根据分数计算等级"""
        if score >= 90:
            return Grade.EXCELLENT.value
        elif score >= 75:
            return Grade.GOOD.value
        elif score >= 60:
            return Grade.PASS.value
        else:
            return Grade.FAIL.value
    
    def evaluate_content(
        self,
        content: str,
        agent_type: str = "writer",
        context: Dict[str, Any] = None,
    ) -> ReviewScore:
        """
        评估内容质量
        
        Args:
            content: 待评估的内容
            agent_type: Agent 类型
            context: 上下文信息
            
        Returns:
            ReviewScore: 评估结果
        """
        # 如果有 LLM，使用 AI 评估
        if self.llm:
            return self._ai_evaluate(content, agent_type, context)
        else:
            # 否则使用规则评估
            return self._rule_evaluate(content)
    
    def _ai_evaluate(
        self,
        content: str,
        agent_type: str,
        context: Dict[str, Any] = None,
    ) -> ReviewScore:
        """使用 AI 进行评估"""
        from langchain_core.messages import HumanMessage
        
        context_str = ""
        if context:
            context_str = f"\n## 上下文\n{context.get('outline', '')[:500]}"
        
        prompt = f"""你是一个专业的文章评审专家。请对以下内容进行多维度评分。

## 待评估内容
{content[:2000]}

{context_str}

## 评分维度
1. 内容质量 (0-40分): 内容准确性、完整性、深度
2. 结构逻辑 (0-30分): 逻辑清晰、层次分明
3. 语言表达 (0-20分): 表达流畅、风格一致
4. 格式规范 (0-10分): 格式正确、标点规范

## 输出格式（JSON，不要添加任何其他文本）
{{
  "content_quality": 35,
  "structure_logic": 25,
  "language_expression": 15,
  "format_norm": 8,
  "strengths": ["优点1", "优点2"],
  "weaknesses": ["缺点1", "缺点2"],
  "suggestions": ["建议1", "建议2"]
}}

请直接输出 JSON："""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result_text = response.content if hasattr(response, "content") else str(response)
            
            # 提取 JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                import json
                result = json.loads(json_match.group())
                
                total = (
                    result.get("content_quality", 0) +
                    result.get("structure_logic", 0) +
                    result.get("language_expression", 0) +
                    result.get("format_norm", 0)
                )
                
                return ReviewScore(
                    total_score=total,
                    grade=self.calculate_grade(total),
                    content_quality=result.get("content_quality", 0),
                    structure_logic=result.get("structure_logic", 0),
                    language_expression=result.get("language_expression", 0),
                    format_norm=result.get("format_norm", 0),
                    strengths=result.get("strengths", []),
                    weaknesses=result.get("weaknesses", []),
                    suggestions=result.get("suggestions", []),
                    needs_revision=total < self.APPROVAL_THRESHOLD,
                    needs_rewrite=total < self.REVISION_THRESHOLD,
                )
        except Exception as e:
            print(f"[Scoring] AI 评估失败: {e}")
        
        # 降级到规则评估
        return self._rule_evaluate(content)
    
    def _rule_evaluate(self, content: str) -> ReviewScore:
        """使用规则进行快速评估"""
        score = 50  # 默认分数
        weaknesses = []
        suggestions = []
        
        # 检查内容长度
        if len(content) < 100:
            score -= 10
            weaknesses.append("内容过短")
            suggestions.append("增加内容长度")
        elif len(content) > 5000:
            score -= 5
            weaknesses.append("内容过长")
        
        # 检查是否包含标点
        if "。" not in content and "，" not in content:
            score -= 5
            weaknesses.append("缺少标点符号")
        
        # 检查段落结构
        if "\n\n" not in content:
            score -= 5
            weaknesses.append("缺少段落分隔")
        
        # 检查是否有多余空格
        if "  " in content:
            score -= 3
            suggestions.append("清理多余空格")
        
        # 基础分
        score = max(0, min(100, score))
        
        return ReviewScore(
            total_score=score,
            grade=self.calculate_grade(score),
            content_quality=min(score * 0.4, 40),
            structure_logic=min(score * 0.3, 30),
            language_expression=min(score * 0.2, 20),
            format_norm=min(score * 0.1, 10),
            strengths=["内容存在"] if len(content) > 0 else [],
            weaknesses=weaknesses,
            suggestions=suggestions if suggestions else ["无"],
            needs_revision=score < self.APPROVAL_THRESHOLD,
            needs_rewrite=score < self.REVISION_THRESHOLD,
        )
    
    def check_and_score(
        self,
        content: str,
        agent_type: str = "writer",
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        检查并评分，返回结构化结果
        
        Returns:
            {{
                "passed": bool,  # 是否通过
                "score": int,  # 总分
                "grade": str,  # 等级
                "needs_revision": bool,  # 是否需要修改
                "needs_rewrite": bool,  # 是否需要重写
                "review_details": {{  # 评审详情
                    "content_quality": int,
                    "structure_logic": int,
                    "language_expression": int,
                    "format_norm": int,
                }},
                "strengths": List[str],
                "weaknesses": List[str],
                "suggestions": List[str],
            }}
        """
        result = self.evaluate_content(content, agent_type, context)
        
        return {
            "passed": result.total_score >= self.APPROVAL_THRESHOLD,
            "score": result.total_score,
            "grade": result.grade,
            "needs_revision": result.needs_revision,
            "needs_rewrite": result.needs_rewrite,
            "review_details": {
                "content_quality": result.content_quality,
                "structure_logic": result.structure_logic,
                "language_expression": result.language_expression,
                "format_norm": result.format_norm,
            },
            "strengths": result.strengths,
            "weaknesses": result.weaknesses,
            "suggestions": result.suggestions,
        }


# 全局实例
_scoring_system = None


def get_scoring_system(llm=None) -> AgentScoringSystem:
    """获取评分系统实例"""
    global _scoring_system
    if _scoring_system is None:
        _scoring_system = AgentScoringSystem(llm)
    return _scoring_system
