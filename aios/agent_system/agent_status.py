"""
agent_status.py - 太极OS 统一状态词表

核心职责：
1. 定义所有状态常量/枚举
2. 提供状态校验函数
3. 提供默认状态构造器
4. 提供状态映射辅助函数

设计原则：
- 状态词表是唯一真相源（Single Source of Truth）
- 所有状态判断都通过这个模块
- 不允许硬编码状态字符串
- 状态变更必须经过校验

版本：v1.0
最后更新：2026-03-11
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime


# ============================================================================
# 状态词表（三维状态模型）
# ============================================================================

class ReadinessStatus(str, Enum):
    """就绪状态 - 描述对象是否可以进入生产"""
    REGISTERED = "registered"                    # 已注册，但未验证
    EXECUTABLE = "executable"                    # 有执行入口，但未验证
    VALIDATED = "validated"                      # 已验证，但未进入生产
    PRODUCTION_CANDIDATE = "production-candidate"  # 生产候选，观察期
    PRODUCTION_READY = "production-ready"        # 生产就绪
    STABLE = "stable"                            # 稳定运行
    NOT_EXECUTABLE = "not-executable"            # 不可执行（配置在，链路断）
    NOT_EVALUABLE = "not-evaluable"              # 不可评估（缺少必要信息）
    ARCHIVED = "archived"                        # 已归档


class RunStatus(str, Enum):
    """运行状态 - 描述最近一次执行结果"""
    SUCCESS = "success"                          # 成功
    FAILED = "failed"                            # 失败
    TIMEOUT = "timeout"                          # 超时
    ZOMBIE = "zombie"                            # 僵尸（启动但未完成）
    NO_SAMPLE = "no-sample"                      # 无样本（从未运行）
    UNKNOWN = "unknown"                          # 未知


class HealthStatus(str, Enum):
    """健康状态 - 描述整体健康度"""
    HEALTHY = "healthy"                          # 健康
    WARNING = "warning"                          # 警告
    CRITICAL = "critical"                        # 严重
    UNKNOWN = "unknown"                          # 未知


# ============================================================================
# 状态校验
# ============================================================================

def validate_readiness_status(status: str) -> bool:
    """校验就绪状态是否合法"""
    try:
        ReadinessStatus(status)
        return True
    except ValueError:
        return False


def validate_run_status(status: str) -> bool:
    """校验运行状态是否合法"""
    try:
        RunStatus(status)
        return True
    except ValueError:
        return False


def validate_health_status(status: str) -> bool:
    """校验健康状态是否合法"""
    try:
        HealthStatus(status)
        return True
    except ValueError:
        return False


def validate_status_object(obj: Dict[str, Any]) -> tuple[bool, list[str]]:
    """
    校验状态对象是否合法
    
    返回：(是否合法, 错误列表)
    """
    errors = []
    
    # 必需字段
    required_fields = ["readiness_status", "run_status", "health_status", "enabled", "routable"]
    for field in required_fields:
        if field not in obj:
            errors.append(f"Missing required field: {field}")
    
    # 状态字段校验
    if "readiness_status" in obj and not validate_readiness_status(obj["readiness_status"]):
        errors.append(f"Invalid readiness_status: {obj['readiness_status']}")
    
    if "run_status" in obj and not validate_run_status(obj["run_status"]):
        errors.append(f"Invalid run_status: {obj['run_status']}")
    
    if "health_status" in obj and not validate_health_status(obj["health_status"]):
        errors.append(f"Invalid health_status: {obj['health_status']}")
    
    # 布尔字段校验
    for field in ["enabled", "routable"]:
        if field in obj and not isinstance(obj[field], bool):
            errors.append(f"Field {field} must be boolean")
    
    return len(errors) == 0, errors


# ============================================================================
# 默认状态构造器
# ============================================================================

def create_default_agent_status(
    name: str,
    readiness: ReadinessStatus = ReadinessStatus.REGISTERED,
    enabled: bool = False,
    routable: bool = False
) -> Dict[str, Any]:
    """创建默认 Agent 状态对象"""
    return {
        "readiness_status": readiness.value,
        "run_status": RunStatus.NO_SAMPLE.value,
        "health_status": HealthStatus.UNKNOWN.value,
        "enabled": enabled,
        "routable": routable,
        "last_run": None,
        "notes": []
    }


def create_default_skill_status(
    name: str,
    readiness: ReadinessStatus = ReadinessStatus.REGISTERED,
    enabled: bool = False,
    routable: bool = False
) -> Dict[str, Any]:
    """创建默认 Skill 状态对象"""
    return {
        "readiness_status": readiness.value,
        "run_status": RunStatus.NO_SAMPLE.value,
        "health_status": HealthStatus.UNKNOWN.value,
        "enabled": enabled,
        "routable": routable,
        "validation_date": None,
        "validation_status": None,
        "notes": [],
        "next_steps": []
    }


# ============================================================================
# 状态映射辅助函数
# ============================================================================

def map_legacy_status(legacy_status: str) -> ReadinessStatus:
    """
    映射旧状态到新状态词表
    
    用于迁移 agents.json 中的旧状态字段
    """
    mapping = {
        "active": ReadinessStatus.PRODUCTION_READY,
        "stable": ReadinessStatus.STABLE,
        "experimental": ReadinessStatus.PRODUCTION_CANDIDATE,
        "draft": ReadinessStatus.VALIDATED,
        "disabled": ReadinessStatus.ARCHIVED,
        "registered": ReadinessStatus.REGISTERED,
    }
    return mapping.get(legacy_status.lower(), ReadinessStatus.REGISTERED)


def infer_health_from_stats(stats: Dict[str, Any]) -> HealthStatus:
    """
    从统计数据推断健康状态
    
    规则：
    - 成功率 >= 80% → healthy
    - 成功率 60-79% → warning
    - 成功率 < 60% → critical
    - 无数据 → unknown
    """
    if not stats or "tasks_completed" not in stats:
        return HealthStatus.UNKNOWN
    
    completed = stats.get("tasks_completed", 0)
    failed = stats.get("tasks_failed", 0)
    total = completed + failed
    
    if total == 0:
        return HealthStatus.UNKNOWN
    
    success_rate = completed / total
    
    if success_rate >= 0.8:
        return HealthStatus.HEALTHY
    elif success_rate >= 0.6:
        return HealthStatus.WARNING
    else:
        return HealthStatus.CRITICAL


def should_be_routable(obj: Dict[str, Any]) -> bool:
    """
    判断对象是否应该可路由
    
    规则：
    - readiness_status >= production-candidate
    - enabled = true
    - health_status != critical
    """
    readiness = obj.get("readiness_status")
    enabled = obj.get("enabled", False)
    health = obj.get("health_status")
    
    routable_readiness = [
        ReadinessStatus.PRODUCTION_CANDIDATE.value,
        ReadinessStatus.PRODUCTION_READY.value,
        ReadinessStatus.STABLE.value
    ]
    
    return (
        readiness in routable_readiness
        and enabled
        and health != HealthStatus.CRITICAL.value
    )


# ============================================================================
# 状态转换规则
# ============================================================================

def can_transition(
    from_status: ReadinessStatus,
    to_status: ReadinessStatus
) -> tuple[bool, Optional[str]]:
    """
    检查状态转换是否合法
    
    返回：(是否合法, 错误原因)
    """
    # 允许的转换路径
    allowed_transitions = {
        ReadinessStatus.REGISTERED: [
            ReadinessStatus.EXECUTABLE,
            ReadinessStatus.NOT_EXECUTABLE,
            ReadinessStatus.ARCHIVED
        ],
        ReadinessStatus.EXECUTABLE: [
            ReadinessStatus.VALIDATED,
            ReadinessStatus.NOT_EVALUABLE,
            ReadinessStatus.ARCHIVED
        ],
        ReadinessStatus.VALIDATED: [
            ReadinessStatus.PRODUCTION_CANDIDATE,
            ReadinessStatus.ARCHIVED
        ],
        ReadinessStatus.PRODUCTION_CANDIDATE: [
            ReadinessStatus.PRODUCTION_READY,
            ReadinessStatus.VALIDATED,  # 降级
            ReadinessStatus.ARCHIVED
        ],
        ReadinessStatus.PRODUCTION_READY: [
            ReadinessStatus.STABLE,
            ReadinessStatus.PRODUCTION_CANDIDATE,  # 降级
            ReadinessStatus.ARCHIVED
        ],
        ReadinessStatus.STABLE: [
            ReadinessStatus.PRODUCTION_READY,  # 降级
            ReadinessStatus.ARCHIVED
        ],
        ReadinessStatus.NOT_EXECUTABLE: [
            ReadinessStatus.EXECUTABLE,
            ReadinessStatus.ARCHIVED
        ],
        ReadinessStatus.NOT_EVALUABLE: [
            ReadinessStatus.VALIDATED,
            ReadinessStatus.ARCHIVED
        ],
        ReadinessStatus.ARCHIVED: []  # 归档后不可转换
    }
    
    if to_status in allowed_transitions.get(from_status, []):
        return True, None
    else:
        return False, f"Cannot transition from {from_status.value} to {to_status.value}"


# ============================================================================
# 工具函数
# ============================================================================

def get_status_summary(obj: Dict[str, Any]) -> str:
    """生成状态摘要字符串"""
    readiness = obj.get("readiness_status", "unknown")
    run = obj.get("run_status", "unknown")
    health = obj.get("health_status", "unknown")
    enabled = "enabled" if obj.get("enabled", False) else "disabled"
    routable = "routable" if obj.get("routable", False) else "not-routable"
    
    return f"{readiness} / {run} / {health} / {enabled} / {routable}"


def is_production_ready(obj: Dict[str, Any]) -> bool:
    """判断对象是否生产就绪"""
    readiness = obj.get("readiness_status")
    return readiness in [
        ReadinessStatus.PRODUCTION_READY.value,
        ReadinessStatus.STABLE.value
    ]


def is_healthy(obj: Dict[str, Any]) -> bool:
    """判断对象是否健康"""
    health = obj.get("health_status")
    return health == HealthStatus.HEALTHY.value


def needs_attention(obj: Dict[str, Any]) -> bool:
    """判断对象是否需要关注"""
    health = obj.get("health_status")
    run = obj.get("run_status")
    
    return (
        health in [HealthStatus.WARNING.value, HealthStatus.CRITICAL.value]
        or run in [RunStatus.FAILED.value, RunStatus.TIMEOUT.value, RunStatus.ZOMBIE.value]
    )
