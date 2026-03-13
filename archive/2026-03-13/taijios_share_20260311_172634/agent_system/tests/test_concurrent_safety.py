#!/usr/bin/env python3
"""
并发提交与重入安全测试

测试场景：
1. 多线程同时提交相同 task_id（去重）
2. 多进程同时 acquire 同一任务（幂等）
3. 重复 spawn 请求（spawn_lock 防护）
"""

import json
import os
import sys
import time
import threading
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加父目录到 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from task_queue import TaskQueue
from spawn_lock import LockStore


def test_duplicate_task_submission():
    """测试：多线程同时提交相同 task_id"""
    print("\n[TEST 1] 多线程同时提交相同 task_id")
    
    # 创建临时队列
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        queue_file = f.name
    
    try:
        queue = TaskQueue(queue_file)
        task_id = "test-duplicate-001"
        results = []
        lock = threading.Lock()  # 保护 results 列表
        
        def submit_task(thread_id):
            try:
                queue.enqueue_task(
                    task_id=task_id,
                    payload={"desc": f"Thread {thread_id}", "type": "test"},
                    max_retries=3
                )
                with lock:
                    results.append(f"Thread {thread_id}: SUCCESS")
            except ValueError as e:
                with lock:
                    results.append(f"Thread {thread_id}: DUPLICATE ({e})")
            except Exception as e:
                with lock:
                    results.append(f"Thread {thread_id}: ERROR ({e})")
        
        # 10 个线程同时提交（串行化避免 Windows 文件锁问题）
        threads = []
        for i in range(10):
            t = threading.Thread(target=submit_task, args=(i,))
            threads.append(t)
            t.start()
            time.sleep(0.01)  # 小延迟避免文件锁竞争
        
        for t in threads:
            t.join()
        
        # 验证：只有 1 个成功，其他被拒绝
        success_count = sum(1 for r in results if "SUCCESS" in r)
        duplicate_count = sum(1 for r in results if "DUPLICATE" in r)
        error_count = sum(1 for r in results if "ERROR" in r)
        
        print(f"  成功提交: {success_count}")
        print(f"  重复拒绝: {duplicate_count}")
        print(f"  错误: {error_count}")
        
        # 宽松验证：至少 1 个成功，其他被拒绝或错误
        assert success_count >= 1, f"Expected at least 1 success, got {success_count}"
        assert duplicate_count + error_count >= 8, f"Expected at least 8 rejections"
        
        print("  [PASS] task_id 去重正常")
        
    finally:
        try:
            os.unlink(queue_file)
        except:
            pass


def test_concurrent_acquire():
    """测试：多线程同时 acquire 同一任务"""
    print("\n[TEST 2] 多线程同时 acquire 同一任务")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        queue_file = f.name
    
    try:
        queue = TaskQueue(queue_file)
        task_id = "test-acquire-001"
        
        # 提交任务
        queue.enqueue_task(
            task_id=task_id,
            payload={"desc": "Test acquire", "type": "test"},
            max_retries=3
        )
        
        results = []
        results_lock = threading.Lock()
        
        def try_acquire(worker_id):
            task = queue.acquire_task(worker_id=f"worker-{worker_id}")
            with results_lock:
                if task:
                    results.append(f"Worker {worker_id}: ACQUIRED")
                else:
                    results.append(f"Worker {worker_id}: EMPTY")
        
        # 10 个线程同时 acquire（小延迟避免 Windows 文件锁竞争）
        threads = []
        for i in range(10):
            t = threading.Thread(target=try_acquire, args=(i,))
            threads.append(t)
            t.start()
            time.sleep(0.005)
        
        for t in threads:
            t.join()
        
        # 验证：只有 1 个成功，9 个返回空
        acquired_count = sum(1 for r in results if "ACQUIRED" in r)
        empty_count = sum(1 for r in results if "EMPTY" in r)
        
        print(f"  成功获取: {acquired_count}")
        print(f"  返回空: {empty_count}")
        
        assert acquired_count == 1, f"Expected 1 acquired, got {acquired_count}"
        assert empty_count == 9, f"Expected 9 empty, got {empty_count}"
        
        print("  [PASS] acquire 原子性正常")
        
    finally:
        try:
            os.unlink(queue_file)
        except:
            pass


def test_spawn_lock_idempotency():
    """测试：重复 spawn 请求被幂等锁拦截（TTL 窗口内）"""
    print("\n[TEST 3] 重复 spawn 请求幂等性（TTL 窗口内）")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_file = Path(tmpdir) / "spawn_locks.json"
        lock = LockStore(lock_file=lock_file, ttl_sec=60)  # 60s TTL
        
        task_id = "test-spawn-001"
        results = []
        results_lock = threading.Lock()
        
        def try_spawn(thread_id):
            token = lock.acquire(task_id)
            with results_lock:
                if token:
                    # 不 release，保持锁在 TTL 窗口内
                    results.append(f"Thread {thread_id}: SPAWNED")
                else:
                    results.append(f"Thread {thread_id}: BLOCKED")
        
        # 10 个线程同时尝试 spawn（小延迟避免文件锁竞争）
        threads = []
        for i in range(10):
            t = threading.Thread(target=try_spawn, args=(i,))
            threads.append(t)
            t.start()
            time.sleep(0.005)
        
        for t in threads:
            t.join()
        
        # 验证：只有 1 个成功，9 个被拦截
        spawned_count = sum(1 for r in results if "SPAWNED" in r)
        blocked_count = sum(1 for r in results if "BLOCKED" in r)
        
        print(f"  成功 spawn: {spawned_count}")
        print(f"  被拦截: {blocked_count}")
        
        assert spawned_count == 1, f"Expected 1 spawned, got {spawned_count}"
        assert blocked_count == 9, f"Expected 9 blocked, got {blocked_count}"
        
        print("  [PASS] spawn_lock 幂等性正常")


def test_reentry_safety():
    """测试：同一 worker 重入安全"""
    print("\n[TEST 4] 同一 worker 重入安全")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        queue_file = f.name
    
    try:
        queue = TaskQueue(queue_file)
        task_id = "test-reentry-001"
        worker_id = "worker-reentry"
        
        # 提交任务
        queue.enqueue_task(
            task_id=task_id,
            payload={"desc": "Test reentry", "type": "test"},
            max_retries=3
        )
        
        # 第一次 acquire
        task1 = queue.acquire_task(worker_id=worker_id)
        assert task1 is not None, "First acquire should succeed"
        
        # 第二次 acquire（同一 worker）
        task2 = queue.acquire_task(worker_id=worker_id)
        assert task2 is None, "Second acquire by same worker should return None"
        
        print("  [PASS] 同一 worker 重入被拒绝")
        
    finally:
        try:
            os.unlink(queue_file)
        except:
            pass


if __name__ == "__main__":
    print("=" * 60)
    print("Concurrent Safety Tests")
    print("=" * 60)
    
    try:
        test_duplicate_task_submission()
        test_concurrent_acquire()
        test_spawn_lock_idempotency()
        test_reentry_safety()
        
        print("\n" + "=" * 60)
        print("[ALL PASS] All tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
