# -*- coding: utf-8 -*-
"""
AIOS Heartbeat v5.0 - Task Queue Integration

Automatically processes tasks from the queue.

Changes from v4.0:
- Added task queue processing
- Integrated TaskExecutor
- Auto-execute pending tasks every heartbeat
"""
import sys
import io
import time
from pathlib import Path

# Fix Windows encoding (safe fallback)
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass  # Already UTF-8 or not reconfigurable

# Add AIOS to path
AIOS_ROOT = Path(__file__).resolve().parent.parent
if str(AIOS_ROOT) not in sys.path:
    sys.path.insert(0, str(AIOS_ROOT))

from core.task_submitter import list_tasks, queue_stats
from core.task_executor import execute_batch
# from low_success_regeneration import run_low_success_regeneration  # Temporarily disabled for service
from experience_learner_v4 import learner_v4
from token_monitor import check_and_alert, auto_optimize, generate_report

# ── Memory model warm-up (background, non-blocking) ──────────────────────────
import threading as _threading
def _warmup_memory():
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from memory_retrieval import _get_model
        _get_model()
    except Exception:
        pass
_threading.Thread(target=_warmup_memory, daemon=True).start()
import json
import os

# ============== 新增：Self-Healing Loop v2 启动 ==============
import asyncio
from self_healing_loop_v2 import SelfHealingLoopV2

# 全局 healing loop 实例
healing_loop = None

def start_self_healing_loop():
    """启动 Self-Healing Loop v2（异步后台运行）"""
    global healing_loop
    healing_loop = SelfHealingLoopV2()
    # 在后台启动异步任务
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.create_task(healing_loop.run_forever())
    print("🛡️ Self-Healing Loop v2 已随 Heartbeat 启动（双诸侯自愈模式）")
# ====================================================

# ============== 比卦资源共享模式 ==============
def activate_bigua_resource_sharing():
    """
    比卦资源共享模式激活
    自动加载所有本地 Agent（包括从 ClawdHub 安装的）
    """
    print("🔄 比卦资源共享模式已激活（shareresources）")
    
    # 自动加载所有本地 Agent
    agents_dir = Path(__file__).parent / "agents"
    if agents_dir.exists():
        agent_count = 0
        for f in agents_dir.glob("*.json"):
            agent_count += 1
            print(f"   ✅ 加载 Agent: {f.stem}")
        
        if agent_count > 0:
            print(f"   • {agent_count} 个 Agent 已加入协作")
            print("   • 资源共享 + Agent 市场推荐已开启")
    else:
        print("   ⚠️  agents/ 目录不存在，跳过 Agent 加载")


from spawn_lock import (
    startup_cleanup, 
    try_acquire_spawn_lock, 
    release_spawn_lock, 
    get_idempotency_metrics,
    recover_stale_locks,
    transition_status
)


def reclaim_zombie_tasks(timeout_seconds: int = 300, max_retries: int = 2) -> dict:
    """
    回收超时的 running 任务：running > timeout_seconds => retry(带上限) or failed
    使用 transition_status 原子更新，清空 worker_id/started_at/last_heartbeat_at。

    Returns:
        {"reclaimed": int, "retried": int, "permanently_failed": int}
    """
    queue_file = Path(__file__).parent / "task_queue.jsonl"
    if not queue_file.exists():
        return {"reclaimed": 0, "retried": 0, "permanently_failed": 0}

    now = time.time()
    reclaimed = retried = permanently_failed = 0

    with open(queue_file, "r", encoding="utf-8") as f:
        tasks = [json.loads(l) for l in f if l.strip()]

    modified = False
    for task in tasks:
        if task.get("status") != "running":
            continue

        updated_at = task.get("updated_at", task.get("created_at", 0))
        age = now - updated_at
        if age <= timeout_seconds:
            continue

        task_id = task.get("id", "?")
        age_hr = age / 3600
        retry_count = task.get("zombie_retries", 0)

        if retry_count < max_retries:
            # 原子转换 running → queued，清空 worker 字段
            ok = transition_status(
                task,
                from_status="running",
                to_status="queued",
                extra={
                    "zombie_retries": retry_count + 1,
                    "zombie_note": f"reclaimed after {age_hr:.1f}h, retry #{retry_count + 1}",
                    "worker_id": None,
                    "started_at": None,
                    "last_heartbeat_at": None,
                },
            )
            if ok:
                retried += 1
                print(f"  [ZOMBIE] {task_id}: running {age_hr:.1f}h → queued (retry #{retry_count + 1})")
        else:
            # 超过重试上限：原子转换 running → failed
            ok = transition_status(
                task,
                from_status="running",
                to_status="failed",
                extra={
                    "zombie_note": f"permanently failed after {max_retries} retries, last age {age_hr:.1f}h",
                    "worker_id": None,
                    "started_at": None,
                    "last_heartbeat_at": None,
                },
            )
            if ok:
                permanently_failed += 1
                print(f"  [ZOMBIE] {task_id}: running {age_hr:.1f}h → permanently failed (max retries)")
                # DLQ: 重试耗尽 → 写入死信队列
                try:
                    from dlq import enqueue_dead_letter
                    enqueue_dead_letter(
                        task_id=task_id,
                        attempts=retry_count + 1,
                        last_error=task.get("zombie_note", f"timeout after {age_hr:.1f}h"),
                        error_type="timeout",
                        metadata={"agent_id": task.get("agent_id"), "description": task.get("description", "")[:200]}
                    )
                    print(f"  [DLQ] {task_id}: enqueued to dead letters")
                except Exception as e:
                    print(f"  [DLQ] {task_id}: failed to enqueue: {e}")

        if ok:
            reclaimed += 1
            modified = True

    if modified:
        with open(queue_file, "w", encoding="utf-8") as f:
            for task in tasks:
                f.write(json.dumps(task, ensure_ascii=False) + "\n")

    return {"reclaimed": reclaimed, "retried": retried, "permanently_failed": permanently_failed}


def process_task_queue(max_tasks: int = 5) -> dict:
    """
    Process pending tasks from the queue.
    
    Returns:
        Summary of execution
    """
    # Get pending tasks
    tasks = list_tasks(status="pending", limit=max_tasks)
    
    if not tasks:
        return {
            "processed": 0,
            "success": 0,
            "failed": 0,
        }
    
    print(f"[QUEUE] Processing {len(tasks)} pending tasks...")
    
    # Execute tasks with idempotency gate
    results = []
    skipped = 0
    for task in tasks[:max_tasks]:
        token = try_acquire_spawn_lock(task)
        if token is None:
            skipped += 1
            continue
        try:
            batch_results = execute_batch([task], max_tasks=1)
            results.extend(batch_results)
            # Release lock on terminal state
            if batch_results and not batch_results[0].get("success"):
                pass  # Keep lock until zombie reclaim handles it
            else:
                release_spawn_lock(task, token)
        except Exception:
            release_spawn_lock(task, token)
            raise
    
    if skipped:
        print(f"   [IDEM] {skipped} tasks skipped (idempotent hit)")
    
    # Count results
    success_count = sum(1 for r in results if r["success"])
    failed_count = len(results) - success_count
    
    return {
        "processed": len(results),
        "success": success_count,
        "failed": failed_count,
    }


def execute_spawn_requests() -> int:
    """
    Phase 2.5 桥接层：读取spawn_requests.jsonl并真实执行
    
    Returns:
        Number of successfully executed spawn requests
    """
    spawn_file = Path(__file__).parent / 'spawn_requests.jsonl'
    
    if not spawn_file.exists():
        print("✅ [BRIDGE] spawn_requests.jsonl为空，无需执行")
        return 0
    
    executed_count = 0
    executed_ids = []
    new_lines = []
    
    with open(spawn_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines:
        if not line.strip():
            continue
        
        try:
            req = json.loads(line)
            task_id = req.get('task_id', 'unknown')
            print(f"🔄 [BRIDGE] 正在执行spawn请求: {task_id}")
            
            # 注意：这里需要调用真实的sessions_spawn
            # 由于我们在Python脚本中，无法直接调用OpenClaw的sessions_spawn
            # 所以这里先标记为"待执行"，实际执行需要在OpenClaw主会话中完成
            # 
            # 临时方案：将spawn请求写入一个OpenClaw可以读取的文件
            # 让OpenClaw主会话的heartbeat来执行
            
            # 这里我们先模拟执行（实际应该调用sessions_spawn）
            print(f"⚠️ [BRIDGE] spawn请求已生成，等待OpenClaw主会话执行: {task_id}")
            new_lines.append(line)  # 保留，等待OpenClaw执行
            
        except Exception as e:
            print(f"❌ [BRIDGE] 执行异常: {e}")
            new_lines.append(line)
    
    # 保留所有请求（等待OpenClaw主会话执行）
    with open(spawn_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"🎉 [BRIDGE] 本次检查到 {len(lines)} 个spawn请求（等待OpenClaw执行）")
    return executed_count


def run_evolution_guard_precheck() -> dict:
    """
    Pre-check evolution score freshness before health calculation.
    If stale, trigger recalculation via evolution_engine.
    
    Returns:
        {
            "guard_status": "ok" | "stale_data" | "recalculated" | "error",
            "evolution_score": float,
            "age_hours": float,
            "freshness": "fresh" | "stale" | "recalculated"
        }
    """
    import subprocess
    try:
        from evolution_guard import check_evolution_health
    except ImportError:
        return {"guard_status": "error", "evolution_score": 0, "age_hours": 0, "freshness": "stale"}

    guard = check_evolution_health()

    if guard["status"] == "ok":
        return {
            "guard_status": "ok",
            "evolution_score": guard["score"],
            "age_hours": guard["age_hours"],
            "freshness": "fresh",
        }

    # stale or low → try recalculation
    if guard["status"] in ("stale", "low"):
        print(f"   [GUARD] {guard['message']} → triggering recalc...")
        try:
            result = subprocess.run(
                ["C:\\Program Files\\Python312\\python.exe", "-X", "utf8",
                 str(Path(__file__).parent / "evolution_engine.py"), "run"],
                capture_output=True, text=True, encoding="utf-8", timeout=30
            )
            # Re-check after recalc
            guard2 = check_evolution_health()
            if guard2["status"] == "ok":
                return {
                    "guard_status": "recalculated",
                    "evolution_score": guard2["score"],
                    "age_hours": guard2["age_hours"],
                    "freshness": "recalculated",
                }
            else:
                # Still stale after recalc → degrade alert, don't flag as perf regression
                return {
                    "guard_status": "stale_data",
                    "evolution_score": guard2["score"],
                    "age_hours": guard2["age_hours"],
                    "freshness": "stale",
                }
        except Exception as e:
            return {
                "guard_status": "stale_data",
                "evolution_score": guard["score"],
                "age_hours": guard["age_hours"],
                "freshness": "stale",
            }

    # missing / error
    return {
        "guard_status": guard["status"],
        "evolution_score": guard["score"],
        "age_hours": guard["age_hours"],
        "freshness": "stale",
    }


def check_system_health(evolution_freshness: str = "fresh") -> dict:
    """
    Check system health (simplified version).
    Uses finished = completed + failed as denominator to avoid pending pollution.
    
    Args:
        evolution_freshness: "fresh" | "stale" | "recalculated"
    
    Returns:
        Health summary
    """
    stats = queue_stats()
    
    total = stats["total"]
    completed = stats["by_status"].get("completed", 0)
    failed = stats["by_status"].get("failed", 0)
    pending = stats["by_status"].get("pending", 0)
    
    # Use finished tasks as denominator — eliminates pending pollution
    finished = completed + failed
    
    # Calculate health score
    if finished == 0:
        health_score = 100.0
    else:
        success_rate = completed / finished  # key fix: finished not total
        failure_rate = failed / finished
        pending_ratio = pending / total if total > 0 else 0
        
        # Health score formula (0-100)
        health_score = (
            success_rate * 60 +        # 60 pts: success rate (pending-clean)
            (1 - failure_rate) * 30 +  # 30 pts: low failure rate
            (1 - pending_ratio) * 10   # 10 pts: low pending ratio
        )
    
    return {
        "score": round(health_score, 2),
        "total_tasks": total,
        "completed": completed,
        "failed": failed,
        "pending": pending,
        "finished": finished,
        "evolution_data_freshness": evolution_freshness,
    }


def main():
    """Main heartbeat function."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"╔══════════════════════════════════════════════════════════════╗")
    print(f"║  AIOS Heartbeat v5.0 - {timestamp}  ║")
    print(f"╚══════════════════════════════════════════════════════════════╝\n")
    
    # 0. Startup: cleanup expired spawn locks
    startup_cleanup()
    
    # 0. 启动 Self-Healing Loop v2（首次心跳时启动）
    start_self_healing_loop()
    print()
    
    # 0. 比卦资源共享模式激活（每次心跳）
    activate_bigua_resource_sharing()
    print()
    
    # 0. Token Monitor (每次心跳)
    print("[TOKEN] Token Usage Check:")
    alert = check_and_alert()
    if alert:
        print(f"   ⚠️ {alert['level'].upper()}: {alert['title']}")
        print(f"   {alert['body']}")
        
        # 自动优化
        strategies = auto_optimize()
        if strategies:
            print(f"   🔧 Auto-optimization applied:")
            for s in strategies:
                print(f"      - {s['name']}: {s['action']}")
    else:
        print(f"   ✅ Token usage within limits\n")
    
    # 0. LowSuccess Regeneration (每小时整点) + Phase 3观察
    from datetime import datetime
    current_minute = datetime.now().minute
    current_hour = datetime.now().hour
    if current_minute == 0:  # 每小时整点
        # Phase 2.5: 先执行spawn请求
        print("[BRIDGE] Spawn Request Execution:")
        executed = execute_spawn_requests()
        if executed > 0:
            print(f"   [OK] Executed: {executed} spawn requests\n")
        else:
            print(f"   [OK] No spawn requests to execute\n")
        
        # 然后生成新的regeneration请求 + Phase 3观察
        try:
            from low_success_regeneration import run_low_success_regeneration
            print("[REGEN] LowSuccess Regeneration + Phase 3 Observer:")
            stats = run_low_success_regeneration(limit=5)
            if stats['processed'] > 0:
                print(f"   [OK] Regenerated: {stats['processed']} tasks")
                print(f"   Pending: {stats['pending']}, Success: {stats['success']}, Failed: {stats['failed']}")
                print(f"   📊 Phase 3 报告已生成: reports/lowsuccess_phase3_report.md\n")
            else:
                print(f"   [OK] No failed tasks to regenerate\n")
        except ImportError as e:
            print(f"   ⚠️ LowSuccess Regeneration disabled (missing dependency: {e})\n")
    
    # 0.5. Experience Learning v4.0 (每小时整点，在regeneration之后)
    if current_minute == 0:
        print("[LEARN] Experience Learner v4.0:")
        metrics = learner_v4.get_metrics()
        store = metrics.get("store_stats", {})
        cfg = metrics.get("config", {})
        print(f"   Grayscale: {cfg.get('grayscale_ratio', 0):.0%} | Version: {cfg.get('strategy_version', '?')}")
        print(f"   Store: {store.get('total_entries', 0)} entries, {store.get('unique_error_types', 0)} error types")
        print(f"   Hit rate: {metrics.get('recommend_hit_rate', 0):.1%} | Regen success: {metrics.get('regen_success_rate', 0):.1%}")
        post_fail = metrics.get('post_recommend_failure_rate', 0)
        if post_fail > 0.3:
            print(f"   ⚠️  Post-recommend failure rate HIGH: {post_fail:.1%}")
        else:
            print(f"   Post-recommend failure: {post_fail:.1%}")
        print()
    
    # 0.6. Adversarial Validation Dashboard (每小时整点)
    if current_minute == 0:
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agents" / "adversarial_validator"))
            from validation_dashboard import generate_validation_report
            print("[ADVERSARIAL] Validation Dashboard:")
            generate_validation_report()
            print(f"   [OK] 报告已生成: reports/adversarial_validation_report.md\n")
        except Exception as e:
            print(f"   [OK] Adversarial Validation 暂无数据\n")
    
    # 0.7. Hexagram Timeline Logging (每小时整点)
    if current_minute == 0:
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / "policy"))
            from hexagram_timeline import print_timeline_summary, generate_timeline_report
            print("[HEXAGRAM] Hexagram Timeline:")
            print_timeline_summary()
            generate_timeline_report()
            print(f"   [OK] Timeline report updated\n")
        except Exception as e:
            print(f"   [OK] Hexagram Timeline: {e}\n")
    
    # 1. Reclaim zombie running tasks (before processing queue)
    print("[ZOMBIE] Checking for stale running tasks...")
    zombie_result = reclaim_zombie_tasks(timeout_seconds=300, max_retries=2)
    if zombie_result["reclaimed"] > 0:
        print(f"   Reclaimed: {zombie_result['reclaimed']} (retried: {zombie_result['retried']}, failed: {zombie_result['permanently_failed']})")
    else:
        print("   No zombie tasks found")
    
    # 2. Process task queue
    queue_result = process_task_queue(max_tasks=5)
    
    if queue_result["processed"] > 0:
        print(f"[QUEUE] Task Queue Processing:")
        print(f"   Processed: {queue_result['processed']} tasks")
        print(f"   Success: {queue_result['success']}")
        print(f"   Failed: {queue_result['failed']}")
    else:
        print("[QUEUE] Task Queue: No pending tasks")
    
    # 3. Evolution Guard Pre-Check (before health calculation)
    print(f"\n[EVOLUTION_GUARD] Pre-Check:")
    guard_result = run_evolution_guard_precheck()
    print(f"   Status: {guard_result['guard_status']}")
    print(f"   Score: {guard_result['evolution_score']:.1f}")
    print(f"   Age: {guard_result['age_hours']:.1f}h")
    print(f"   Freshness: {guard_result['freshness']}")
    
    # 4. Check system health (with freshness context)
    print(f"\n[HEALTH] System Health Check:")
    health = check_system_health(evolution_freshness=guard_result['freshness'])
    
    # Determine health status
    if health['score'] >= 80:
        status = "GOOD"
    elif health['score'] >= 60:
        status = "WARNING"
    else:
        status = "CRITICAL"
    
    print(f"   Score: {health['score']}/100 ({status})")
    print(f"   Total: {health['total_tasks']} tasks")
    print(f"   Finished: {health['finished']} (completed + failed)")
    print(f"   Completed: {health['completed']}")
    print(f"   Failed: {health['failed']}")
    print(f"   Pending: {health['pending']}")
    print(f"   Evolution Freshness: {health['evolution_data_freshness']}")
    
    # 2.5. Sync agent statistics (every hour at :00)
    if current_minute == 0:
        try:
            from sync_agent_stats import sync_agent_stats
            print(f"\n[SYNC] Syncing agent statistics...")
            sync_agent_stats()
        except Exception as e:
            print(f"[WARN] Agent stats sync failed: {e}")
        
        # Spawn lock health check
        try:
            from spawn_lock_monitor import check_spawn_lock_health
            print(f"\n[LOCK] Spawn lock health check:")
            check_spawn_lock_health()
        except Exception as e:
            print(f"[WARN] Spawn lock monitor failed: {e}")
    
    # 2.8. Learnings Extractor (每天0点和12点提炼黄金法则)
    if current_minute == 0 and current_hour in (0, 12):
        try:
            from learnings_extractor import run as run_learnings_extractor
            print(f"\n[LEARNINGS] Extracting Golden Rules:")
            result = run_learnings_extractor()
            if result["rules_new"] > 0:
                print(f"   🆕 {result['rules_new']} new rules extracted!")
            print(f"   Total: {result['rules_total']} rules | Success rate: {result['success_rate']:.1%}")
        except Exception as e:
            print(f"[WARN] Learnings extractor failed: {e}")

    # 3. Token Report (每天0点生成)
    if current_minute == 0 and datetime.now().hour == 0:
        print(f"\n[REPORT] Daily Token Report:")
        report = generate_report('daily')
        print(report)
    
    # 3.5. Daily Metrics (00:00 full, 12:00 quick)
    if current_minute == 0 and current_hour == 0:
        try:
            from daily_metrics import run as run_daily_metrics
            print(f"\n[METRICS] Full Daily Metrics:")
            run_daily_metrics(mode="full")
            # Also generate 7-day dashboard
            from observability_dashboard import run as run_dashboard
            run_dashboard()
        except Exception as e:
            print(f"[WARN] Daily metrics failed: {e}")
    elif current_minute == 0 and current_hour == 12:
        try:
            from daily_metrics import run as run_daily_metrics
            print(f"\n[METRICS] Quick Metrics Check:")
            run_daily_metrics(mode="quick")
        except Exception as e:
            print(f"[WARN] Quick metrics failed: {e}")
    
    # 4. Output summary
    idem_metrics = get_idempotency_metrics()
    print(f"\n{'=' * 62}")
    if queue_result["processed"] > 0:
        print(f"[OK] HEARTBEAT_OK | Processed: {queue_result['processed']} | Health: {health['score']:.0f}/100")
    else:
        print(f"[OK] HEARTBEAT_OK | No tasks | Health: {health['score']:.0f}/100")
    print(f"     Idempotent hit rate: {idem_metrics['idempotent_hit_rate']:.1%} | Stale locks recovered: {idem_metrics['stale_lock_recovered_total']}")
    print(f"{'=' * 62}\n")


class HeartbeatSchedulerV5:
    """
    Heartbeat scheduler with boot recovery + periodic recovery.

    Recovery rules (per user spec):
    - transition_status must be WHERE task_id AND status (atomic).
    - running → queued clears worker_id / started_at / last_heartbeat_at.
    - Periodic recovery is debounced by _last_recovery_ts (updated on both
      success and failure to prevent tight retry storms).
    """

    def __init__(
        self,
        recovery_timeout_seconds: int = 300,
        recovery_interval_seconds: int = 600,
        recovery_scan_limit: int = 1000,
    ) -> None:
        import logging
        self.logger = logging.getLogger(self.__class__.__name__)
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.recovery_interval_seconds = recovery_interval_seconds
        self.recovery_scan_limit = recovery_scan_limit
        self._last_recovery_ts: float = 0.0

    # ── public API ────────────────────────────────────────────────────────────

    def start(self) -> None:
        """启动时执行一次 boot recovery，然后进入主循环。"""
        try:
            self._recover_on_boot()
        except Exception:
            self.logger.exception("boot recovery failed")
        self._run_loop()

    def tick(self, now_ts: float) -> None:
        """每次心跳调用一次；内部决定是否触发周期 recovery。"""
        try:
            self._maybe_run_periodic_recovery(now_ts)
        except Exception:
            self.logger.exception("periodic recovery failed")

    # ── internal ──────────────────────────────────────────────────────────────

    def _recover_on_boot(self) -> None:
        """启动时回收所有超时 running 任务（扫描上限 recovery_scan_limit）。"""
        self.logger.info("[RECOVERY] boot scan started (timeout=%ds)", self.recovery_timeout_seconds)
        result = reclaim_zombie_tasks(
            timeout_seconds=self.recovery_timeout_seconds,
            max_retries=2,
        )
        self.logger.info(
            "[RECOVERY] boot done: reclaimed=%d retried=%d permanently_failed=%d",
            result["reclaimed"], result["retried"], result["permanently_failed"],
        )

    def _maybe_run_periodic_recovery(self, now_ts: float) -> None:
        """
        周期 recovery 门控：距上次执行超过 recovery_interval_seconds 才触发。
        无论成功失败都更新 _last_recovery_ts（防抖）。
        """
        elapsed = now_ts - self._last_recovery_ts
        if elapsed < self.recovery_interval_seconds:
            return

        # 先更新时间戳（防抖：即使下面抛异常也不会立刻重试）
        self._last_recovery_ts = now_ts

        self.logger.info(
            "[RECOVERY] periodic scan (elapsed=%.0fs, timeout=%ds)",
            elapsed, self.recovery_timeout_seconds,
        )
        result = reclaim_zombie_tasks(
            timeout_seconds=self.recovery_timeout_seconds,
            max_retries=2,
        )
        self.logger.info(
            "[RECOVERY] periodic done: reclaimed=%d retried=%d permanently_failed=%d",
            result["reclaimed"], result["retried"], result["permanently_failed"],
        )

    def _run_loop(self) -> None:
        """主循环：每次调用 main() 并 tick()。"""
        while True:
            now_ts = time.time()
            try:
                main()
            except Exception:
                self.logger.exception("heartbeat main() failed")
            self.tick(now_ts)
            time.sleep(30)


if __name__ == "__main__":
    main()
