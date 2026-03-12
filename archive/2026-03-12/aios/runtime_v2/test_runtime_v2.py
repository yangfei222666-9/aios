"""
Runtime v2 完整流程测试

测试流程：
1. 提交 3 个任务（code/analysis/monitor）
2. 启动 runtime（运行 3 个 tick）
3. 验证所有任务都完成
"""

import sys
import time
from pathlib import Path

# 添加 aios 到 path
sys.path.insert(0, str(Path(__file__).parent.parent))

from runtime_v2 import get_queue, get_state, get_dispatcher, get_worker


def test_runtime_v2():
    print("=" * 60)
    print("Runtime v2 完整流程测试")
    print("=" * 60)
    print()
    
    # Step 1: 提交任务
    print("[STEP 1] 提交任务")
    queue = get_queue()
    
    task1 = queue.enqueue(task_type="code", description="重构 scheduler.py", priority="high")
    print(f"  [OK] Task 1: {task1}")
    
    task2 = queue.enqueue(task_type="analysis", description="分析失败日志", priority="normal")
    print(f"  [OK] Task 2: {task2}")
    
    task3 = queue.enqueue(task_type="monitor", description="检查磁盘使用率", priority="low")
    print(f"  [OK] Task 3: {task3}")
    print()
    
    # Step 2: 检查初始状态
    print("[STEP 2] 检查初始状态")
    state = get_state()
    pending = state.list_pending_tasks()
    print(f"  Pending tasks: {len(pending)}")
    for task in pending:
        print(f"    - {task['task_id']} | {task['task_data']['type']} | {task['task_data']['description']}")
    print()
    
    # Step 3: 运行 dispatcher（3 个 tick）
    print("[STEP 3] 运行 dispatcher（3 个 tick）")
    dispatcher = get_dispatcher()
    worker = get_worker()
    
    for i in range(3):
        print(f"\n  Tick #{i+1}")
        result = dispatcher.tick()
        print(f"    Pending: {result['pending']}")
        print(f"    Running: {result['running']}")
        print(f"    Spawned: {result['spawned']}")
        
        # 执行 spawned 任务
        if result['spawned'] > 0:
            running_tasks = state.list_running_tasks()
            for task in running_tasks:
                if task["last_event"]["event_type"] == "task_started":
                    worker.execute(task)
        
        time.sleep(0.5)
    
    print()
    
    # Step 4: 检查最终状态
    print("[STEP 4] 检查最终状态")
    pending = state.list_pending_tasks()
    running = state.list_running_tasks()
    completed = state.list_completed_tasks()
    failed = state.list_failed_tasks()
    
    print(f"  Pending: {len(pending)}")
    print(f"  Running: {len(running)}")
    print(f"  Completed: {len(completed)}")
    print(f"  Failed: {len(failed)}")
    print()
    
    # Step 5: 验证结果
    print("[STEP 5] 验证结果")
    if len(completed) == 3:
        print("  [OK] 所有任务都完成！")
        print()
        print("  完成的任务：")
        for task in completed:
            print(f"    - {task['task_id']} | {task['task_data']['type']} | {task['task_data']['description']}")
    else:
        print(f"  [FAIL] 只有 {len(completed)} 个任务完成（预期 3 个）")
    
    print()
    print("=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_runtime_v2()
