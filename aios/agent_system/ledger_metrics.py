"""
ledger_metrics.py - Reality Ledger 离线指标统计 v0.2

v0.2 变更：
- 所有率指标改成 action-based（按唯一 action_id 算，不按事件数）
- 新增 7 个率指标（acceptance/start/success/skip/reject/release_without_execution/stale_lock）
- 两层架构：聚合器 + 指标计算

用法：
    python ledger_metrics.py
    python ledger_metrics.py --hours 24
    python ledger_metrics.py --json
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

from paths import ACTION_LEDGER, ACTIONS_STATE


def parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def load_jsonl(path) -> List[Dict[str, Any]]:
    items = []
    if not path.exists():
        return items
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                continue
    return items


def percentile(values: List[float], p: float) -> Optional[float]:
    if not values:
        return None
    if len(values) == 1:
        return float(values[0])
    values = sorted(values)
    k = (len(values) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(values[int(k)])
    d0 = values[f] * (c - k)
    d1 = values[c] * (k - f)
    return float(d0 + d1)


def summarize_series(values: List[float]) -> Dict[str, Optional[float]]:
    if not values:
        return {"count": 0, "avg": None, "p50": None, "p95": None, "max": None}
    return {
        "count": len(values),
        "avg": round(sum(values) / len(values), 2),
        "p50": round(percentile(values, 0.50), 2),
        "p95": round(percentile(values, 0.95), 2),
        "max": round(max(values), 2),
    }


def ms_between(a: Optional[datetime], b: Optional[datetime]) -> Optional[float]:
    if not a or not b:
        return None
    delta = (b - a).total_seconds() * 1000
    return round(delta, 2) if delta >= 0 else None


# ══════════════════════════════════════════════════════════════
# 第一层：聚合器（按 action_id 聚合事件）
# ══════════════════════════════════════════════════════════════

def aggregate_actions(
    events: List[Dict[str, Any]],
    actions: List[Dict[str, Any]],
    since: datetime,
) -> Dict[str, Dict[str, Any]]:
    """
    按 action_id 聚合事件，返回 action-level 中间结构。
    
    返回格式：
    {
        action_id: {
            "first_proposed_at": datetime | None,
            "first_locked_at": datetime | None,
            "first_executing_at": datetime | None,
            "first_completed_at": datetime | None,
            "first_failed_at": datetime | None,
            "first_released_at": datetime | None,
            "first_skipped_at": datetime | None,
            "first_rejected_at": datetime | None,
            "final_status": str,
            "final_outcome": str,
            "action_type": str,
            "resource_type": str,
            "ever_locked": bool,
            "ever_executing": bool,
            "ever_completed": bool,
            "ever_failed": bool,
        }
    }
    """
    # 构建 action 索引
    action_index = {a.get("action_id"): a for a in actions if a.get("action_id")}
    
    # 按 action_id 聚合事件
    agg: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "first_proposed_at": None,
        "first_locked_at": None,
        "first_executing_at": None,
        "first_completed_at": None,
        "first_failed_at": None,
        "first_released_at": None,
        "first_skipped_at": None,
        "first_rejected_at": None,
        "final_status": "unknown",
        "final_outcome": "unknown",
        "action_type": "unknown",
        "resource_type": "unknown",
        "ever_locked": False,
        "ever_executing": False,
        "ever_completed": False,
        "ever_failed": False,
    })
    
    # 遍历事件，记录第一次出现的时间
    for evt in sorted(events, key=lambda e: e.get("timestamp", "")):
        action_id = evt.get("action_id")
        if not action_id:
            continue
        
        ts = parse_iso(evt.get("timestamp"))
        if not ts or ts < since:
            continue
        
        status = evt.get("status_after") or evt.get("event_type")
        if not status:
            continue
        
        rec = agg[action_id]
        
        # 记录第一次出现的时间
        if status == "proposed" and not rec["first_proposed_at"]:
            rec["first_proposed_at"] = ts
        elif status == "locked" and not rec["first_locked_at"]:
            rec["first_locked_at"] = ts
            rec["ever_locked"] = True
        elif status == "executing" and not rec["first_executing_at"]:
            rec["first_executing_at"] = ts
            rec["ever_executing"] = True
        elif status == "completed" and not rec["first_completed_at"]:
            rec["first_completed_at"] = ts
            rec["ever_completed"] = True
        elif status == "failed" and not rec["first_failed_at"]:
            rec["first_failed_at"] = ts
            rec["ever_failed"] = True
        elif status == "released" and not rec["first_released_at"]:
            rec["first_released_at"] = ts
        elif status == "skipped" and not rec["first_skipped_at"]:
            rec["first_skipped_at"] = ts
        elif status == "rejected" and not rec["first_rejected_at"]:
            rec["first_rejected_at"] = ts
    
    # 补充 final_status / final_outcome / action_type / resource_type
    for action_id, rec in agg.items():
        action = action_index.get(action_id, {})
        rec["final_status"] = action.get("status", "unknown")
        rec["final_outcome"] = action.get("outcome", "unknown")
        rec["action_type"] = action.get("action_type", "unknown")
        rec["resource_type"] = action.get("resource_type", "unknown")
    
    return dict(agg)


# ══════════════════════════════════════════════════════════════
# 第二层：指标计算（在 action-level 上算率和时延）
# ══════════════════════════════════════════════════════════════

def compute_metrics(hours: int = 24) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=hours)
    
    events = load_jsonl(ACTION_LEDGER)
    actions = load_jsonl(ACTIONS_STATE)
    
    # 第一层：聚合
    agg = aggregate_actions(events, actions, since)
    
    # 过滤窗口内的 action（至少有一个事件在窗口内）
    window_actions = {
        aid: rec for aid, rec in agg.items()
        if rec["first_proposed_at"] and rec["first_proposed_at"] >= since
    }
    
    # ── 1. 24h 概览（action 计数）──
    proposed_actions = set()
    accepted_actions = set()  # 进入过 locked
    started_actions = set()   # 进入过 executing
    completed_actions = set()
    failed_actions = set()
    skipped_actions = set()
    rejected_actions = set()
    released_without_execution = set()  # locked 但从未 executing
    
    for aid, rec in window_actions.items():
        if rec["first_proposed_at"]:
            proposed_actions.add(aid)
        if rec["ever_locked"]:
            accepted_actions.add(aid)
        if rec["ever_executing"]:
            started_actions.add(aid)
        if rec["final_outcome"] == "completed":
            completed_actions.add(aid)
        if rec["final_outcome"] == "failed":
            failed_actions.add(aid)
        if rec["final_outcome"] == "skipped":
            skipped_actions.add(aid)
        if rec["final_outcome"] == "rejected":
            rejected_actions.add(aid)
        
        # released_without_execution: locked 但从未 executing
        if rec["ever_locked"] and not rec["ever_executing"] and rec["final_status"] == "released":
            released_without_execution.add(aid)
    
    # ── 2. 核心率（action-based）──
    n_proposed = len(proposed_actions)
    n_accepted = len(accepted_actions)
    n_started = len(started_actions)
    n_completed = len(completed_actions)
    n_failed = len(failed_actions)
    n_skipped = len(skipped_actions)
    n_rejected = len(rejected_actions)
    n_released_without_execution = len(released_without_execution)
    
    proposal_acceptance_rate = round(n_accepted / n_proposed, 4) if n_proposed else None
    execution_start_rate = round(n_started / n_accepted, 4) if n_accepted else None
    execution_success_rate = round(n_completed / (n_completed + n_failed), 4) if (n_completed + n_failed) else None
    skip_rate = round(n_skipped / n_proposed, 4) if n_proposed else None
    reject_rate = round(n_rejected / n_proposed, 4) if n_proposed else None
    release_without_execution_rate = round(n_released_without_execution / n_accepted, 4) if n_accepted else None
    
    # ── 3. 时延（action-level）──
    queue_wait_ms = []      # proposed -> locked
    action_duration_ms = [] # proposed -> completed/failed
    lock_hold_ms = []       # locked -> released
    
    for aid, rec in window_actions.items():
        v = ms_between(rec["first_proposed_at"], rec["first_locked_at"])
        if v is not None:
            queue_wait_ms.append(v)
        
        done_at = rec["first_completed_at"] or rec["first_failed_at"]
        v = ms_between(rec["first_proposed_at"], done_at)
        if v is not None:
            action_duration_ms.append(v)
        
        v = ms_between(rec["first_locked_at"], rec["first_released_at"])
        if v is not None:
            lock_hold_ms.append(v)
    
    # ── 4. 当前状态（从 actions_state.jsonl）──
    current_status_counts = Counter()
    current_locked_actions = set()
    stale_locked_actions = set()  # locked 超过 5 分钟
    
    for action in actions:
        status = action.get("status", "unknown")
        current_status_counts[status] += 1
        
        if status == "locked":
            aid = action.get("action_id")
            current_locked_actions.add(aid)
            
            # 判断是否 stale（locked 超过 5 分钟）
            updated_at = parse_iso(action.get("updated_at"))
            if updated_at and (now - updated_at).total_seconds() > 300:
                stale_locked_actions.add(aid)
    
    stale_lock_rate = round(len(stale_locked_actions) / len(current_locked_actions), 4) if current_locked_actions else None
    
    # ── 5. 异常信号 ──
    failed_by_action_type = Counter()
    for aid, rec in window_actions.items():
        if rec["final_outcome"] == "failed":
            failed_by_action_type[rec["action_type"]] += 1
    
    top_failed_action_type = failed_by_action_type.most_common(3)
    
    # ── 6. 按维度聚合 ──
    by_action_type = defaultdict(lambda: {
        "proposed": 0, "accepted": 0, "started": 0,
        "completed": 0, "failed": 0, "skipped": 0, "rejected": 0,
    })
    by_resource_type = defaultdict(lambda: {
        "proposed": 0, "accepted": 0, "started": 0,
        "completed": 0, "failed": 0, "skipped": 0, "rejected": 0,
    })
    
    for aid, rec in window_actions.items():
        at = rec["action_type"]
        rt = rec["resource_type"]
        
        if rec["first_proposed_at"]:
            by_action_type[at]["proposed"] += 1
            by_resource_type[rt]["proposed"] += 1
        if rec["ever_locked"]:
            by_action_type[at]["accepted"] += 1
            by_resource_type[rt]["accepted"] += 1
        if rec["ever_executing"]:
            by_action_type[at]["started"] += 1
            by_resource_type[rt]["started"] += 1
        if rec["final_outcome"] == "completed":
            by_action_type[at]["completed"] += 1
            by_resource_type[rt]["completed"] += 1
        if rec["final_outcome"] == "failed":
            by_action_type[at]["failed"] += 1
            by_resource_type[rt]["failed"] += 1
        if rec["final_outcome"] == "skipped":
            by_action_type[at]["skipped"] += 1
            by_resource_type[rt]["skipped"] += 1
        if rec["final_outcome"] == "rejected":
            by_action_type[at]["rejected"] += 1
            by_resource_type[rt]["rejected"] += 1
    
    # ── 返回完整指标 ──
    return {
        "window": {
            "hours": hours,
            "since": since.isoformat(timespec="seconds"),
            "until": now.isoformat(timespec="seconds"),
        },
        "overview": {
            "proposed": n_proposed,
            "accepted": n_accepted,
            "started": n_started,
            "completed": n_completed,
            "failed": n_failed,
            "skipped": n_skipped,
            "rejected": n_rejected,
        },
        "rates": {
            "proposal_acceptance_rate": proposal_acceptance_rate,
            "execution_start_rate": execution_start_rate,
            "execution_success_rate": execution_success_rate,
            "skip_rate": skip_rate,
            "reject_rate": reject_rate,
            "release_without_execution_rate": release_without_execution_rate,
            "stale_lock_rate": stale_lock_rate,
        },
        "durations_ms": {
            "queue_wait_duration_ms": summarize_series(queue_wait_ms),
            "action_duration_ms": summarize_series(action_duration_ms),
            "lock_hold_duration_ms": summarize_series(lock_hold_ms),
        },
        "current_state": {
            "status_distribution": dict(current_status_counts),
            "locked_count": len(current_locked_actions),
            "stale_locked_count": len(stale_locked_actions),
        },
        "anomalies": {
            "top_failed_action_type": [{"action_type": k, "count": v} for k, v in top_failed_action_type],
            "released_without_execution_count": n_released_without_execution,
        },
        "by_action_type": {k: dict(v) for k, v in by_action_type.items()},
        "by_resource_type": {k: dict(v) for k, v in by_resource_type.items()},
        "data_volume": {
            "events_total": len(events),
            "actions_total": len(actions),
            "window_actions": len(window_actions),
        },
    }


def render_report(metrics: Dict[str, Any]) -> str:
    lines = []
    lines.append("Reality Ledger Metrics Report v0.2")
    lines.append("=" * 60)
    lines.append(f"Window: last {metrics['window']['hours']}h")
    lines.append(f"Since : {metrics['window']['since']}")
    lines.append(f"Until : {metrics['window']['until']}")
    lines.append("")
    
    lines.append("[A] 24h Overview (action-based)")
    for k, v in metrics["overview"].items():
        lines.append(f"  - {k}: {v}")
    lines.append("")
    
    lines.append("[B] Core Rates (action-based)")
    for k, v in metrics["rates"].items():
        lines.append(f"  - {k}: {v}")
    lines.append("")
    
    lines.append("[C] Durations (ms)")
    for name, stat in metrics["durations_ms"].items():
        lines.append(
            f"  - {name}: count={stat['count']} avg={stat['avg']} p50={stat['p50']} p95={stat['p95']} max={stat['max']}"
        )
    lines.append("")
    
    lines.append("[D] Anomaly Signals")
    lines.append(f"  - Current locked: {metrics['current_state']['locked_count']}")
    lines.append(f"  - Stale locked: {metrics['current_state']['stale_locked_count']}")
    lines.append(f"  - Released without execution: {metrics['anomalies']['released_without_execution_count']}")
    lines.append("  - Top failed action_type:")
    for item in metrics["anomalies"]["top_failed_action_type"]:
        lines.append(f"      {item['action_type']}: {item['count']}")
    lines.append("")
    
    lines.append("[E] Current Status Distribution")
    for k, v in metrics["current_state"]["status_distribution"].items():
        lines.append(f"  - {k}: {v}")
    lines.append("")
    
    lines.append("[F] Data Volume")
    for k, v in metrics["data_volume"].items():
        lines.append(f"  - {k}: {v}")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    
    metrics = compute_metrics(hours=args.hours)
    if args.json:
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
    else:
        print(render_report(metrics))


if __name__ == "__main__":
    main()
