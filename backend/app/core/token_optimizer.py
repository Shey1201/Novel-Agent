"""
Token Optimizer - Token 优化器
提供上下文压缩、智能截断和 Token 预算管理
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json


@dataclass
class TokenStats:
    """Token 统计信息"""
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    compressed_tokens: int
    savings: int
    compression_ratio: float


class TokenEstimator:
    """
    Token 估算器
    
    使用简单的启发式方法估算文本的 Token 数量
    实际应用中可以使用 tiktoken 库进行更精确的估算
    """
    
    # 中文字符平均每个字符约 1.5 个 token
    # 英文单词平均每个单词约 1.3 个 token
    
    @staticmethod
    def estimate(text: str) -> int:
        """
        估算文本的 Token 数量
        
        Args:
            text: 输入文本
            
        Returns:
            估算的 Token 数量
        """
        if not text:
            return 0
        
        # 统计中文字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        
        # 统计英文单词
        english_words = len(re.findall(r'[a-zA-Z]+', text))
        
        # 统计数字
        numbers = len(re.findall(r'\d+', text))
        
        # 统计标点符号
        punctuations = len(re.findall(r'[^\w\s]', text))
        
        # 估算公式
        tokens = (
            chinese_chars * 1.5 +  # 中文字符
            english_words * 1.3 +   # 英文单词
            numbers * 1.0 +         # 数字
            punctuations * 0.5      # 标点
        )
        
        return int(tokens) + 1  # +1 用于结束符
    
    @staticmethod
    def estimate_messages(messages: List[Dict[str, str]]) -> int:
        """
        估算消息列表的 Token 数量
        
        Args:
            messages: OpenAI 格式的消息列表
            
        Returns:
            估算的 Token 数量
        """
        total = 0
        for msg in messages:
            # 每条消息有固定的 4 个 token 开销
            total += 4
            total += TokenEstimator.estimate(msg.get("content", ""))
            total += TokenEstimator.estimate(msg.get("role", ""))
        
        # 回复的 3 个 token 开销
        total += 3
        
        return total


class ContextCompressor:
    """
    上下文压缩器
    
    提供多种策略压缩上下文，减少 Token 使用
    """
    
    def __init__(self):
        self.estimator = TokenEstimator()
    
    def compress(
        self,
        text: str,
        target_tokens: int,
        strategy: str = "smart"
    ) -> str:
        """
        压缩文本到目标 Token 数量
        
        Args:
            text: 原始文本
            target_tokens: 目标 Token 数量
            strategy: 压缩策略 (truncate/summarize/smart)
            
        Returns:
            压缩后的文本
        """
        current_tokens = self.estimator.estimate(text)
        
        if current_tokens <= target_tokens:
            return text
        
        if strategy == "truncate":
            return self._truncate(text, target_tokens)
        elif strategy == "summarize":
            return self._summarize(text, target_tokens)
        elif strategy == "smart":
            return self._smart_compress(text, target_tokens)
        else:
            return self._truncate(text, target_tokens)
    
    def _truncate(self, text: str, target_tokens: int) -> str:
        """简单截断"""
        # 估算每个字符的 token 数
        chars_per_token = len(text) / self.estimator.estimate(text)
        target_chars = int(target_tokens * chars_per_token * 0.9)  # 留一些余量
        
        truncated = text[:target_chars]
        
        # 尝试在句子边界截断
        last_sentence = max(
            truncated.rfind("。"),
            truncated.rfind("!"),
            truncated.rfind("?"),
            truncated.rfind(".")
        )
        
        if last_sentence > len(truncated) * 0.8:
            truncated = truncated[:last_sentence + 1]
        
        return truncated + "\n[内容已截断...]"
    
    def _summarize(self, text: str, target_tokens: int) -> str:
        """提取关键信息摘要"""
        lines = text.split("\n")
        
        # 保留标题和关键行
        important_lines = []
        for line in lines:
            # 保留标题行
            if line.startswith("#") or line.startswith("【"):
                important_lines.append(line)
            # 保留包含关键信息的行
            elif any(kw in line for kw in ["角色", "设定", "关键", "重要", "主线"]):
                important_lines.append(line)
        
        summary = "\n".join(important_lines)
        
        # 如果还是太长，继续截断
        if self.estimator.estimate(summary) > target_tokens:
            return self._truncate(summary, target_tokens)
        
        return summary + "\n[详细内容已省略...]"
    
    def _smart_compress(self, text: str, target_tokens: int) -> str:
        """智能压缩 - 结合多种策略"""
        current_tokens = self.estimator.estimate(text)
        
        # 如果只需要稍微压缩，使用截断
        if current_tokens <= target_tokens * 1.5:
            return self._truncate(text, target_tokens)
        
        # 如果需要大幅压缩，使用摘要
        if current_tokens <= target_tokens * 3:
            return self._summarize(text, target_tokens)
        
        # 如果需要极大压缩，提取关键信息
        return self._extract_key_points(text, target_tokens)
    
    def _extract_key_points(self, text: str, target_tokens: int) -> str:
        """提取关键点"""
        # 提取角色名
        characters = re.findall(r'[\u4e00-\u9fff]{2,4}(?=[，。：\s])', text)
        character_str = ", ".join(set(characters[:10])) if characters else ""
        
        # 提取关键事件
        events = re.findall(r'[^。！？\n]{10,30}(?:发生|出现|开始|结束|完成)', text)
        event_str = "; ".join(events[:5]) if events else ""
        
        key_points = f"""[关键信息摘要]
涉及角色: {character_str}
关键事件: {event_str}
[原始内容长度: {len(text)} 字符]
"""
        
        return key_points


class TokenBudgetManager:
    """
    Token 预算管理器
    
    管理多个组件的 Token 分配
    """
    
    def __init__(self, total_budget: int = 8000):
        self.total_budget = total_budget
        self.reserved_tokens = 1000  # 为回复预留
        self.available_budget = total_budget - self.reserved_tokens
        self.estimator = TokenEstimator()
    
    def allocate_budget(
        self,
        components: Dict[str, Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        为各个组件分配 Token 预算
        
        Args:
            components: 组件配置
                {
                    "component_name": {
                        "priority": 1-10,
                        "content": str,
                        "min_tokens": int
                    }
                }
                
        Returns:
            各组件的预算分配
        """
        allocations = {}
        remaining_budget = self.available_budget
        
        # 首先满足最低需求
        for name, config in components.items():
            min_tokens = config.get("min_tokens", 100)
            allocations[name] = min_tokens
            remaining_budget -= min_tokens
        
        # 按优先级分配剩余预算
        if remaining_budget > 0:
            # 计算总优先级
            total_priority = sum(
                config.get("priority", 5) for config in components.values()
            )
            
            for name, config in components.items():
                priority = config.get("priority", 5)
                content = config.get("content", "")
                
                # 根据优先级分配
                priority_share = (priority / total_priority) * remaining_budget
                
                # 检查内容实际需要多少
                content_tokens = self.estimator.estimate(content)
                
                # 取最小值
                additional = min(priority_share, content_tokens - allocations[name])
                additional = max(0, additional)
                
                allocations[name] += int(additional)
        
        return allocations
    
    def optimize_context(
        self,
        components: Dict[str, str],
        priorities: Optional[Dict[str, int]] = None
    ) -> Dict[str, str]:
        """
        优化上下文，确保总 Token 在预算内
        
        Args:
            components: 组件内容
            priorities: 组件优先级
            
        Returns:
            优化后的组件内容
        """
        priorities = priorities or {}
        
        # 准备配置
        configs = {}
        for name, content in components.items():
            configs[name] = {
                "priority": priorities.get(name, 5),
                "content": content,
                "min_tokens": 50
            }
        
        # 分配预算
        budgets = self.allocate_budget(configs)
        
        # 压缩内容
        optimized = {}
        compressor = ContextCompressor()
        
        for name, content in components.items():
            budget = budgets.get(name, 500)
            optimized[name] = compressor.compress(content, budget, "smart")
        
        return optimized


class SmartContextBuilder:
    """
    智能上下文构建器
    
    根据 Token 预算智能构建上下文
    """
    
    def __init__(self, budget: int = 6000):
        self.budget = budget
        self.estimator = TokenEstimator()
        self.compressor = ContextCompressor()
    
    def build_writing_context(
        self,
        story_memory: str,
        semantic_memories: List[str],
        character_context: Dict[str, Any],
        world_context: Dict[str, Any],
        current_scene: str
    ) -> str:
        """
        构建写作上下文
        
        Args:
            story_memory: 故事记忆
            semantic_memories: 语义检索结果
            character_context: 角色上下文
            world_context: 世界上下文
            current_scene: 当前场景
            
        Returns:
            构建的上下文
        """
        # 定义优先级
        priorities = {
            "current_scene": 10,      # 当前场景最高优先级
            "story_memory": 8,        # 故事记忆次高
            "character_context": 7,   # 角色信息
            "world_context": 5,       # 世界设定
            "semantic_memories": 6,   # 语义检索
        }
        
        # 准备组件
        components = {
            "current_scene": current_scene,
            "story_memory": story_memory,
            "character_context": json.dumps(character_context, ensure_ascii=False),
            "world_context": json.dumps(world_context, ensure_ascii=False),
            "semantic_memories": "\n".join(semantic_memories),
        }
        
        # 创建预算管理器
        manager = TokenBudgetManager(self.budget)
        
        # 优化上下文
        optimized = manager.optimize_context(components, priorities)
        
        # 组装最终上下文
        context_parts = [
            "[当前场景]",
            optimized["current_scene"],
            "",
            "[故事背景]",
            optimized["story_memory"],
            "",
            "[角色信息]",
            optimized["character_context"],
            "",
            "[相关设定]",
            optimized["semantic_memories"],
            "",
            "[世界观]",
            optimized["world_context"],
        ]
        
        return "\n".join(context_parts)
    
    def build_chat_context(
        self,
        chat_history: List[Dict[str, str]],
        story_context: str,
        user_query: str
    ) -> List[Dict[str, str]]:
        """
        构建聊天上下文
        
        Args:
            chat_history: 聊天历史
            story_context: 故事上下文
            user_query: 用户查询
            
        Returns:
            构建的消息列表
        """
        messages = []
        
        # 系统消息
        system_content = f"""你是一位专业的小说创作助手。

[故事上下文]
{self.compressor.compress(story_context, 2000, "smart")}

请基于以上信息回答用户问题。"""
        
        messages.append({"role": "system", "content": system_content})
        
        # 压缩聊天历史
        remaining_budget = self.budget - self.estimator.estimate(system_content) - 500
        
        # 从后往前添加历史消息
        compressed_history = []
        for msg in reversed(chat_history[-10:]):  # 最多最近10条
            msg_tokens = self.estimator.estimate(msg.get("content", ""))
            
            if remaining_budget >= msg_tokens:
                compressed_history.insert(0, msg)
                remaining_budget -= msg_tokens
            else:
                break
        
        messages.extend(compressed_history)
        
        # 添加用户查询
        messages.append({"role": "user", "content": user_query})
        
        return messages


class TokenOptimizer:
    """
    Token 优化器主类
    
    提供统一的 Token 优化接口
    """
    
    def __init__(self, default_budget: int = 8000):
        self.default_budget = default_budget
        self.estimator = TokenEstimator()
        self.compressor = ContextCompressor()
        self.budget_manager = TokenBudgetManager(default_budget)
        self.context_builder = SmartContextBuilder(default_budget)
    
    def optimize(
        self,
        text: str,
        target_tokens: Optional[int] = None
    ) -> Tuple[str, TokenStats]:
        """
        优化文本
        
        Args:
            text: 原始文本
            target_tokens: 目标 Token 数
            
        Returns:
            (优化后的文本, 统计信息)
        """
        target = target_tokens or self.default_budget
        
        original_tokens = self.estimator.estimate(text)
        
        if original_tokens <= target:
            return text, TokenStats(
                total_tokens=original_tokens,
                prompt_tokens=original_tokens,
                completion_tokens=0,
                compressed_tokens=original_tokens,
                savings=0,
                compression_ratio=1.0
            )
        
        compressed = self.compressor.compress(text, target, "smart")
        compressed_tokens = self.estimator.estimate(compressed)
        
        savings = original_tokens - compressed_tokens
        ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0
        
        stats = TokenStats(
            total_tokens=compressed_tokens,
            prompt_tokens=compressed_tokens,
            completion_tokens=0,
            compressed_tokens=compressed_tokens,
            savings=savings,
            compression_ratio=ratio
        )
        
        return compressed, stats
    
    def get_stats(self, text: str) -> TokenStats:
        """获取文本统计信息"""
        tokens = self.estimator.estimate(text)
        return TokenStats(
            total_tokens=tokens,
            prompt_tokens=tokens,
            completion_tokens=0,
            compressed_tokens=tokens,
            savings=0,
            compression_ratio=1.0
        )


# 便捷函数
def estimate_tokens(text: str) -> int:
    """估算 Token 数量"""
    return TokenEstimator.estimate(text)


def compress_text(text: str, target_tokens: int) -> str:
    """压缩文本"""
    compressor = ContextCompressor()
    return compressor.compress(text, target_tokens, "smart")


def optimize_context(components: Dict[str, str], budget: int = 6000) -> Dict[str, str]:
    """优化上下文"""
    manager = TokenBudgetManager(budget)
    return manager.optimize_context(components)


# 全局优化器实例
_token_optimizer: Optional[TokenOptimizer] = None


def get_token_optimizer(budget: int = 8000) -> TokenOptimizer:
    """获取 Token 优化器实例"""
    global _token_optimizer
    if _token_optimizer is None:
        _token_optimizer = TokenOptimizer(budget)
    return _token_optimizer
