"""
worker.py - Isolated task worker for AIOS runtime v2

Runs as a subprocess. Minimal imports. Full fault isolation.
Usage: python worker.py --task-id <id> --task-type <type> --task-desc <desc>
"""

import sys
import os
import json
import time
import argparse
from datetime import datetime, timezone

# Minimal path setup — do NOT import runtime internals
sys.path.insert(0, os.path.dirname(__file__))
from event_log import append_event

RESULTS_LOG = os.path.join(os.path.dirname(__file__), "task_results.jsonl")


def _now():
    return datetime.now(timezone.utc).isoformat()


def save_result(task_id: str, success: bool, output: str = None, error: str = None):
    import portalocker
    record = {
        "timestamp": _now(),
        "task_id": task_id,
        "success": success,
        "output": output,
        "error": error,
    }
    with open(RESULTS_LOG, "a", encoding="utf-8") as f:
        portalocker.lock(f, portalocker.LOCK_EX)
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        portalocker.unlock(f)


def execute_task(task_id: str, task_type: str, task_desc: str) -> tuple[bool, str]:
    """
    Execute the actual task. Currently simulates agent execution.
    Replace this with real agent dispatch when ready.
    """
    # TODO: replace with real agent routing
    # e.g. from agents.coder import CoderAgent; CoderAgent().run(task)
    time.sleep(1)  # simulate work
    return True, f"Task '{task_desc}' executed by {task_type} agent"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--task-type", default="generic")
    parser.add_argument("--task-desc", default="")
    args = parser.parse_args()

    task_id = args.task_id
    task_type = args.task_type
    task_desc = args.task_desc
    worker_id = f"worker-{os.getpid()}"

    # Log: task started
    append_event({
        "timestamp": _now(),
        "task_id": task_id,
        "event": "task_started",
        "worker_id": worker_id,
        "task_type": task_type,
    })

    try:
        success, output = execute_task(task_id, task_type, task_desc)

        if success:
            append_event({
                "timestamp": _now(),
                "task_id": task_id,
                "event": "task_completed",
                "worker_id": worker_id,
                "output": output,
            })
            save_result(task_id, True, output=output)
            sys.exit(0)
        else:
            raise RuntimeError(output)

    except Exception as e:
        append_event({
            "timestamp": _now(),
            "task_id": task_id,
            "event": "task_failed",
            "worker_id": worker_id,
            "error": str(e),
        })
        save_result(task_id, False, error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
