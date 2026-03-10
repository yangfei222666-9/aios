# -*- coding: utf-8 -*-
"""
core/task_submitter.py - Unified task queue interface

All reads/writes go through paths.TASK_QUEUE (data/task_queue.jsonl).
Provides: submit_task, list_tasks, queue_stats
"""
import json
import time
import uuid
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paths import TASK_QUEUE


def _task_id(task: dict) -> str:
    """Extract task id, compatible with both 'id' and 'task_id' fields."""
    return task.get("id") or task.get("task_id") or "unknown"


def _load_all() -> list:
    """Load all tasks from the canonical queue file."""
    if not TASK_QUEUE.exists():
        return []
    tasks = []
    with open(TASK_QUEUE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    tasks.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return tasks


def _save_all(tasks: list) -> None:
    """Save all tasks to the canonical queue file (atomic via tmp)."""
    tmp = TASK_QUEUE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for t in tasks:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    if TASK_QUEUE.exists():
        try:
            TASK_QUEUE.unlink()
        except Exception:
            pass
    tmp.replace(TASK_QUEUE)


def submit_task(
    description: str,
    task_type: str = "code",
    priority: str = "normal",
    agent_id: str = "",
    metadata: dict = None,
) -> dict:
    """
    Submit a new task to the queue.
    Returns the created task dict.
    """
    task = {
        "id": f"task-{int(time.time()*1000)}-{uuid.uuid4().hex[:8]}",
        "description": description,
        "type": task_type,
        "priority": priority,
        "agent_id": agent_id,
        "status": "pending",
        "created_at": time.time(),
        "metadata": metadata or {},
    }
    with open(TASK_QUEUE, "a", encoding="utf-8") as f:
        f.write(json.dumps(task, ensure_ascii=False) + "\n")
    return task


def list_tasks(status: str = None, limit: int = 100) -> list:
    """
    List tasks, optionally filtered by status.
    Compatible with both 'id' and 'task_id' field names.
    """
    tasks = _load_all()
    if status:
        tasks = [t for t in tasks if t.get("status") == status]
    return tasks[:limit]


def queue_stats() -> dict:
    """
    Return queue statistics.
    """
    tasks = _load_all()
    by_status = defaultdict(int)
    for t in tasks:
        by_status[t.get("status", "unknown")] += 1
    return {
        "total": len(tasks),
        "by_status": dict(by_status),
    }
