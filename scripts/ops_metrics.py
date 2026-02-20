# scripts/ops_metrics.py - 14天运营期指标收集器
"""
每日收集四个验收指标：
1. MTTR (Mean Time To Recovery): 故障平均恢复时长
2. Noise Rate: 告警噪音率（可行动告警占比）
3. Retry Yield: 重试挽回率（重试成功占比）
4. Rollback Safety: 回滚成功率

数据源：
- alerts_history.jsonl (MTTR + Noise Rate)
- job_queue 数据 (Retry Yield)
- safe_run changes_log.jsonl (Rollback Safety)

输出：memory/ops_metrics.jsonl (每日追加一条)
"""
import json, time, sys, os
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

WS = Path(__file__).parent.parent
ALERTS_HISTORY = WS / "memory" / "alerts_history.jsonl"
ALERTS_LOG = WS / "memory" / "alerts_log.jsonl"
JOB_QUEUE_DIR = WS / "scripts" / ".job_queue"
CHANGES_LOG = WS / "scripts" / "changes_log.jsonl"
METRICS_FILE = WS / "memory" / "ops_metrics.jsonl"


def _load_jsonl(path: Path, days: int = 1) -> list:
    if not path.exists():
        return []
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            ts = obj.get("ts", obj.get("timestamp", ""))
            if ts >= cutoff:
                out.append(obj)
        except Exception:
            continue
    return out


# ========== 指标1: MTTR ==========

def calc_mttr(days: int = 1) -> dict:
    """
    MTTR = 从 OPEN 到 RESOLVED 的平均时长（秒）
    
    数据源：alerts_history.jsonl
    格式：{"ts", "alert_id", "old_state", "new_state", ...}
    """
    history = _load_jsonl(ALERTS_HISTORY, days)
    
    # 找所有 OPEN → RESOLVED 的配对
    open_times = {}  # alert_id → open_ts
    resolved_times = []  # [(alert_id, duration_seconds)]
    
    for h in history:
        aid = h.get("alert_id", "")
        old = h.get("old_state", "")
        new = h.get("new_state", "")
        ts_str = h.get("ts", "")
        
        if not aid or not ts_str:
            continue
        
        ts = datetime.fromisoformat(ts_str).timestamp()
        
        if new == "OPEN":
            open_times[aid] = ts
        elif new == "RESOLVED" and aid in open_times:
            duration = ts - open_times[aid]
            resolved_times.append((aid, duration))
            del open_times[aid]
    
    if not resolved_times:
        return {"mttr_seconds": None, "resolved_count": 0, "open_count": len(open_times)}
    
    avg_mttr = sum(d for _, d in resolved_times) / len(resolved_times)
    
    return {
        "mttr_seconds": round(avg_mttr, 1),
        "mttr_minutes": round(avg_mttr / 60, 1),
        "resolved_count": len(resolved_times),
        "open_count": len(open_times),
    }


# ========== 指标2: Noise Rate ==========

def calc_noise_rate(days: int = 1) -> dict:
    """
    Noise Rate = 可行动告警 / 总告警
    
    可行动定义：CRIT 或 WARN 级别，且不是重复/误报
    数据源：alerts_log.jsonl
    """
    logs = _load_jsonl(ALERTS_LOG, days)
    
    by_level = defaultdict(int)
    for log in logs:
        level = log.get("level", "INFO")
        by_level[level] += 1
    
    total_alerts = by_level["CRIT"] + by_level["WARN"]
    if total_alerts == 0:
        return {"noise_rate": None, "actionable": 0, "total": 0}
    
    # 简化：假设所有 CRIT/WARN 都是可行动的（后续可加误报检测）
    actionable = total_alerts
    noise_rate = actionable / total_alerts
    
    return {
        "noise_rate": round(noise_rate, 4),
        "actionable": actionable,
        "total": total_alerts,
        "crit": by_level["CRIT"],
        "warn": by_level["WARN"],
        "info": by_level["INFO"],
    }


# ========== 指标3: Retry Yield ==========

def calc_retry_yield(days: int = 1) -> dict:
    """
    Retry Yield = 重试后成功 / 总重试次数
    
    数据源：job_queue 的 jobs.jsonl
    """
    jobs_file = JOB_QUEUE_DIR / "jobs.jsonl"
    if not jobs_file.exists():
        return {"retry_yield": None, "retry_success": 0, "total_retries": 0}
    
    jobs = _load_jsonl(jobs_file, days)
    
    retry_success = 0
    total_retries = 0
    
    for job in jobs:
        status = job.get("status", "")
        retries = job.get("retries", 0)
        
        if retries > 0:
            total_retries += retries
            if status == "SUCCESS":
                retry_success += retries
    
    if total_retries == 0:
        return {"retry_yield": None, "retry_success": 0, "total_retries": 0}
    
    yield_rate = retry_success / total_retries
    
    return {
        "retry_yield": round(yield_rate, 4),
        "retry_success": retry_success,
        "total_retries": total_retries,
    }


# ========== 指标4: Rollback Safety ==========

def calc_rollback_safety(days: int = 1) -> dict:
    """
    Rollback Safety = 回滚成功 / 总回滚次数
    
    数据源：changes_log.jsonl
    """
    if not CHANGES_LOG.exists():
        return {"rollback_safety": None, "rollback_success": 0, "total_rollbacks": 0}
    
    changes = _load_jsonl(CHANGES_LOG, days)
    
    rollback_success = 0
    total_rollbacks = 0
    
    for c in changes:
        action = c.get("action", "")
        if action == "rollback":
            total_rollbacks += 1
            if c.get("success", False):
                rollback_success += 1
    
    if total_rollbacks == 0:
        return {"rollback_safety": 1.0, "rollback_success": 0, "total_rollbacks": 0}
    
    safety_rate = rollback_success / total_rollbacks
    
    return {
        "rollback_safety": round(safety_rate, 4),
        "rollback_success": rollback_success,
        "total_rollbacks": total_rollbacks,
    }


# ========== 汇总 ==========

def collect_daily_metrics(days: int = 1) -> dict:
    """收集今日指标"""
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "ts": datetime.now().isoformat(),
        "period_days": days,
        "mttr": calc_mttr(days),
        "noise_rate": calc_noise_rate(days),
        "retry_yield": calc_retry_yield(days),
        "rollback_safety": calc_rollback_safety(days),
    }


def append_metrics(metrics: dict):
    """追加到 metrics 文件"""
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with METRICS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(metrics, ensure_ascii=False) + "\n")


def load_metrics_history(limit: int = 14) -> list:
    """加载最近N天的指标"""
    if not METRICS_FILE.exists():
        return []
    lines = METRICS_FILE.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines[-limit:]:
        if line.strip():
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out


def generate_trend_report(limit: int = 7) -> str:
    """生成趋势报告"""
    history = load_metrics_history(limit)
    if len(history) < 2:
        return "数据不足（需要至少2天数据）"
    
    lines = [f"📊 运营期趋势报告 ({len(history)} 天数据)"]
    lines.append(f"期间：{history[0]['date']} ~ {history[-1]['date']}")
    lines.append("")
    
    # MTTR 趋势
    mttr_vals = [m["mttr"]["mttr_minutes"] for m in history if m["mttr"]["mttr_minutes"] is not None]
    if mttr_vals:
        lines.append(f"MTTR: {mttr_vals[0]:.1f}min → {mttr_vals[-1]:.1f}min")
    
    # Noise Rate 趋势
    noise_vals = [m["noise_rate"]["noise_rate"] for m in history if m["noise_rate"]["noise_rate"] is not None]
    if noise_vals:
        lines.append(f"Noise Rate: {noise_vals[0]:.1%} → {noise_vals[-1]:.1%}")
    
    # Retry Yield 趋势
    retry_vals = [m["retry_yield"]["retry_yield"] for m in history if m["retry_yield"]["retry_yield"] is not None]
    if retry_vals:
        lines.append(f"Retry Yield: {retry_vals[0]:.1%} → {retry_vals[-1]:.1%}")
    
    # Rollback Safety 趋势
    rollback_vals = [m["rollback_safety"]["rollback_safety"] for m in history if m["rollback_safety"]["rollback_safety"] is not None]
    if rollback_vals:
        lines.append(f"Rollback Safety: {rollback_vals[0]:.1%} → {rollback_vals[-1]:.1%}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "collect"
    
    if action == "collect":
        metrics = collect_daily_metrics()
        append_metrics(metrics)
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
    elif action == "trend":
        print(generate_trend_report())
    elif action == "history":
        for m in load_metrics_history():
            print(json.dumps(m, ensure_ascii=False))
    else:
        print("Usage: ops_metrics.py [collect|trend|history]")
