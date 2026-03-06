#!/usr/bin/env python3
"""
Idempotent Spawn Lock - 方案 A（本地文件锁）
支持 fcntl (Linux/Mac) / msvcrt (Windows) 双平台

接口抽象为 LockStore，后续可平滑切 Redis（方案 B）。

硬约束：
1. 原子加锁：读→判定→写在文件锁临界区内一次完成
2. 锁带 owner：记录 worker_id + lock_token + locked_at
3. 崩溃恢复：TTL 到期可抢占；启动时清理过期锁
4. 可观测性：idempotent_hit_rate / lock_acquire_latency / stale_lock_recovered_total
"""

import json
import os
import time
import uuid
import platform
from pathlib import Path
from contextlib import contextmanager
from typing import Optional

# ── 配置 ──────────────────────────────────────────────────────────────────────
IDEMPOTENCY_TTL_SEC = 15 * 60   # 15 分钟窗口内同一任务只 spawn 一次
LOCK_FILE = Path(__file__).parent / "spawn_locks.json"
METRICS_FILE = Path(__file__).parent / "spawn_lock_metrics.json"
WORKER_ID = f"worker-{os.getpid()}"


# ── 平台兼容文件锁 ─────────────────────────────────────────────────────────────
@contextmanager
def _file_mutex(path: Path):
    """跨平台文件互斥锁（临界区保护）"""
    lock_path = path.with_suffix(".lock")
    lock_path.touch(exist_ok=True)
    fh = open(lock_path, "r+")
    try:
        if platform.system() == "Windows":
            import msvcrt
            # Windows: 非阻塞尝试，失败则等待重试
            for _ in range(50):  # 最多等 500ms
                try:
                    msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    time.sleep(0.01)
            else:
                # 最后尝试阻塞锁
                msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(fh, fcntl.LOCK_EX)
        yield
    finally:
        if platform.system() == "Windows":
            import msvcrt
            try:
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
            except Exception:
                pass
        else:
            import fcntl
            fcntl.flock(fh, fcntl.LOCK_UN)
        fh.close()


# ── LockStore 抽象（接口位，后续可换 Redis）────────────────────────────────────
class LockStore:
    """
    本地文件实现的幂等锁存储。
    接口与 Redis 版本保持一致，后续切换只需替换此类。
    """

    def __init__(self, lock_file: Path = LOCK_FILE, ttl_sec: int = IDEMPOTENCY_TTL_SEC):
        self.lock_file = lock_file
        self.ttl_sec = ttl_sec
        self._metrics = self._load_metrics()

    # ── 内部：读写锁表 ────────────────────────────────────────────────────────
    def _read_locks(self) -> dict:
        if not self.lock_file.exists():
            return {}
        try:
            return json.loads(self.lock_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _write_locks(self, locks: dict):
        self.lock_file.write_text(json.dumps(locks, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── 指标 ──────────────────────────────────────────────────────────────────
    def _load_metrics(self) -> dict:
        if METRICS_FILE.exists():
            try:
                return json.loads(METRICS_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "acquire_total": 0,
            "acquire_success": 0,
            "idempotent_hit_total": 0,
            "stale_lock_recovered_total": 0,
            "acquire_latency_ms_sum": 0.0,
        }

    def _save_metrics(self):
        METRICS_FILE.write_text(json.dumps(self._metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_metrics(self) -> dict:
        total = self._metrics["acquire_total"]
        hits = self._metrics["idempotent_hit_total"]
        latency_avg = (
            self._metrics["acquire_latency_ms_sum"] / total if total > 0 else 0.0
        )
        return {
            "idempotent_hit_rate": round(hits / total, 4) if total > 0 else 0.0,
            "idempotent_hit_total": hits,
            "acquire_total": total,
            "acquire_success": self._metrics["acquire_success"],
            "lock_acquire_latency_ms_avg": round(latency_avg, 2),
            "stale_lock_recovered_total": self._metrics["stale_lock_recovered_total"],
        }

    # ── 核心接口 ──────────────────────────────────────────────────────────────
    def acquire(self, task_key: str) -> Optional[str]:
        """
        尝试获取幂等锁。
        返回 lock_token（成功）或 None（已被锁定，幂等命中）。
        原子操作：读→判定→写在文件锁临界区内完成。
        """
        t0 = time.time()
        self._metrics["acquire_total"] += 1
        now = time.time()
        token = None

        with _file_mutex(self.lock_file):
            locks = self._read_locks()
            existing = locks.get(task_key)

            if existing:
                age = now - existing.get("locked_at", 0)
                if age < self.ttl_sec:
                    # 幂等命中：锁仍有效
                    self._metrics["idempotent_hit_total"] += 1
                    latency_ms = (time.time() - t0) * 1000
                    self._metrics["acquire_latency_ms_sum"] += latency_ms
                    self._save_metrics()
                    return None
                else:
                    # 锁已过期（崩溃恢复）：可抢占
                    self._metrics["stale_lock_recovered_total"] += 1

            # 写入新锁
            token = str(uuid.uuid4())
            locks[task_key] = {
                "worker_id": WORKER_ID,
                "lock_token": token,
                "locked_at": now,
                "task_key": task_key,
            }
            self._write_locks(locks)

        self._metrics["acquire_success"] += 1
        latency_ms = (time.time() - t0) * 1000
        self._metrics["acquire_latency_ms_sum"] += latency_ms
        self._save_metrics()
        return token

    def release(self, task_key: str, lock_token: str) -> bool:
        """
        释放锁（仅释放自己持有的锁，防止误删）。
        返回 True 表示成功释放。
        """
        with _file_mutex(self.lock_file):
            locks = self._read_locks()
            existing = locks.get(task_key)
            if not existing:
                return False
            # 校验 owner + token（CAS 语义）
            if existing.get("lock_token") != lock_token:
                return False
            del locks[task_key]
            self._write_locks(locks)
        return True

    def cleanup_expired(self) -> int:
        """
        清理所有过期锁（Heartbeat 启动时调用）。
        返回清理数量。
        """
        now = time.time()
        cleaned = 0
        with _file_mutex(self.lock_file):
            locks = self._read_locks()
            expired_keys = [
                k for k, v in locks.items()
                if now - v.get("locked_at", 0) >= self.ttl_sec
            ]
            for k in expired_keys:
                del locks[k]
                cleaned += 1
            if cleaned:
                self._write_locks(locks)
        if cleaned:
            self._metrics["stale_lock_recovered_total"] += cleaned
            self._save_metrics()
        return cleaned


# ── 全局单例 ──────────────────────────────────────────────────────────────────
_lock_store: Optional[LockStore] = None

def get_lock_store() -> LockStore:
    global _lock_store
    if _lock_store is None:
        _lock_store = LockStore()
    return _lock_store


def idem_key(task: dict) -> str:
    """生成幂等 key：task_id + attempt（同一任务不同重试视为不同 key）"""
    tid = task.get("id") or task.get("task_id", "unknown")
    attempt = task.get("zombie_retries", 0)
    return f"{tid}:v{attempt}"


# ── Heartbeat 集成接口 ─────────────────────────────────────────────────────────
def startup_cleanup() -> int:
    """Heartbeat 启动时调用，清理过期锁"""
    store = get_lock_store()
    cleaned = store.cleanup_expired()
    if cleaned:
        print(f"  [IDEM] Startup cleanup: {cleaned} expired locks removed")
    return cleaned


def try_acquire_spawn_lock(task: dict) -> Optional[str]:
    """
    尝试为任务获取 spawn 锁。
    返回 lock_token（可以 spawn）或 None（幂等命中，跳过）。
    """
    store = get_lock_store()
    key = idem_key(task)
    return store.acquire(key)


def acquire_or_reuse(task: dict, existing_token: Optional[str] = None) -> tuple[Optional[str], bool]:
    """
    重试场景专用：如果已持有锁（existing_token 有效），直接复用，不重新 acquire。
    
    这保证"重试不重跑"：同一任务的重试不会产生新的锁文件，
    也不会触发幂等命中计数（因为锁本来就是自己的）。
    
    Args:
        task: 任务对象
        existing_token: 上次 acquire 返回的 token（如果有）
    
    Returns:
        (token, is_reused)
        - token: 有效的 lock_token（None 表示被其他 worker 锁定）
        - is_reused: True 表示复用了已有锁，False 表示新 acquire
    
    Usage:
        # 首次执行
        token, _ = acquire_or_reuse(task)
        
        # 重试时复用
        token, reused = acquire_or_reuse(task, existing_token=token)
        if reused:
            # 锁已持有，直接重试，不产生新锁文件
            pass
    """
    store = get_lock_store()
    key = idem_key(task)
    
    # 如果有 existing_token，验证锁是否仍然有效
    if existing_token:
        with _file_mutex(store.lock_file):
            locks = store._read_locks()
            existing = locks.get(key)
            if existing and existing.get("lock_token") == existing_token:
                # 锁仍然有效且属于自己，直接复用
                return (existing_token, True)
    
    # 否则正常 acquire
    token = store.acquire(key)
    return (token, False)


def release_spawn_lock(task: dict, lock_token: str) -> bool:
    """任务终态（成功/永久失败）时释放锁"""
    store = get_lock_store()
    key = idem_key(task)
    return store.release(key, lock_token)


def get_idempotency_metrics() -> dict:
    """获取幂等指标（用于 Heartbeat 上报）"""
    return get_lock_store().get_metrics()


# ── Atomic Status Transition ───────────────────────────────────────────────────
def transition_status(
    task: dict,
    from_status: str,
    to_status: str,
    extra: Optional[dict] = None,
) -> bool:
    """
    原子状态转换：WHERE task_id AND status = from_status → to_status。
    
    Args:
        task: 任务对象（必须包含 id 或 task_id）
        from_status: 当前状态（原子校验）
        to_status: 目标状态
        extra: 额外字段更新（如 worker_id=None 清空 worker）
    
    Returns:
        True 表示转换成功，False 表示状态不匹配（CAS 失败）
    
    清空 worker 字段规则：
    - running → queued 时自动清空 worker_id / started_at / last_heartbeat_at
    """
    task_id = task.get("id") or task.get("task_id")
    if not task_id:
        return False
    
    # 原子校验：当前状态必须匹配
    if task.get("status") != from_status:
        return False
    
    # 更新状态
    task["status"] = to_status
    task["updated_at"] = time.time()
    
    # 应用额外字段
    if extra:
        for k, v in extra.items():
            if v is None:
                # None 表示删除字段
                task.pop(k, None)
            else:
                task[k] = v
    
    # running → queued 时自动清空 worker 字段
    if from_status == "running" and to_status == "queued":
        task.pop("worker_id", None)
        task.pop("started_at", None)
        task.pop("last_heartbeat_at", None)
    
    return True


def recover_stale_locks(
    timeout_seconds: int = 300,
    scan_limit: int = 1000,
) -> dict:
    """
    周期性恢复：扫描所有 running 任务，超时的转为 queued（带重试计数）。
    
    Args:
        timeout_seconds: 超时阈值（默认 5 分钟）
        scan_limit: 最大扫描数量（防止大表扫描）
    
    Returns:
        {"recovered": int, "retried": int, "failed": int}
    """
    queue_file = Path(__file__).parent / "task_queue.jsonl"
    if not queue_file.exists():
        return {"recovered": 0, "retried": 0, "failed": 0}
    
    now = time.time()
    recovered = retried = failed = 0
    
    with open(queue_file, "r", encoding="utf-8") as f:
        tasks = [json.loads(l) for l in f if l.strip()][:scan_limit]
    
    modified = False
    for task in tasks:
        if task.get("status") != "running":
            continue
        
        updated_at = task.get("updated_at", task.get("created_at", 0))
        age = now - updated_at
        if age <= timeout_seconds:
            continue
        
        # 超时了
        task_id = task.get("id", "?")
        age_hr = age / 3600
        retry_count = task.get("zombie_retries", 0)
        
        if retry_count < 2:  # max_retries = 2
            # 原子转换 running → queued
            ok = transition_status(
                task,
                from_status="running",
                to_status="queued",
                extra={
                    "zombie_retries": retry_count + 1,
                    "zombie_note": f"recovered after {age_hr:.1f}h, retry #{retry_count + 1}",
                },
            )
            if ok:
                retried += 1
                recovered += 1
        else:
            # 超过重试上限：原子转换 running → failed
            ok = transition_status(
                task,
                from_status="running",
                to_status="failed",
                extra={
                    "zombie_note": f"permanently failed after 2 retries, last age {age_hr:.1f}h",
                },
            )
            if ok:
                failed += 1
                recovered += 1
        
        if ok:
            modified = True
    
    if modified:
        with open(queue_file, "w", encoding="utf-8") as f:
            for task in tasks:
                f.write(json.dumps(task, ensure_ascii=False) + "\n")
    
    return {"recovered": recovered, "retried": retried, "failed": failed}


# ── Task-level Lock (for Durable Execution) ────────────────────────────────────
def task_lock_key(task_id: str) -> str:
    """Generate lock key for task-level locking."""
    return f"task:{task_id}"


@contextmanager
def with_task_lock(task_id: str, owner: str, ttl_seconds: int = 30):
    """
    Context manager for task-level locking.
    Yields True if lock acquired, False otherwise.
    
    Usage:
        with with_task_lock("task-123", "worker-1") as acquired:
            if acquired:
                # Do work
                pass
    """
    store = get_lock_store()
    # Override TTL for task locks
    original_ttl = store.ttl_sec
    store.ttl_sec = ttl_seconds
    
    key = task_lock_key(task_id)
    token = store.acquire(key)
    
    try:
        yield token is not None
    finally:
        if token:
            store.release(key, token)
        # Restore original TTL
        store.ttl_sec = original_ttl


# ── CLI 测试 ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== Idempotent Spawn Lock - 自测 ===\n")

    store = LockStore()

    # 清理启动
    cleaned = store.cleanup_expired()
    print(f"Startup cleanup: {cleaned} expired locks\n")

    # 测试 1：正常获取
    task = {"id": "test-001", "zombie_retries": 0}
    token = try_acquire_spawn_lock(task)
    assert token is not None, "Should acquire lock"
    print(f"[OK] Acquired lock: {token[:8]}...")

    # 测试 2：幂等命中（同一任务再次尝试）
    token2 = try_acquire_spawn_lock(task)
    assert token2 is None, "Should be idempotent hit"
    print("[OK] Idempotent hit: second acquire blocked")

    # 测试 3：释放后可重新获取
    released = release_spawn_lock(task, token)
    assert released, "Should release"
    token3 = try_acquire_spawn_lock(task)
    assert token3 is not None, "Should acquire after release"
    print(f"[OK] Re-acquired after release: {token3[:8]}...")
    release_spawn_lock(task, token3)

    # 测试 4：错误 token 无法释放（CAS 保护）
    token4 = try_acquire_spawn_lock(task)
    bad_release = release_spawn_lock(task, "wrong-token")
    assert not bad_release, "Wrong token should not release"
    print("[OK] CAS protection: wrong token rejected")
    release_spawn_lock(task, token4)

    # 指标
    metrics = get_idempotency_metrics()
    print(f"\n[METRICS]")
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    print("\n✅ All tests passed")
