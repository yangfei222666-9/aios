from core.task_executor import execute_batch
result = execute_batch(max_tasks=1)
print(f"Executed: {result.get('executed',0)} | Success: {result.get('success',0)} | Failed: {result.get('failed',0)}")
