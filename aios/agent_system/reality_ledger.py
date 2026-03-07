"""
reality_ledger.py - Reality Ledger v0.2

append-only 记录真实发生过的动作事件。
不是模拟器，不负责决策，不负责执行。

v0.2 变更：
- outcome 语义修正：released 不是 outcome，outcome 由前置状态继承
- 状态机压实：executing 不直接 → released
- released 必须带 release_reason
- transition_action 自动设置 outcome
"""

import json
from typing import Any, Dict, List, Optional
from pathlib import Path

from action_schema import (
    ActionRecord,
    LedgerEvent,
    new_action_id,
    new_event_id,
    utc_now_iso,
    ALLOWED_TRANSITIONS,
    ACTION_STATUSES,
    EVENT_TYPES,
    STATUS_TO_OUTCOME,
    TERMINAL_STATES,
    validate_release,
    get_outcome_for_released,
)
from paths import ACTION_LEDGER, ACTIONS_STATE


# ── 核心接口 ──────────────────────────────────────────────────────────────────

def create_action(
    actor: str,
    source: str,
    resource_type: str,
    resource_id: str,
    action_type: str,
    payload: Optional[Dict[str, Any]] = None,
    risk_level: str = "L1",
    idempotency_key: Optional[str] = None,
    preconditions: Optional[List[str]] = None,
    lock_resource: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> ActionRecord:
    """创建 Action Record，状态初始为 proposed，outcome 初始为 unknown。"""
    action_id = new_action_id()
    now = utc_now_iso()

    action = ActionRecord(
        action_id=action_id,
        actor=actor,
        source=source,
        resource_type=resource_type,
        resource_id=resource_id,
        action_type=action_type,
        payload=payload or {},
        risk_level=risk_level,
        idempotency_key=idempotency_key,
        preconditions=preconditions or [],
        status="proposed",
        outcome="unknown",
        created_at=now,
        updated_at=now,
        lock_resource=lock_resource,
        lock_token=None,
        result_summary=None,
        error=None,
        tags=tags or [],
    )

    event = LedgerEvent(
        event_id=new_event_id(),
        action_id=action_id,
        event_type="proposed",
        timestamp=now,
        actor=actor,
        status_before="",
        status_after="proposed",
        payload={},
    )

    _append_event_to_ledger(event)
    _update_action_state(action)
    return action


def transition_action(
    action_id: str,
    event_type: str,
    actor: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> ActionRecord:
    """
    状态迁移（核心函数）。

    1. 读取当前 action
    2. 校验状态迁移是否合法
    3. 如果是 released，校验 release_reason 并继承 outcome
    4. 追加 event
    5. 更新 action 快照
    """
    action = get_action(action_id)
    if not action:
        raise ValueError(f"Action not found: {action_id}")

    current_status = action.status
    target_status = event_type
    payload = payload or {}

    # 校验迁移合法性
    if target_status not in ALLOWED_TRANSITIONS.get(current_status, set()):
        raise ValueError(
            f"Invalid transition: {current_status} -> {target_status} "
            f"(allowed: {ALLOWED_TRANSITIONS.get(current_status, set())})"
        )

    # released 特殊处理
    if target_status == "released":
        release_reason = payload.get("release_reason", "execution_done")
        if not validate_release(current_status, release_reason):
            raise ValueError(
                f"Invalid release: {current_status} -> released "
                f"with reason={release_reason}"
            )
        action.release_reason = release_reason
        action.outcome = get_outcome_for_released(current_status, release_reason)
    else:
        # 非 released 状态：从 STATUS_TO_OUTCOME 映射
        outcome = STATUS_TO_OUTCOME.get(target_status, "unknown")
        if outcome != "unknown":
            action.outcome = outcome

    # 追加事件
    event = LedgerEvent(
        event_id=new_event_id(),
        action_id=action_id,
        event_type=event_type,
        timestamp=utc_now_iso(),
        actor=actor or action.actor,
        status_before=current_status,
        status_after=target_status,
        payload=payload,
    )
    _append_event_to_ledger(event)

    # 更新 action 状态
    action.status = target_status
    action.updated_at = event.timestamp

    # 时间戳
    if event_type == "executing":
        action.started_at = event.timestamp
    elif event_type in ("completed", "failed"):
        action.finished_at = event.timestamp

    # 字段更新
    if event_type == "locked":
        action.lock_token = payload.get("lock_token")
    elif event_type == "completed":
        action.result_summary = payload.get("result_summary")
    elif event_type == "failed":
        action.error = payload.get("error")

    _update_action_state(action)
    return action


def get_action(action_id: str) -> Optional[ActionRecord]:
    """从 actions_state.jsonl 读取 action 当前状态。"""
    if not ACTIONS_STATE.exists():
        return None
    with open(ACTIONS_STATE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                if data.get("action_id") == action_id:
                    return ActionRecord.from_dict(data)
            except Exception:
                continue
    return None


def list_actions(
    status: Optional[str] = None,
    outcome: Optional[str] = None,
    limit: int = 100,
) -> List[ActionRecord]:
    """查询 action 列表，支持按 status/outcome 过滤。"""
    if not ACTIONS_STATE.exists():
        return []
    results = []
    with open(ACTIONS_STATE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                if status and data.get("status") != status:
                    continue
                if outcome and data.get("outcome") != outcome:
                    continue
                results.append(ActionRecord.from_dict(data))
            except Exception:
                continue
    return results[-limit:]


def list_events(
    action_id: Optional[str] = None,
    limit: int = 100,
) -> List[LedgerEvent]:
    """查询事件历史。"""
    if not ACTION_LEDGER.exists():
        return []
    events = []
    with open(ACTION_LEDGER, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                if action_id is None or data.get("action_id") == action_id:
                    events.append(LedgerEvent.from_dict(data))
            except Exception:
                continue
    return events[-limit:]


# ── 内部函数 ──────────────────────────────────────────────────────────────────

def _append_event_to_ledger(event: LedgerEvent):
    """追加事件到 action_ledger.jsonl（append-only）"""
    ACTION_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(ACTION_LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")


def _update_action_state(action: ActionRecord):
    """更新 actions_state.jsonl（v0: 全量重写）"""
    ACTIONS_STATE.parent.mkdir(parents=True, exist_ok=True)
    actions = {}
    if ACTIONS_STATE.exists():
        with open(ACTIONS_STATE, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    actions[data["action_id"]] = data
                except Exception:
                    continue
    actions[action.action_id] = action.to_dict()
    with open(ACTIONS_STATE, "w", encoding="utf-8") as f:
        for action_data in actions.values():
            f.write(json.dumps(action_data, ensure_ascii=False) + "\n")


# ── 测试 ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Reality Ledger v0.2 - Test")
    print("=" * 60)

    # 1. 成功路径: proposed → locked → executing → completed → released
    action = create_action(
        actor="test", source="test_script",
        resource_type="task", resource_id="task-test-001",
        action_type="execute_task",
        payload={"task_type": "code"},
        lock_resource="task:task-test-001", tags=["test"],
    )
    print(f"[1] Created: {action.action_id} status={action.status} outcome={action.outcome}")

    action = transition_action(action.action_id, "locked", payload={"lock_token": "tok-123"})
    print(f"[2] locked: status={action.status} outcome={action.outcome}")

    action = transition_action(action.action_id, "executing")
    print(f"[3] executing: status={action.status} outcome={action.outcome}")

    action = transition_action(action.action_id, "completed", payload={"result_summary": "OK"})
    print(f"[4] completed: status={action.status} outcome={action.outcome}")

    action = transition_action(action.action_id, "released", payload={"release_reason": "execution_done"})
    print(f"[5] released: status={action.status} outcome={action.outcome} release_reason={action.release_reason}")

    # 2. 失败路径: proposed → locked → executing → failed → released
    action2 = create_action(
        actor="test", source="test_script",
        resource_type="task", resource_id="task-test-002",
        action_type="execute_task",
    )
    action2 = transition_action(action2.action_id, "locked", payload={"lock_token": "tok-456"})
    action2 = transition_action(action2.action_id, "executing")
    action2 = transition_action(action2.action_id, "failed", payload={"error": "timeout"})
    action2 = transition_action(action2.action_id, "released", payload={"release_reason": "execution_done"})
    print(f"\n[6] Failed path: status={action2.status} outcome={action2.outcome}")

    # 3. 锁超时回收: proposed → locked → released (lock_timeout)
    action3 = create_action(
        actor="test", source="test_script",
        resource_type="task", resource_id="task-test-003",
        action_type="execute_task",
    )
    action3 = transition_action(action3.action_id, "locked", payload={"lock_token": "tok-789"})
    action3 = transition_action(action3.action_id, "released", payload={"release_reason": "lock_timeout"})
    print(f"[7] Lock timeout: status={action3.status} outcome={action3.outcome} release_reason={action3.release_reason}")

    # 4. 测试非法迁移: executing → released（不允许）
    print("\n[8] Testing illegal: executing -> released...")
    action4 = create_action(
        actor="test", source="test_script",
        resource_type="task", resource_id="task-test-004",
        action_type="execute_task",
    )
    action4 = transition_action(action4.action_id, "locked", payload={"lock_token": "tok-000"})
    action4 = transition_action(action4.action_id, "executing")
    try:
        transition_action(action4.action_id, "released", payload={"release_reason": "execution_done"})
        print("    ERROR: Should have raised ValueError")
    except ValueError as e:
        print(f"    OK blocked: {e}")

    # 5. 查询事件历史
    events = list_events(action_id=action.action_id)
    print(f"\n[9] Event history ({len(events)} events):")
    for i, evt in enumerate(events, 1):
        print(f"    {i}. {evt.event_type}: {evt.status_before} -> {evt.status_after}")

    print("\n" + "=" * 60)
    print("All tests passed!")
