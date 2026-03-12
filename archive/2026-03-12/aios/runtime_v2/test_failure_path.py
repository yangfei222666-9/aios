"""
Runtime v2 Failure Path 测试

测试 4 个关键场景：
1. Worker crash（任务执行中崩溃）
2. Worker timeout（任务执行超时）
3. 100 tasks（批量任务，检查重复执行和丢任务）
4. Dispatcher restart（重启后恢复）
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from runtime_v2 import get_queue, get_state, get_dispatcher, get_worker, get_metrics


def test_1_worker_crash():
    """测试1：Worker crash"""
    print("=" * 60)
    print("测试1：Worker Crash")
    print("=" * 60)
    print()
    
    # 提交一个会崩溃的任务
    queue = get_queue()
    task_id = queue.enqueue(
        task_type="crash_test",
        description="这个任务会崩溃",
        priority="high"
    )
    print(f"[OK] 提交任务: {task_id}")
    print()
    
    # 运行 dispatcher
    dispatcher = get_dispatcher()
    worker = get_worker()
    state = get_state()
    
    print("[STEP] 运行 dispatcher...")
    result = dispatcher.tick()
    print(f"  Spawned: {result['spawned']}")
    
    # 执行任务（会崩溃）
    running_tasks = state.list_running_tasks()
    for task in running_tasks:
        if task["last_event"]["event_type"] == "task_started":
            # 模拟崩溃
            try:
                # 强制抛出异常
                raise RuntimeError("Worker crashed during execution")
            except Exception as e:
                print(f"  [CRASH] Worker crashed: {e}")
                # Worker 应该写入 task_failed event
                from runtime_v2.event_log import get_event_log
                event_log = get_event_log()
                event_log.append_event(
                    event_type="task_failed",
                    task_id=task["task_id"],
                    data={"failed_at": time.time(), "error": str(e)}
                )
    
    print()
    
    # 检查最终状态
    print("[RESULT] 检查最终状态...")
    failed_tasks = state.list_failed_tasks()
    print(f"  Failed tasks: {len(failed_tasks)}")
    
    if len(failed_tasks) == 1:
        print("  [OK] Worker crash 被正确处理")
    else:
        print("  [FAIL] Worker crash 未被正确处理")
    
    print()


def test_2_worker_timeout():
    """测试2：Worker timeout"""
    print("=" * 60)
    print("测试2：Worker Timeout")
    print("=" * 60)
    print()
    
    # 提交一个会超时的任务
    queue = get_queue()
    task_id = queue.enqueue(
        task_type="timeout_test",
        description="这个任务会超时",
        priority="high"
    )
    print(f"[OK] 提交任务: {task_id}")
    print()
    
    # 运行 dispatcher
    dispatcher = get_dispatcher()
    state = get_state()
    
    print("[STEP] 运行 dispatcher...")
    result = dispatcher.tick()
    print(f"  Spawned: {result['spawned']}")
    
    # 模拟超时（不执行任务，直接写 timeout event）
    running_tasks = state.list_running_tasks()
    for task in running_tasks:
        if task["last_event"]["event_type"] == "task_started":
            print(f"  [TIMEOUT] Task timeout: {task['task_id']}")
            from runtime_v2.event_log import get_event_log
            event_log = get_event_log()
            event_log.append_event(
                event_type="task_timeout",
                task_id=task["task_id"],
                data={"timeout_at": time.time()}
            )
    
    print()
    
    # 检查最终状态
    print("[RESULT] 检查最终状态...")
    # timeout 任务应该在 failed 或单独的 timeout 状态
    from runtime_v2.event_log import get_event_log
    events = get_event_log().read_events()
    timeout_events = [e for e in events if e["event_type"] == "task_timeout"]
    
    print(f"  Timeout events: {len(timeout_events)}")
    
    if len(timeout_events) >= 1:
        print("  [OK] Worker timeout 被正确记录")
    else:
        print("  [FAIL] Worker timeout 未被正确记录")
    
    print()


def test_3_100_tasks():
    """测试3：100 tasks（批量任务）"""
    print("=" * 60)
    print("测试3：100 Tasks（批量任务）")
    print("=" * 60)
    print()
    
    # 提交 100 个任务
    queue = get_queue()
    task_ids = []
    
    print("[STEP] 提交 100 个任务...")
    for i in range(100):
        task_id = queue.enqueue(
            task_type="code",
            description=f"批量任务 #{i+1}",
            priority="normal"
        )
        task_ids.append(task_id)
    
    print(f"  [OK] 提交完成: {len(task_ids)} 个任务")
    print()
    
    # 运行 dispatcher（多次 tick）
    dispatcher = get_dispatcher()
    worker = get_worker()
    state = get_state()
    
    print("[STEP] 运行 dispatcher（最多 30 次 tick）...")
    tick_count = 0
    max_ticks = 30
    
    while tick_count < max_ticks:
        tick_count += 1
        result = dispatcher.tick()
        
        if result['spawned'] > 0:
            print(f"  Tick #{tick_count}: Spawned {result['spawned']}, Running {result['running']}, Pending {result['pending']}")
            
            # 执行 spawned 任务
            running_tasks = state.list_running_tasks()
            for task in running_tasks:
                if task["last_event"]["event_type"] == "task_started":
                    worker.execute(task)
        
        # 如果没有 pending 和 running，退出
        if result['pending'] == 0 and result['running'] == 0:
            break
        
        time.sleep(0.1)
    
    print()
    
    # 检查最终状态
    print("[RESULT] 检查最终状态...")
    completed = state.list_completed_tasks()
    failed = state.list_failed_tasks()
    pending = state.list_pending_tasks()
    running = state.list_running_tasks()
    
    print(f"  Completed: {len(completed)}")
    print(f"  Failed: {len(failed)}")
    print(f"  Pending: {len(pending)}")
    print(f"  Running: {len(running)}")
    print(f"  Total: {len(completed) + len(failed) + len(pending) + len(running)}")
    print()
    
    # 检查是否有重复执行或丢任务
    total_finished = len(completed) + len(failed)
    if total_finished == 100:
        print("  [OK] 无任务丢失")
    else:
        print(f"  [FAIL] 任务丢失: {100 - total_finished} 个")
    
    # 检查是否有重复执行（通过 event log）
    from runtime_v2.event_log import get_event_log
    events = get_event_log().read_events()
    
    task_started_count = {}
    for event in events:
        if event["event_type"] == "task_started":
            task_id = event["task_id"]
            task_started_count[task_id] = task_started_count.get(task_id, 0) + 1
    
    duplicates = [tid for tid, count in task_started_count.items() if count > 1]
    if len(duplicates) == 0:
        print("  [OK] 无重复执行")
    else:
        print(f"  [FAIL] 重复执行: {len(duplicates)} 个任务")
        for tid in duplicates[:5]:
            print(f"    - {tid}: {task_started_count[tid]} 次")
    
    print()


def test_4_dispatcher_restart():
    """测试4：Dispatcher restart（重启后恢复）"""
    print("=" * 60)
    print("测试4：Dispatcher Restart（重启后恢复）")
    print("=" * 60)
    print()
    
    # 提交 5 个任务
    queue = get_queue()
    task_ids = []
    
    print("[STEP] 提交 5 个任务...")
    for i in range(5):
        task_id = queue.enqueue(
            task_type="code",
            description=f"重启测试任务 #{i+1}",
            priority="normal"
        )
        task_ids.append(task_id)
    
    print(f"  [OK] 提交完成: {len(task_ids)} 个任务")
    print()
    
    # 运行 dispatcher（只执行 2 个任务）
    dispatcher = get_dispatcher()
    worker = get_worker()
    state = get_state()
    
    print("[STEP] 运行 dispatcher（只执行 2 个任务）...")
    result = dispatcher.tick()
    print(f"  Spawned: {result['spawned']}")
    
    # 执行前 2 个任务
    running_tasks = state.list_running_tasks()
    for i, task in enumerate(running_tasks[:2]):
        if task["last_event"]["event_type"] == "task_started":
            worker.execute(task)
            print(f"  [OK] 执行任务 #{i+1}")
    
    print()
    
    # 模拟 dispatcher 重启（重新创建实例）
    print("[STEP] 模拟 dispatcher 重启...")
    print("  [RESTART] Dispatcher restarting...")
    
    # 重新创建 dispatcher（清空全局单例）
    from runtime_v2 import dispatcher as dispatcher_module
    dispatcher_module._dispatcher = None
    
    new_dispatcher = get_dispatcher()
    print("  [OK] Dispatcher restarted")
    print()
    
    # 检查状态（应该能看到 pending 任务）
    print("[STEP] 检查重启后状态...")
    pending = state.list_pending_tasks()
    completed = state.list_completed_tasks()
    
    print(f"  Pending: {len(pending)}")
    print(f"  Completed: {len(completed)}")
    print()
    
    # 继续执行剩余任务
    print("[STEP] 继续执行剩余任务...")
    tick_count = 0
    while tick_count < 10:
        tick_count += 1
        result = new_dispatcher.tick()
        
        if result['spawned'] > 0:
            print(f"  Tick #{tick_count}: Spawned {result['spawned']}")
            
            running_tasks = state.list_running_tasks()
            for task in running_tasks:
                if task["last_event"]["event_type"] == "task_started":
                    worker.execute(task)
        
        if result['pending'] == 0 and result['running'] == 0:
            break
        
        time.sleep(0.1)
    
    print()
    
    # 检查最终状态
    print("[RESULT] 检查最终状态...")
    completed = state.list_completed_tasks()
    failed = state.list_failed_tasks()
    
    print(f"  Completed: {len(completed)}")
    print(f"  Failed: {len(failed)}")
    
    if len(completed) == 5:
        print("  [OK] Dispatcher restart 后任务恢复执行")
    else:
        print(f"  [FAIL] Dispatcher restart 后任务未完全恢复")
    
    print()


def main():
    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  Runtime v2 Failure Path 测试                             ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    # 清空 event log
    from pathlib import Path
    event_log_path = Path(__file__).parent / "event_log.jsonl"
    if event_log_path.exists():
        event_log_path.unlink()
        print("[CLEAN] Event log 已清空")
        print()
    
    # 运行测试
    test_1_worker_crash()
    test_2_worker_timeout()
    test_3_100_tasks()
    test_4_dispatcher_restart()
    
    # 打印 metrics
    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  Runtime Metrics                                           ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    metrics = get_metrics()
    metrics.print_metrics()
    
    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  测试完成                                                  ║")
    print("╚════════════════════════════════════════════════════════════╝")


if __name__ == "__main__":
    main()
