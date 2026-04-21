"""
Agent 评估矩阵 - 基于 Agent 职责的评估规则

定义了每个 Agent 完成后应该由谁来评估，以及评估什么维度
"""

# Agent 评估矩阵
# key: 刚完成的 Agent
# value: 应该参与评估的 Agent 列表 + 评估优先级
AGENT_EVALUATION_MATRIX = {
    "planner": {
        "evaluators": ["editor", "consistency"],  # 结构合理 + 一致性
        "reasons": {
            "editor": "评估章节结构是否合理",
            "consistency": "检查大纲逻辑一致性",
        },
        "default_rounds": 1,
    },
    "conflict": {
        "evaluators": ["critic", "consistency"],  # 冲突有效性 + 逻辑
        "reasons": {
            "critic": "评估冲突设计是否合理",
            "consistency": "检查冲突与世界观的一致性",
        },
        "default_rounds": 1,
    },
    "writer": {
        "evaluators": ["reader", "critic", "editor"],  # 阅读体验 + 逻辑 + 结构
        "reasons": {
            "reader": "评估阅读体验和情感共鸣",
            "critic": "评估情节逻辑和人物行为",
            "editor": "评估语言表达和结构",
        },
        "default_rounds": 2,
    },
    "editor": {
        "evaluators": ["reader", "consistency"],  # 阅读体验 + 一致性
        "reasons": {
            "reader": "评估修订后的阅读体验",
            "consistency": "检查修订后的一致性",
        },
        "default_rounds": 1,
    },
    "consistency": {
        "evaluators": ["critic"],  # 一致性问题需要 critic 评估
        "reasons": {
            "critic": "评估一致性问题的严重性",
        },
        "default_rounds": 1,
    },
    "reader": {
        "evaluators": ["editor"],  # 读者反馈需要编辑整理
        "reasons": {
            "editor": "整理读者反馈为改进建议",
        },
        "default_rounds": 1,
    },
    "critic": {
        "evaluators": ["editor"],  # 批评需要编辑转化为建议
        "reasons": {
            "editor": "将批评转化为可操作的建议",
        },
        "default_rounds": 1,
    },
    "summary": {
        "evaluators": [],  # 摘要不需要评估
        "reasons": {},
        "default_rounds": 0,
    },
}

# 特殊规则
SPECIAL_RULES = {
    # 如果内容很短，跳过某些评估
    "skip_heavy_evaluation": lambda content: len(content) < 500,
    # 如果用户需求明确不需要评估
    "skip_if_user_said": lambda requirement: "不需要评估" in requirement or "不需要反馈" in requirement,
}

# 评估优先级（数字越大优先级越高）
EVALUATOR_PRIORITY = {
    "consistency": 10,  # 一致性最高优先级
    "critic": 8,
    "editor": 6,
    "reader": 4,
    "summary": 2,
}


def get_evaluators_for_agent(agent_id: str, enabled_agents: list) -> list:
    """
    获取某个 Agent 完成后应该由哪些 Agent 评估
    
    Args:
        agent_id: 刚完成的 Agent
        enabled_agents: 当前启用的 Agent 列表
    
    Returns:
        应该参与评估的 Agent 列表
    """
    if agent_id not in AGENT_EVALUATION_MATRIX:
        return []
    
    evaluators = AGENT_EVALUATION_MATRIX[agent_id]["evaluators"]
    
    # 过滤掉未启用的 Agent
    return [e for e in evaluators if e in enabled_agents]


def get_evaluation_config(agent_id: str) -> dict:
    """获取某个 Agent 的评估配置"""
    return AGENT_EVALUATION_MATRIX.get(agent_id, {
        "evaluators": [],
        "reasons": {},
        "default_rounds": 0,
    })
