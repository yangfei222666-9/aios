import sys, json, uuid
sys.path.insert(0, '.')

print('=== 干净环境二次闭环验证 ===')
print()

from task_queue import TaskQueue

tq = TaskQueue()
task_id = 'clean-env-verify-' + str(uuid.uuid4())[:8]
results = {}

# Step 1: 提交
print('[Step 1] 提交测试任务...')
tq.enqueue_task(task_id=task_id, payload={'type': 'monitor', 'agent_id': 'monitor', 'description': '干净环境验证'})
pending = tq.list_tasks_by_status('pending')
found = any(t.task_id == task_id for t in pending)
results['submit_to_pending'] = found
print(f'  submit -> pending: {"OK" if found else "FAIL"}')

# Step 2: acquire（pending → running）
print()
print('[Step 2] acquire_task（pending -> running）...')
# 先 acquire 直到拿到我们的任务（FIFO 队列）
acquired_our_task = False
for _ in range(10):  # 最多尝试 10 次
    task = tq.acquire_task(worker_id='clean-env-test')
    if task and task.task_id == task_id:
        acquired_our_task = True
        print(f'  acquired our task: {task.task_id}')
        break
    elif task:
        print(f'  skipped other task: {task.task_id}')
    else:
        break

running = tq.list_tasks_by_status('running')
found_running = any(t.task_id == task_id for t in running)
results['pending_to_running'] = found_running
print(f'  pending -> running: {"OK" if found_running else "FAIL"}')

# Step 3: 完成（running → succeeded）
print()
print('[Step 3] transition_status（running -> succeeded）...')
try:
    tq.transition_status(task_id, from_status='running', to_status='succeeded', patch={'result': 'ok'})
    succeeded = tq.list_tasks_by_status('succeeded')
    found_done = any(t.task_id == task_id for t in succeeded)
    results['running_to_succeeded'] = found_done
    print(f'  running -> succeeded: {"OK" if found_done else "FAIL"}')
except Exception as e:
    results['running_to_succeeded'] = False
    print(f'  running -> succeeded: FAIL ({e})')

print()
print('=== 最终状态 ===')
print(f'  pending: {len(tq.list_tasks_by_status("pending"))} 条')
print(f'  running: {len(tq.list_tasks_by_status("running"))} 条')
print(f'  succeeded: {len(tq.list_tasks_by_status("succeeded"))} 条')

print()
print('=== 验证结论 ===')
all_pass = all(results.values())
for k, v in results.items():
    print(f'  {k}: {"PASS" if v else "FAIL"}')
print()
print('RESULT:', 'PASS - 干净环境验证通过，无脏数据依赖' if all_pass else 'FAIL - 存在问题')
