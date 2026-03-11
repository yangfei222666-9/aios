"""
Skill Router Schema - 输入输出定义
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class TaskType(str, Enum):
    """任务类型"""
    CODE = "code"
    ANALYSIS = "analysis"
    MONITOR = "monitor"
    BACKUP = "backup"
    LEARNING = "learning"
    ALERT = "alert"
    HEARTBEAT = "heartbeat"
    UNKNOWN = "unknown"


class Priority(str, Enum):
    """优先级"""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class RiskLevel(str, Enum):
    """风险等级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SAFE = "safe"


@dataclass
class TaskContext:
    """标准输入 - 任务上下文"""
    source: str  # 来源（heartbeat/user/system/cron）
    task_type: str  # 任务类型
    content: str  # 任务内容描述
    priority: str  # 优先级
    risk_level: str  # 风险等级
    system_state: Dict[str, Any]  # 当前系统状态
    recent_history: List[Dict[str, Any]]  # 最近历史
    available_handlers: List[str]  # 可用处理器列表

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CandidateHandler:
    """候选处理器"""
    handler_name: str  # 处理器名称
    match_score: float  # 匹配分数（0-100）
    match_reasons: List[str]  # 匹配原因
    reject_reasons: List[str]  # 拒绝原因（如果有）
    capability_match: bool  # 能力匹配
    context_match: bool  # 上下文匹配
    history_score: float  # 历史表现分数（0-100）
    # 分数明细
    l0_score: float  # L0 信号过滤分数
    l1_score: float  # L1 上下文匹配分数
    l2_score: float  # L2 最终决策分数
    final_score: float  # 最终分数（等于 match_score）


@dataclass
class RouterOutput:
    """标准输出 - 路由决策"""
    situation_type: str  # 情况类型
    candidates: List[CandidateHandler]  # 所有候选
    chosen_handler: Optional[str]  # 选中的处理器
    decision_reason: str  # 决策原因
    rejected_handlers: List[Dict[str, Any]]  # 被拒绝的处理器及原因
    confidence: float  # 决策置信度（0-100）
    fallback_handlers: List[str]  # 备选处理器
    routing_metadata: Dict[str, Any]  # 路由元数据

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['candidates'] = [asdict(c) for c in self.candidates]
        return result


@dataclass
class RoutingDecision:
    """完整路由决策记录"""
    task_context: TaskContext
    router_output: RouterOutput
    timestamp: str
    router_version: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_context': self.task_context.to_dict(),
            'router_output': self.router_output.to_dict(),
            'timestamp': self.timestamp,
            'router_version': self.router_version
        }
