"""
selflearn-state.json 最小 schema

目标：让学习系统状态可观测，不追求完整学习闭环。

Version: 1.0
Created: 2026-03-11
"""

from typing import Literal, TypedDict
from datetime import datetime


class SelfLearnState(TypedDict):
    """selflearn-state.json 最小结构"""
    
    # 时间戳
    updated_at: str  # ISO 8601 格式
    last_run_at: str | None  # 最后一次任意学习 Agent 运行时间
    last_success_at: str | None  # 最后一次成功运行时间
    
    # 最后执行的 Agent
    last_agent: str | None  # Agent ID
    
    # 学习循环状态
    learning_loop_status: Literal["healthy", "degraded", "blocked", "unknown"]
    
    # 计数
    validated_learning_agents_count: int  # 已验证的学习 Agent 数量
    active_learning_agents_count: int  # 活跃的学习 Agent 数量（近 7 天有运行）
    pending_lessons_count: int  # 待处理的 lesson 数量
    rules_derived_count: int  # 已提炼的规则数量


def get_default_state() -> SelfLearnState:
    """返回默认状态"""
    return {
        "updated_at": datetime.now().isoformat(),
        "last_run_at": None,
        "last_success_at": None,
        "last_agent": None,
        "learning_loop_status": "unknown",
        "validated_learning_agents_count": 0,
        "active_learning_agents_count": 0,
        "pending_lessons_count": 0,
        "rules_derived_count": 0,
    }


def validate_state(state: dict) -> bool:
    """验证 state 结构是否合法"""
    required_keys = {
        "updated_at",
        "last_run_at",
        "last_success_at",
        "last_agent",
        "learning_loop_status",
        "validated_learning_agents_count",
        "active_learning_agents_count",
        "pending_lessons_count",
        "rules_derived_count",
    }
    
    if not all(key in state for key in required_keys):
        return False
    
    if state["learning_loop_status"] not in ["healthy", "degraded", "blocked", "unknown"]:
        return False
    
    return True
