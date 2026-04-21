"""
递归内容生成系统 - 支持多层级内容展开

功能：
- 支持多层级递归生成 (Level 1-3)
- 自动判断是否需要展开子节点
- 支持大纲 → 章节 → 小节 → 细节 的树形结构
"""
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json


class ContentLevel(Enum):
    """内容层级"""
    COLUMN = 0  # 专栏/书本级别
    CHAPTER = 1  # 章节级别
    SECTION = 2  # 小节级别
    DETAIL = 3  # 细节级别


@dataclass
class ContentNode:
    """内容节点"""
    id: str
    title: str
    level: ContentLevel
    content: str = ""
    description: str = ""
    children: List['ContentNode'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_child(self, child: 'ContentNode'):
        """添加子节点"""
        self.children.append(child)
    
    def count_words(self) -> int:
        """统计字数"""
        count = len(self.content) if self.content else 0
        for child in self.children:
            count += child.count_words()
        return count
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "level": self.level.value,
            "content": self.content,
            "description": self.description,
            "children": [c.to_dict() for c in self.children],
            "metadata": self.metadata,
            "word_count": self.count_words(),
        }


class RecursiveContentGenerator:
    """
    递归内容生成器
    
    工作流程：
    1. 用户提供主题/大纲
    2. 生成顶层内容 (Column/Chapter)
    3. 判断是否需要展开子节点
    4. 递归生成子节点 (Section/Detail)
    5. 达到最大深度或不需要展开时停止
    """
    
    MAX_DEPTH = 3  # 最大递归深度
    
    def __init__(
        self,
        llm=None,
        generate_func: Callable = None,
        scoring_func: Callable = None,
    ):
        """
        初始化递归生成器
        
        Args:
            llm: LLM 实例
            generate_func: 自定义生成函数 (node, context) -> content
            scoring_func: 自定义评分函数 (content) -> score
        """
        self.llm = llm
        self.generate_func = generate_func
        self.scoring_func = scoring_func
    
    def generate(
        self,
        topic: str,
        context: Dict[str, Any] = None,
        max_depth: int = None,
    ) -> ContentNode:
        """
        开始递归生成内容
        
        Args:
            topic: 主题
            context: 上下文信息
            max_depth: 最大深度
            
        Returns:
            ContentNode: 生成的内容树
        """
        if max_depth is None:
            max_depth = self.MAX_DEPTH
        
        # 创建根节点
        root = ContentNode(
            id="root",
            title=topic,
            level=ContentLevel.CHAPTER,
            description=context.get("description", "") if context else "",
        )
        
        # 递归生成
        self._recursive_generate(root, context or {}, depth=1, max_depth=max_depth)
        
        return root
    
    def _recursive_generate(
        self,
        node: ContentNode,
        context: Dict[str, Any],
        depth: int,
        max_depth: int,
    ):
        """递归生成内容"""
        if depth > max_depth:
            print(f"[Recursive] 达到最大深度 {max_depth}，停止展开")
            return
        
        # 生成当前节点内容
        print(f"[Recursive] 生成 Level {depth}: {node.title[:30]}...")
        
        if self.generate_func:
            # 使用自定义生成函数
            content = self.generate_func(node, context)
        else:
            # 使用默认生成方式
            content = self._generate_content(node, context, depth)
        
        node.content = content
        node.metadata["depth"] = depth
        node.metadata["word_count"] = len(content)
        
        # 判断是否需要展开子节点
        if depth < max_depth and self._should_expand(content, depth):
            # 生成子节点
            subsections = self._generate_subsections(node, context, depth)
            
            for sub in subsections:
                child = ContentNode(
                    id=f"{node.id}_{sub['id']}",
                    title=sub["title"],
                    level=ContentLevel(depth),
                    description=sub.get("description", ""),
                )
                node.add_child(child)
                
                # 递归生成子节点
                self._recursive_generate(child, context, depth + 1, max_depth)
    
    def _generate_content(
        self,
        node: ContentNode,
        context: Dict[str, Any],
        depth: int,
    ) -> str:
        """生成节点内容"""
        from langchain_core.messages import HumanMessage
        
        level_names = {
            1: "章节",
            2: "小节", 
            3: "细节",
        }
        level_name = level_names.get(depth, "内容")
        
        word_counts = {
            1: "1000-2000",
            2: "500-1000",
            3: "200-500",
        }
        target_words = word_counts.get(depth, "500-1000")
        
        prompt = f"""请根据以下大纲生成{level_name}内容。

标题: {node.title}
描述: {node.description}

目标字数: {target_words}字

上下文:
{json.dumps(context, ensure_ascii=False, indent=2)[:500]}

要求:
1. 内容完整、逻辑清晰
2. 语言流畅、表达准确
3. 结构层次分明

请直接输出内容，不要添加任何格式前缀："""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            print(f"[Recursive] 生成失败: {e}")
            return f"这是 {node.title} 的内容（生成失败）"
    
    def _should_expand(self, content: str, depth: int) -> bool:
        """
        判断是否需要展开子节点
        
        使用 AI 判断或规则判断
        """
        # 使用评分函数判断
        if self.scoring_func:
            score = self.scoring_func(content)
            # 内容分数高且深度浅时展开
            return score > 60 and depth < 2
        
        # 使用规则判断：内容越长越可能需要展开
        if len(content) > 1500 and depth < 2:
            return True
        
        # 特定关键词触发展开
        expand_keywords = ["首先", "其次", "最后", "第一", "第二", "包括"]
        has_keywords = any(kw in content for kw in expand_keywords)
        
        return has_keywords and depth < 2
    
    def _generate_subsections(
        self,
        node: ContentNode,
        context: Dict[str, Any],
        depth: int,
    ) -> List[Dict]:
        """生成子节点列表"""
        from langchain_core.messages import HumanMessage
        
        prompt = f"""请为以下内容生成子章节结构。

标题: {node.title}
当前层级: {depth}

请生成 2-4 个子章节，每个子章节包含：
- id: 唯一标识
- title: 子章节标题
- description: 50字以内的描述

输出格式（JSON）：
[
  {{"id": "1", "title": "子标题1", "description": "描述1"}},
  {{"id": "2", "title": "子标题2", "description": "描述2"}}
]

请直接输出 JSON："""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            text = response.content if hasattr(response, "content") else str(response)
            
            import re
            json_match = re.search(r'\[[\s\S]*\]', text)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"[Recursive] 生成子节点失败: {e}")
        
        # 默认返回
        return [
            {"id": "1", "title": f"{node.title} - 第一节", "description": "第一节内容"},
            {"id": "2", "title": f"{node.title} - 第二节", "description": "第二节内容"},
        ]
    
    def to_markdown(self, node: ContentNode, depth: int = 0) -> str:
        """将内容树转换为 Markdown"""
        md = []
        
        # 标题
        heading = "#" * (depth + 1)
        md.append(f"{heading} {node.title}\n")
        
        # 内容
        if node.content:
            md.append(node.content)
            md.append("\n")
        
        # 子节点
        for child in node.children:
            md.append(self.to_markdown(child, depth + 1))
        
        return "\n".join(md)
    
    def flatten(self, node: ContentNode) -> List[ContentNode]:
        """扁平化内容树为列表"""
        result = [node]
        
        for child in node.children:
            result.extend(self.flatten(child))
        
        return result


# 便捷函数
def create_recursive_generator(
    llm=None,
    generate_func: Callable = None,
    scoring_func: Callable = None,
) -> RecursiveContentGenerator:
    """创建递归内容生成器"""
    return RecursiveContentGenerator(llm, generate_func, scoring_func)
