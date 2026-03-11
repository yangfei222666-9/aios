"""
Decide and Dispatch Schema - 统一入口输入输出定义
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class InputSource(str, Enum):
    """输入来源"""
    TASK = "task"
    EVENT = "event"
    ALERT = "alert"
    HEARTBEAT = "heartbeat"


class FinalStatus(str, Enum):
    """最终状态"""
    PLANNED = "planned"
    DISPATCHED = "dispatched"
    DEGRADED = "degraded"
    BLOCKED = "blocked"
    FAILED = "failed"


class DispatchMode(str, Enum):
    """派发模式"""
    REAL = "real"
    SIMULATED = "simulated"
    DEGRADED = "degraded"


@dataclass
class TaskContext:
    """标准输入 - 任务上下文"""
    source: str  # 来源（task/event/alert/heartbeat）
    task_type: str  # 任务类型
    content: str  # 任务内容
    priority: str  # 优先级
    risk_level: str  # 风险等级
    system_state: Dict[str, Any]  # 系统状态
    recent_history: List[Dict[str, Any]]  # 最近历史
    available_handlers: List[str]  # 可用处理器
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionPlan:
    """执行计划"""
    handler: str  # 处理器
    mode: str  # 模式（real/simulated/degraded）
    steps: List[str]  # 执行步骤
    fallback: Optional[str]  # 降级方案
    expected_output: str  # 期望输出
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DispatchResult:
    """派发结果"""
    status: str  # 状态（dispatched/degraded/blocked/failed）
    handler_used: Optional[str]  # 实际使用的处理器
    execution_time: float  # 执行时间（秒）
    output: Optional[str]  # 输出
    error: Optional[str]  # 错误信息
    fallback_triggered: bool  # 是否触发降级
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionRecord:
    """标准输出 - 决策记录"""
    current_situation: str  # 当前情况
    router_result: Dict[str, Any]  # 路由结果
    policy_result: Dict[str, Any]  # 策略结果
    chosen_handler: Optional[str]  # 选中的处理器
    execution_plan: Optional[ExecutionPlan]  # 执行计划
    dispatch_result: Optional[DispatchResult]  # 派发结果
    observation: Dict[str, Any]  # 观测数据
    memory_writeback: Dict[str, Any]  # 记忆回写
    final_status: str  # 最终状态
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'current_situation': self.current_situation,
            'router_result': self.router_result,
            'policy_result': self.policy_result,
            'chosen_handler': self.chosen_handler,
            'execution_plan': self.execution_plan.to_dict() if self.execution_plan else None,
            'dispatch_result': self.dispatch_result.to_dict() if self.dispatch_result else None,
            'observation': self.observation,
            'memory_writeback': self.memory_writeback,
            'final_status': self.final_status
        }
        return result


@dataclass
class DispatchDecision:
    """完整派发决策记录"""
    task_context: TaskContext
    decision_record: DecisionRecord
    timestamp: str
    dispatch_version: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_context': self.task_context.to_dict(),
            'decision_record': self.decision_record.to_dict(),
            'timestamp': self.timestamp,
            'dispatch_version': self.dispatch_version
        }
