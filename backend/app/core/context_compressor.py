"""
Context Compressor - 上下文压缩器
将长文本上下文压缩为精简的摘要形式
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import re


@dataclass
class CompressedContext:
    """压缩后的上下文"""
    chapter_summary: str      # 章节摘要
    character_states: str     # 角色状态
    plot_goals: str          # 剧情目标
    key_events: str          # 关键事件
    total_tokens: int        # 预估总 tokens


class ContextCompressor:
    """
    上下文压缩器
    
    将整章小说上下文压缩为精简形式：
    - 章节摘要
    - 角色状态
    - 剧情目标
    - 关键事件
    
    从 3000 tokens 压缩到 200 tokens
    """
    
    def __init__(self):
        self.max_summary_length = 100      # 摘要最大字符数
        self.max_character_length = 80     # 角色状态最大字符数
        self.max_goals_length = 60         # 目标最大字符数
        self.max_events_length = 80        # 事件最大字符数
    
    def compress_chapter_content(
        self,
        chapter_content: str,
        characters: List[str] = None,
        current_plot: str = ""
    ) -> CompressedContext:
        """
        压缩章节内容
        
        Args:
            chapter_content: 完整章节内容
            characters: 涉及的角色列表
            current_plot: 当前剧情线
            
        Returns:
            压缩后的上下文
        """
        # 生成章节摘要
        chapter_summary = self._extract_summary(chapter_content)
        
        # 提取角色状态
        character_states = self._extract_character_states(chapter_content, characters or [])
        
        # 提取剧情目标
        plot_goals = self._extract_plot_goals(chapter_content, current_plot)
        
        # 提取关键事件
        key_events = self._extract_key_events(chapter_content)
        
        # 估算 tokens (中文字符约 1.5 tokens/字)
        total_chars = len(chapter_summary) + len(character_states) + len(plot_goals) + len(key_events)
        total_tokens = int(total_chars * 1.5)
        
        return CompressedContext(
            chapter_summary=chapter_summary,
            character_states=character_states,
            plot_goals=plot_goals,
            key_events=key_events,
            total_tokens=total_tokens
        )
    
    def _extract_summary(self, content: str) -> str:
        """提取章节摘要"""
        # 提取前几句作为摘要
        sentences = re.split(r'[。！？\n]', content)
        summary = ""
        
        for sent in sentences[:3]:  # 取前3句
            sent = sent.strip()
            if len(sent) > 10:  # 过滤太短的句子
                summary += sent + "。"
                if len(summary) >= self.max_summary_length:
                    break
        
        return summary[:self.max_summary_length]
    
    def _extract_character_states(self, content: str, characters: List[str]) -> str:
        """提取角色状态"""
        if not characters:
            # 自动提取角色名（2-4字中文名词）
            characters = list(set(re.findall(r'[\u4e00-\u9fff]{2,4}(?=[，。：\s])', content)))[:5]
        
        states = []
        for char in characters[:3]:  # 最多3个角色
            # 查找角色相关描述
            pattern = f"{char}[^。！？]{{5,30}}[。！？]"
            matches = re.findall(pattern, content)
            if matches:
                # 提取角色动作或状态
                state = matches[0].replace(char, "").strip("。！？")
                states.append(f"{char}:{state}")
        
        result = ";".join(states)
        return result[:self.max_character_length]
    
    def _extract_plot_goals(self, content: str, current_plot: str) -> str:
        """提取剧情目标"""
        # 如果有当前剧情线，直接使用
        if current_plot:
            return current_plot[:self.max_goals_length]
        
        # 否则从内容中提取目标相关语句
        goal_patterns = [
            r'(?:要|想要|决定|计划)[^。！？]{5,20}',
            r'(?:目标|目的|任务)[^。！？]{5,20}',
            r'(?:为了|以便)[^。！？]{5,20}',
        ]
        
        goals = []
        for pattern in goal_patterns:
            matches = re.findall(pattern, content)
            goals.extend(matches[:2])
        
        result = ";".join(goals)
        return result[:self.max_goals_length] if result else "推进剧情"
    
    def _extract_key_events(self, content: str) -> str:
        """提取关键事件"""
        # 查找动作和事件
        event_patterns = [
            r'[^。！？]{3,15}(?:发现|出现|发生|开始|结束|完成|遇到|找到)',
            r'(?:突然|忽然)[^。！？]{5,20}',
            r'[^。！？]{3,15}(?:战斗|对话|相遇|离别)',
        ]
        
        events = []
        for pattern in event_patterns:
            matches = re.findall(pattern, content)
            events.extend(matches[:2])
        
        result = ";".join(list(set(events)))  # 去重
        return result[:self.max_events_length]
    
    def format_for_agent(self, context: CompressedContext, agent_type: str = "") -> str:
        """
        格式化为 Agent 可用的上下文
        
        Args:
            context: 压缩后的上下文
            agent_type: Agent 类型，用于定制格式
            
        Returns:
            格式化后的字符串
        """
        formatted = f"""[上下文摘要]
章节概要：{context.chapter_summary}
角色状态：{context.character_states}
剧情目标：{context.plot_goals}
关键事件：{context.key_events}
"""
        
        # 根据不同 Agent 添加特定信息
        if agent_type == "writer":
            formatted += "\n[写作提示]\n基于以上上下文继续创作，保持情节连贯。"
        elif agent_type == "editor":
            formatted += "\n[编辑重点]\n关注逻辑一致性和叙事流畅度。"
        elif agent_type == "conflict":
            formatted += "\n[冲突分析]\n分析当前冲突强度和后续发展可能。"
        
        return formatted
    
    def compress_for_discussion(
        self,
        chapter_content: str,
        previous_chapters_summary: str = "",
        characters: List[str] = None
    ) -> str:
        """
        为讨论压缩上下文
        
        更激进的压缩，用于 Agent 讨论
        """
        # 提取核心情节
        sentences = re.split(r'[。！？\n]', chapter_content)
        key_sentences = []
        
        # 关键词筛选
        keywords = ["主角", "发现", "决定", "冲突", "问题", "目标", "计划", "遇到"]
        
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 10:
                continue
            if any(kw in sent for kw in keywords):
                key_sentences.append(sent)
                if len(key_sentences) >= 5:
                    break
        
        core_plot = "。".join(key_sentences)
        
        # 角色列表
        char_list = ", ".join(characters[:3]) if characters else "主角"
        
        return f"""[讨论上下文]
核心情节：{core_plot[:100]}
涉及角色：{char_list}
前文概要：{previous_chapters_summary[:50] if previous_chapters_summary else "无"}
"""


# 全局实例
context_compressor = ContextCompressor()


def get_context_compressor() -> ContextCompressor:
    """获取上下文压缩器实例"""
    return context_compressor
