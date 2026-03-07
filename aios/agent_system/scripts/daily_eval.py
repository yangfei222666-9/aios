#!/usr/bin/env python3
"""
daily_eval.py - Memory Retrieval 7-Day Evaluation Panel

Reads memory_retrieval_log.jsonl + task_executions.jsonl,
computes daily metrics, outputs Markdown report.

Usage:
  python scripts/daily_eval.py              # today
  python scripts/daily_eval.py --days 7     # last 7 days
  python scripts/daily_eval.py --date 2026-03-05
"""
import json
import sys
import os
import argparse
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MEMORY_LOG = BASE_DIR / "memory_retrieval_log.jsonl"
EXEC_LOG    = BASE_DIR / "task_executions.jsonl"
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# ── Thresholds ────────────────────────────────────────────────────────────────
THRESHOLDS = {
    "latency_p95_ms":   {"pass": 100,  "warn": 300},   # ms
    "hit_rate":         {"pass": 0.80, "warn": 0.60},   # fraction
    "helpfulness":      {"pass": 0.70, "warn": 0.50},   # fraction
    "degraded_rate":    {"pass": 0.05, "warn": 0.15},   # fraction (lower=better)
    "feedback_count":   {"pass": 20,   "warn": 5},      # absolute count
}

# Phase gate: enter "active task generation"
PHASE_GATE = {
    "helpfulness_min":      0.75,
    "feedback_total_min":   100,
    "degraded_rate_max":    0.05,
    "consecutive_days":     3,
}


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").strip().split("\n"):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows


def _parse_ts(ts_str: str) -> datetime:
    """Parse ISO timestamp to UTC datetime."""
    try:
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def compute_day_metrics(date: datetime.date) -> dict:
    """Compute metrics for a single day."""
    day_start = datetime(date.year, date.month, date.day, tzinfo=timezone.utc)
    day_end   = day_start + timedelta(days=1)

    # ── Memory retrieval log ─────────────────────────────────────────────────
    mem_rows = _load_jsonl(MEMORY_LOG)
    day_mem  = [r for r in mem_rows
                if day_start <= _parse_ts(r.get("ts", "")) < day_end]

    feedback_count   = len(day_mem)
    helpful_count    = sum(1 for r in day_mem if r.get("helpful", False))
    helpfulness      = helpful_count / feedback_count if feedback_count else None

    # ── Task executions log ──────────────────────────────────────────────────
    exec_rows = _load_jsonl(EXEC_LOG)
    day_exec  = [r for r in exec_rows
                 if day_start <= datetime.fromtimestamp(
                     r.get("timestamp", 0), tz=timezone.utc) < day_end]

    total_tasks   = len(day_exec)
    success_tasks = sum(1 for r in day_exec
                        if r.get("result", {}).get("success", False))
    success_rate  = success_tasks / total_tasks if total_tasks else None

    # ── Latency from memory_retrieval_log (actual retrieval latency) ─────────
    # Fall back to exec log duration if no memory log entries
    mem_latencies = [
        r.get("latency_ms") for r in day_mem
        if isinstance(r.get("latency_ms"), (int, float))
    ]
    if not mem_latencies:
        # Proxy: use exec duration * 0.1 as rough estimate (not ideal)
        mem_latencies = [
            r["result"]["duration"] * 100  # scale down
            for r in day_exec
            if isinstance(r.get("result", {}).get("duration"), (int, float))
        ]
    latency_p50 = statistics.median(mem_latencies) if mem_latencies else None
    latency_p95 = (sorted(mem_latencies)[int(len(mem_latencies) * 0.95)]
                   if len(mem_latencies) >= 2 else
                   (mem_latencies[0] if mem_latencies else None))

    # ── Retrieved / injected counts from feedback log ────────────────────────
    retrieved_counts = [len(r.get("memory_ids", [])) for r in day_mem]
    total_retrieved  = sum(retrieved_counts)
    total_injected   = sum(1 for c in retrieved_counts if c > 0)
    hit_rate         = total_injected / feedback_count if feedback_count else None

    # ── Degraded count (from exec log — tasks with very short duration = degraded) 
    # We track degraded via memory_retrieval_log entries where helpful is None
    # For now use proxy: tasks with duration < 0.1s as "degraded" (no real work)
    degraded_count = sum(1 for r in day_exec
                         if r.get("result", {}).get("duration", 999) < 0.1)
    degraded_rate  = degraded_count / total_tasks if total_tasks else 0.0

    return {
        "date":            str(date),
        "feedback_count":  feedback_count,
        "helpful_count":   helpful_count,
        "helpfulness":     helpfulness,
        "total_tasks":     total_tasks,
        "success_tasks":   success_tasks,
        "success_rate":    success_rate,
        "latency_p50_ms":  latency_p50,
        "latency_p95_ms":  latency_p95,
        "total_retrieved": total_retrieved,
        "hit_rate":        hit_rate,
        "degraded_count":  degraded_count,
        "degraded_rate":   degraded_rate,
    }


def _judge(metric: str, value) -> str:
    """Return PASS / WARN / FAIL for a metric value."""
    if value is None:
        return "N/A"
    t = THRESHOLDS.get(metric)
    if not t:
        return "N/A"
    # lower-is-better metrics
    if metric in ("degraded_rate", "latency_p95_ms"):
        if value <= t["pass"]:  return "✅ PASS"
        if value <= t["warn"]:  return "⚠️ WARN"
        return "❌ FAIL"
    # higher-is-better
    if value >= t["pass"]:  return "✅ PASS"
    if value >= t["warn"]:  return "⚠️ WARN"
    return "❌ FAIL"


def _fmt(value, fmt=".1f", suffix="") -> str:
    if value is None:
        return "N/A"
    return f"{value:{fmt}}{suffix}"


def check_phase_gate(days_metrics: list[dict]) -> tuple[str, list[str]]:
    """Check if system is ready for active task generation phase."""
    reasons = []

    # Total feedback across all days
    total_feedback = sum(d["feedback_count"] for d in days_metrics)
    if total_feedback < PHASE_GATE["feedback_total_min"]:
        reasons.append(f"feedback_total={total_feedback} < {PHASE_GATE['feedback_total_min']}")

    # Consecutive days with helpfulness > threshold
    consecutive = 0
    for d in reversed(days_metrics):
        h = d.get("helpfulness")
        if h is not None and h >= PHASE_GATE["helpfulness_min"]:
            consecutive += 1
        else:
            break
    if consecutive < PHASE_GATE["consecutive_days"]:
        reasons.append(f"helpfulness_consecutive={consecutive} < {PHASE_GATE['consecutive_days']} days")

    # Degraded rate
    recent = days_metrics[-1] if days_metrics else {}
    dr = recent.get("degraded_rate", 1.0)
    if dr > PHASE_GATE["degraded_rate_max"]:
        reasons.append(f"degraded_rate={dr:.1%} > {PHASE_GATE['degraded_rate_max']:.1%}")

    if not reasons:
        return "🚀 GO_TASK_GENERATION", []
    return "🔒 HOLD", reasons


def generate_report(days: int = 7, target_date: datetime.date = None) -> str:
    """Generate Markdown evaluation report."""
    today = target_date or datetime.now(timezone.utc).date()
    dates = [today - timedelta(days=i) for i in range(days - 1, -1, -1)]

    all_metrics = [compute_day_metrics(d) for d in dates]
    today_m = all_metrics[-1]

    phase, phase_reasons = check_phase_gate(all_metrics)

    lines = []
    lines.append(f"# Memory Retrieval Evaluation Report")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  ")
    lines.append(f"**Period:** {dates[0]} → {dates[-1]}  ")
    lines.append(f"**Phase Decision:** {phase}")
    if phase_reasons:
        for r in phase_reasons:
            lines.append(f"  - {r}")
    lines.append("")

    # ── Today's summary ───────────────────────────────────────────────────────
    lines.append("## Today's Metrics")
    lines.append("")
    lines.append("| Metric | Value | Status |")
    lines.append("|--------|-------|--------|")

    lp95 = today_m["latency_p95_ms"]
    lines.append(f"| latency p50 | {_fmt(today_m['latency_p50_ms'], '.0f', 'ms')} | — |")
    lines.append(f"| latency p95 | {_fmt(lp95, '.0f', 'ms')} | {_judge('latency_p95_ms', lp95)} |")
    lines.append(f"| hit rate | {_fmt(today_m['hit_rate'], '.1%')} | {_judge('hit_rate', today_m['hit_rate'])} |")
    lines.append(f"| helpfulness | {_fmt(today_m['helpfulness'], '.1%')} | {_judge('helpfulness', today_m['helpfulness'])} |")
    lines.append(f"| degraded rate | {_fmt(today_m['degraded_rate'], '.1%')} | {_judge('degraded_rate', today_m['degraded_rate'])} |")
    lines.append(f"| feedback count | {today_m['feedback_count']} | {_judge('feedback_count', today_m['feedback_count'])} |")
    lines.append(f"| task success rate | {_fmt(today_m['success_rate'], '.1%')} | — |")
    lines.append(f"| total tasks | {today_m['total_tasks']} | — |")
    lines.append("")

    # ── 7-day trend table ─────────────────────────────────────────────────────
    lines.append("## 7-Day Trend")
    lines.append("")
    lines.append("| Date | Tasks | Success% | Hit Rate | Helpfulness | p95 Latency | Degraded | Feedback |")
    lines.append("|------|-------|----------|----------|-------------|-------------|----------|----------|")
    for m in all_metrics:
        lines.append(
            f"| {m['date']} "
            f"| {m['total_tasks']} "
            f"| {_fmt(m['success_rate'], '.0%')} "
            f"| {_fmt(m['hit_rate'], '.0%')} "
            f"| {_fmt(m['helpfulness'], '.0%')} "
            f"| {_fmt(m['latency_p95_ms'], '.0f', 'ms')} "
            f"| {m['degraded_count']} "
            f"| {m['feedback_count']} |"
        )
    lines.append("")

    # ── Threshold summary ─────────────────────────────────────────────────────
    lines.append("## Threshold Summary")
    lines.append("")
    lines.append("| Metric | PASS threshold | WARN threshold | Today |")
    lines.append("|--------|---------------|----------------|-------|")
    for metric, t in THRESHOLDS.items():
        val = today_m.get(metric)
        lines.append(
            f"| {metric} | {t['pass']} | {t['warn']} | {_fmt(val, '.3g')} {_judge(metric, val)} |"
        )
    lines.append("")

    # ── Phase gate detail ─────────────────────────────────────────────────────
    lines.append("## Phase Gate: Active Task Generation")
    lines.append("")
    total_fb = sum(d["feedback_count"] for d in all_metrics)
    lines.append(f"- Total feedback collected: **{total_fb}** (need {PHASE_GATE['feedback_total_min']})")
    consec = 0
    for d in reversed(all_metrics):
        h = d.get("helpfulness")
        if h is not None and h >= PHASE_GATE["helpfulness_min"]:
            consec += 1
        else:
            break
    lines.append(f"- Consecutive days helpfulness ≥ {PHASE_GATE['helpfulness_min']:.0%}: **{consec}** (need {PHASE_GATE['consecutive_days']})")
    lines.append(f"- Latest degraded rate: **{_fmt(today_m['degraded_rate'], '.1%')}** (max {PHASE_GATE['degraded_rate_max']:.0%})")
    lines.append("")
    lines.append(f"**Decision: {phase}**")
    lines.append("")

    # ── Anomaly summary ───────────────────────────────────────────────────────
    total_degraded = sum(d["degraded_count"] for d in all_metrics)
    if total_degraded > 0:
        lines.append("## Anomaly Summary")
        lines.append("")
        lines.append(f"- Total DEGRADED events (7d): **{total_degraded}**")
        worst = max(all_metrics, key=lambda d: d["degraded_count"])
        lines.append(f"- Worst day: **{worst['date']}** ({worst['degraded_count']} degraded)")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Memory Retrieval Daily Evaluation")
    parser.add_argument("--days",  type=int, default=7, help="Number of days to evaluate")
    parser.add_argument("--date",  type=str, default=None, help="Target date YYYY-MM-DD")
    parser.add_argument("--print", action="store_true", help="Print to stdout only")
    args = parser.parse_args()

    target = None
    if args.date:
        target = datetime.strptime(args.date, "%Y-%m-%d").date()

    report = generate_report(days=args.days, target_date=target)

    today_str = (target or datetime.now(timezone.utc).date()).strftime("%Y-%m-%d")
    out_path = REPORTS_DIR / f"memory_eval_{today_str}.md"

    if not args.print:
        out_path.write_text(report, encoding="utf-8")
        print(f"[OK] Report saved: {out_path}", flush=True)

    print(report)


if __name__ == "__main__":
    main()
