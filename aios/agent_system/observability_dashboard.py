#!/usr/bin/env python3
"""
AIOS Observability Dashboard - 7-Day Trend

读取 reports/daily_metrics_*.json，生成 7 天趋势表格。
输出: reports/observability_7day.md

只做 4 个趋势: success_rate / debate_rate / fast_ratio / failure_count
"""

import json
import os
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
TZ = timezone(timedelta(hours=8))


def load_metrics(date_str):
    path = os.path.join(REPORTS_DIR, f"daily_metrics_{date_str}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run():
    today = datetime.now(TZ)
    dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]

    rows = []
    for d in dates:
        m = load_metrics(d)
        if m:
            rows.append({
                "date": d,
                "success_rate": m.get("task_metrics", {}).get("success_rate", "-"),
                "debate_rate": m.get("debate_metrics", {}).get("debate_rate", "-"),
                "fast_ratio": m.get("router_metrics", {}).get("fast_ratio", "-"),
                "failure_count": m.get("failure_taxonomy", {}).get("failure_total", "-"),
                "avg_latency": m.get("task_metrics", {}).get("avg_task_latency_s", "-"),
                "tasks_total": m.get("task_metrics", {}).get("tasks_total", "-"),
            })
        else:
            rows.append({
                "date": d,
                "success_rate": "-",
                "debate_rate": "-",
                "fast_ratio": "-",
                "failure_count": "-",
                "avg_latency": "-",
                "tasks_total": "-",
            })

    # Generate markdown
    lines = [
        "# AIOS 7-Day Observability Dashboard",
        f"Generated: {today.isoformat()}",
        "",
        "## Trend Table",
        "",
        "| Date | Tasks | Success% | Debate% | Fast% | Failures | Latency(s) |",
        "|------|-------|----------|---------|-------|----------|------------|",
    ]

    for r in rows:
        sr = f"{r['success_rate']}%" if r['success_rate'] != "-" else "-"
        dr = f"{r['debate_rate']}%" if r['debate_rate'] != "-" else "-"
        fr = f"{r['fast_ratio']}%" if r['fast_ratio'] != "-" else "-"
        lines.append(
            f"| {r['date']} | {r['tasks_total']} | {sr} | {dr} | {fr} | {r['failure_count']} | {r['avg_latency']} |"
        )

    # Summary
    valid = [r for r in rows if r["success_rate"] != "-"]
    if valid:
        avg_sr = sum(r["success_rate"] for r in valid) / len(valid)
        total_failures = sum(r["failure_count"] for r in valid if isinstance(r["failure_count"], (int, float)))
        total_tasks = sum(r["tasks_total"] for r in valid if isinstance(r["tasks_total"], (int, float)))
        lines.extend([
            "",
            "## 7-Day Summary",
            f"  Total tasks: {total_tasks}",
            f"  Avg success rate: {avg_sr:.1f}%",
            f"  Total failures: {total_failures}",
            f"  Days with data: {len(valid)}/7",
        ])

    # Failure pattern (aggregate)
    all_failures = {}
    for d in dates:
        m = load_metrics(d)
        if m:
            for ftype, count in m.get("failure_taxonomy", {}).get("failure_counts", {}).items():
                all_failures[ftype] = all_failures.get(ftype, 0) + count

    if all_failures:
        lines.extend([
            "",
            "## Failure Pattern (7-Day)",
        ])
        total_f = sum(all_failures.values())
        for ftype, count in sorted(all_failures.items(), key=lambda x: -x[1]):
            pct = round(count / total_f * 100, 1) if total_f > 0 else 0
            lines.append(f"  {ftype}: {count} ({pct}%)")

    # Memory Gate evaluation
    try:
        from memory_gate import collect_metrics, evaluate_gate, format_gate_telegram
        gate_metrics = collect_metrics(today.strftime("%Y-%m-%d"))
        gate_result = evaluate_gate(gate_metrics)
        lines.extend([
            "",
            "## Memory Retrieval Gate",
            f"  Decision: {gate_result['decision']}",
            f"  FAIL: {gate_result['summary']['fail_count']} | WARN: {gate_result['summary']['warn_count']} | INFO: {gate_result['summary']['info_count']}",
            f"  Feedback: {gate_result['summary']['total_feedback']}/100 | Green days: {gate_result['summary']['green_days']}/3",
            "",
            "  Gate Reasons:",
        ])
        for reason in gate_result["reasons"][:5]:
            lines.append(f"    {reason}")
    except Exception as e:
        lines.extend(["", f"## Memory Retrieval Gate", f"  [ERROR] {e}"])

    lines.append("")

    # Write
    os.makedirs(REPORTS_DIR, exist_ok=True)
    path = os.path.join(REPORTS_DIR, "observability_7day.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # Also save as JSON for future use
    json_path = os.path.join(REPORTS_DIR, "observability_7day.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": today.isoformat(),
            "days": rows,
            "failure_pattern": all_failures,
        }, f, ensure_ascii=False, indent=2)

    print(f"7-Day Dashboard generated:")
    print(f"  MD:   {path}")
    print(f"  JSON: {json_path}")
    print()

    # Print table to stdout
    for r in rows:
        sr = f"{r['success_rate']}%" if r['success_rate'] != "-" else "-"
        print(f"  {r['date']}  tasks:{r['tasks_total']}  success:{sr}  failures:{r['failure_count']}")


if __name__ == "__main__":
    run()
