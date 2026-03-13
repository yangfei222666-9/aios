"""
Durable Recovery - Boot-time recovery for timed-out running tasks.
"""
from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Optional
from .task_queue import TaskQueue, TaskRecord


@dataclass
class RecoveryResult:
    """Result of a recovery operation."""
    scanned: int = 0
    recovered_to_queue: int = 0
    moved_to_permanent_fail: int = 0
    errors: int = 0


class DurableRecovery:
    """Handles boot-time recovery of timed-out running tasks."""
    
    def __init__(self, task_queue: TaskQueue):
        self.task_queue = task_queue
    
    def recover_on_boot(
        self,
        worker_id: str,
        timeout_seconds: int,
        now_ts: Optional[float] = None,
        scan_limit: int = 1000,
    ) -> RecoveryResult:
        """
        Recover timed-out running tasks on boot.
        
        For each timed-out task:
        - If retry_count < max_retries: requeue (status → queued, retry_count++)
        - If retry_count >= max_retries: permanent fail (status → permanently_failed)
        
        Uses atomic CAS to prevent double recovery by concurrent workers.
        """
        if now_ts is None:
            now_ts = time.time()
        
        result = RecoveryResult()
        
        # Find all recoverable running tasks
        tasks = self.task_queue.list_recoverable_running(
            now_ts=now_ts,
            timeout_seconds=timeout_seconds,
            limit=scan_limit,
        )
        
        result.scanned = len(tasks)
        
        for task in tasks:
            try:
                if self._recover_single_task(task, worker_id, now_ts):
                    if task.retry_count >= task.max_retries:
                        result.moved_to_permanent_fail += 1
                    else:
                        result.recovered_to_queue += 1
            except Exception as e:
                result.errors += 1
                print(f"[ERROR] Failed to recover task {task.task_id}: {e}")
        
        return result
    
    def _recover_single_task(
        self,
        task: TaskRecord,
        worker_id: str,
        now_ts: float,
    ) -> bool:
        """
        Recover a single task using atomic CAS.
        Returns True if recovery succeeded, False if another worker won the race.
        """
        # Check if we should requeue or permanently fail
        new_retry_count = task.retry_count + 1
        
        if new_retry_count > task.max_retries:
            # Permanent failure
            success = self.task_queue.transition_status(
                task_id=task.task_id,
                from_status="running",
                to_status="permanently_failed",
                patch={
                    "retry_count": new_retry_count,
                    "worker_id": None,
                    "last_heartbeat_at": None,
                    "recovered_at": now_ts,
                    "recovered_by": worker_id,
                    "recover_reason": f"boot_recovery:max_retries_exceeded",
                },
            )
        else:
            # Requeue for retry
            success = self.task_queue.transition_status(
                task_id=task.task_id,
                from_status="running",
                to_status="pending",
                patch={
                    "retry_count": new_retry_count,
                    "worker_id": None,
                    "last_heartbeat_at": None,
                    "recovered_at": now_ts,
                    "recovered_by": worker_id,
                    "recover_reason": "boot_recovery",
                },
            )
        
        return success
