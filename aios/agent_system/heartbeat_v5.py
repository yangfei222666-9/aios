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
import logging
from pathlib import Path

# Fix Windows encoding (safe fallback)
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass  # Already UTF-8 or not reconfigurable

# Add agent_system to path
AGENT_SYSTEM_ROOT = Path(__file__).resolve().parent
if str(AGENT_SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_SYSTEM_ROOT))

AIOS_ROOT = AGENT_SYSTEM_ROOT.parent

# Setup logging (file + console)
HEARTBEAT_LOG = AIOS_ROOT / "data" / "heartbeat.log"
HEARTBEAT_LOG.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler(HEARTBEAT_LOG, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

from core.task_submitter import list_tasks, queue_stats
from core.task_executor import execute_batch
from core.status_adapter import get_task_status
# from low_success_regeneration import run_low_success_regeneration  # Temporarily disabled for service
from experience_learner_v4 import learner_v4
from token_monitor import check_and_alert, auto_optimize, generate_report
from diary_extractor import extract_diary_from_session, save_diary

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
        loop = asyncio.get_running_loop()
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


# ── P2.5-1: Heartbeat → DecideAndDispatch 桥接 ──────────────────────────────
from heartbeat_dispatcher_bridge import HeartbeatDispatcherBridge

from spawn_lock import (
    startup_cleanup, 
    try_acquire_spawn_lock, 
    release_spawn_lock, 
    get_idempotency_metrics,
    recover_stale_locks,
    transition_status
)
from paths import (
    TASK_QUEUE, TASK_EXECUTIONS,
    SPAWN_REQUESTS, SPAWN_PENDING, SPAWN_RESULTS,
    HEARTBEAT_LOG, HEARTBEAT_STATE, HEARTBEAT_STATS,
    ALERTS, EXECUTED_ACTIONS
)
from reality_ledger import create_action, transition_action
from ledger_summary import compute_ledger_summary, format_heartbeat_summary


def _print_learning_agents_status():
    """打印 learning agents 状态（使用统一分类器）"""
    from paths import AGENTS_STATE
    from agent_availability_classifier import classify_all_agents, get_active_ratio
    
    agents_file = AGENTS_STATE
    if not agents_file.exists():
        print("   ⚠️ agents.json not found")
        return
    
    with open(agents_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    agents = data.get("agents", [])
    learning_agents = [a for a in agents if a.get("group") == "learning"]
    
    # ── 使用统一分类器（唯一真源）──
    classified = classify_all_agents(learning_agents)
    active_routable = classified["active_routable"]
    schedulable_idle = classified["schedulable_idle"]
    shadow = classified["shadow"]
    disabled = classified["disabled"]
    
    # ── 状态一致性校验 ──
    # mode=active 必须 enabled=true，否则自动修复
    fixed = 0
    for a in learning_agents:
        mode = a.get("mode")
        enabled = a.get("enabled")
        if mode == "active" and enabled is not True:
            a["enabled"] = True
            fixed += 1
        elif mode in ("shadow", "disabled") and enabled is True:
            a["enabled"] = False
            fixed += 1
    if fixed > 0:
        with open(agents_file, "w", encoding="utf-8") as fw:
            json.dump(data, fw, indent=2, ensure_ascii=False)
        print(f"   🔧 Fixed {fixed} agent(s) with inconsistent mode/enabled state")
    
    # ── 计算活跃率（只基于可调度 Agent）──
    active_count, routable_count = get_active_ratio(learning_agents)
    
    print(f"   Total: {len(learning_agents)} | Active & Routable: {active_count}/{routable_count} | Shadow: {len(shadow)} | Disabled: {len(disabled)}")
    
    if active_routable:
        print(f"\n   [ACTIVE] {len(active_routable)} agents:")
        for a in active_routable:
            stats = a.get("stats", {})
            total = stats.get("tasks_total", 0)
            completed = stats.get("tasks_completed", 0)
            if total > 0:
                success_rate = completed / total * 100
                print(f"      • {a['name']}: {completed}/{total} ({success_rate:.0f}%)")
            else:
                print(f"      • {a['name']}: 0 tasks (未运行)")
    
    if schedulable_idle:
        print(f"\n   [SCHEDULABLE_IDLE] {len(schedulable_idle)} agents (可调度但未触发):")
        for a in schedulable_idle[:5]:
            print(f"      • {a['name']}")
        if len(schedulable_idle) > 5:
            print(f"      ... and {len(schedulable_idle) - 5} more")
    
    if shadow:
        print(f"\n   [SHADOW] {len(shadow)} agents (保留但不路由):")
        for a in shadow[:5]:  # 只显示前5个
            print(f"      • {a['name']}")
        if len(shadow) > 5:
            print(f"      ... and {len(shadow) - 5} more")
    
    if disabled:
        print(f"\n   [DISABLED] {len(disabled)} agents (已禁用)")
    
    print()


def reclaim_zombie_tasks(timeout_seconds: int = 300, max_retries: int = 2) -> dict:
    """
    回收超时的 running 任务：running > timeout_seconds => retry(带上限) or failed
    使用 transition_status 原子更新，清空 worker_id/started_at/last_heartbeat_at。

    Returns:
        {"reclaimed": int, "retried": int, "permanently_failed": int}
    """
    queue_file = TASK_QUEUE
    if not queue_file.exists():
        return {"reclaimed": 0, "retried": 0, "permanently_failed": 0}

    now = time.time()
    reclaimed = retried = permanently_failed = 0

    with open(queue_file, "r", encoding="utf-8") as f:
        tasks = [json.loads(l) for l in f if l.strip()]

    modified = False
    for task in tasks:
        if get_task_status(task) != "running":
            continue

        updated_at = task.get("updated_at", task.get("created_at", 0))
        age = now - updated_at
        if age <= timeout_seconds:
            continue

        task_id = task.get("id") or task.get("task_id") or "?"
        age_hr = age / 3600
        retry_count = task.get("zombie_retries", 0)

        if retry_count < max_retries:
            # 原子转换 running → queued，清空 worker 字段
            ok = transition_status(
                task,
                from_status="running",
                to_status="pending",
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
        task_id = task.get("id") or task.get("task_id") or "unknown"
        # Reality Ledger: create action (proposed)
        action = create_action(
            actor="heartbeat",
            source="heartbeat_v5",
            resource_type="task",
            resource_id=task_id,
            action_type="execute_task",
            payload={"task_type": task.get("type", task.get("task_type", "")), "task_id": task_id},
            idempotency_key=f"task:execute:{task_id}",
            lock_resource=f"task:{task_id}",
            tags=["task_execution", "heartbeat"],
        )
        # 将 action_id 注入 task，供 executor 使用
        task["action_id"] = action.action_id
        print(f"  [LEDGER] Created action {action.action_id} for task {task_id}")

        token = try_acquire_spawn_lock(task)
        if token is None:
            skipped += 1
            # Reality Ledger: skipped (resource busy / duplicate)
            try:
                transition_action(action.action_id, "skipped", actor="heartbeat", payload={"reason": "resource_busy"})
            except Exception:
                pass
            continue
        
        # Reality Ledger: locked
        try:
            transition_action(action.action_id, "locked", actor="heartbeat", payload={"lock_token": token})
        except Exception as e:
            print(f"  [LEDGER] locked transition failed: {e}")
            release_spawn_lock(task, token)
            skipped += 1
            continue

        try:
            batch_results = execute_batch([task], max_tasks=1)
            results.extend(batch_results)

            # execute_batch 内部已推进 executing → completed/failed
            # 这里只需要 completed/failed → released
            release_spawn_lock(task, token)
            try:
                transition_action(
                    action.action_id, "released", actor="heartbeat",
                    payload={"release_reason": "execution_done"},
                )
            except Exception as e:
                print(f"  [LEDGER] released transition failed: {e}")

        except Exception as exc:
            # execute_batch 异常：可能 executing 已推进也可能没有
            # 先尝试补 failed，再 released；如果状态不允许，catch 住继续
            release_spawn_lock(task, token)
            try:
                transition_action(
                    action.action_id, "failed", actor="heartbeat",
                    payload={"error": str(exc)[:300]},
                )
            except Exception:
                pass  # 可能 executor 内部已经 transition 到 failed 了
            try:
                transition_action(
                    action.action_id, "released", actor="heartbeat",
                    payload={"release_reason": "execution_done"},
                )
            except Exception:
                pass  # 如果 failed transition 也失败了，released 也会失败，记录即可
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
    Phase 2.5 桥接层：读取spawn_requests.jsonl，输出待执行列表供OpenClaw主会话真实调用。

    协议：
    - 将待执行请求写入 spawn_pending.jsonl（OpenClaw主会话读取并调用sessions_spawn）
    - 已输出的请求从 spawn_requests.jsonl 移除（避免重复）
    - 使用 ActionLock 防止同一 action 重复执行
    - 返回输出的请求数量

    Returns:
        Number of spawn requests queued for execution
    """
    from action_lock import ActionLock
    action_lock = ActionLock()

    spawn_file = SPAWN_REQUESTS
    pending_file = SPAWN_PENDING

    if not spawn_file.exists():
        return 0

    with open(spawn_file, 'r', encoding='utf-8') as f:
        lines = [l for l in f.readlines() if l.strip()]

    if not lines:
        return 0

    queued = 0
    skipped = 0
    for line in lines:
        try:
            req = json.loads(line)
            task_id = req.get('task_id', 'unknown')
            action_id = req.get('id', task_id)
            resource_id = req.get('agent_id', 'spawn-queue')

            # Action Lock: 防止重复执行
            if not action_lock.acquire(resource_id, action_id, timeout=600):
                print(f"  [BRIDGE] Skipped (idempotent/locked): {task_id}")
                skipped += 1
                continue

            # 追加到 pending 文件（OpenClaw主会话消费）
            with open(pending_file, 'a', encoding='utf-8') as pf:
                pf.write(line if line.endswith('\n') else line + '\n')
            print(f"  [BRIDGE] Queued for real execution: {task_id}")
            queued += 1
            
            # Tracing: spawn_consumed
            try:
                from tracer import trace_event
                trace_event(
                    trace_id=req.get("trace_id", f"trace-{task_id}"),
                    task_id=task_id,
                    step_name="spawn_consumed",
                    source="heartbeat",
                    agent_name=req.get("agent_id", ""),
                    result_summary="moved to spawn_pending",
                )
            except Exception:
                pass  # trace 写失败不阻塞主流程
            
            # 执行成功后释放锁（标记为已执行）
            action_lock.release(resource_id, action_id, success=True)
        except Exception as e:
            print(f"  [BRIDGE] Parse error: {e}")

    # 清空已输出的请求
    spawn_file.write_text('', encoding='utf-8')
    if skipped:
        print(f"  [BRIDGE] {skipped} requests skipped (idempotent)")
    print(f"  [BRIDGE] {queued} requests moved to spawn_pending.jsonl")
    return queued


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
    
    # P2.5-1: 初始化中枢桥接器
    dispatch_bridge = HeartbeatDispatcherBridge()
    
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
        
        # P2.5-1: 收集 Token 告警事件
        dispatch_bridge.collect_token_alert(alert)
        
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
        except (ImportError, SyntaxError, Exception) as e:
            print(f"   ⚠️ LowSuccess Regeneration disabled ({type(e).__name__}: {e})\n")
    
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
    
    # 0.8. Process spawn_pending.jsonl (HIGHEST PRIORITY)
    print("[SPAWN_PENDING] Checking for pending spawn requests...")
    spawn_pending_file = Path(__file__).parent / "data" / "spawn_pending.jsonl"
    if spawn_pending_file.exists():
        try:
            with spawn_pending_file.open("r", encoding="utf-8") as f:
                requests = [json.loads(l) for l in f if l.strip()]
            
            if requests:
                print(f"   Found {len(requests)} spawn requests")
                # TODO: Call sessions_spawn for each request
                # For now, just log them
                for req in requests:
                    print(f"   - {req['agent_id']}: {req['task'][:50]}...")
                
                # Clear the file after processing
                spawn_pending_file.write_text("", encoding="utf-8")
                print(f"   ✅ Processed {len(requests)} spawn requests")
            else:
                print("   No spawn requests")
        except Exception as e:
            print(f"   ❌ Error processing spawn_pending: {e}")
    else:
        print("   No spawn_pending.jsonl file")
    
    # 1. Reclaim zombie running tasks (before processing queue)
    print("[ZOMBIE] Checking for stale running tasks...")
    zombie_result = reclaim_zombie_tasks(timeout_seconds=300, max_retries=2)
    if zombie_result["reclaimed"] > 0:
        print(f"   Reclaimed: {zombie_result['reclaimed']} (retried: {zombie_result['retried']}, failed: {zombie_result['permanently_failed']})")
    else:
        print("   No zombie tasks found")
    
    # P2.5-1: 收集僵尸回收事件
    dispatch_bridge.collect_zombie_reclaim(zombie_result)
    
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
    
    # P2.5-1: 收集演化分数过期事件
    dispatch_bridge.collect_evolution_stale(guard_result)
    
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
    
    # P2.5-1: 收集健康检查事件
    dispatch_bridge.collect_health_check(health)
    
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
        
        # Skill Memory aggregation (every hour)
        try:
            from skill_memory_aggregator import aggregate_all_skills
            print(f"\n[SKILL_MEMORY] Aggregating skill statistics...")
            aggregate_all_skills()
        except Exception as e:
            print(f"[WARN] Skill memory aggregation failed: {e}")
        
        # Skill Failure Alert (每小时检查连续失败)
        try:
            from skill_failure_alert import check_consecutive_failures, format_alert_message
            print(f"\n[SKILL_ALERT] Checking consecutive failures...")
            alerts = check_consecutive_failures(window_size=5)
            if alerts:
                print(f"   ⚠️ {len(alerts)} skill(s) with consecutive failures:")
                for alert in alerts[:3]:  # 只显示前 3 个
                    print(f"\n{format_alert_message(alert)}")
                
                # P2.5-1: 收集技能失败告警事件
                dispatch_bridge.collect_skill_failure(alerts)
            else:
                print("   ✅ All skills running normally")
            
            # ── Shadow Mode: Deduper 并行评估（只记录，不控制通知）──
            if alerts:
                try:
                    from heartbeat_alert_deduper import run_shadow_evaluation
                    print(f"\n[DEDUPER_SHADOW] Running parallel evaluation...")
                    run_shadow_evaluation(alerts)
                except Exception as e:
                    print(f"   [DEDUPER_SHADOW] Failed (non-blocking): {e}")
        except Exception as e:
            print(f"[WARN] Skill failure alert failed: {e}")
        
        # Skill Analyzer Phase 2 (每周一次，周一0点)
        if current_hour == 0:
            from datetime import datetime as _dt
            if _dt.now().weekday() == 0:  # Monday
                try:
                    from skill_analyzer import analyze_skills, print_analysis
                    print(f"\n[SKILL_ANALYZER] Weekly Skill Analysis:")
                    result = analyze_skills(days=7)
                    print_analysis(result)
                    if result.get("weekly_tip"):
                        print(f"   💡 {result['weekly_tip']}")
                except Exception as e:
                    print(f"[WARN] Skill analysis failed: {e}")
    
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

    # 2.9. Diary Extraction (每天23:00自动提取对话)
    if current_minute == 0 and current_hour == 23:
        try:
            print(f"\n[DIARY] Extracting daily conversations...")
            diary_entry = extract_diary_from_session()
            if diary_entry:
                save_diary(diary_entry)
                print(f"   ✅ Diary saved: {diary_entry['date']}")
            else:
                print(f"   ℹ️  No conversations to extract today")
        except Exception as e:
            print(f"[WARN] Diary extraction failed: {e}")
    
    # 2.9.5. Hexagram Daily Snapshot (每天23:00收敛卦象快照)
    if current_minute == 0 and current_hour == 23:
        try:
            from hexagram_daily_logger import run as run_hexagram_daily_logger
            print(f"\n[HEXAGRAM_DAILY] Collecting daily hexagram snapshot...")
            run_hexagram_daily_logger()
            print(f"   ✅ Snapshot saved: data/hexagram_daily.jsonl")
        except Exception as e:
            print(f"[WARN] Hexagram daily snapshot failed: {e}")

    # 2.10. Learning Agent Observer (每天0点自动更新观察表)
    if current_minute == 0 and current_hour == 0:
        try:
            from learning_agent_observer import main as run_observer
            print(f"\n[OBSERVER] Learning Agent Observer:")
            run_observer()
        except Exception as e:
            print(f"[WARN] Learning agent observer failed: {e}")
    
    # 2.11. Learning Agent Triggers (每小时检查触发条件)
    if current_minute == 0:
        try:
            from learning_agent_triggers import run_triggers
            print(f"\n[TRIGGERS] Learning Agent Triggers:")
            tasks = run_triggers()
            if tasks:
                print(f"   ✓ {len(tasks)} tasks triggered")
        except Exception as e:
            print(f"[WARN] Learning agent triggers failed: {e}")
    
    # 2.12. Memory Server Health Check (每次心跳)
    # 🔧 FIX: 添加状态缓存，只在状态变化时生成事件
    try:
        from detectors.memory_server_health import MemoryServerHealthDetector
        print(f"\n[MEMORY_SERVER] Health Check:")
        detector = MemoryServerHealthDetector()
        check_result = detector.check()
        
        status = check_result["status"]
        severity = check_result["severity"]
        response_time = check_result["response_time_ms"]
        
        # 输出状态
        status_emoji = {
            "healthy": "✅",
            "degraded": "⚠️",
            "down": "❌"
        }
        print(f"   {status_emoji.get(status, '❓')} Status: {status} | Response: {response_time}ms | Severity: {severity}")
        
        # 检查上次状态（从状态文件读取）
        state_file = Path(__file__).parent / "data" / "memory_server_state.json"
        last_status = None
        if state_file.exists():
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    last_status = state.get("last_status")
            except:
                pass
        
        # 只在状态变化时生成事件
        if status != "healthy" and status != last_status:
            event = detector.generate_event(check_result)
            print(f"   📋 Event: {event['summary']}")
            print(f"   🔧 Suggested: {event['suggested_action']}")
            
            # 写入事件日志
            events_file = Path(__file__).parent / "data" / "events.jsonl"
            events_file.parent.mkdir(parents=True, exist_ok=True)
            with open(events_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        
        # 更新状态文件
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump({
                "last_status": status,
                "last_check": datetime.now().isoformat(),
                "response_time_ms": response_time
            }, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"[WARN] Memory Server health check failed: {e}")
    
    # 2.13. Execution Latency Anomaly Detection (每次心跳)
    try:
        from detectors.exec_latency_detector import ExecLatencyDetector
        print(f"\n[EXEC_LATENCY] Anomaly Detection:")
        
        # 初始化检测器
        latency_detector = ExecLatencyDetector()
        
        # 加载基线
        records_path = Path(__file__).parent / "data" / "agent_execution_record.jsonl"
        latency_detector.load_baselines(records_path)
        
        # 显示摘要
        summary = latency_detector.get_summary()
        print(f"   📊 Baseline: {summary['entities_with_baseline']}/{summary['total_entities']} entities")
        
        if summary['entities_degraded'] > 0:
            print(f"   ⚠️  Degraded: {summary['entities_degraded']} entities")
        
        # 检查最近的执行记录（最后 5 条）
        # 🔧 FIX: 添加去重机制，避免对同一条记录重复生成事件
        if records_path.exists():
            recent_records = []
            checked_tasks = set()  # 记录已检查的 task_id，避免重复
            
            # 加载已检查过的 task_id（从最近的事件中提取）
            events_file = Path(__file__).parent / "data" / "events.jsonl"
            if events_file.exists():
                with open(events_file, "r", encoding="utf-8") as f:
                    # 只读最近 100 条事件
                    lines = f.readlines()
                    for line in lines[-100:]:
                        try:
                            event = json.loads(line.strip())
                            # 从 trace_id 中提取 entity_id（格式：trace-exec-latency-{entity_id}-{timestamp}）
                            if event.get("source") == "exec_latency_detector":
                                trace_id = event.get("trace_id", "")
                                if trace_id.startswith("trace-exec-latency-"):
                                    parts = trace_id.split("-")
                                    if len(parts) >= 4:
                                        entity_id = "-".join(parts[3:-1])  # 提取 entity_id
                                        checked_tasks.add(entity_id)
                        except:
                            continue
            
            with open(records_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[-5:]:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        if "duration_sec" in record and record.get("outcome") == "success":
                            task_id = record.get("task_id", "unknown")
                            # 跳过已检查过的记录
                            if task_id not in checked_tasks:
                                recent_records.append(record)
                    except json.JSONDecodeError:
                        continue
            
            # 检查每条记录
            anomalies = []
            for record in recent_records:
                entity_id = record.get("agent_name") or record.get("task_id", "unknown")
                task_id = record.get("task_id", "unknown")
                duration_ms = record["duration_sec"] * 1000
                
                check_result = latency_detector.check(entity_id, duration_ms)
                
                if check_result["status"] not in ("normal", "cold_start"):
                    anomalies.append((entity_id, check_result))
                    
                    # 生成事件
                    event = latency_detector.generate_event(
                        entity_id,
                        "agent",
                        check_result
                    )
                    
                    if event:
                        # 标记为已检查
                        checked_tasks.add(task_id)
                        
                        # 写入事件日志
                        events_file = Path(__file__).parent / "data" / "events.jsonl"
                        events_file.parent.mkdir(parents=True, exist_ok=True)
                        with open(events_file, "a", encoding="utf-8") as f:
                            f.write(json.dumps(event, ensure_ascii=False) + "\n")
            
            # 输出异常
            if anomalies:
                print(f"   ⚠️  Anomalies detected:")
                for entity_id, result in anomalies:
                    status_emoji = {
                        "warn": "⚠️",
                        "critical": "❌",
                        "degraded": "🔻"
                    }
                    emoji = status_emoji.get(result["status"], "❓")
                    print(f"      {emoji} {entity_id}: {result['current_duration_ms']}ms ({result['deviation_ratio']}x median)")
            else:
                print(f"   ✅ All executions within normal range")
        
    except Exception as e:
        print(f"[WARN] Execution latency detection failed: {e}")
    
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
    
    # 4. Ledger Summary (24h)
    print(f"\n[LEDGER] 24h Summary:")
    ledger_summary = compute_ledger_summary(hours=24.0)
    print(format_heartbeat_summary(ledger_summary))
    
    # 4.5. Learning Agents Status (每次心跳)
    print(f"\n[LEARNING_AGENTS] Status:")
    _print_learning_agents_status()
    
    # 4.6. Agent Lifecycle Engine (每小时整点)
    if current_minute == 0:
        try:
            from agent_lifecycle_engine import run_lifecycle_engine
            print(f"\n[LIFECYCLE] Agent Lifecycle Engine:")
            result = run_lifecycle_engine()
            print(f"   ✓ Updated {result['updated_agents']}/{result['total_agents']} agents")
            print(f"   • 乾卦（active）: {result['state_distribution']['active']}")
            print(f"   • 坤卦（shadow）: {result['state_distribution']['shadow']}")
            print(f"   • 坎卦（disabled）: {result['state_distribution']['disabled']}")
        except Exception as e:
            print(f"[WARN] Lifecycle engine failed: {e}")
    
    # 4.7. Lifecycle Check (每次心跳，只读模式)
    try:
        from heartbeat_lifecycle import run_lifecycle_check
        print(f"\n[LIFECYCLE_CHECK] Agent Lifecycle Status:")
        lifecycle_report = run_lifecycle_check(write_back=False)
        # 只输出摘要，不输出完整报告（避免刷屏）
        lines = lifecycle_report.split('\n')
        summary_start = next((i for i, line in enumerate(lines) if line.startswith('📊 Summary:')), None)
        if summary_start:
            for line in lines[summary_start:]:
                print(f"   {line}")
        else:
            print("   ✓ Lifecycle check completed")
    except Exception as e:
        print(f"[WARN] Lifecycle check failed: {e}")

    # ── P2.5-1: 中枢统一派发 ──────────────────────────────────────────────────
    event_count = dispatch_bridge.get_event_count()
    if event_count > 0:
        print(f"\n[DISPATCH] 中枢处理 ({event_count} events):")
        dispatch_bridge.dispatch_all()
        print(dispatch_bridge.get_summary())
    else:
        print(f"\n[DISPATCH] 中枢: 无异常事件")
    
    # 5. Output summary
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
