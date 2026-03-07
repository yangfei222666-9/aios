"""
action_schema.py - 动作状态机常量 + 数据结构

这是 REALITY_LEDGER.md 的代码实现约束。
文档是规范，代码常量是真实约束。

v0.2 (2026-03-07):
  - outcome 移除 released（released 是生命周期终态，不是执行结果）
  - 状态机压实：executing 不直接 → released，必须先 → failed
  - locked → released 仅限锁超时回收，必须带 release_reason
  - completed/failed → released 是唯一的正常 released 入口
  - 新增 RELEASE_REASONS 枚举
  - 新增 ActionRecord / LedgerEvent dataclass
"""

from __future__ import annotations
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set


# ══════════════════════════════════════════════════════════════
# 常量定义
# ══════════════════════════════════════════════════════════════

# Status 值（生命周期阶段）- 8 个
ACTION_STATUSES: Set[str] = {
    "proposed",     # 已提议，等待锁定
    "locked",       # 已锁定，等待执行
    "executing",    # 正在执行
    "completed",    # 执行成功（中间态，等待 released）
    "failed",       # 执行失败（中间态，等待 released）
    "released",     # 资源已释放，生命周期结束（终态）
    "skipped",      # 被跳过（终态）
    "rejected",     # 被拒绝（终态）
}

# 兼容旧名
STATUS_VALUES = ACTION_STATUSES

# Outcome 值（执行结果）- 5 个
OUTCOME_VALUES: Set[str] = {
    "unknown",      # 未完成（proposed/locked/executing）
    "completed",    # 成功完成
    "failed",       # 执行失败
    "skipped",      # 被跳过
    "rejected",     # 被拒绝
}
# 注意：released 不在 outcome 里。released 是生命周期终态，不是执行结果。

# 合法状态迁移（压实版）
ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    # 主链
    "proposed":  {"locked", "skipped", "rejected"},
    "locked":    {"executing", "released"},       # locked→released 仅限锁超时回收
    "executing": {"completed", "failed"},          # 不允许 executing→released
    "completed": {"released"},                     # 成功后释放
    "failed":    {"released"},                     # 失败后释放
    # 终态
    "released":  set(),
    "skipped":   set(),
    "rejected":  set(),
}

# 终态集合
TERMINAL_STATES: Set[str] = {"released", "skipped", "rejected"}

# 注意：completed 和 failed 不是终态！它们还要 → released。
# 但它们是"结果已确定"的状态。
OUTCOME_DETERMINED_STATES: Set[str] = {"completed", "failed", "skipped", "rejected"}

# released 的合法 release_reason
RELEASE_REASONS: Set[str] = {
    "execution_done",   # 正常执行完毕（completed/failed → released）
    "lock_timeout",     # 锁超时回收（locked → released）
    "manual_cancel",    # 人工取消（locked → released）
    "cleanup",          # 系统清理（locked → released）
}

# Status → Outcome 映射
# released 的 outcome 取决于它从哪个状态来，不在这里硬编码
STATUS_TO_OUTCOME: Dict[str, str] = {
    "proposed":  "unknown",
    "locked":    "unknown",
    "executing": "unknown",
    "completed": "completed",
    "failed":    "failed",
    "skipped":   "skipped",
    "rejected":  "rejected",
    # released 的 outcome 由 transition 时从前置状态继承
}

# Event Types（审计事件类型）
EVENT_TYPES: Set[str] = {
    "proposed", "locked", "executing",
    "completed", "failed", "released",
    "skipped", "rejected",
    "illegal_transition_blocked",
}

# 状态描述（用于日志和报告）
STATUS_DESCRIPTIONS: Dict[str, str] = {
    "proposed":  "已提议，等待锁定",
    "locked":    "已锁定，等待执行",
    "executing": "正在执行",
    "completed": "执行成功",
    "failed":    "执行失败",
    "released":  "资源已释放，生命周期结束",
    "skipped":   "被跳过（条件不满足）",
    "rejected":  "被拒绝（幂等/冲突）",
}

OUTCOME_DESCRIPTIONS: Dict[str, str] = {
    "unknown":   "未完成",
    "completed": "成功完成",
    "failed":    "执行失败",
    "skipped":   "被跳过",
    "rejected":  "被拒绝",
}


# ══════════════════════════════════════════════════════════════
# 数据结构
# ══════════════════════════════════════════════════════════════

def new_action_id() -> str:
    return f"act-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"

def new_event_id() -> str:
    return f"evt-{uuid.uuid4().hex[:12]}"

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


@dataclass
class ActionRecord:
    action_id: str
    actor: str
    source: str
    resource_type: str
    resource_id: str
    action_type: str
    status: str = "proposed"
    outcome: str = "unknown"
    payload: Dict[str, Any] = field(default_factory=dict)
    risk_level: str = "L1"
    idempotency_key: Optional[str] = None
    preconditions: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    lock_resource: Optional[str] = None
    lock_token: Optional[str] = None
    release_reason: Optional[str] = None
    result_summary: Any = None
    error: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ActionRecord":
        # 过滤掉不在 __init__ 里的字段
        valid = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in d.items() if k in valid})


@dataclass
class LedgerEvent:
    event_id: str
    action_id: str
    event_type: str
    timestamp: str
    actor: str
    status_before: str
    status_after: str
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LedgerEvent":
        valid = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in d.items() if k in valid})


# ══════════════════════════════════════════════════════════════
# 校验函数
# ══════════════════════════════════════════════════════════════

def validate_transition(from_status: str, to_status: str) -> bool:
    """验证状态迁移是否合法"""
    if from_status not in STATUS_VALUES:
        raise ValueError(f"Invalid from_status: {from_status}")
    if to_status not in STATUS_VALUES:
        raise ValueError(f"Invalid to_status: {to_status}")
    return to_status in ALLOWED_TRANSITIONS.get(from_status, set())


def is_terminal(status: str) -> bool:
    """判断是否为终态（released/skipped/rejected）"""
    return status in TERMINAL_STATES


def get_outcome_for_released(from_status: str, release_reason: str) -> str:
    """
    released 事件的 outcome 取决于从哪个状态来。

    completed → released: outcome=completed
    failed → released:    outcome=failed
    locked → released:    outcome=unknown（未执行，系统回收）
    """
    if from_status == "completed":
        return "completed"
    elif from_status == "failed":
        return "failed"
    elif from_status == "locked":
        # 未执行就释放，outcome 保持 unknown
        return "unknown"
    else:
        return "unknown"


def validate_release(from_status: str, release_reason: str) -> bool:
    """
    校验 released 事件是否合法。

    规则：
    - completed/failed → released: release_reason 必须是 execution_done
    - locked → released: release_reason 必须是 lock_timeout/manual_cancel/cleanup
    - 其他 → released: 不允许
    """
    if from_status in ("completed", "failed"):
        return release_reason == "execution_done"
    elif from_status == "locked":
        return release_reason in ("lock_timeout", "manual_cancel", "cleanup")
    else:
        return False


def validate_status_outcome_pair(status: str, outcome: str) -> bool:
    """验证 status 和 outcome 的组合是否合法"""
    if status in ("proposed", "locked", "executing"):
        return outcome == "unknown"
    if status == "completed":
        return outcome == "completed"
    if status == "failed":
        return outcome == "failed"
    if status == "skipped":
        return outcome == "skipped"
    if status == "rejected":
        return outcome == "rejected"
    if status == "released":
        # released 的 outcome 继承自前置状态，可以是 completed/failed/unknown
        return outcome in ("completed", "failed", "unknown")
    return False
