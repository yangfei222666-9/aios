"""
dispatcher.py - Task dispatcher for AIOS runtime v2

Heartbeat calls dispatcher.tick() each cycle.
Dispatcher manages worker lifecycle: spawn, monitor, timeout, cleanup.
"""

import os
import sys
import time
import subprocess
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
from event_log import append_event, get_pending_tasks

WORKER_SCRIPT = os.path.join(os.path.dirname(__file__), "worker.py")
PYTHON = sys.executable

# Tune these as the system grows
MAX_WORKERS = 1       # Start conservative; bump to 4 once stable
TASK_TIMEOUT = 300    # 5 minutes — covers P99 of 10-30s tasks with headroom


def _now():
    return datetime.now(timezone.utc).isoformat()


class Dispatcher:
    def __init__(self):
        # {task_id: {"proc": Popen, "start_time": float, "worker_id": str}}
        self.running_workers: dict = {}

    def tick(self):
        """One control loop cycle. Call from Heartbeat."""
        self._cleanup_finished_workers()
        self._kill_timed_out_workers()

        if len(self.running_workers) >= MAX_WORKERS:
            return  # pool full

        pending = get_pending_tasks()
        # Skip tasks already running
        running_ids = set(self.running_workers.keys())
        available = [t for t in pending if t["task_id"] not in running_ids]

        if not available:
            return

        task = available[0]  # FIFO — add priority sort later
        self._spawn_worker(task)

    def _spawn_worker(self, task: dict):
        task_id = task["task_id"]
        task_type = task.get("task_type", "generic")
        task_desc = task.get("description", "")
        worker_id = f"worker-{task_id[:8]}"

        proc = subprocess.Popen(
            [
                PYTHON, WORKER_SCRIPT,
                "--task-id", task_id,
                "--task-type", task_type,
                "--task-desc", task_desc,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        self.running_workers[task_id] = {
            "proc": proc,
            "start_time": time.time(),
            "worker_id": worker_id,
        }

        print(f"[DISPATCH] Spawned {worker_id} for task {task_id} (type={task_type})")

    def _cleanup_finished_workers(self):
        finished = []
        for task_id, info in self.running_workers.items():
            ret = info["proc"].poll()
            if ret is not None:
                finished.append(task_id)
                duration = time.time() - info["start_time"]
                status = "completed" if ret == 0 else "failed"
                print(f"[DISPATCH] Worker {info['worker_id']} finished: {status} in {duration:.1f}s")

        for task_id in finished:
            del self.running_workers[task_id]

    def _kill_timed_out_workers(self):
        now = time.time()
        timed_out = []
        for task_id, info in self.running_workers.items():
            elapsed = now - info["start_time"]
            if elapsed > TASK_TIMEOUT:
                timed_out.append(task_id)

        for task_id in timed_out:
            info = self.running_workers[task_id]
            print(f"[DISPATCH] Timeout! Killing worker {info['worker_id']} after {TASK_TIMEOUT}s")
            try:
                info["proc"].kill()
            except Exception:
                pass
            append_event({
                "timestamp": _now(),
                "task_id": task_id,
                "event": "task_timeout",
                "worker_id": info["worker_id"],
                "elapsed": TASK_TIMEOUT,
            })
            del self.running_workers[task_id]

    def status(self) -> dict:
        return {
            "running_workers": len(self.running_workers),
            "max_workers": MAX_WORKERS,
            "worker_ids": [v["worker_id"] for v in self.running_workers.values()],
        }


# Singleton for use in Heartbeat
_dispatcher = Dispatcher()


def tick():
    """Entry point for Heartbeat: dispatcher.tick()"""
    _dispatcher.tick()


def status():
    return _dispatcher.status()
