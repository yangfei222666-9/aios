"""
event_log.py - Append-only event log for AIOS runtime v2

All state is derived from events. Never mutate, only append.
"""

import json
import os
import portalocker
from datetime import datetime, timezone

EVENT_LOG = os.path.join(os.path.dirname(__file__), "task_events.jsonl")


def _now():
    return datetime.now(timezone.utc).isoformat()


def append_event(event: dict):
    """Append a single event to the log. Thread/process safe via file lock."""
    event.setdefault("timestamp", _now())
    line = json.dumps(event, ensure_ascii=False) + "\n"
    with open(EVENT_LOG, "a", encoding="utf-8") as f:
        portalocker.lock(f, portalocker.LOCK_EX)
        f.write(line)
        portalocker.unlock(f)


def load_events(task_id: str = None) -> list:
    """Load all events, optionally filtered by task_id."""
    if not os.path.exists(EVENT_LOG):
        return []
    events = []
    with open(EVENT_LOG, "r", encoding="utf-8") as f:
        portalocker.lock(f, portalocker.LOCK_SH)
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                if task_id is None or e.get("task_id") == task_id:
                    events.append(e)
            except json.JSONDecodeError:
                pass
        portalocker.unlock(f)
    return events


def get_task_state(task_id: str) -> str:
    """Derive current task state from event log (state machine projection)."""
    events = load_events(task_id)
    state = "unknown"
    for e in events:
        ev = e.get("event")
        if ev == "task_created":
            state = "pending"
        elif ev == "task_started":
            state = "running"
        elif ev == "task_completed":
            state = "completed"
        elif ev == "task_failed":
            state = "failed"
        elif ev == "task_timeout":
            state = "failed"
        elif ev == "task_retry":
            state = "pending"
    return state


def get_all_task_states() -> dict:
    """Return {task_id: state} for all tasks in the log."""
    events = load_events()
    # Process in order — last event wins per task
    states = {}
    for e in events:
        task_id = e.get("task_id")
        if not task_id:
            continue
        ev = e.get("event")
        if ev == "task_created":
            states[task_id] = "pending"
        elif ev == "task_started":
            states[task_id] = "running"
        elif ev == "task_completed":
            states[task_id] = "completed"
        elif ev == "task_failed":
            states[task_id] = "failed"
        elif ev == "task_timeout":
            states[task_id] = "failed"
        elif ev == "task_retry":
            states[task_id] = "pending"
    return states


def get_pending_tasks() -> list:
    """Return list of task_created events whose current state is 'pending'."""
    events = load_events()
    # Build task metadata from task_created events
    created = {}
    for e in events:
        if e.get("event") == "task_created":
            created[e["task_id"]] = e

    states = get_all_task_states()
    pending = []
    for task_id, state in states.items():
        if state == "pending" and task_id in created:
            pending.append(created[task_id])
    return pending
