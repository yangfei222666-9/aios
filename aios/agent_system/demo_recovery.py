#!/usr/bin/env python3
"""
Recovery 机制演示 - 完整流程展示

演示场景：
1. 启动时清理过期锁（startup_cleanup）
2. 任务执行时幂等加锁（try_acquire_spawn_lock）
3. 任务超时后自动恢复（reclaim_zombie_tasks）
4. 周期性恢复扫描（HeartbeatSchedulerV5.tick）
"""
import json
import time
from pathlib import Path
from spawn_lock import (
    startup_cleanup,
    try_acquire_spawn_lock,
    release_spawn_lock,
    get_idempotency_metrics,
    transition_status,
)
from heartbeat_v5 import reclaim_zombie_tasks


def demo_startup_cleanup():
    """演示 1: 启动时清理过期锁"""
    print("=" * 60)
    print("演示 1: 启动时清理过期锁")
    print("=" * 60)
    
    cleaned = startup_cleanup()
    print(f"✅ 清理了 {cleaned} 个过期锁\n")


def demo_idempotent_spawn():
    """演示 2: 幂等 spawn（同一任务只执行一次）"""
    print("=" * 60)
    print("演示 2: 幂等 spawn（同一任务只执行一次）")
    print("=" * 60)
    
    task = {"id": "demo-task-001", "zombie_retries": 0}
    
    # 第一次尝试：成功获取锁
    token1 = try_acquire_spawn_lock(task)
    if token1:
        print(f"✅ 第一次 spawn: 成功获取锁 (token={token1[:8]}...)")
    else:
        print("❌ 第一次 spawn: 幂等命中（不应该发生）")
    
    # 第二次尝试：幂等命中（15 分钟内）
    token2 = try_acquire_spawn_lock(task)
    if token2:
        print("❌ 第二次 spawn: 成功获取锁（不应该发生）")
    else:
        print("✅ 第二次 spawn: 幂等命中（跳过重复执行）")
    
    # 释放锁
    if token1:
        released = release_spawn_lock(task, token1)
        print(f"✅ 释放锁: {'成功' if released else '失败'}")
    
    # 释放后可以重新获取
    token3 = try_acquire_spawn_lock(task)
    if token3:
        print(f"✅ 第三次 spawn: 成功获取锁 (token={token3[:8]}...)")
        release_spawn_lock(task, token3)
    
    print()


def demo_zombie_recovery():
    """演示 3: 僵尸任务恢复"""
    print("=" * 60)
    print("演示 3: 僵尸任务恢复（超时任务自动重试）")
    print("=" * 60)
    
    # 创建一个超时的 running 任务
    queue_file = Path(__file__).parent / "task_queue.jsonl"
    
    # 读取现有任务
    tasks = []
    if queue_file.exists():
        with open(queue_file, "r", encoding="utf-8") as f:
            tasks = [json.loads(l) for l in f if l.strip()]
    
    # 添加一个超时任务（模拟）
    demo_task = {
        "id": "demo-zombie-001",
        "status": "running",
        "worker_id": "demo-worker",
        "started_at": time.time() - 400,  # 超时 400s
        "last_heartbeat_at": time.time() - 400,
        "created_at": time.time() - 500,
        "updated_at": time.time() - 400,
        "zombie_retries": 0,
    }
    
    tasks.append(demo_task)
    
    # 写入队列
    with open(queue_file, "w", encoding="utf-8") as f:
        for task in tasks:
            f.write(json.dumps(task, ensure_ascii=False) + "\n")
    
    print(f"📝 创建超时任务: demo-zombie-001 (running 400s)")
    
    # 执行恢复
    result = reclaim_zombie_tasks(timeout_seconds=300, max_retries=2)
    
    print(f"✅ 恢复结果:")
    print(f"   - 回收: {result['reclaimed']} 个任务")
    print(f"   - 重试: {result['retried']} 个任务")
    print(f"   - 永久失败: {result['permanently_failed']} 个任务")
    
    # 验证结果
    with open(queue_file, "r", encoding="utf-8") as f:
        tasks = [json.loads(l) for l in f if l.strip()]
    
    demo_task_after = next((t for t in tasks if t["id"] == "demo-zombie-001"), None)
    
    if demo_task_after:
        print(f"✅ 任务状态: {demo_task_after['status']}")
        print(f"✅ 重试次数: {demo_task_after.get('zombie_retries', 0)}")
        print(f"✅ worker_id: {demo_task_after.get('worker_id', 'None (已清空)')}")
    
    # 清理演示任务
    tasks = [t for t in tasks if t["id"] != "demo-zombie-001"]
    with open(queue_file, "w", encoding="utf-8") as f:
        for task in tasks:
            f.write(json.dumps(task, ensure_ascii=False) + "\n")
    
    print()


def demo_metrics():
    """演示 4: 幂等指标"""
    print("=" * 60)
    print("演示 4: 幂等指标（可观测性）")
    print("=" * 60)
    
    metrics = get_idempotency_metrics()
    
    print("📊 当前指标:")
    print(f"   - 总加锁次数: {metrics['acquire_total']}")
    print(f"   - 成功加锁: {metrics['acquire_success']}")
    print(f"   - 幂等命中: {metrics['idempotent_hit_total']}")
    print(f"   - 幂等命中率: {metrics['idempotent_hit_rate']:.1%}")
    print(f"   - 平均延迟: {metrics['lock_acquire_latency_ms_avg']:.2f}ms")
    print(f"   - 过期锁恢复: {metrics['stale_lock_recovered_total']}")
    
    print()


def demo_transition_status():
    """演示 5: 原子状态转换"""
    print("=" * 60)
    print("演示 5: 原子状态转换（CAS 语义）")
    print("=" * 60)
    
    task = {
        "id": "demo-transition-001",
        "status": "running",
        "worker_id": "demo-worker",
        "started_at": time.time(),
        "last_heartbeat_at": time.time(),
    }
    
    print(f"📝 初始状态: {task['status']}")
    print(f"   worker_id: {task.get('worker_id')}")
    
    # 正常转换：running → queued
    ok = transition_status(
        task,
        from_status="running",
        to_status="queued",
        extra={"zombie_retries": 1},
    )
    
    print(f"✅ 转换结果: {'成功' if ok else '失败'}")
    print(f"   新状态: {task['status']}")
    print(f"   worker_id: {task.get('worker_id', 'None (已清空)')}")
    print(f"   zombie_retries: {task.get('zombie_retries')}")
    
    # CAS 失败：状态不匹配
    ok2 = transition_status(
        task,
        from_status="running",  # 当前已经是 queued
        to_status="failed",
    )
    
    print(f"✅ CAS 保护: {'失败（预期）' if not ok2 else '成功（不应该）'}")
    print(f"   状态保持: {task['status']}")
    
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("AIOS Recovery 机制完整演示")
    print("=" * 60 + "\n")
    
    try:
        demo_startup_cleanup()
        demo_idempotent_spawn()
        demo_transition_status()
        demo_zombie_recovery()
        demo_metrics()
        
        print("=" * 60)
        print("✅ 演示完成！")
        print("=" * 60)
        print("\n核心特性:")
        print("  1. ✅ 启动时自动清理过期锁")
        print("  2. ✅ 幂等 spawn（15 分钟窗口内同一任务只执行一次）")
        print("  3. ✅ 原子状态转换（CAS 语义 + 自动清空 worker 字段）")
        print("  4. ✅ 僵尸任务自动恢复（超时 → 重试 → 永久失败）")
        print("  5. ✅ 完整可观测性（幂等命中率、延迟、恢复次数）")
        print("\n观察期: 2026-03-06 12:00 ~ 2026-03-08 12:00 (48h)")
        print("复盘时间: 2026-03-08 11:05")
        
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
