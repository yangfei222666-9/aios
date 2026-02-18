# aios/learning/analyze.py - 自动分析器
"""
从 events.jsonl 分析，产出三类输出：
  A. 质量指标 (Metrics)
  B. Top 问题 (Top Issues)
  C. 建议 (Suggestions)
"""
import json, time, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.engine import load_events, count_by_type
from core.config import get_int, get_float

AIOS_ROOT = Path(__file__).resolve().parent.parent
LEARNING_DIR = AIOS_ROOT / "learning"
LEARNING_DIR.mkdir(exist_ok=True)

CORRECTION_THRESHOLD = get_int("analysis.correction_threshold", 3)
LOW_SCORE_THRESHOLD = get_float("analysis.low_score_threshold", 0.80)


def compute_metrics(days: int = 1) -> dict:
    events = load_events(days)
    matches = [e for e in events if e.get("type") == "match"]
    corrections = [e for e in events if e.get("type") == "correction"]
    tools = [e for e in events if e.get("type") in ("tool", "task")]
    http_errors = [e for e in events if e.get("type") == "http_error"]

    total_match = len(matches) + len(corrections)
    correction_rate = len(corrections) / total_match if total_match > 0 else 0

    low_score = [m for m in matches if (m.get("data") or {}).get("score", 1.0) < LOW_SCORE_THRESHOLD]
    low_score_ratio = len(low_score) / len(matches) if matches else 0

    tool_ok = [t for t in tools if (t.get("data") or {}).get("ok", True)]
    tool_success_rate = len(tool_ok) / len(tools) if tools else 1.0

    http_status_counts = Counter((e.get("data") or {}).get("status_code", "?") for e in http_errors)

    return {
        "period_days": days,
        "match_correction_rate": round(correction_rate, 3),
        "low_score_ratio": round(low_score_ratio, 3),
        "tool_success_rate": round(tool_success_rate, 3),
        "tool_total": len(tools),
        "http_error_count": len(http_errors),
        "http_status_breakdown": dict(http_status_counts),
        "total_events": len(events),
    }


def compute_top_issues(days: int = 7) -> dict:
    events = load_events(days)
    corrections = [e for e in events if e.get("type") == "correction"]
    errors = [e for e in events if e.get("type") in ("error", "http_error")]
    tools = [e for e in events if e.get("type") in ("tool", "task") and not (e.get("data") or {}).get("ok", True)]

    correction_inputs = Counter((e.get("data") or {}).get("input", e.get("summary", "?")) for e in corrections)
    failed_tools = Counter((e.get("data") or {}).get("tool", e.get("source", "?")) for e in tools)
    error_types = Counter(
        f"{e.get('type')}:{(e.get('data') or {}).get('status_code', '')}" if e.get("type") == "http_error"
        else e.get("source", "?")
        for e in errors
    )

    return {
        "top_corrected_inputs": dict(correction_inputs.most_common(10)),
        "top_failed_tools": dict(failed_tools.most_common(5)),
        "top_error_types": dict(error_types.most_common(5)),
    }


def compute_suggestions(days: int = 7) -> dict:
    events = load_events(days)
    corrections = [e for e in events if e.get("type") == "correction"]
    matches = [e for e in events if e.get("type") == "match"]
    http_errors = [e for e in events if e.get("type") == "http_error"]

    alias_suggestions = []
    threshold_warnings = []
    route_suggestions = []

    # alias
    correction_targets = defaultdict(list)
    for c in corrections:
        data = c.get("data", {})
        inp = data.get("input", "")
        target = data.get("correct_target", "")
        if inp and target:
            correction_targets[inp].append(target)

    for inp, targets in correction_targets.items():
        tc = Counter(targets)
        top, count = tc.most_common(1)[0]
        if count >= CORRECTION_THRESHOLD:
            alias_suggestions.append({
                "input": inp,
                "suggested": top,
                "reason": f"corrected_{count}_times",
                "confidence": round(count / len(targets), 2),
            })

    # threshold
    total_match = len(matches) + len(corrections)
    if total_match > 0:
        cr = len(corrections) / total_match
        if cr > 0.15:
            threshold_warnings.append({
                "field": "correction_rate",
                "current": round(cr, 2),
                "suggested": 0.10,
                "reason": "high_correction_rate",
            })
        low = [m for m in matches if (m.get("data") or {}).get("score", 1.0) < LOW_SCORE_THRESHOLD]
        lsr = len(low) / len(matches) if matches else 0
        if lsr > 0.15:
            threshold_warnings.append({
                "field": "low_score_rate",
                "current": round(lsr, 2),
                "suggested": 0.10,
                "reason": "too_many_low_score_matches",
            })

    # route
    status_counts = Counter((e.get("data") or {}).get("status_code", 0) for e in http_errors)
    for code, cnt in status_counts.items():
        if cnt >= 3:
            route_suggestions.append({
                "status_code": code,
                "count": cnt,
                "reason": f"http_{code}_x{cnt}",
                "action": "consider_fallback",
            })

    return {
        "generated_at": time.strftime("%Y-%m-%d"),
        "alias_suggestions": alias_suggestions,
        "threshold_warnings": threshold_warnings,
        "route_suggestions": route_suggestions,
    }


def generate_suggestions(days: int = 7) -> dict:
    sug = compute_suggestions(days)
    out = LEARNING_DIR / "suggestions.json"
    out.write_text(json.dumps(sug, ensure_ascii=False, indent=2), encoding="utf-8")
    return sug


def generate_daily_report(days: int = 1) -> str:
    metrics = compute_metrics(days)
    issues = compute_top_issues(days)
    suggestions = compute_suggestions(days)

    lines = [
        f"# AIOS Daily Report",
        f"Date: {time.strftime('%Y-%m-%d')}",
        f"Period: last {days} day(s)\n",
        "## A. Metrics",
        f"- match correction_rate: {metrics['match_correction_rate']:.1%}",
        f"- low_score_ratio: {metrics['low_score_ratio']:.1%}",
        f"- tool success_rate: {metrics['tool_success_rate']:.1%} ({metrics['tool_total']} total)",
        f"- http_errors: {metrics['http_error_count']}",
    ]
    for code, cnt in metrics["http_status_breakdown"].items():
        lines.append(f"  - {code}: x{cnt}")

    lines.append(f"\n## B. Top Issues")
    if issues["top_corrected_inputs"]:
        for inp, cnt in issues["top_corrected_inputs"].items():
            lines.append(f"- corrected: \"{inp}\" x{cnt}")
    if issues["top_failed_tools"]:
        for tool, cnt in issues["top_failed_tools"].items():
            lines.append(f"- failed_tool: {tool} x{cnt}")
    if issues["top_error_types"]:
        for et, cnt in issues["top_error_types"].items():
            lines.append(f"- error: {et} x{cnt}")
    if not any(issues.values()):
        lines.append("- none")

    lines.append(f"\n## C. Suggestions")
    if suggestions["alias_suggestions"]:
        for s in suggestions["alias_suggestions"]:
            lines.append(f"- alias: \"{s['input']}\" -> \"{s['suggested']}\" ({s['reason']})")
    if suggestions["threshold_warnings"]:
        for s in suggestions["threshold_warnings"]:
            lines.append(f"- threshold: {s['field']} {s['current']} -> {s['suggested']}")
    if suggestions["route_suggestions"]:
        for s in suggestions["route_suggestions"]:
            lines.append(f"- route: HTTP {s['status_code']} x{s['count']}")
    if not any([suggestions["alias_suggestions"], suggestions["threshold_warnings"], suggestions["route_suggestions"]]):
        lines.append("- none")

    report = "\n".join(lines)
    (LEARNING_DIR / "daily_report.md").write_text(report, encoding="utf-8")
    return report


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "report"
    if action == "metrics":
        print(json.dumps(compute_metrics(), ensure_ascii=False, indent=2))
    elif action == "issues":
        print(json.dumps(compute_top_issues(), ensure_ascii=False, indent=2))
    elif action == "suggestions":
        sug = generate_suggestions()
        print(json.dumps(sug, ensure_ascii=False, indent=2))
    elif action == "report":
        print(generate_daily_report())
    else:
        print("Usage: analyze.py [metrics|issues|suggestions|report]")
