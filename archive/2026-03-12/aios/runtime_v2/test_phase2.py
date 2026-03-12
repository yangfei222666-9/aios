"""
Phase 2 测试：真实 Agent 集成

只接入 coder_agent，验证：
1. spawn_request 正确生成
2. 写入 spawn_requests.jsonl
3. 其他 type 仍然模拟执行
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from runtime_v2 import get_queue, get_state, get_dispatcher
from runtime_v2.real_worker import get_real_worker


def test_real_coder_integration():
    print("=" * 60)
    print("Phase 2 测试：真实 coder_agent 集成")
    print("=" * 60)
    print()
    
    # 清空 event log 和 spawn_requests
    event_log_path = Path(__file__).parent / "event_log.jsonl"
    spawn_requests_path = Path(__file__).parent.parent / "agent_system" / "spawn_requests.jsonl"
    
    if event_log_path.exists():
        event_log_path.unlink()
    if spawn_requests_path.exists():
        spawn_requests_path.unlink()
    
    print("[CLEAN] Event log 和 spawn_requests 已清空")
    print()
    
    # 提交 3 个任务（1 code + 2 其他）
    queue = get_queue()
    
    print("[STEP 1] 提交任务")
    task1 = queue.enqueue(
        task_type="code",
        description="重构 scheduler.py 的 tick() 方法",
        priority="high"
    )
    print(f"  [OK] Task 1 (code): {task1}")
    
    task2 = queue.enqueue(
        task_type="analysis",
        description="分析失败日志",
        priority="normal"
    )
    print(f"  [OK] Task 2 (analysis): {task2}")
    
    task3 = queue.enqueue(
        task_type="monitor",
        description="检查磁盘使用率",
        priority="low"
    )
    print(f"  [OK] Task 3 (monitor): {task3}")
    print()
    
    # 运行 dispatcher（使用 real_worker）
    dispatcher = get_dispatcher()
    real_worker = get_real_worker()
    state = get_state()
    
    print("[STEP 2] 运行 dispatcher（使用 real_worker）")
    result = dispatcher.tick()
    print(f"  Spawned: {result['spawned']}")
    print()
    
    # 执行任务
    print("[STEP 3] 执行任务")
    running_tasks = state.list_running_tasks()
    for task in running_tasks:
        if task["last_event"]["event_type"] == "task_started":
            real_worker.execute(task)
    print()
    
    # 检查 spawn_requests.jsonl
    print("[STEP 4] 检查 spawn_requests.jsonl")
    if spawn_requests_path.exists():
        with open(spawn_requests_path, "r", encoding="utf-8") as f:
            spawn_requests = [line.strip() for line in f if line.strip()]
        
        print(f"  [OK] Spawn requests 生成: {len(spawn_requests)} 个")
        
        import json
        for i, req_str in enumerate(spawn_requests):
            req = json.loads(req_str)
            print(f"    #{i+1}: {req['agent_id']} | {req['task'][:50]}")
    else:
        print("  [FAIL] spawn_requests.jsonl 未生成")
    print()
    
    # 检查最终状态
    print("[STEP 5] 检查最终状态")
    completed = state.list_completed_tasks()
    failed = state.list_failed_tasks()
    
    print(f"  Completed: {len(completed)}")
    print(f"  Failed: {len(failed)}")
    print()
    
    # 验证结果
    print("[RESULT] 验证结果")
    if len(completed) == 3:
        print("  [OK] 所有任务都完成")
    else:
        print(f"  [FAIL] 只有 {len(completed)} 个任务完成")
    
    if spawn_requests_path.exists():
        print("  [OK] coder_agent spawn_request 已生成")
    else:
        print("  [FAIL] coder_agent spawn_request 未生成")
    
    print()
    print("=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_real_coder_integration()
