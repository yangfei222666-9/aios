#!/usr/bin/env python3
"""
AIOS Baseline Snapshot - 可靠性关键指标基线
用于 48h 观测期前后对比

基线时间：2026-03-06 11:31
复盘时间：2026-03-08 11:05
"""

import json
import time
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent
BASELINE_FILE = WORKSPACE / "baseline_snapshot.json"

# 指标文件路径 - 统一从 paths.py 获取
try:
    from paths import TASK_QUEUE, TASK_EXECUTIONS
except ImportError:
    TASK_QUEUE = WORKSPACE / "data" / "task_queue.jsonl"
    TASK_EXECUTIONS = WORKSPACE / "data" / "task_executions.jsonl"
PHASE3_LOG = WORKSPACE / "phase3_observations.jsonl"
SPAWN_LOCK_METRICS = WORKSPACE / "spawn_lock_metrics.json"


def load_phase3_metrics() -> dict:
    """Phase 3 字段完整率"""
    if not PHASE3_LOG.exists():
        return {"total": 0, "complete_fields": 0, "completeness_rate": 0.0}
    
    total = 0
    complete = 0
    with open(PHASE3_LOG, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            total += 1
            obs = json.loads(line)
            # 检查关键字段：agent_id / reborn_at / outcome
            if all(k in obs for k in ["agent_id", "reborn_at", "outcome"]):
                complete += 1
    
    return {
        "total": total,
        "complete_fields": complete,
        "completeness_rate": round(complete / total, 4) if total > 0 else 0.0,
    }


def load_zombie_metrics() -> dict:
    """僵尸任务回收率、重试耗尽率、永久失败率"""
    if not TASK_QUEUE.exists():
        return {
            "total_tasks": 0,
            "zombie_reclaimed": 0,
            "zombie_retried": 0,
            "zombie_permanently_failed": 0,
            "reclaim_rate": 0.0,
        }
    
    total = 0
    reclaimed = 0
    retried = 0
    permanently_failed = 0
    
    with open(TASK_QUEUE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            task = json.loads(line)
            total += 1
            if "zombie_retries" in task:
                reclaimed += 1
                if task.get("status") == "pending":
                    retried += 1
                elif task.get("status") == "failed" and "permanently failed" in task.get("zombie_note", ""):
                    permanently_failed += 1
    
    return {
        "total_tasks": total,
        "zombie_reclaimed": reclaimed,
        "zombie_retried": retried,
        "zombie_permanently_failed": permanently_failed,
        "reclaim_rate": round(reclaimed / total, 4) if total > 0 else 0.0,
    }


def load_failure_classification() -> dict:
    """simulation 与真实失败分层成功率"""
    if not TASK_EXECUTIONS.exists():
        return {
            "total_executions": 0,
            "simulation_failures": 0,
            "real_failures": 0,
            "simulation_rate": 0.0,
        }
    
    total = 0
    simulation_fails = 0
    real_fails = 0
    
    with open(TASK_EXECUTIONS, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            exec_entry = json.loads(line)
            if not exec_entry.get("result", {}).get("success", False):
                total += 1
                error = exec_entry.get("result", {}).get("error", "").lower()
                if "simulated" in error or "simulation" in error:
                    simulation_fails += 1
                else:
                    real_fails += 1
    
    return {
        "total_failures": total,
        "simulation_failures": simulation_fails,
        "real_failures": real_fails,
        "simulation_rate": round(simulation_fails / total, 4) if total > 0 else 0.0,
    }


def load_spawn_lock_metrics() -> dict:
    """spawn_lock 冲突率、超时释放率、误拦截率"""
    if not SPAWN_LOCK_METRICS.exists():
        return {
            "idempotent_hit_rate": 0.0,
            "lock_acquire_latency_ms_avg": 0.0,
            "stale_lock_recovered_total": 0,
        }
    
    try:
        metrics = json.loads(SPAWN_LOCK_METRICS.read_text(encoding="utf-8"))
        total = metrics.get("acquire_total", 0)
        hits = metrics.get("idempotent_hit_total", 0)
        latency_sum = metrics.get("acquire_latency_ms_sum", 0.0)
        
        return {
            "idempotent_hit_rate": round(hits / total, 4) if total > 0 else 0.0,
            "lock_acquire_latency_ms_avg": round(latency_sum / total, 2) if total > 0 else 0.0,
            "stale_lock_recovered_total": metrics.get("stale_lock_recovered_total", 0),
            "acquire_total": total,
        }
    except Exception:
        return {
            "idempotent_hit_rate": 0.0,
            "lock_acquire_latency_ms_avg": 0.0,
            "stale_lock_recovered_total": 0,
        }


def capture_baseline() -> dict:
    """捕获当前基线快照"""
    baseline = {
        "timestamp": datetime.now().isoformat(),
        "phase3": load_phase3_metrics(),
        "zombie": load_zombie_metrics(),
        "failure_classification": load_failure_classification(),
        "spawn_lock": load_spawn_lock_metrics(),
    }
    
    BASELINE_FILE.write_text(json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Baseline snapshot saved: {BASELINE_FILE}")
    return baseline


def print_baseline(baseline: dict):
    """打印基线快照"""
    print("\n" + "=" * 70)
    print("AIOS Baseline Snapshot - 可靠性关键指标")
    print("=" * 70)
    print(f"时间: {baseline['timestamp']}")
    print()
    
    print("[Phase 3] 字段完整率")
    p3 = baseline["phase3"]
    print(f"  总观测数: {p3['total']}")
    print(f"  完整字段: {p3['complete_fields']}")
    print(f"  完整率: {p3['completeness_rate']:.1%}")
    print()
    
    print("[Zombie] 僵尸任务回收")
    z = baseline["zombie"]
    print(f"  总任务数: {z['total_tasks']}")
    print(f"  已回收: {z['zombie_reclaimed']}")
    print(f"  重试中: {z['zombie_retried']}")
    print(f"  永久失败: {z['zombie_permanently_failed']}")
    print(f"  回收率: {z['reclaim_rate']:.1%}")
    print()
    
    print("[Failure] 失败分类")
    f = baseline["failure_classification"]
    print(f"  总失败数: {f['total_failures']}")
    print(f"  模拟失败: {f['simulation_failures']}")
    print(f"  真实失败: {f['real_failures']}")
    print(f"  模拟占比: {f['simulation_rate']:.1%}")
    print()
    
    print("[Spawn Lock] 幂等锁")
    sl = baseline["spawn_lock"]
    print(f"  冲突率: {sl['idempotent_hit_rate']:.1%}")
    print(f"  平均延迟: {sl['lock_acquire_latency_ms_avg']:.2f}ms")
    print(f"  过期锁恢复: {sl['stale_lock_recovered_total']}")
    print(f"  总获取次数: {sl.get('acquire_total', 0)}")
    print()
    print("=" * 70)


if __name__ == "__main__":
    baseline = capture_baseline()
    print_baseline(baseline)
