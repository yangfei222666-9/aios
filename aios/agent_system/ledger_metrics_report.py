"""
ledger_metrics_report.py - Reality Ledger 摘要报告生成器

面向 heartbeat / daily report 的摘要格式。
4 段式结构：概览 / 核心率 / 时延 / 异常信号。

用法：
    python ledger_metrics_report.py
    python ledger_metrics_report.py --hours 24
    python ledger_metrics_report.py --format markdown
    python ledger_metrics_report.py --format telegram
"""

import argparse
import json
from typing import Dict, Any

from ledger_metrics import compute_metrics


def format_rate(rate: float | None) -> str:
    if rate is None:
        return "N/A"
    return f"{rate * 100:.1f}%"


def format_duration(stat: Dict[str, Any]) -> str:
    if stat["count"] == 0:
        return "N/A"
    return f"avg={stat['avg']:.0f}ms p95={stat['p95']:.0f}ms"


def render_markdown(metrics: Dict[str, Any]) -> str:
    lines = []
    lines.append("# Reality Ledger Report")
    lines.append("")
    lines.append(f"**Window:** Last {metrics['window']['hours']}h")
    lines.append("")
    
    # A. 24h 概览
    lines.append("## A. 24h Overview")
    lines.append("")
    ov = metrics["overview"]
    lines.append(f"- **Proposed:** {ov['proposed']}")
    lines.append(f"- **Accepted:** {ov['accepted']} (locked)")
    lines.append(f"- **Started:** {ov['started']} (executing)")
    lines.append(f"- **Completed:** {ov['completed']}")
    lines.append(f"- **Failed:** {ov['failed']}")
    lines.append(f"- **Skipped:** {ov['skipped']}")
    lines.append(f"- **Rejected:** {ov['rejected']}")
    lines.append("")
    
    # B. 核心率
    lines.append("## B. Core Rates")
    lines.append("")
    rates = metrics["rates"]
    lines.append(f"- **Proposal Acceptance:** {format_rate(rates['proposal_acceptance_rate'])}")
    lines.append(f"- **Execution Start:** {format_rate(rates['execution_start_rate'])}")
    lines.append(f"- **Execution Success:** {format_rate(rates['execution_success_rate'])}")
    lines.append(f"- **Skip Rate:** {format_rate(rates['skip_rate'])}")
    lines.append(f"- **Reject Rate:** {format_rate(rates['reject_rate'])}")
    lines.append(f"- **Release w/o Execution:** {format_rate(rates['release_without_execution_rate'])}")
    lines.append(f"- **Stale Lock Rate:** {format_rate(rates['stale_lock_rate'])}")
    lines.append("")
    
    # C. 时延
    lines.append("## C. Durations")
    lines.append("")
    dur = metrics["durations_ms"]
    lines.append(f"- **Queue Wait:** {format_duration(dur['queue_wait_duration_ms'])}")
    lines.append(f"- **Action Duration:** {format_duration(dur['action_duration_ms'])}")
    lines.append(f"- **Lock Hold:** {format_duration(dur['lock_hold_duration_ms'])}")
    lines.append("")
    
    # D. 异常信号
    lines.append("## D. Anomaly Signals")
    lines.append("")
    cs = metrics["current_state"]
    anom = metrics["anomalies"]
    lines.append(f"- **Current Locked:** {cs['locked_count']}")
    lines.append(f"- **Stale Locked:** {cs['stale_locked_count']}")
    lines.append(f"- **Released w/o Execution:** {anom['released_without_execution_count']}")
    lines.append("")
    
    if anom["top_failed_action_type"]:
        lines.append("**Top Failed Action Types:**")
        for item in anom["top_failed_action_type"]:
            lines.append(f"  - {item['action_type']}: {item['count']}")
    else:
        lines.append("**Top Failed Action Types:** None")
    
    return "\n".join(lines)


def render_telegram(metrics: Dict[str, Any]) -> str:
    lines = []
    lines.append("📊 Reality Ledger Report")
    lines.append("")
    lines.append(f"⏱ Last {metrics['window']['hours']}h")
    lines.append("")
    
    # A. 24h 概览
    ov = metrics["overview"]
    lines.append("📋 Overview:")
    lines.append(f"  Proposed: {ov['proposed']}")
    lines.append(f"  Accepted: {ov['accepted']}")
    lines.append(f"  Started: {ov['started']}")
    lines.append(f"  ✅ Completed: {ov['completed']}")
    lines.append(f"  ❌ Failed: {ov['failed']}")
    lines.append(f"  ⏭ Skipped: {ov['skipped']}")
    lines.append(f"  🚫 Rejected: {ov['rejected']}")
    lines.append("")
    
    # B. 核心率
    rates = metrics["rates"]
    lines.append("📈 Rates:")
    lines.append(f"  Acceptance: {format_rate(rates['proposal_acceptance_rate'])}")
    lines.append(f"  Start: {format_rate(rates['execution_start_rate'])}")
    lines.append(f"  Success: {format_rate(rates['execution_success_rate'])}")
    lines.append(f"  Skip: {format_rate(rates['skip_rate'])}")
    lines.append(f"  Reject: {format_rate(rates['reject_rate'])}")
    lines.append("")
    
    # C. 时延
    dur = metrics["durations_ms"]
    lines.append("⏱ Durations:")
    lines.append(f"  Queue: {format_duration(dur['queue_wait_duration_ms'])}")
    lines.append(f"  Action: {format_duration(dur['action_duration_ms'])}")
    lines.append(f"  Lock: {format_duration(dur['lock_hold_duration_ms'])}")
    lines.append("")
    
    # D. 异常信号
    cs = metrics["current_state"]
    anom = metrics["anomalies"]
    lines.append("⚠️ Anomalies:")
    lines.append(f"  Locked: {cs['locked_count']}")
    lines.append(f"  Stale: {cs['stale_locked_count']}")
    lines.append(f"  Released w/o exec: {anom['released_without_execution_count']}")
    
    if anom["top_failed_action_type"]:
        lines.append("")
        lines.append("Top Failed:")
        for item in anom["top_failed_action_type"][:2]:
            lines.append(f"  • {item['action_type']}: {item['count']}")
    
    return "\n".join(lines)


def render_compact(metrics: Dict[str, Any]) -> str:
    """紧凑格式，适合 heartbeat 单行输出"""
    ov = metrics["overview"]
    rates = metrics["rates"]
    cs = metrics["current_state"]
    
    parts = [
        f"proposed={ov['proposed']}",
        f"accepted={ov['accepted']}",
        f"completed={ov['completed']}",
        f"failed={ov['failed']}",
        f"success={format_rate(rates['execution_success_rate'])}",
        f"locked={cs['locked_count']}",
        f"stale={cs['stale_locked_count']}",
    ]
    return " | ".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--format", choices=["markdown", "telegram", "compact", "json"], default="markdown")
    args = parser.parse_args()
    
    metrics = compute_metrics(hours=args.hours)
    
    if args.format == "json":
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
    elif args.format == "markdown":
        print(render_markdown(metrics))
    elif args.format == "telegram":
        print(render_telegram(metrics))
    elif args.format == "compact":
        print(render_compact(metrics))


if __name__ == "__main__":
    main()
