"""处理 Agent 任务队列"""
from auto_dispatcher import AutoDispatcher
from pathlib import Path

workspace = Path("C:/Users/A/.openclaw/workspace")
dispatcher = AutoDispatcher(workspace)

print("开始处理任务队列...")
results = dispatcher.process_queue(max_tasks=3)

print(f"\n处理了 {len(results)} 个任务:")
for r in results:
    task_id = r.get("id", "unknown")
    status = r.get("status", "unknown")
    task_type = r.get("type", "unknown")
    print(f"  - [{task_type}] {task_id}: {status}")

print("\n任务已分发到对应的 Agent")
