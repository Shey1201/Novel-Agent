"""
Reflection 模式 - Agent 自我反思与优化

功能：
- 生成初稿后自动进行自我评审
- 根据评审意见自动优化内容
- 一步到位，不需要独立的评审流程
- 类似于人类"写完读一遍再改"的创作习惯
"""
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass


@dataclass
class ReflectionResult:
    """反思结果"""
    original_content: str  # 原始内容
    improved_content: str  # 改进后的内容
    reflection_notes: str  # 反思笔记
    improvements_made: List[str]  # 做的改进
    iteration_count: int  # 迭代次数


class ReflectionAgent:
    """
    反思Agent - 模拟人类创作习惯
    
    工作流程：
    1. 生成初稿
    2. 自我反思 (Critique)
    3. 根据反思优化 (Refine)
    4. 重复直到满意或达到最大次数
    
    优点：
    - 一步到位，不需要独立评审流程
    - 模拟人类创作习惯
    - 效率更高
    """
    
    def __init__(
        self,
        llm=None,
        scoring_func: Callable = None,
        max_iterations: int = 2,
    ):
        """
        初始化反思Agent
        
        Args:
            llm: LLM 实例
            scoring_func: 评分函数 (可选)
            max_iterations: 最大迭代次数
        """
        self.llm = llm
        self.scoring_func = scoring_func
        self.max_iterations = max_iterations
    
    def generate_and_refine(
        self,
        prompt: str,
        context: Dict[str, Any] = None,
    ) -> ReflectionResult:
        """
        生成并优化内容
        
        Args:
            prompt: 生成内容的提示
            context: 上下文信息
            
        Returns:
            ReflectionResult: 包含原始内容、改进内容和反思笔记
        """
        from langchain_core.messages import HumanMessage
        
        # Step 1: 生成初稿
        print("[Reflection] 生成初稿...")
        initial_content = self._generate_content(prompt, context)
        
        original_content = initial_content
        current_content = initial_content
        improvements_made = []
        
        # Step 2-4: 反思和优化循环
        for iteration in range(1, self.max_iterations + 1):
            print(f"[Reflection] 反思迭代 {iteration}/{self.max_iterations}...")
            
            # 自我反思
            reflection_notes = self._reflect(current_content, context)
            
            # 检查是否需要改进
            if not self._needs_improvement(reflection_notes):
                print("[Reflection] 内容已经足够好，跳过改进")
                break
            
            # 根据反思优化
            print(f"[Reflection] 根据反思改进内容...")
            improved_content = self._refine(current_content, reflection_notes, context)
            
            # 检查改进是否有效
            if self._is_improvement(current_content, improved_content):
                improvements_made.append(f"迭代 {iteration}: {reflection_notes[:50]}...")
                current_content = improved_content
                print(f"[Reflection] 改进完成，当前长度: {len(current_content)} 字符")
            else:
                print("[Reflection] 改进效果不明显，停止迭代")
                break
        
        return ReflectionResult(
            original_content=original_content,
            improved_content=current_content,
            reflection_notes=reflection_notes if iteration > 0 else "",
            improvements_made=improvements_made,
            iteration_count=iteration,
        )
    
    def _generate_content(
        self,
        prompt: str,
        context: Dict[str, Any] = None,
    ) -> str:
        """生成初稿"""
        from langchain_core.messages import HumanMessage
        
        context_str = ""
        if context:
            context_str = f"\n\n## 上下文\n{json.dumps(context, ensure_ascii=False)[:500]}"
        
        full_prompt = f"""{prompt}

{context_str}

请直接输出内容："""
        
        try:
            response = self.llm.invoke([HumanMessage(content=full_prompt)])
            content = response.content if hasattr(response, "content") else str(response)
            
            # 清理 markdown 格式
            import re
            if "```" in content:
                match = re.search(r'```[\w]*\n?([\s\S]*?)```', content)
                if match:
                    content = match.group(1).strip()
            
            return content
        except Exception as e:
            print(f"[Reflection] 生成失败: {e}")
            return "内容生成失败"
    
    def _reflect(
        self,
        content: str,
        context: Dict[str, Any] = None,
    ) -> str:
        """
        自我反思 - 评估当前内容
        
        返回反思笔记，包含：
        - 优点
        - 缺点
        - 改进建议
        """
        from langchain_core.messages import HumanMessage
        
        prompt = f"""请作为专业编辑，阅读以下内容并进行自我反思。

## 内容
{content[:1500]}

请从以下维度进行评估：
1. 内容质量 - 准确性、完整性、深度
2. 结构逻辑 - 层次清晰、逻辑通顺
3. 语言表达 - 流畅性、风格
4. 格式规范 - 标点、段落

请输出反思结果，格式如下：
```
优点：
- 优点1
- 缺点2

缺点：
- 缺点1
- 缺点2

改进建议：
- 建议1
- 建议2
```

请直接输出，不要添加任何前缀："""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            print(f"[Reflection] 反思失败: {e}")
            return ""
    
    def _needs_improvement(self, reflection_notes: str) -> bool:
        """
        判断是否需要改进
        
        如果反思笔记中包含明确的改进建议，则需要改进
        """
        if not reflection_notes:
            return False
        
        # 关键词判断
        improvement_keywords = [
            "改进", "优化", "完善", "修改", "调整",
            "可以更好", "需要改进", "建议修改"
        ]
        
        return any(kw in reflection_notes for kw in improvement_keywords)
    
    def _refine(
        self,
        content: str,
        reflection_notes: str,
        context: Dict[str, Any] = None,
    ) -> str:
        """
        根据反思笔记改进内容
        """
        from langchain_core.messages import HumanMessage
        
        context_str = ""
        if context:
            context_str = f"\n\n## 上下文\n{json.dumps(context, ensure_ascii=False)[:300]}"
        
        prompt = f"""请根据以下反思笔记改进内容。

## 原始内容
{content[:1500]}

## 反思笔记
{reflection_notes[:500]}

{context_str}

要求：
1. 保留原文中好的部分
2. 根据反思笔记进行针对性改进
3. 改进后的内容应该更完整、更有逻辑

请直接输出改进后的内容，不要添加任何前缀："""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content if hasattr(response, "content") else str(response)
            
            # 清理 markdown 格式
            import re
            if "```" in content:
                match = re.search(r'```[\w]*\n?([\s\S]*?)```', content)
                if match:
                    content = match.group(1).strip()
            
            return content
        except Exception as e:
            print(f"[Reflection] 改进失败: {e}")
            return content
    
    def _is_improvement(
        self,
        original: str,
        improved: str,
    ) -> bool:
        """
        判断改进是否有效
        
        规则：
        1. 改进后内容不能太短（至少保持 50% 长度）
        2. 改进后内容不能和原来完全相同
        """
        if not improved:
            return False
        
        # 长度检查
        if len(improved) < len(original) * 0.5:
            return False
        
        # 相同检查
        if improved.strip() == original.strip():
            return False
        
        return True


# 便捷函数
import json


def create_reflection_agent(
    llm=None,
    scoring_func: Callable = None,
    max_iterations: int = 2,
) -> ReflectionAgent:
    """创建反思Agent"""
    return ReflectionAgent(llm, scoring_func, max_iterations)
