# -*- coding: utf-8 -*-
"""
core/task_executor.py - Task batch executor with Memory Retrieval integration

execute_batch(tasks, max_tasks) → list of result dicts
Each result: {task_id, agent_id, success, output, duration_ms, memory_ids}
"""

import sys
import time
import json
import importlib
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent.parent  # agent_system/

# ── Dependency pre-check ─────────────────────────────────────────────────────
# Maps module name → pip package name (for error messages)
_REQUIRED_MODULES: dict[str, str] = {
    "json": "json",
    "pathlib": "pathlib",
    "datetime": "datetime",
}

# Optional but important modules — warn instead of raise
_OPTIONAL_MODULES: dict[str, str] = {
    "numpy": "numpy",
    "requests": "requests",
    "httpx": "httpx",
}


def check_dependencies(
    extra_required: dict[str, str] | None = None,
    extra_optional: dict[str, str] | None = None,
) -> dict:
    """
    Validate that required modules are importable before task execution.

    Args:
        extra_required: {module: pip_name} — missing any raises DependencyError
        extra_optional: {module: pip_name} — missing any logs a warning only

    Returns:
        {
            "ok": bool,
            "missing_required": list[str],
            "missing_optional": list[str],
            "checked_at": float,
        }

    Raises:
        DependencyError if any required module is unavailable.
    """
    required = {**_REQUIRED_MODULES, **(extra_required or {})}
    optional = {**_OPTIONAL_MODULES, **(extra_optional or {})}

    missing_required: list[str] = []
    missing_optional: list[str] = []

    for mod, pkg in required.items():
        try:
            importlib.import_module(mod)
        except ImportError:
            missing_required.append(pkg)

    for mod, pkg in optional.items():
        try:
            importlib.import_module(mod)
        except ImportError:
            missing_optional.append(pkg)

    if missing_optional:
        print(
            f"  [DEP:WARN] optional modules unavailable: {missing_optional} "
            f"(install with pip if needed)",
            flush=True,
        )

    result = {
        "ok": len(missing_required) == 0,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "checked_at": time.time(),
    }

    if missing_required:
        raise DependencyError(
            f"dependency_error: missing required modules: {missing_required}. "
            f"Run: pip install {' '.join(missing_required)}"
        )

    return result


class DependencyError(RuntimeError):
    """Raised when a required dependency is missing or incompatible."""
    pass

# ── Memory integration (optional import, graceful fallback) ──────────────────
try:
    sys.path.insert(0, str(BASE_DIR))
    from task_executor import (
        build_memory_context,
        write_memory_feedback,
        _log_memory_event,
        AGENT_PROMPTS,
        SPAWN_CONFIG,
    )
    MEMORY_AVAILABLE = True
except Exception:
    MEMORY_AVAILABLE = False
    AGENT_PROMPTS = {}
    SPAWN_CONFIG = {}

TASK_EXECUTIONS_PATH = BASE_DIR / "task_executions.jsonl"
QUEUE_PATH = BASE_DIR / "task_queue.jsonl"


def _update_task_status(task_id: str, status: str, result: dict) -> None:
    """Update task status in task_queue.jsonl."""
    if not QUEUE_PATH.exists():
        return
    lines = QUEUE_PATH.read_text(encoding="utf-8").strip().split("\n")
    new_lines = []
    for line in lines:
        if not line.strip():
            continue
        try:
            t = json.loads(line)
            if t.get("id") == task_id:
                t["status"] = status
                t["completed_at"] = datetime.now(timezone.utc).isoformat()
                t["result"] = result
            new_lines.append(json.dumps(t, ensure_ascii=False))
        except json.JSONDecodeError:
            new_lines.append(line)
    QUEUE_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def _record_execution(task_id: str, task_type: str, description: str,
                      success: bool, output: str, duration_s: float,
                      agent_id: str) -> None:
    """Append to task_executions.jsonl."""
    entry = {
        "timestamp": time.time(),
        "task_id": task_id,
        "task_type": task_type,
        "description": description,
        "result": {
            "success": success,
            "agent": agent_id,
            "duration": duration_s,
            "output": output[:500] if output else "",
        },
    }
    with open(TASK_EXECUTIONS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _simulate_execute(task: dict) -> dict:
    """
    Simulate task execution (placeholder until real sessions_spawn is wired).
    Returns {success, output, duration_s}.
    """
    t0 = time.time()
    desc = task.get("description", "")
    agent_id = task.get("agent_id", "unknown")
    # Simulate work
    time.sleep(0.05)
    return {
        "success": True,
        "output": f"Task completed by {agent_id} agent",
        "duration_s": round(time.time() - t0, 3),
    }


def execute_batch(tasks: list, max_tasks: int = 5,
                  extra_required: dict | None = None,
                  extra_optional: dict | None = None) -> list:
    """
    Execute a batch of tasks with Memory Retrieval context injection.

    Flow per task:
      0. check_dependencies()              → raises DependencyError on missing deps
      1. build_memory_context(desc, type)  → memory_hints + memory_ids
      2. inject hints into prompt
      3. execute (simulate / real spawn)
      4. write_memory_feedback(task_id, memory_ids, helpful, score, reason)
      5. record to task_executions.jsonl + update queue status

    Args:
        tasks: list of task dicts
        max_tasks: cap on tasks processed
        extra_required: additional {module: pip_name} to treat as required
        extra_optional: additional {module: pip_name} to treat as optional

    Returns list of result dicts.
    Raises DependencyError before any task runs if a required dep is missing.
    """
    # ── Step 0: Dependency pre-check ─────────────────────────────────────────
    dep_result = check_dependencies(extra_required, extra_optional)
    print(
        f"  [DEP:OK] all required dependencies verified "
        f"(optional_missing={dep_result['missing_optional']})",
        flush=True,
    )

    results = []
    for task in tasks[:max_tasks]:
        task_id = task.get("id", "unknown")
        desc = task.get("description", "")
        task_type = task.get("type", task.get("task_type", ""))
        agent_id = task.get("agent_id", "unknown")

        t0 = time.time()
        mem_ctx = {"memory_hints": [], "memory_ids": [], "retrieved_count": 0,
                   "used_count": 0, "latency_ms": 0, "degraded": True}

        # ── Step 1 & 2: Memory context ────────────────────────────────────
        if MEMORY_AVAILABLE:
            try:
                mem_ctx = build_memory_context(desc, task_type)
                _log_memory_event(task_id, mem_ctx, "BUILD")
            except Exception as e:
                print(f"  [MEMORY:BUILD] ERROR {e}", flush=True)

        # ── Step 3: Execute ───────────────────────────────────────────────
        exec_result = _simulate_execute(task)
        duration_s = round(time.time() - t0, 3)
        success = exec_result["success"]
        output = exec_result.get("output", "")

        # ── Step 4: Feedback (success AND failure) ────────────────────────
        if MEMORY_AVAILABLE and mem_ctx["memory_ids"]:
            try:
                write_memory_feedback(
                    task_id=task_id,
                    memory_ids=mem_ctx["memory_ids"],
                    helpful=success,
                    score=1.0 if success else 0.0,
                    reason="task_success" if success else "task_failed",
                )
                print(
                    f"  [MEMORY:FEEDBACK] feedback_written=True "
                    f"ids={len(mem_ctx['memory_ids'])} helpful={success}",
                    flush=True,
                )
            except Exception as e:
                print(f"  [MEMORY:FEEDBACK] ERROR {e}", flush=True)

        # ── Step 5: Record ────────────────────────────────────────────────
        _record_execution(task_id, task_type, desc, success, output, duration_s, agent_id)
        status = "completed" if success else "failed"
        _update_task_status(task_id, status, {"success": success, "output": output})

        # ── DLQ: 失败路径接入 ─────────────────────────────────────────────
        if not success:
            retry_count = task.get("zombie_retries", 0)
            max_retries = task.get("max_retries", 3)
            error_type = exec_result.get("error_type", "unknown")
            last_error = exec_result.get("error", output or "task failed")

            # 路径 1: 重试耗尽
            retry_exhausted = retry_count >= max_retries
            # 路径 2: 不可重试错误（logic_error 不重试）
            non_retryable = error_type == "logic_error"

            if retry_exhausted or non_retryable:
                try:
                    from dlq import enqueue_dead_letter
                    reason = "retry_exhausted" if retry_exhausted else "non_retryable"
                    enqueued = enqueue_dead_letter(
                        task_id=task_id,
                        attempts=retry_count + 1,
                        last_error=str(last_error)[:500],
                        error_type=error_type,
                        metadata={
                            "agent_id": agent_id,
                            "description": desc[:200],
                            "reason": reason,
                        }
                    )
                    if enqueued:
                        print(f"  [DLQ] {task_id}: enqueued ({reason})", flush=True)
                except Exception as dlq_err:
                    print(f"  [DLQ] {task_id}: failed to enqueue: {dlq_err}", flush=True)

        results.append({
            "task_id": task_id,
            "agent_id": agent_id,
            "success": success,
            "output": output,
            "duration_ms": round(duration_s * 1000),
            "memory_ids": mem_ctx["memory_ids"],
            "memory_retrieved": mem_ctx["retrieved_count"],
            "memory_latency_ms": mem_ctx["latency_ms"],
        })

        tag = "✓" if success else "✗"
        print(
            f"  [{tag}] {task_id[:20]} | {agent_id} | "
            f"mem={mem_ctx['used_count']} hints | {round(duration_s*1000)}ms",
            flush=True,
        )

    return results
