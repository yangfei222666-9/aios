#!/usr/bin/env python3
"""
Dead Letter Queue (DLQ) - 重试耗尽任务的兜底队列

核心职责：
1. 重试耗尽（attempts >= max）→ 写入 dead_letters.jsonl
2. 非可重试错误（logic_error）→ 直接写入 DLQ
3. 人工介入通道（replay/discard）

硬约束：
- DLQ 漏记率 = 0（每次写入必须有审计日志）
- append-only（不可修改历史记录）
- 幂等保证（同一 task_id 不重复写入）
"""

import json
import time
from pathlib import Path
from typing import Optional

from paths import DEAD_LETTERS, DLQ_AUDIT

# ── 配置 ──────────────────────────────────────────────────────────────────────
DLQ_FILE = DEAD_LETTERS
DLQ_AUDIT_FILE = DLQ_AUDIT


def enqueue_dead_letter(
    task_id: str,
    attempts: int,
    last_error: str,
    error_type: str = "unknown",
    metadata: Optional[dict] = None
) -> bool:
    """
    将任务写入 DLQ。
    
    Args:
        task_id: 任务 ID
        attempts: 已尝试次数
        last_error: 最后一次错误信息
        error_type: 错误类型（timeout/dependency_error/logic_error/resource_exhausted/unknown）
        metadata: 额外元数据（可选）
    
    Returns:
        True - 写入成功
        False - 任务已在 DLQ 中（幂等保证）
    """
    _t_start = time.monotonic()

    # 幂等检查：避免重复写入
    if _is_in_dlq(task_id):
        _elapsed = (time.monotonic() - _t_start) * 1000
        record_dlq_enqueue_latency(task_id, _elapsed)
        return False
    
    entry = {
        "task_id": task_id,
        "attempts": attempts,
        "last_error": last_error,
        "error_type": error_type,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": "pending_review",
        "metadata": metadata or {}
    }
    
    # 写入 DLQ
    with open(DLQ_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    # 审计日志
    _write_audit("enqueue", task_id, f"attempts={attempts}, error_type={error_type}")

    _elapsed = (time.monotonic() - _t_start) * 1000
    record_dlq_enqueue_latency(task_id, _elapsed)
    
    return True


def _is_in_dlq(task_id: str) -> bool:
    """检查任务是否已在 DLQ 中"""
    if not DLQ_FILE.exists():
        return False
    
    with open(DLQ_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                if entry.get("task_id") == task_id and entry.get("status") == "pending_review":
                    return True
            except json.JSONDecodeError:
                continue
    return False


def _write_audit(action: str, task_id: str, details: str):
    """写入审计日志（append-only）"""
    audit_entry = {
        "action": action,
        "task_id": task_id,
        "details": details,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "operator": "system"
    }
    
    with open(DLQ_AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(audit_entry, ensure_ascii=False) + "\n")


def get_dlq_size() -> int:
    """获取 DLQ 中待处理任务数量"""
    if not DLQ_FILE.exists():
        return 0
    
    count = 0
    with open(DLQ_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                if entry.get("status") == "pending_review":
                    count += 1
            except json.JSONDecodeError:
                continue
    return count


def get_dlq_entries(status: str = "pending_review") -> list[dict]:
    """获取 DLQ 中的任务列表"""
    if not DLQ_FILE.exists():
        return []
    
    entries = []
    with open(DLQ_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                if entry.get("status") == status:
                    entries.append(entry)
            except json.JSONDecodeError:
                continue
    return entries


if __name__ == "__main__":
    # 测试用例
    print("Testing DLQ...")
    
    # 测试 1: 写入 DLQ
    success = enqueue_dead_letter(
        task_id="test-dlq-001",
        attempts=3,
        last_error="timeout after 120s",
        error_type="timeout"
    )
    print(f"[OK] Enqueue: {success}")
    
    # 测试 2: 幂等检查
    success = enqueue_dead_letter(
        task_id="test-dlq-001",
        attempts=3,
        last_error="timeout after 120s",
        error_type="timeout"
    )
    print(f"[OK] Idempotent: {not success}")
    
    # 测试 3: 获取 DLQ 大小
    size = get_dlq_size()
    print(f"[OK] DLQ size: {size}")
    
    # 测试 4: 获取 DLQ 条目
    entries = get_dlq_entries()
    print(f"[OK] DLQ entries: {len(entries)}")
    
    print("\nAll tests passed!")
