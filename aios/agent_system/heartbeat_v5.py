"""
AIOS Heartbeat v5.0 - Task Queue Integration

Automatically processes tasks from the queue.

Changes from v4.0:
- Added task queue processing
- Integrated TaskExecutor
- Auto-execute pending tasks every heartbeat
"""
import sys
import time
from pathlib import Path

# Add AIOS to path
AIOS_ROOT = Path(__file__).resolve().parent.parent
if str(AIOS_ROOT) not in sys.path:
    sys.path.insert(0, str(AIOS_ROOT))

from core.task_submitter import list_tasks, queue_stats
from core.task_executor import execute_batch


def process_task_queue(max_tasks: int = 5) -> dict:
    """
    Process pending tasks from the queue.
    
    Returns:
        Summary of execution
    """
    # Get pending tasks
    tasks = list_tasks(status="pending", limit=max_tasks)
    
    if not tasks:
        return {
            "processed": 0,
            "success": 0,
            "failed": 0,
        }
    
    print(f"[QUEUE] Processing {len(tasks)} pending tasks...")
    
    # Execute tasks
    results = execute_batch(tasks, max_tasks=max_tasks)
    
    # Count results
    success_count = sum(1 for r in results if r["success"])
    failed_count = len(results) - success_count
    
    return {
        "processed": len(results),
        "success": success_count,
        "failed": failed_count,
    }


def check_system_health() -> dict:
    """
    Check system health (simplified version).
    
    Returns:
        Health summary
    """
    stats = queue_stats()
    
    total = stats["total"]
    completed = stats["by_status"].get("completed", 0)
    failed = stats["by_status"].get("failed", 0)
    pending = stats["by_status"].get("pending", 0)
    
    # Calculate health score
    if total == 0:
        health_score = 100.0
    else:
        success_rate = completed / total if total > 0 else 0
        failure_rate = failed / total if total > 0 else 0
        pending_rate = pending / total if total > 0 else 0
        
        # Health score formula (0-100)
        health_score = (
            success_rate * 60 +  # 60 points for success rate
            (1 - failure_rate) * 30 +  # 30 points for low failure rate
            (1 - pending_rate) * 10  # 10 points for low pending rate
        )
    
    return {
        "score": round(health_score, 2),
        "total_tasks": total,
        "completed": completed,
        "failed": failed,
        "pending": pending,
    }


def main():
    """Main heartbeat function."""
    print("AIOS Heartbeat v5.0 Started\n")
    
    # 1. Process task queue
    queue_result = process_task_queue(max_tasks=5)
    
    if queue_result["processed"] > 0:
        print(f"\n[QUEUE] Processed {queue_result['processed']} tasks")
        print(f"  Success: {queue_result['success']}")
        print(f"  Failed: {queue_result['failed']}")
    else:
        print("[QUEUE] No pending tasks")
    
    # 2. Check system health
    print("\n[HEALTH] Checking system health...")
    health = check_system_health()
    
    print(f"   Health Score: {health['score']}/100")
    print(f"   Total Tasks: {health['total_tasks']}")
    print(f"   Completed: {health['completed']}")
    print(f"   Failed: {health['failed']}")
    print(f"   Pending: {health['pending']}")
    
    # Determine health status
    if health['score'] >= 80:
        status = "GOOD"
    elif health['score'] >= 60:
        status = "WARNING"
    else:
        status = "CRITICAL"
    
    print(f"   Status: {status}")
    
    # 3. Output
    if queue_result["processed"] > 0:
        print(f"\nHEARTBEAT_OK (processed={queue_result['processed']}, health={health['score']:.0f})")
    else:
        print(f"\nHEARTBEAT_OK (no_tasks, health={health['score']:.0f})")
    
    print("\nHeartbeat Completed")


if __name__ == "__main__":
    main()
