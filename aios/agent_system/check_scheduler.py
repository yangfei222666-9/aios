#!/usr/bin/env python3
"""快速检查任务调度状态"""
import sys
sys.path.insert(0, r'C:\Users\A\.openclaw\workspace\aios\agent_system')

from task_queue import TaskQueue

q = TaskQueue()

running = q.list_tasks_by_status('running')
queued = q.list_tasks_by_status('queued')
succeeded = q.list_tasks_by_status('succeeded')
failed = q.list_tasks_by_status('failed')

print(f"Task Queue Status:")
print(f"  Running: {len(running)}")
print(f"  Queued: {len(queued)}")
print(f"  Succeeded: {len(succeeded)}")
print(f"  Failed: {len(failed)}")
print()

if running:
    print("Running Tasks:")
    for t in running[:5]:
        print(f"  - {t.task_id} (worker={t.worker_id})")
    print()

if queued:
    print("Queued Tasks:")
    for t in queued[:5]:
        task_type = t.payload.get('type', 'unknown')
        priority = t.payload.get('priority', 'normal')
        print(f"  - {t.task_id} | type={task_type} | priority={priority}")
