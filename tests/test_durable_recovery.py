"""
Tests for Durable Recovery - Boot-time recovery for timed-out running tasks.
"""
import threading
import pytest
from pathlib import Path
import tempfile
import os

from aios.agent_system.task_queue import TaskQueue, TaskRecord
from aios.agent_system.durable_recovery import DurableRecovery, RecoveryResult


@pytest.fixture
def temp_queue_file():
    """Create a temporary queue file for testing."""
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def task_queue(temp_queue_file):
    """Create a TaskQueue instance for testing."""
    return TaskQueue(queue_file=temp_queue_file)


@pytest.fixture
def durable_recovery(task_queue):
    """Create a DurableRecovery instance for testing."""
    return DurableRecovery(task_queue)


def test_boot_recovery_requeues_timeout_running(task_queue, durable_recovery):
    """Test that timed-out running tasks are requeued with retry_count++."""
    now_ts = 1_700_000_000.0
    
    # Insert a running task that timed out 2 hours ago
    task_queue.enqueue_task(
        task_id="t1",
        payload={"test": "data"},
        max_retries=3,
    )
    task_queue.transition_status(
        task_id="t1",
        from_status="queued",
        to_status="running",
        patch={
            "worker_id": "old_worker",
            "last_heartbeat_at": now_ts - 7200,  # 2 hours ago
        },
    )
    
    # Run recovery
    result = durable_recovery.recover_on_boot(
        worker_id="w1",
        timeout_seconds=300,  # 5 minutes
        now_ts=now_ts,
        scan_limit=1000,
    )
    
    # Verify recovery result
    assert result.scanned == 1
    assert result.recovered_to_queue == 1
    assert result.moved_to_permanent_fail == 0
    assert result.errors == 0
    
    # Verify task state
    task = task_queue.get_task("t1")
    assert task.status == "queued"
    assert task.retry_count == 1
    assert task.worker_id is None
    assert task.last_heartbeat_at is None
    assert task.recover_reason == "boot_recovery"


def test_boot_recovery_respects_max_retries_to_permanent_fail(task_queue, durable_recovery):
    """Test that tasks exceeding max_retries are moved to permanently_failed."""
    now_ts = 1_700_000_000.0
    
    # Insert a running task that has already hit max retries
    task_queue.enqueue_task(
        task_id="t2",
        payload={"test": "data"},
        max_retries=3,
    )
    task_queue.transition_status(
        task_id="t2",
        from_status="queued",
        to_status="running",
        patch={
            "retry_count": 3,  # Already at max
            "worker_id": "old_worker",
            "last_heartbeat_at": now_ts - 7200,
        },
    )
    
    # Run recovery
    result = durable_recovery.recover_on_boot(
        worker_id="w1",
        timeout_seconds=300,
        now_ts=now_ts,
        scan_limit=1000,
    )
    
    # Verify recovery result
    assert result.scanned == 1
    assert result.recovered_to_queue == 0
    assert result.moved_to_permanent_fail == 1
    assert result.errors == 0
    
    # Verify task state
    task = task_queue.get_task("t2")
    assert task.status == "permanently_failed"
    assert task.retry_count == 4
    assert "max_retries_exceeded" in task.recover_reason


def test_double_worker_recovery_only_one_wins_lock(task_queue, durable_recovery):
    """Test that concurrent recovery attempts only succeed once (CAS protection)."""
    now_ts = 1_700_000_000.0
    
    # Insert a timed-out running task
    task_queue.enqueue_task(
        task_id="t3",
        payload={"test": "data"},
        max_retries=3,
    )
    task_queue.transition_status(
        task_id="t3",
        from_status="queued",
        to_status="running",
        patch={
            "worker_id": "old_worker",
            "last_heartbeat_at": now_ts - 7200,
        },
    )
    
    results = []
    
    def run(worker_id: str):
        r = durable_recovery.recover_on_boot(
            worker_id=worker_id,
            timeout_seconds=300,
            now_ts=now_ts,
            scan_limit=1000,
        )
        results.append(r)
    
    # Run two workers concurrently
    th1 = threading.Thread(target=run, args=("w1",))
    th2 = threading.Thread(target=run, args=("w2",))
    th1.start()
    th2.start()
    th1.join()
    th2.join()
    
    # Verify task state
    task = task_queue.get_task("t3")
    assert task.status in ("queued", "permanently_failed")
    assert task.retry_count == 1  # Only recovered once
    
    # Verify only one worker succeeded
    total_requeued = sum(r.recovered_to_queue for r in results)
    total_perm_failed = sum(r.moved_to_permanent_fail for r in results)
    total_effective = total_requeued + total_perm_failed
    assert total_effective == 1  # Only one worker won the CAS
    assert sum(r.scanned for r in results) >= 1


def test_boot_recovery_ignores_healthy_running_tasks(task_queue, durable_recovery):
    """Test that tasks with recent heartbeats are not recovered."""
    now_ts = 1_700_000_000.0
    
    # Insert a healthy running task (heartbeat 1 minute ago)
    task_queue.enqueue_task(
        task_id="t4",
        payload={"test": "data"},
        max_retries=3,
    )
    task_queue.transition_status(
        task_id="t4",
        from_status="queued",
        to_status="running",
        patch={
            "worker_id": "healthy_worker",
            "last_heartbeat_at": now_ts - 60,  # 1 minute ago
        },
    )
    
    # Run recovery with 5-minute timeout
    result = durable_recovery.recover_on_boot(
        worker_id="w1",
        timeout_seconds=300,
        now_ts=now_ts,
        scan_limit=1000,
    )
    
    # Verify no recovery happened
    assert result.scanned == 0
    assert result.recovered_to_queue == 0
    assert result.moved_to_permanent_fail == 0
    
    # Verify task is still running
    task = task_queue.get_task("t4")
    assert task.status == "running"
    assert task.worker_id == "healthy_worker"


def test_boot_recovery_handles_null_heartbeat(task_queue, durable_recovery):
    """Test that tasks with NULL heartbeat are recovered (crashed immediately after start)."""
    now_ts = 1_700_000_000.0
    
    # Insert a running task with no heartbeat (crashed immediately)
    task_queue.enqueue_task(
        task_id="t5",
        payload={"test": "data"},
        max_retries=3,
    )
    task_queue.transition_status(
        task_id="t5",
        from_status="queued",
        to_status="running",
        patch={
            "worker_id": "crashed_worker",
            "last_heartbeat_at": None,  # No heartbeat recorded
        },
    )
    
    # Run recovery
    result = durable_recovery.recover_on_boot(
        worker_id="w1",
        timeout_seconds=300,
        now_ts=now_ts,
        scan_limit=1000,
    )
    
    # Verify recovery happened
    assert result.scanned == 1
    assert result.recovered_to_queue == 1
    
    # Verify task is requeued
    task = task_queue.get_task("t5")
    assert task.status == "queued"
    assert task.retry_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
