"""
智能 Agent 协调器
- 根据配置动态选择需要调用的 Agent
- 集成 agent_memory 的配置
- 集成 skill_memory 的约束
- 支持并行执行和缓存
"""
import os
import time
import hashlib
import json
from typing import Any, Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

# 设置 API 密钥（从环境变量读取，永不硬编码）
os.environ['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', '')
os.environ['OPENAI_BASE_URL'] = os.environ.get('OPENAI_BASE_URL', 'https://api.deepseek.com/v1')

import openai
from openai import OpenAI

# 全局客户端
_client = None

def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.environ['OPENAI_API_KEY'],
            base_url=os.environ['OPENAI_BASE_URL']
        )
    return _client


# ============ Agent 配置加载 ============

class AgentCoordinator:
    """智能 Agent 协调器"""
    
    def __init__(self, story_id: str = "default"):
        self.story_id = story_id
        self._load_agent_configs()
        self._load_skill_constraints()
        self._init_cache()
        
    def _load_agent_configs(self):
        """从 agent_memory 加载 Agent 配置"""
        try:
            from app.memory.agent_memory import agent_memory
            configs = agent_memory.get_all_configs()
            
            # 构建 Agent 配置字典
            self.agent_configs = {}
            for config in configs:
                agent_id = config.agent_id
                self.agent_configs[agent_id] = {
                    "enabled": config.enabled,
                    "name": config.name,
                    "role": config.role,
                    "prompt": config.prompt,
                    "temperature": config.temperature,
                    "personality": config.personality
                }
                
            print(f"[Coordinator] Loaded {len(self.agent_configs)} agent configs")
            for agent_id, cfg in self.agent_configs.items():
                status = "ON" if cfg["enabled"] else "OFF"
                print(f"   - {agent_id}: {status}")
                
        except Exception as e:
            print(f"[Coordinator] Warning: Could not load agent configs: {e}")
            # 使用默认配置
            self.agent_configs = self._get_default_configs()
            
    def _load_skill_constraints(self):
        """从 skill_memory 加载技能约束"""
        try:
            from app.memory.skill_memory import skill_memory
            self.skill_memory = skill_memory
            print(f"[Coordinator] Skill memory loaded")
        except Exception as e:
            print(f"[Coordinator] Warning: Could not load skill memory: {e}")
            self.skill_memory = None
            
    def _init_cache(self):
        """初始化缓存"""
        self.cache: Dict[str, Any] = {}
        self.cache_enabled = True
        
    def _get_default_configs(self) -> Dict[str, Dict]:
        """获取默认 Agent 配置"""
        return {
            "planner": {
                "enabled": True,
                "name": "Planner Agent",
                "role": "制定写作计划",
                "prompt": "你是一个专业的故事规划师...",
                "temperature": 0.7,
                "personality": "理性、逻辑性强"
            },
            "conflict": {
                "enabled": True,
                "name": "Conflict Agent",
                "role": "分析冲突需求",
                "prompt": "你是一个故事冲突分析师...",
                "temperature": 0.6,
                "personality": "挑剔、善于发现问题"
            },
            "writer": {
                "enabled": True,
                "name": "Writing Agent",
                "role": "生成内容",
                "prompt": "你是一个专业的小说作家...",
                "temperature": 0.8,
                "personality": "创意丰富、文笔优美"
            },
            "editor": {
                "enabled": True,
                "name": "Editor Agent",
                "role": "编辑改进",
                "prompt": "你是一个资深编辑...",
                "temperature": 0.5,
                "personality": "严谨、注重细节"
            },
            "reader": {
                "enabled": True,
                "name": "Reader Agent",
                "role": "模拟读者反馈",
                "prompt": "你是一个普通读者...",
                "temperature": 0.6,
                "personality": "客观、真实"
            },
            "summary": {
                "enabled": True,
                "name": "Summary Agent",
                "role": "生成摘要",
                "prompt": "你是一个摘要生成器...",
                "temperature": 0.4,
                "personality": "简洁、准确"
            }
        }
        
    def _get_enabled_agents(self) -> List[str]:
        """获取已启用的 Agent 列表"""
        enabled = []
        for agent_id, config in self.agent_configs.items():
            if config.get("enabled", True):
                enabled.append(agent_id)
        return enabled
        
    def _get_agent_prompt(self, agent_id: str) -> str:
        """获取 Agent 的 prompt"""
        config = self.agent_configs.get(agent_id, {})
        return config.get("prompt", "")
        
    def _get_skill_constraint(self, agent_id: str) -> str:
        """获取技能约束"""
        if not self.skill_memory:
            return ""
        try:
            return self.skill_memory.build_agent_prompt(self.story_id, agent_id) or ""
        except:
            return ""
            
    def _build_full_prompt(self, agent_id: str, base_prompt: str) -> str:
        """构建完整的 prompt（基础 + 配置 + 技能约束）"""
        parts = [base_prompt]
        
        # 添加 Agent 配置的 prompt
        agent_prompt = self._get_agent_prompt(agent_id)
        if agent_prompt:
            parts.append(agent_prompt)
            
        # 添加技能约束
        skill_constraint = self._get_skill_constraint(agent_id)
        if skill_constraint:
            parts.append(f"\n\n[技能约束]\n{skill_constraint}")
            
        return "\n\n".join(parts)
        
    def _get_cache_key(self, agent_id: str, input_text: str) -> str:
        """生成缓存键"""
        key_str = f"{agent_id}:{input_text[:100]}"
        return hashlib.md5(key_str.encode()).hexdigest()
        
    def _get_from_cache(self, agent_id: str, input_text: str) -> Optional[str]:
        """从缓存获取"""
        if not self.cache_enabled:
            return None
        key = self._get_cache_key(agent_id, input_text)
        cached = self.cache.get(key)
        if cached:
            print(f"[Coordinator] Cache HIT: {agent_id}")
            return cached
        return None
        
    def _save_to_cache(self, agent_id: str, input_text: str, result: str):
        """保存到缓存"""
        if not self.cache_enabled:
            return
        key = self._get_cache_key(agent_id, input_text)
        self.cache[key] = result
        # 限制缓存大小
        if len(self.cache) > 100:
            # 删除最老的 20 个
            keys = list(self.cache.keys())[:20]
            for k in keys:
                del self.cache[k]


# ============ Agent 执行器 ============

class AgentExecutor:
    """单个 Agent 执行器"""
    
    def __init__(self, coordinator: AgentCoordinator):
        self.coordinator = coordinator
        self.client = _get_client()
        
    def call_llm(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """调用 LLM"""
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[LLM Error] {e}")
            return ""
            
    def execute(self, agent_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Agent"""
        start_time = time.time()
        
        # 获取 Agent 配置
        config = self.coordinator.agent_configs.get(agent_id, {})
        if not config.get("enabled", True):
            return {
                "status": "skipped",
                "reason": "Agent is disabled",
                "elapsed": 0
            }
            
        # 提取输入文本
        input_text = input_data.get("text") or input_data.get("draft_text") or ""
        
        # 检查缓存
        cached = self.coordinator._get_from_cache(agent_id, input_text)
        if cached:
            return {
                "status": "success",
                "result": cached,
                "elapsed": 0,
                "cached": True
            }
            
        # 构建 prompt
        base_prompt = self._build_base_prompt(agent_id, input_text)
        full_prompt = self.coordinator._build_full_prompt(agent_id, base_prompt)
        
        # 执行
        temperature = config.get("temperature", 0.7)
        result = self.call_llm(full_prompt, max_tokens=1500, temperature=temperature)
        
        # 保存缓存
        self.coordinator._save_to_cache(agent_id, input_text, result)
        
        elapsed = time.time() - start_time
        
        return {
            "status": "success",
            "result": result,
            "elapsed": elapsed,
            "cached": False
        }
        
    def _build_base_prompt(self, agent_id: str, input_text: str) -> str:
        """构建基础 prompt"""
        prompts = {
            "planner": f"""为以下故事制定大纲：

{input_text}

请列出：主题、主角、核心冲突、3个情节点。""",
            
            "conflict": f"""分析以下章节，找出可以增强的冲突：

{input_text}

列出2-3个具体建议。""",
            
            "writer": f"""你是小说作家。根据大纲写章节：

{input_text}

要求：人物鲜活、情节生动。""",
            
            "editor": f"""编辑改进以下章节：

{input_text}

检查流畅度和语法，直接输出改进版本。""",
            
            "reader": f"""作为读者，评价以下章节：

{input_text}

给出反馈和建议。""",
            
            "summary": f"""为以下章节写50字摘要：

{input_text}

"""
        }
        return prompts.get(agent_id, input_text)


# ============ 智能工作流执行器 ============

class SmartWorkflowExecutor:
    """智能工作流执行器 - 根据配置动态选择 Agent"""
    
    def __init__(self, story_id: str = "default"):
        self.coordinator = AgentCoordinator(story_id)
        self.executor = AgentExecutor(self.coordinator)
        self.execution_log: List[Dict] = []
        
    def run(self, outline: str, agent_sequence: List[str] = None) -> Dict[str, Any]:
        """
        运行智能工作流
        
        Args:
            outline: 故事大纲
            agent_sequence: 指定 Agent 执行顺序，默认使用启用的 Agents
            
        Returns:
            包含所有 Agent 结果的字典
        """
        # 确定要执行的 Agents
        if agent_sequence is None:
            agent_sequence = self.coordinator._get_enabled_agents()
            
        print(f"\n{'='*60}")
        print(f"  Smart Workflow Execution")
        print(f"{'='*60}")
        print(f"  Enabled Agents: {agent_sequence}")
        print(f"{'='*60}\n")
        
        # 初始化状态
        state = {
            "input_text": outline,
            "plan_text": "",
            "conflict_suggestions": [],
            "draft_text": "",
            "edited_text": "",
            "reader_feedback": [],
            "summary_text": "",
            "final_text": ""
        }
        
        total_start = time.time()
        
        # 按顺序执行 Agents
        for i, agent_id in enumerate(agent_sequence):
            print(f"\n[{i+1}/{len(agent_sequence)}] Executing: {agent_id}")
            
            # 准备输入
            input_data = self._prepare_input(agent_id, state)
            
            # 执行
            result = self.executor.execute(agent_id, input_data)
            
            # 记录日志
            self.execution_log.append({
                "agent": agent_id,
                "status": result.get("status"),
                "elapsed": result.get("elapsed", 0),
                "cached": result.get("cached", False)
            })
            
            if result["status"] == "success" and not result.get("cached"):
                # 更新状态
                state = self._update_state(agent_id, result.get("result", ""), state)
                print(f"   Status: OK, Time: {result['elapsed']:.2f}s")
            elif result["status"] == "success" and result.get("cached"):
                print(f"   Status: CACHED (0.00s)")
            else:
                print(f"   Status: SKIPPED - {result.get('reason', 'Unknown')}")
                
        total_time = time.time() - total_start
        
        # 汇总结果
        return {
            "state": state,
            "log": self.execution_log,
            "total_time": total_time,
            "agents_executed": len([l for l in self.execution_log if l["status"] == "success"]),
            "cache_hits": len([l for l in self.execution_log if l.get("cached")])
        }
        
    def _prepare_input(self, agent_id: str, state: Dict) -> Dict[str, Any]:
        """准备 Agent 输入"""
        inputs = {
            "planner": {"text": state.get("input_text", "")},
            "conflict": {"draft_text": state.get("plan_text", "")},
            "writer": {"text": f"{state.get('plan_text', '')}\n\n冲突建议：{state.get('conflict_suggestions', [])}"},
            "editor": {"draft_text": state.get("draft_text", "")},
            "reader": {"draft_text": state.get("edited_text", "")},
            "summary": {"text": state.get("edited_text", "")}
        }
        return inputs.get(agent_id, {"text": state.get("input_text", "")})
        
    def _update_state(self, agent_id: str, result: str, state: Dict) -> Dict:
        """更新状态"""
        mappings = {
            "planner": ("plan_text", result),
            "conflict": ("conflict_suggestions", result.split("\n")),
            "writer": ("draft_text", result),
            "editor": ("edited_text", result),
            "reader": ("reader_feedback", result.split("\n")),
            "summary": ("summary_text", result)
        }
        
        if agent_id in mappings:
            key, value = mappings[agent_id]
            state[key] = value
            
        return state
        
    def run_parallel(self, outline: str, parallel_agents: List[str] = None) -> Dict[str, Any]:
        """
        并行执行多个 Agents
        
        适用于可以同时执行的 Agents（如 conflict 和 summary）
        """
        if parallel_agents is None:
            parallel_agents = ["conflict", "summary"]
            
        # 先执行 planner 和 writer
        state = {"input_text": outline}
        sequential = ["planner", "writer"]
        
        for agent_id in sequential:
            result = self.executor.execute(agent_id, {"text": state.get("input_text", "")})
            state = self._update_state(agent_id, result.get("result", ""), state)
            
        # 并行执行
        with ThreadPoolExecutor(max_workers=len(parallel_agents)) as executor:
            futures = {}
            for agent_id in parallel_agents:
                input_data = self._prepare_input(agent_id, state)
                futures[agent_id] = executor.submit(self.executor.execute, agent_id, input_data)
                
            for agent_id, future in futures.items():
                result = future.result()
                state = self._update_state(agent_id, result.get("result", ""), state)
                
        return state


# ============ 测试函数 ============

def test_smart_workflow():
    """测试智能工作流"""
    print("\n" + "="*60)
    print("  Smart Agent Coordinator Test")
    print("="*60)
    
    # 创建协调器
    coordinator = AgentCoordinator(story_id="test-story")
    
    # 查看启用的 Agents
    enabled = coordinator._get_enabled_agents()
    print(f"\nEnabled Agents: {enabled}")
    
    # 测试执行
    executor = SmartWorkflowExecutor(story_id="test-story")
    
    result = executor.run(
        outline="一个关于青春成长的故事，主角是高中生，面对高考压力找到人生方向",
        agent_sequence=["planner", "writer", "summary"]  # 只执行这3个
    )
    
    print(f"\n{'='*60}")
    print(f"  Results")
    print(f"{'='*60}")
    print(f"Total Time: {result['total_time']:.2f}s")
    print(f"Agents Executed: {result['agents_executed']}")
    print(f"Cache Hits: {result['cache_hits']}")
    
    # 打印执行日志
    print(f"\nExecution Log:")
    for log in result["log"]:
        cached_str = " (cached)" if log.get("cached") else ""
        print(f"  - {log['agent']}: {log['status']} ({log['elapsed']:.2f}s){cached_str}")
        
    # 打印结果预览
    print(f"\nResults Preview:")
    print(f"  Plan: {result['state'].get('plan_text', '')[:100]}...")
    print(f"  Draft: {result['state'].get('draft_text', '')[:100]}...")
    print(f"  Summary: {result['state'].get('summary_text', '')}")
    
    print(f"\n{'='*60}")


def test_full_workflow_timing():
    """完整工作流时间测试"""
    print("\n" + "="*60)
    print("  Full Workflow Timing Test")
    print("="*60)
    
    # 测试不同配置
    configurations = [
        ["planner", "conflict", "writer", "editor", "reader", "summary"],  # 全部
        ["planner", "writer", "editor"],  # 最简
        ["planner", "writer", "summary"],  # 快速
    ]
    
    for i, agents in enumerate(configurations, 1):
        print(f"\n[Test {i}] Agents: {agents}")
        executor = SmartWorkflowExecutor(story_id=f"test-{i}")
        
        result = executor.run(
            outline="一个冒险故事",
            agent_sequence=agents
        )
        
        print(f"  Time: {result['total_time']:.2f}s")
        print(f"  Executed: {result['agents_executed']}")
        

if __name__ == "__main__":
    test_smart_workflow()
    # test_full_workflow_timing()