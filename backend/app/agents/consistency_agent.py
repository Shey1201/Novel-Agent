"""
Consistency Agent - 一致性检查 Agent
负责检查剧情、角色、世界观的一致性
拥有高优先级插话权
"""

from typing import Dict, List, Any, Optional
import json
import re

from app.agents.base_agent import BaseAgent


class ConsistencyAgent(BaseAgent):
    """
    一致性检查 Agent
    
    职责：
    1. 检查角色设定一致性（性格、能力、状态）
    2. 检查世界观设定一致性（规则、地理、历史）
    3. 检查剧情逻辑一致性（时间线、因果关系）
    4. 在 Writers Room 中高优先级插话
    """
    
    def __init__(self, name: str = "consistency", llm: Any = None):
        super().__init__(name=name, llm=llm)
        self.interruption_priority = 10  # 最高优先级
    
    def check_character_consistency(
        self, 
        text: str, 
        character_profiles: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        检查角色一致性
        
        Args:
            text: 待检查文本
            character_profiles: 角色档案
            
        Returns:
            不一致问题列表
        """
        issues = []
        
        # 构建检查提示
        profiles_text = json.dumps(character_profiles, ensure_ascii=False, indent=2)
        
        prompt = f"""检查以下文本中的角色设定一致性：

[角色档案]
{profiles_text}

[待检查文本]
{text[:2000]}

请检查：
1. 角色的行为是否符合其性格设定
2. 角色的能力使用是否超出设定范围
3. 角色的状态变化是否合理（如受伤、位置）
4. 角色的语言风格是否一致

如果发现不一致，请以 JSON 格式输出：
{{
    "issues": [
        {{
            "character": "角色名",
            "issue_type": "行为/能力/状态/语言",
            "description": "具体问题描述",
            "severity": "critical/medium/low",
            "suggestion": "修改建议"
        }}
    ]
}}

如果没有问题，输出：{{"issues": []}}"""
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # 提取 JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group())
                return result.get("issues", [])
        except Exception as e:
            print(f"角色一致性检查出错: {e}")
        
        return issues
    
    def check_world_consistency(
        self, 
        text: str, 
        world_bible: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        检查世界观一致性
        
        Args:
            text: 待检查文本
            world_bible: 世界圣经（设定集）
            
        Returns:
            不一致问题列表
        """
        issues = []
        
        world_text = json.dumps(world_bible, ensure_ascii=False, indent=2)
        
        prompt = f"""检查以下文本中的世界观设定一致性：

[世界设定]
{world_text}

[待检查文本]
{text[:2000]}

请检查：
1. 魔法/能力规则是否被遵守
2. 地理设定是否正确
3. 历史事件时间线是否一致
4. 社会规则/法律是否被违反
5. 物理规则（如重力、时间）是否合理

如果发现不一致，请以 JSON 格式输出：
{{
    "issues": [
        {{
            "issue_type": "规则/地理/历史/社会/物理",
            "description": "具体问题描述",
            "severity": "critical/medium/low",
            "reference": "违反的设定",
            "suggestion": "修改建议"
        }}
    ]
}}

如果没有问题，输出：{{"issues": []}}"""
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group())
                return result.get("issues", [])
        except Exception as e:
            print(f"世界观一致性检查出错: {e}")
        
        return issues
    
    def check_plot_consistency(
        self, 
        text: str, 
        plot_summary: str,
        previous_chapters: List[str]
    ) -> List[Dict[str, Any]]:
        """
        检查剧情逻辑一致性
        
        Args:
            text: 待检查文本
            plot_summary: 当前剧情摘要
            previous_chapters: 前几章摘要
            
        Returns:
            不一致问题列表
        """
        issues = []
        
        previous_text = "\n".join([f"第{i+1}章: {s}" for i, s in enumerate(previous_chapters[-3:])])
        
        prompt = f"""检查以下文本中的剧情逻辑一致性：

[前文摘要]
{previous_text}

[当前剧情]
{plot_summary}

[待检查文本]
{text[:2000]}

请检查：
1. 时间线是否合理（无时间跳跃错误）
2. 因果关系是否清晰
3. 伏笔是否正确回收
4. 角色的行动动机是否合理
5. 事件发展是否符合前文铺垫

如果发现不一致，请以 JSON 格式输出：
{{
    "issues": [
        {{
            "issue_type": "时间线/因果/伏笔/动机/铺垫",
            "description": "具体问题描述",
            "severity": "critical/medium/low",
            "suggestion": "修改建议"
        }}
    ]
}}

如果没有问题，输出：{{"issues": []}}"""
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group())
                return result.get("issues", [])
        except Exception as e:
            print(f"剧情一致性检查出错: {e}")
        
        return issues
    
    def quick_check_for_writers_room(
        self, 
        proposal: str,
        story_bible: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        快速检查（用于 Writers Room 插话）
        
        Args:
            proposal: 当前讨论的议案/提议
            story_bible: 故事圣经
            
        Returns:
            如果发现问题，返回插话内容；否则返回 None
        """
        world_rules = story_bible.get("world_rules", "")
        character_rules = story_bible.get("character_rules", "")
        
        prompt = f"""快速一致性检查：

[世界规则]
{world_rules[:500]}

[角色规则]
{character_rules[:500]}

[讨论提议]
{proposal}

这个提议是否违反任何设定规则？
如果违反，简要说明问题；如果没有，回答OK。

回复格式：
- 如果违反：VIOLATION: [问题描述]
- 如果没有：OK
"""
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            if "VIOLATION" in content.upper():
                # 提取问题描述
                violation_match = re.search(r'VIOLATION[:：]\s*(.+)', content, re.IGNORECASE)
                description = violation_match.group(1) if violation_match else content
                
                return {
                    "should_interrupt": True,
                    "priority": self.interruption_priority,
                    "message": f"⚠️ 设定冲突提醒：{description}",
                    "type": "consistency_warning"
                }
        except Exception as e:
            print(f"快速检查出错: {e}")
        
        return None
    
    def generate_correction_suggestion(
        self, 
        issue: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """
        生成修正建议
        
        Args:
            issue: 发现的问题
            context: 上下文信息
            
        Returns:
            修正建议文本
        """
        prompt = f"""基于以下问题生成修正建议：

[问题]
{json.dumps(issue, ensure_ascii=False)}

[上下文]
{json.dumps(context, ensure_ascii=False)}

请提供具体的修改建议，使其符合设定。建议要具体、可执行。"""
        
        try:
            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except:
            return issue.get("suggestion", "请检查并修改")


# 便捷函数
def check_consistency(
    text: str,
    story_bible: Dict[str, Any],
    check_type: str = "all"
) -> List[Dict[str, Any]]:
    """
    一致性检查便捷函数
    
    Args:
        text: 待检查文本
        story_bible: 故事圣经
        check_type: 检查类型 (all/character/world/plot)
        
    Returns:
        问题列表
    """
    agent = ConsistencyAgent()
    all_issues = []
    
    if check_type in ["all", "character"]:
        character_profiles = story_bible.get("characters", {})
        issues = agent.check_character_consistency(text, character_profiles)
        all_issues.extend(issues)
    
    if check_type in ["all", "world"]:
        world_data = story_bible.get("world", {})
        issues = agent.check_world_consistency(text, world_data)
        all_issues.extend(issues)
    
    if check_type in ["all", "plot"]:
        plot_data = story_bible.get("plot", {})
        previous = story_bible.get("previous_chapters", [])
        issues = agent.check_plot_consistency(text, plot_data, previous)
        all_issues.extend(issues)
    
    return all_issues
