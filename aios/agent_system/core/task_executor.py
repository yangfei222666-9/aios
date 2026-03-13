# -*- coding: utf-8 -*-
"""
core/task_executor.py - Task batch executor with Memory Retrieval integration

execute_batch(tasks, max_tasks) 鈫?list of result dicts
Each result: {task_id, agent_id, success, output, duration_ms, memory_ids}
"""

import sys
import time
import json
import importlib
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent.parent  # agent_system/

# Import unified paths
import sys
sys.path.insert(0, str(BASE_DIR))
from paths import TASK_QUEUE as QUEUE_PATH, TASK_EXECUTIONS as TASK_EXECUTIONS_PATH
from reality_ledger import transition_action as _transition_action

# 鈹€鈹€ Dependency pre-check 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
# Maps module name 鈫?pip package name (for error messages)
_REQUIRED_MODULES: dict[str, str] = {
    "json": "json",
    "pathlib": "pathlib",
    "datetime": "datetime",
}

# Optional but important modules 鈥?warn instead of raise
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
        extra_required: {module: pip_name} 鈥?missing any raises DependencyError
        extra_optional: {module: pip_name} 鈥?missing any logs a warning only

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

# 鈹€鈹€ Memory integration (optional import, graceful fallback) 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
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

TASK_EXECUTIONS_PATH = TASK_EXECUTIONS_PATH  # from paths.py
QUEUE_PATH = QUEUE_PATH  # from paths.py


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
            tid = t.get("id") or t.get("task_id")
            if tid == task_id:
                t["status"] = status
                t["completed_at"] = datetime.now(timezone.utc).isoformat()
                t["result"] = result
            new_lines.append(json.dumps(t, ensure_ascii=False))
        except json.JSONDecodeError:
            new_lines.append(line)
    QUEUE_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def _record_execution(task_id: str, task_type: str, description: str,
                      success: bool, output: str, duration_s: float,
                      agent_id: str, retry_count: int = 0,
                      side_effects: dict = None, error: str = None) -> None:
    """
    鏍囧噯鍖栨墽琛岃褰曞啓鍏?task_executions_v2.jsonl锛堢粺涓€ Schema锛?    
    浣跨敤鏂扮殑 ExecutionLogger 纭繚鏍煎紡涓€鑷存€?    """
    try:
        # 瀵煎叆缁熶竴鐨勬墽琛岃褰曞櫒
        sys.path.insert(0, str(BASE_DIR))
        from execution_logger import ExecutionLogger
        
        logger = ExecutionLogger()
        
        # 寮€濮嬩换鍔★紙浣跨敤褰撳墠鏃堕棿浣滀负寮€濮嬫椂闂达級
        now = time.time()
        started_at = now - duration_s
        
        # 鎵嬪姩鏋勫缓浠诲姟鐘舵€侊紙鍥犱负浠诲姟宸茬粡鎵ц瀹岋級
        logger._active_tasks[task_id] = {
            "task_id": task_id,
            "agent_id": agent_id,
            "task_type": task_type,
            "description": description[:500],
            "started_at": started_at,
            "source": "heartbeat",  # 榛樿鏉ユ簮
            "trace_id": None,
            "metadata": side_effects or {},
        }
        
        # 记录完成或失败
        if success:
            logger.complete_task(
                task_id=task_id,
                output_summary=output[:500] if output else "",
                output_full=output,
                tokens=None,
                retry_count=retry_count,
            )
        else:
            # 鎺ㄦ柇閿欒绫诲瀷
            error_type = "unknown"
            if error:
                error_lower = error.lower()
                if "timeout" in error_lower:
                    error_type = "timeout"
                elif "network" in error_lower or "connection" in error_lower:
                    error_type = "network_error"
                elif "model" in error_lower or "api" in error_lower:
                    error_type = "model_error"
            
            logger.fail_task(
                task_id=task_id,
                error_type=error_type,
                error_message=error or output[:1000] if output else "task failed",
                output_full=output,
                retry_count=retry_count,
            )
    except Exception as e:
        # 闄嶇骇锛氬鏋滄柊璁板綍鍣ㄥけ璐ワ紝鍐欏叆鏃ф牸寮忥紙淇濊瘉涓嶄腑鏂級
        print(f"  [EXEC:RECORD] ExecutionLogger failed: {e}, fallback to legacy format", flush=True)
        now = datetime.now(timezone.utc).isoformat()
        status = "completed" if success else "failed"
        
        record = {
            "task_id": task_id,
            "agent_id": agent_id,
            "status": status,
            "start_time": now,
            "end_time": now,
            "duration_ms": round(duration_s * 1000),
            "retry_count": retry_count,
            "side_effects": side_effects or {"files_written": [], "tasks_created": [], "api_calls": 0},
        }
        
        if status == "failed":
            record["error"] = error or output[:200] if output else "task failed"
        if status == "completed":
            record["result"] = {"output": output[:500] if output else "", "task_type": task_type}
        
        with open(TASK_EXECUTIONS_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _real_execute(task: dict) -> dict:
    """
    Real execution: write to spawn_pending.jsonl for heartbeat to call sessions_spawn.
    Returns {success, output, duration_s, spawn_requested}.
    """
    t0 = time.time()
    
    task_id = task.get("id") or task.get("task_id", "unknown")
    agent_id = task.get("agent_id", "unknown")
    desc = task.get("description", "")
    
    # Construct spawn request
    spawn_request = {
        "task_id": task_id,
        "agent_id": agent_id,
        "task": desc,
        "label": f"{agent_id}-{task_id[:8]}",
        "cleanup": "delete",
        "runTimeoutSeconds": 300,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    # Write to spawn_pending.jsonl
    spawn_pending = BASE_DIR / "data" / "spawn_pending.jsonl"
    try:
        spawn_pending.parent.mkdir(parents=True, exist_ok=True)
        with spawn_pending.open("a", encoding="utf-8") as f:
            f.write(json.dumps(spawn_request, ensure_ascii=False) + "\n")
        
        duration_s = round(time.time() - t0, 3)
        return {
            "success": True,
            "output": f"Spawn request created for {agent_id} (task: {desc[:50]}...)",
            "duration_s": duration_s,
            "spawn_requested": True,
        }
    except Exception as e:
        duration_s = round(time.time() - t0, 3)
        return {
            "success": False,
            "output": f"Failed to create spawn request: {e}",
            "duration_s": duration_s,
            "spawn_requested": False,
            "error": str(e),
        }


def execute_batch(tasks: list, max_tasks: int = 5,
                  extra_required: dict | None = None,
                  extra_optional: dict | None = None) -> list:
    """
    Execute a batch of tasks with Memory Retrieval context injection.

    Flow per task:
      0. check_dependencies()              鈫?raises DependencyError on missing deps
      1. build_memory_context(desc, type)  鈫?memory_hints + memory_ids
      2. inject hints into prompt
      3. execute (simulate / real spawn)
      4. write_memory_feedback(task_id, memory_ids, helpful, score, reason)
      5. record to task_executions_v2.jsonl + update queue status

    Args:
        tasks: list of task dicts
        max_tasks: cap on tasks processed
        extra_required: additional {module: pip_name} to treat as required
        extra_optional: additional {module: pip_name} to treat as optional

    Returns list of result dicts.
    Raises DependencyError before any task runs if a required dep is missing.
    """
    # 鈹€鈹€ Step 0: Dependency pre-check 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
    dep_result = check_dependencies(extra_required, extra_optional)
    print(
        f"  [DEP:OK] all required dependencies verified "
        f"(optional_missing={dep_result['missing_optional']})",
        flush=True,
    )

    results = []
    for task in tasks[:max_tasks]:
        task_id = task.get("id") or task.get("task_id") or "unknown"
        desc = task.get("description", "")
        task_type = task.get("type", task.get("task_type", ""))
        agent_id = task.get("agent_id", "unknown")

        t0 = time.time()
        mem_ctx = {"memory_hints": [], "memory_ids": [], "retrieved_count": 0,
                   "used_count": 0, "latency_ms": 0, "degraded": True}
        action_id = task.get("action_id")  # injected by heartbeat
        print(f"  [LEDGER:EXEC] Task {task_id} has action_id={action_id}", flush=True)

        # 鈹€鈹€ Step 1 & 2: Memory context 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
        if MEMORY_AVAILABLE:
            try:
                mem_ctx = build_memory_context(desc, task_type)
                _log_memory_event(task_id, mem_ctx, "BUILD")
            except Exception as e:
                print(f"  [MEMORY:BUILD] ERROR {e}", flush=True)

        # 鈹€鈹€ Step 3: Execute 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
        # Tracing: execution_started
        task_tracer = None
        try:
            from tracer import TaskTracer
            task_tracer = TaskTracer(
                task_id=task_id,
                source="task_executor",
                agent_name=agent_id,
                trace_id=task.get("trace_id"),  # 娌跨敤宸叉湁 trace_id
            )
            task_tracer.started()
        except Exception:
            pass  # trace 鍐欏け璐ヤ笉闃诲涓绘祦绋?
        # Reality Ledger: executing
        if action_id:
            try:
                _transition_action(action_id, "executing", actor=agent_id)
            except Exception as e:
                print(f"  [LEDGER] executing transition failed: {e}", flush=True)

        exec_result = _real_execute(task)
        duration_s = round(time.time() - t0, 3)
        success = exec_result["success"]
        output = exec_result.get("output", "")

        # Reality Ledger: completed / failed
        ledger_terminal_ok = True
        if action_id:
            try:
                if success:
                    _transition_action(action_id, "completed", actor=agent_id,
                                       payload={"result_summary": output[:200]})
                else:
                    _transition_action(action_id, "failed", actor=agent_id,
                                       payload={"error": exec_result.get("error", output[:200])})
            except Exception as e:
                ledger_terminal_ok = False
                print(f"  [LEDGER] terminal transition failed: {e}", flush=True)

        # 鈹€鈹€ Step 4: Feedback (success AND failure) 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
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

        # 鈹€鈹€ Step 5: Record 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
        _record_execution(
            task_id=task_id,
            task_type=task_type,
            description=desc,
            success=success,
            output=output,
            duration_s=duration_s,
            agent_id=agent_id,
            retry_count=task.get("zombie_retries", 0),
            side_effects=None,  # TODO: auto-collect side_effects
            error=exec_result.get("error") if not success else None,
        )
        status = "completed" if success else "failed"
        if action_id and not ledger_terminal_ok:
            print(
                f"  [QUEUE] skip status update because ledger terminal transition failed "
                f"(task_id={task_id}, action_id={action_id})",
                flush=True,
            )
        else:
            _update_task_status(task_id, status, {"success": success, "output": output})

        # Tracing: execution_finished / execution_failed
        if task_tracer:
            try:
                if success:
                    task_tracer.finished(
                        duration_ms=round(duration_s * 1000),
                        result_summary=output[:200] if output else "",
                    )
                else:
                    task_tracer.failed(
                        duration_ms=round(duration_s * 1000),
                        error_type=exec_result.get("error_type", "unknown"),
                        result_summary=output[:200] if output else "task failed",
                    )
            except Exception:
                pass  # trace 鍐欏け璐ヤ笉闃诲涓绘祦绋?
        # 鈹€鈹€ DLQ: 澶辫触璺緞鎺ュ叆 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
        if not success:
            retry_count = task.get("zombie_retries", 0)
            max_retries = task.get("max_retries", 3)
            error_type = exec_result.get("error_type", "unknown")
            last_error = exec_result.get("error", output or "task failed")

            # 璺緞 1: 閲嶈瘯鑰楀敖
            retry_exhausted = retry_count >= max_retries
            # 璺緞 2: 涓嶅彲閲嶈瘯閿欒锛坙ogic_error 涓嶉噸璇曪級
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

        tag = "OK" if success else "FAIL"
        print(
            f"  [{tag}] {task_id[:20]} | {agent_id} | "
            f"mem={mem_ctx['used_count']} hints | {round(duration_s*1000)}ms",
            flush=True,
        )

    return results

