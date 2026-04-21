"""
增强版 Pipeline 服务 - 集成评分系统、Reflection 模式、递归生成

功能特性：
1. 评分系统 - 生成后自动评估内容质量
2. Reflection 模式 - 自我反思与优化
3. 递归生成 - 支持多层级内容展开
4. 字数统计 - 各阶段字数实时显示
"""
from typing import Any, Dict, List, Optional
import time

from app.memory.story_memory import StoryBible, StoryMemory
from app.memory.agent_memory import agent_memory
from app.services.agent_scoring_system import AgentScoringSystem
from app.services.reflection_agent import ReflectionAgent
from app.services.recursive_content_generator import RecursiveContentGenerator
from app.core.llm import get_llm


class EnhancedPipelineService:
    """
    增强版 Pipeline 服务
    
    集成功能：
    - 评分系统：生成后自动评估
    - Reflection：自我反思优化
    - 递归生成：多层级展开
    - 字数统计：实时显示
    """
    
    def __init__(
        self,
        story_id: str = "demo-story",
        chapter_id: str = None,
        enable_scoring: bool = True,
        enable_reflection: bool = True,
        enable_recursive: bool = False,
    ):
        self.story_id = story_id
        self.chapter_id = chapter_id
        self.enable_scoring = enable_scoring
        self.enable_reflection = enable_reflection
        self.enable_recursive = enable_recursive
        
        # 初始化 LLM
        self.llm = get_llm()
        
        # 初始化各功能模块
        self.scoring = AgentScoringSystem(self.llm) if enable_scoring else None
        self.reflection = ReflectionAgent(self.llm, max_iterations=2) if enable_reflection else None
        self.recursive = RecursiveContentGenerator(self.llm) if enable_recursive else None
        
        # 统计信息
        self.stats = {
            "total_time": 0,
            "agent_times": {},
            "word_counts": {},
            "scores": {},
        }
    
    def run(
        self,
        outline: str,
        user_requirement: str = None,
    ) -> Dict[str, Any]:
        """
        运行增强版 Pipeline
        
        Args:
            outline: 章节大纲
            user_requirement: 用户需求（可选）
            
        Returns:
            包含内容和统计信息的字典
        """
        t0 = time.time()
        
        # Step 1: 生成大纲/计划
        plan_text = self._generate_plan(outline)
        self.stats["word_counts"]["plan"] = len(plan_text)
        
        # Step 2: 生成初稿
        draft_text = self._generate_draft(plan_text)
        self.stats["word_counts"]["draft"] = len(draft_text)
        
        # Step 3: 评分（可选）
        if self.enable_scoring and self.scoring:
            score_result = self.scoring.check_and_score(draft_text, "writer")
            self.stats["scores"]["draft"] = score_result
            print(f"[Pipeline] 初稿评分: {score_result['score']}/100 ({score_result['grade']})")
        
        # Step 4: Reflection 优化（可选）
        if self.enable_reflection and self.reflection:
            reflection_result = self.reflection.generate_and_refine(
                f"请根据以下大纲生成小说章节内容：\n\n{plan_text}"
            )
            draft_text = reflection_result.improved_content
            self.stats["word_counts"]["draft_refined"] = len(draft_text)
            self.stats["reflection"] = {
                "iterations": reflection_result.iteration_count,
                "improvements": reflection_result.improvements_made,
            }
            print(f"[Pipeline] Reflection 优化完成: {reflection_result.iteration_count} 次迭代")
        
        # Step 5: 编辑修订
        edited_text = self._generate_edit(draft_text)
        self.stats["word_counts"]["edited"] = len(edited_text)
        
        # Step 6: 最终评分（可选）
        if self.enable_scoring and self.scoring:
            final_score = self.scoring.check_and_score(edited_text, "editor")
            self.stats["scores"]["final"] = final_score
            print(f"[Pipeline] 最终评分: {final_score['score']}/100 ({final_score['grade']})")
        
        # 汇总时间
        self.stats["total_time"] = time.time() - t0
        
        return {
            "input_text": outline,
            "plan_text": plan_text,
            "draft_text": draft_text,
            "edited_text": edited_text,
            "final_text": edited_text,
            "word_counts": self.stats["word_counts"],
            "scores": self.stats.get("scores", {}),
            "stats": self.stats,
        }
    
    def _generate_plan(self, outline: str) -> str:
        """生成计划/大纲"""
        from app.agents.planner_agent import PlannerAgent
        
        agent = PlannerAgent()
        result = agent.run(outline=outline)
        
        self.stats["agent_times"]["planner"] = result.get("elapsed", 0)
        return result.get("plan_text", outline)
    
    def _generate_draft(self, plan: str) -> str:
        """生成初稿"""
        from app.agents.writing_agent import WritingAgent
        
        agent = WritingAgent()
        result = agent.run(
            outline=plan,
            story_id=self.story_id,
            chapter_id=self.chapter_id,
        )
        
        self.stats["agent_times"]["writer"] = result.get("elapsed", 0)
        return result.get("draft_text", plan)
    
    def _generate_edit(self, draft: str) -> str:
        """生成编辑版本"""
        from app.agents.editor_agent import EditorAgent
        
        agent = EditorAgent()
        result = agent.run(
            draft_text=draft,
            story_id=self.story_id,
        )
        
        self.stats["agent_times"]["editor"] = result.get("elapsed", 0)
        return result.get("edited_text", draft)
    
    def generate_with_recursive(
        self,
        topic: str,
        context: Dict[str, Any] = None,
        max_depth: int = 2,
    ) -> Dict[str, Any]:
        """
        使用递归生成内容
        
        Args:
            topic: 主题
            context: 上下文
            max_depth: 最大深度
            
        Returns:
            包含内容树和统计信息
        """
        if not self.recursive:
            raise ValueError("Recursive generation not enabled")
        
        t0 = time.time()
        
        # 生成内容树
        content_tree = self.recursive.generate(
            topic=topic,
            context=context or {},
            max_depth=max_depth,
        )
        
        # 转换为 Markdown
        final_text = self.recursive.to_markdown(content_tree)
        
        # 统计
        elapsed = time.time() - t0
        word_count = content_tree.count_words()
        
        return {
            "topic": topic,
            "content_tree": content_tree.to_dict(),
            "final_text": final_text,
            "word_count": word_count,
            "depth": max_depth,
            "elapsed": elapsed,
        }
    
    def get_summary(self) -> str:
        """获取执行摘要"""
        lines = [
            "=" * 50,
            "Pipeline 执行摘要",
            "=" * 50,
        ]
        
        # 时间统计
        if self.stats.get("agent_times"):
            lines.append("\n[时间统计]")
            for agent, t in self.stats["agent_times"].items():
                lines.append(f"  {agent}: {t:.1f}s")
        
        # 字数统计
        if self.stats.get("word_counts"):
            lines.append("\n[字数统计]")
            for stage, count in self.stats["word_counts"].items():
                lines.append(f"  {stage}: {count} 字符")
        
        # 评分
        if self.stats.get("scores"):
            lines.append("\n[质量评分]")
            for stage, score in self.stats["scores"].items():
                lines.append(f"  {stage}: {score.get('score', 0)}/100 ({score.get('grade', 'N/A')})")
        
        # 总时间
        lines.append(f"\n[总耗时] {self.stats.get('total_time', 0):.1f}s")
        
        return "\n".join(lines)


def run_enhanced_pipeline(
    outline: str,
    story_id: str = "demo-story",
    enable_scoring: bool = True,
    enable_reflection: bool = True,
) -> Dict[str, Any]:
    """
    便捷函数：运行增强版 Pipeline
    """
    service = EnhancedPipelineService(
        story_id=story_id,
        enable_scoring=enable_scoring,
        enable_reflection=enable_reflection,
    )
    
    return service.run(outline)
