# -*- coding: utf-8 -*-
"""
ledger_summary.py - Heartbeat Ledger Summary

从 action_ledger.jsonl 计算过去 24h 的核心指标，
输出 4 行紧凑格式供 heartbeat 使用。

指标定义：
  proposed            = 24h 内新建的 action 数
  accepted            = 进入 locked 状态的 action 数
  started             = 进入 executing 状态的 action 数
  completed           = 进入 completed 状态的 action 数
  failed              = 进入 failed 状态的 action 数

  proposal_acceptance_rate    = accepted / proposed
  execution_start_rate        = started / accepted
  execution_success_rate      = completed / started
  release_without_execution   = released without executing / accepted
  stale_lock_rate             = lock_timeout releases / accepted

  queue_wait_duration_ms p95  = locked_at - proposed_at (p95)
  action_duration_ms p95      = completed/failed_at - executing_at (p95)
  lock_duration_ms p95        = released_at - locked_at (p95)
"""

import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

from paths import ACTION_LEDGER


def _load_events_24h(hours: float = 24.0) -> List[dict]:
    """读取过去 N 小时的 ledger 事件。"""
    if not ACTION_LEDGER.exists():
        return []

    cutoff_ts = time.time() - hours * 3600
    events = []

    with open(ACTION_LEDGER, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
                # 解析 ISO 时间戳
                ts_str = evt.get("timestamp", "")
                ts = _parse_iso(ts_str)
                if ts and ts >= cutoff_ts:
                    evt["_ts"] = ts
                    events.append(evt)
            except Exception:
                continue

    return events


def _parse_iso(ts_str: str) -> Optional[float]:
    """解析 ISO 8601 时间戳为 Unix 时间戳（秒）。"""
    if not ts_str:
        return None
    try:
        from datetime import datetime, timezone
        # 处理 +00:00 / Z 后缀
        ts_str = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return None


def _p95(values: List[float]) -> float:
    """计算 p95 百分位数。"""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = int(len(sorted_vals) * 0.95)
    idx = min(idx, len(sorted_vals) - 1)
    return sorted_vals[idx]


def compute_ledger_summary(hours: float = 24.0) -> dict:
    """
    计算过去 N 小时的 ledger 指标。

    Returns:
        {
            "proposed": int,
            "accepted": int,
            "started": int,
            "completed": int,
            "failed": int,
            "proposal_acceptance_rate": float,   # 0-1
            "execution_start_rate": float,
            "execution_success_rate": float,
            "release_without_execution_rate": float,
            "stale_lock_rate": float,
            "queue_wait_p95_ms": float,
            "action_duration_p95_ms": float,
            "lock_duration_p95_ms": float,
        }
    """
    events = _load_events_24h(hours)

    # 按 action_id 分组
    by_action: Dict[str, List[dict]] = defaultdict(list)
    for evt in events:
        by_action[evt["action_id"]].append(evt)

    # 统计计数
    proposed = accepted = started = completed = failed = 0
    release_wo_exec = 0   # released without executing
    stale_lock = 0        # lock_timeout releases

    # 延迟样本
    queue_wait_samples: List[float] = []    # locked_ts - proposed_ts
    action_dur_samples: List[float] = []    # completed/failed_ts - executing_ts
    lock_dur_samples: List[float] = []      # released_ts - locked_ts

    for action_id, evts in by_action.items():
        # 按时间排序
        evts_sorted = sorted(evts, key=lambda e: e.get("_ts", 0))

        # 提取各状态时间戳
        ts_map: Dict[str, float] = {}
        for evt in evts_sorted:
            etype = evt.get("event_type", "")
            ts = evt.get("_ts", 0)
            if etype not in ts_map:
                ts_map[etype] = ts

        # 计数
        if "proposed" in ts_map:
            proposed += 1
        if "locked" in ts_map:
            accepted += 1
        if "executing" in ts_map:
            started += 1
        if "completed" in ts_map:
            completed += 1
        if "failed" in ts_map:
            failed += 1

        # release_without_execution: accepted but never executing
        if "locked" in ts_map and "released" in ts_map and "executing" not in ts_map:
            release_wo_exec += 1

        # stale_lock: released with lock_timeout reason
        for evt in evts_sorted:
            if evt.get("event_type") == "released":
                payload = evt.get("payload", {})
                if payload.get("release_reason") == "lock_timeout":
                    stale_lock += 1
                    break

        # 延迟计算
        if "proposed" in ts_map and "locked" in ts_map:
            wait_ms = (ts_map["locked"] - ts_map["proposed"]) * 1000
            if wait_ms >= 0:
                queue_wait_samples.append(wait_ms)

        if "executing" in ts_map:
            end_ts = ts_map.get("completed") or ts_map.get("failed")
            if end_ts:
                dur_ms = (end_ts - ts_map["executing"]) * 1000
                if dur_ms >= 0:
                    action_dur_samples.append(dur_ms)

        if "locked" in ts_map and "released" in ts_map:
            lock_ms = (ts_map["released"] - ts_map["locked"]) * 1000
            if lock_ms >= 0:
                lock_dur_samples.append(lock_ms)

    # 计算 rates
    def safe_rate(num: int, denom: int) -> float:
        return round(num / denom, 4) if denom > 0 else 0.0

    return {
        "proposed": proposed,
        "accepted": accepted,
        "started": started,
        "completed": completed,
        "failed": failed,
        "proposal_acceptance_rate": safe_rate(accepted, proposed),
        "execution_start_rate": safe_rate(started, accepted),
        "execution_success_rate": safe_rate(completed, started),
        "release_without_execution_rate": safe_rate(release_wo_exec, accepted),
        "stale_lock_rate": safe_rate(stale_lock, accepted),
        "queue_wait_p95_ms": round(_p95(queue_wait_samples), 1),
        "action_duration_p95_ms": round(_p95(action_dur_samples), 1),
        "lock_duration_p95_ms": round(_p95(lock_dur_samples), 1),
    }


def format_heartbeat_summary(s: dict) -> str:
    """
    格式化为 4 行紧凑输出。

    示例：
      Ledger24h: proposed 32 | accepted 28 | started 26 | completed 21 | failed 5
      Rates: accept 87.5% | start 92.9% | success 80.8%
      Latency: queue p95 1.2s | exec p95 8.4s | lock p95 9.1s
      Risk: release_wo_exec 7.1% | stale_lock 0.0%
    """
    def pct(v: float) -> str:
        return f"{v * 100:.1f}%"

    def ms_to_s(ms: float) -> str:
        return f"{ms / 1000:.1f}s"

    lines = [
        (f"Ledger24h: proposed {s['proposed']} | accepted {s['accepted']} | "
         f"started {s['started']} | completed {s['completed']} | failed {s['failed']}"),
        (f"Rates: accept {pct(s['proposal_acceptance_rate'])} | "
         f"start {pct(s['execution_start_rate'])} | "
         f"success {pct(s['execution_success_rate'])}"),
        (f"Latency: queue p95 {ms_to_s(s['queue_wait_p95_ms'])} | "
         f"exec p95 {ms_to_s(s['action_duration_p95_ms'])} | "
         f"lock p95 {ms_to_s(s['lock_duration_p95_ms'])}"),
        (f"Risk: release_wo_exec {pct(s['release_without_execution_rate'])} | "
         f"stale_lock {pct(s['stale_lock_rate'])}"),
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    summary = compute_ledger_summary()
    print(format_heartbeat_summary(summary))
    print()
    print("Raw:", json.dumps(summary, indent=2))
