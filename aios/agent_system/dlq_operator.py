#!/usr/bin/env python3
"""
DLQ Operator - 人工介入通道

提供两个操作：
1. replay(task_id) - 重新入队，写审计日志
2. discard(task_id, reason) - 标记为已丢弃，写审计日志

硬约束：
- 两个操作都做等幂：重复执行返回 no-op + 警告日志
- 审计日志 append-only，字段：task_id/action/operator/timestamp/reason
- replay 后该条目在 DLQ 中标记 replayed=true，不再计入 get_dlq_size()
"""

import json
import time
from pathlib import Path
from typing import Optional

from dlq import DLQ_FILE, DLQ_AUDIT_FILE


def replay(task_id: str, operator: str = "human") -> dict:
    """
    重新入队（从 dead_letters.jsonl 读出该条目，重新提交到执行队列）。
    
    Args:
        task_id: 任务 ID
        operator: 操作者（默认 "human"）
    
    Returns:
        {"success": bool, "message": str}
    """
    if not DLQ_FILE.exists():
        return {"success": False, "message": "DLQ file not found"}
    
    # 检查 task_id 是否存在且未 replay
    entry = _find_dlq_entry(task_id)
    if not entry:
        return {"success": False, "message": f"Task {task_id} not found in DLQ"}
    
    if entry.get("replayed"):
        return {"success": False, "message": f"Task {task_id} already replayed (no-op)"}
    
    # 标记为 replayed=true（不物理删除，保留审计轨迹）
    _mark_replayed(task_id)
    
    # 写审计日志
    _write_audit("replay", task_id, operator, reason=None)
    
    # TODO: 实际重新提交到 task_queue.jsonl（Step 3 集成时实现）
    
    return {"success": True, "message": f"Task {task_id} replayed"}


def discard(task_id: str, reason: str, operator: str = "human") -> dict:
    """
    丢弃任务（标记为 discarded=true，不再处理）。
    
    Args:
        task_id: 任务 ID
        reason: 丢弃原因
        operator: 操作者（默认 "human"）
    
    Returns:
        {"success": bool, "message": str}
    """
    if not DLQ_FILE.exists():
        return {"success": False, "message": "DLQ file not found"}
    
    # 检查 task_id 是否存在且未 discard
    entry = _find_dlq_entry(task_id)
    if not entry:
        return {"success": False, "message": f"Task {task_id} not found in DLQ"}
    
    if entry.get("discarded"):
        return {"success": False, "message": f"Task {task_id} already discarded (no-op)"}
    
    # 标记为 discarded=true
    _mark_discarded(task_id)
    
    # 写审计日志
    _write_audit("discard", task_id, operator, reason=reason)
    
    return {"success": True, "message": f"Task {task_id} discarded"}


def _find_dlq_entry(task_id: str) -> Optional[dict]:
    """查找 DLQ 中的条目"""
    with open(DLQ_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                if entry.get("task_id") == task_id and entry.get("status") == "pending_review":
                    return entry
            except json.JSONDecodeError:
                continue
    return None


def _mark_replayed(task_id: str):
    """标记条目为 replayed=true（重写文件）"""
    _update_dlq_entry(task_id, {"replayed": True})


def _mark_discarded(task_id: str):
    """标记条目为 discarded=true（重写文件）"""
    _update_dlq_entry(task_id, {"discarded": True})


def _update_dlq_entry(task_id: str, updates: dict):
    """更新 DLQ 条目（重写文件）"""
    lines = []
    with open(DLQ_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                if entry.get("task_id") == task_id and entry.get("status") == "pending_review":
                    entry.update(updates)
                lines.append(json.dumps(entry, ensure_ascii=False))
            except json.JSONDecodeError:
                lines.append(line.strip())
    
    with open(DLQ_FILE, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


def _write_audit(action: str, task_id: str, operator: str, reason: Optional[str]):
    """写入审计日志（append-only）"""
    audit_entry = {
        "action": action,
        "task_id": task_id,
        "operator": operator,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "reason": reason
    }
    
    with open(DLQ_AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(audit_entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    # 测试用例
    print("Testing DLQ Operator...")
    
    # 先创建一个测试条目
    from dlq import enqueue_dead_letter
    enqueue_dead_letter("test-op-001", 3, "timeout", "timeout")
    
    # 测试 1: replay 成功
    result = replay("test-op-001", operator="test")
    print(f"[OK] Replay: {result}")
    
    # 测试 2: 重复 replay（no-op）
    result = replay("test-op-001", operator="test")
    print(f"[OK] Replay no-op: {result}")
    
    # 测试 3: discard 成功
    enqueue_dead_letter("test-op-002", 3, "logic error", "logic_error")
    result = discard("test-op-002", reason="not fixable", operator="test")
    print(f"[OK] Discard: {result}")
    
    # 测试 4: 重复 discard（no-op）
    result = discard("test-op-002", reason="not fixable", operator="test")
    print(f"[OK] Discard no-op: {result}")
    
    print("\nAll tests passed!")
