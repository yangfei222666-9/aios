"""
Policy Decision Schema - 策略决策输入输出定义
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class OperationType(str, Enum):
    """操作类型"""
    BACKUP_RESTORE = "backup_restore"
    CODE_MODIFY = "code_modify"
    MONITOR = "monitor"
    ANALYSIS = "analysis"
    ALERT_RESPONSE = "alert_response"
    LEARNING = "learning"
    UNKNOWN = "unknown"


class HandlerType(str, Enum):
    """处理器类型"""
    SKILL = "skill"
    AGENT = "agent"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SystemHealth(str, Enum):
    """系统健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"


class PolicyResult(str, Enum):
    """策略结果"""
    AUTO_EXECUTE = "auto_execute"
    REQUIRE_CONFIRMATION = "require_confirmation"
    DEGRADE = "degrade"
    REJECT = "reject"


class FallbackAction(str, Enum):
    """降级动作"""
    RETRY_LATER = "retry_later"
    USE_BACKUP_HANDLER = "use_backup_handler"
    SWITCH_TO_READONLY = "switch_to_readonly"
    REQUIRE_HUMAN = "require_human"


@dataclass
class PolicyInput:
    """策略决策输入"""
    operation_type: str  # 操作类型
    handler_type: str  # 处理器类型
    handler_name: str  # 处理器名称
    risk_level: str  # 风险等级
    system_health: str  # 系统健康状态
    known_failure_patterns: List[str]  # 已知失败模式
    user_policy: Dict[str, Any]  # 用户策略
    router_decision: Dict[str, Any]  # 路由决策结果
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PolicyOutput:
    """策略决策输出"""
    policy_result: str  # 策略结果
    fallback_action: Optional[str]  # 降级动作
    policy_reason: str  # 策略原因
    matched_rules: List[str]  # 匹配的规则
    risk_summary: Dict[str, Any]  # 风险摘要
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PolicyDecision:
    """完整策略决策记录"""
    policy_input: PolicyInput
    policy_output: PolicyOutput
    timestamp: str
    policy_version: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'policy_input': self.policy_input.to_dict(),
            'policy_output': self.policy_output.to_dict(),
            'timestamp': self.timestamp,
            'policy_version': self.policy_version
        }
