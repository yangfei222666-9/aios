# -*- coding: utf-8 -*-
"""
Agent Availability Classifier - 统一的 Agent 状态分类器

这是 AIOS 中唯一的 Agent 可用性分类真源。
所有需要判断 Agent 状态的地方都必须调用这个模块，不允许自行解释状态字段。

分类结果只有 4 种：
- active_routable: 活跃且可路由
- schedulable_idle: 可调度但未触发
- shadow: 保留但不路由
- disabled: 已禁用
"""

def classify_agent_availability(agent: dict) -> str:
    """
    统一的 Agent 可用性分类函数
    
    Args:
        agent: Agent 字典，必须包含 enabled, mode, lifecycle_state 字段
    
    Returns:
        分类结果，只能是以下 4 种之一：
        - "active_routable": 活跃且可路由
        - "schedulable_idle": 可调度但未触发
        - "shadow": 保留但不路由
        - "disabled": 已禁用
    
    规则（优先级从高到低）：
    1. mode="shadow" → shadow（无论 enabled 是什么）
    2. mode="disabled" 或 enabled=False → disabled
    3. enabled=True 且 mode="active" 且有任务记录 → active_routable
    4. enabled=True 且 mode="active" 但无任务记录 → schedulable_idle
    """
    enabled = agent.get("enabled", False)
    mode = agent.get("mode", "")
    stats = agent.get("stats", {})
    tasks_total = stats.get("tasks_total", 0)
    
    # Rule 1: Shadow (highest priority)
    if mode == "shadow":
        return "shadow"
    
    # Rule 2: Disabled
    if mode == "disabled" or not enabled:
        return "disabled"
    
    # Rule 3 & 4: Active agents
    if enabled and mode == "active":
        if tasks_total > 0:
            return "active_routable"
        else:
            return "schedulable_idle"
    
    # Fallback (should not happen if data is clean)
    return "disabled"


def classify_all_agents(agents: list) -> dict:
    """
    批量分类所有 Agent
    
    Args:
        agents: Agent 列表
    
    Returns:
        分类结果字典：
        {
            "active_routable": [agent1, agent2, ...],
            "schedulable_idle": [agent3, ...],
            "shadow": [agent4, ...],
            "disabled": [agent5, ...]
        }
    """
    result = {
        "active_routable": [],
        "schedulable_idle": [],
        "shadow": [],
        "disabled": []
    }
    
    for agent in agents:
        bucket = classify_agent_availability(agent)
        result[bucket].append(agent)
    
    return result


def get_routable_count(agents: list) -> int:
    """
    获取可路由 Agent 数量（只包含 active_routable 和 schedulable_idle）
    
    Args:
        agents: Agent 列表
    
    Returns:
        可路由 Agent 数量
    """
    classified = classify_all_agents(agents)
    return len(classified["active_routable"]) + len(classified["schedulable_idle"])


def get_active_ratio(agents: list) -> tuple:
    """
    获取活跃率（active_routable / 可路由总数）
    
    Args:
        agents: Agent 列表
    
    Returns:
        (active_count, routable_count) 元组
    """
    classified = classify_all_agents(agents)
    active_count = len(classified["active_routable"])
    routable_count = active_count + len(classified["schedulable_idle"])
    return (active_count, routable_count)
