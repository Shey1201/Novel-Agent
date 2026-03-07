"""
Critic Agent - AI 质量评估系统
多维度评分：逻辑一致性、剧情张力、文笔质量
"""

import json
import re
from typing import Dict, List, Any, Optional

from app.agents.base_agent import BaseAgent


class CriticAgent(BaseAgent):
    """
    评论家 Agent - 评估章节质量
    
    评分维度：
    1. Logic Consistency (逻辑一致性) - 权重 0.3
    2. Plot Tension (剧情张力) - 权重 0.25
    3. Prose Quality (文笔质量) - 权重 0.2
    4. Character Voice (角色声音) - 权重 0.15
    5. World Consistency (世界观一致性) - 权重 0.1
    """
    
    def __init__(self, name: str = "critic", llm: Any = None):
        super().__init__(name=name, llm=llm)
        self.weights = {
            "logic_consistency": 0.3,
            "plot_tension": 0.25,
            "prose_quality": 0.2,
            "character_voice": 0.15,
            "world_consistency": 0.1
        }
    
    def _build_prompt(self, chapter: str, context: Dict[str, Any]) -> str:
        """构建评估提示词"""
        plan = context.get("plan", "")
        reader_feedback = context.get("reader_feedback", "")
        
        prompt = f"""你是一位资深文学评论家，请对以下小说章节进行专业评估。

[章节内容]
{chapter[:3000]}...

[原大纲]
{plan}

[读者反馈]
{reader_feedback}

请从以下5个维度进行评分（0-1分，保留两位小数），并提供详细反馈：

1. **Logic Consistency (逻辑一致性)** - 权重 0.3
   - 情节发展是否符合逻辑
   - 角色行为是否符合人设
   - 因果关系是否清晰

2. **Plot Tension (剧情张力)** - 权重 0.25
   - 冲突是否足够强烈
   - 节奏把控是否得当
   - 是否有足够的悬念

3. **Prose Quality (文笔质量)** - 权重 0.2
   - 语言表达是否流畅
   - 描写是否生动具体
   - 修辞手法运用

4. **Character Voice (角色声音)** - 权重 0.15
   - 角色语言是否符合身份
   - 不同角色是否有区分度
   - 内心独白是否真实

5. **World Consistency (世界观一致性)** - 权重 0.1
   - 设定是否前后一致
   - 世界规则是否被遵守
   - 细节是否自洽

请以 JSON 格式输出：
{{
    "scores": {{
        "logic_consistency": 0.85,
        "plot_tension": 0.72,
        "prose_quality": 0.88,
        "character_voice": 0.80,
        "world_consistency": 0.90
    }},
    "total_score": 0.81,
    "feedback": {{
        "strengths": ["优点1", "优点2"],
        "weaknesses": ["缺点1", "缺点2"],
        "suggestions": ["改进建议1", "改进建议2"]
    }},
    "rewrite_needed": false,
    "priority_issues": ["首要问题"]
}}

注意：
- total_score 是加权平均分
- rewrite_needed 为 true 当且仅当 total_score < 0.6
- 评分要严格，0.8分以上代表优秀，0.6分以下需要重写"""
        
        return prompt
    
    def evaluate(self, chapter: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估章节质量
        
        Args:
            chapter: 章节文本
            context: 上下文信息
            
        Returns:
            评估结果字典
        """
        prompt = self._build_prompt(chapter, context)
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # 提取 JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group())
            else:
                raise ValueError("无法解析 JSON 响应")
            
            # 计算加权总分
            scores = result.get("scores", {})
            total_score = sum(
                scores.get(k, 0) * self.weights[k]
                for k in self.weights.keys()
            )
            
            # 确保总分一致
            result["total_score"] = round(total_score, 2)
            result["breakdown"] = scores
            
            # 确定是否需要重写
            result["rewrite_needed"] = total_score < 0.6
            
            return result
            
        except Exception as e:
            # 评估失败时返回默认评分
            return {
                "total_score": 0.5,
                "breakdown": {
                    "logic_consistency": 0.5,
                    "plot_tension": 0.5,
                    "prose_quality": 0.5,
                    "character_voice": 0.5,
                    "world_consistency": 0.5
                },
                "feedback": {
                    "strengths": [],
                    "weaknesses": ["评估过程出错"],
                    "suggestions": [f"错误: {str(e)}"]
                },
                "rewrite_needed": True,
                "priority_issues": ["评估失败，建议人工检查"]
            }
    
    def quick_check(self, text: str, check_type: str = "logic") -> Dict[str, Any]:
        """
        快速检查（用于 Consistency Agent 插话）
        
        Args:
            text: 待检查文本
            check_type: 检查类型 (logic/world/character)
            
        Returns:
            快速检查结果
        """
        checks = {
            "logic": "检查逻辑一致性",
            "world": "检查世界观一致性",
            "character": "检查角色一致性"
        }
        
        prompt = f"""快速{checks.get(check_type, '逻辑')}检查：

文本：{text[:500]}

是否存在明显问题？只回答 YES/NO，如果有问题简要说明。"""
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            has_issue = "YES" in content.upper() or "是" in content
            
            return {
                "has_issue": has_issue,
                "issue_description": content if has_issue else "",
                "check_type": check_type
            }
        except:
            return {
                "has_issue": False,
                "issue_description": "",
                "check_type": check_type
            }


# 便捷函数
def evaluate_chapter(chapter: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """评估章节便捷函数"""
    agent = CriticAgent()
    return agent.evaluate(chapter, context)
