# aios/learning/analyze.py - 自动分析器
"""
从 events.jsonl 分析，产出结构化报告：
  metrics / top_issues / alias_suggestions / tool_suggestions / threshold_warnings
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

    http_status = Counter((e.get("data") or {}).get("status_code", "?") for e in http_errors)

    return {
        "match_correction_rate": round(correction_rate, 3),
        "low_score_ratio": round(low_score_ratio, 3),
        "tool_success_rate": round(tool_success_rate, 3),
        "tool_total": len(tools),
        "http_error_count": len(http_errors),
        "http_status_breakdown": dict(http_status),
        "total_events": len(events),
    }


def compute_top_issues(days: int = 7) -> dict:
    events = load_events(days)
    corrections = [e for e in events if e.get("type") == "correction"]
    errors = [e for e in events if e.get("type") in ("error", "http_error")]
    failed_tools = [e for e in events if e.get("type") in ("tool", "task") and not (e.get("data") or {}).get("ok", True)]

    return {
        "top_corrected_inputs": dict(Counter(
            (e.get("data") or {}).get("input", "?") for e in corrections
        ).most_common(10)),
        "top_failed_tools": dict(Counter(
            (e.get("data") or {}).get("tool", e.get("source", "?")) for e in failed_tools
        ).most_common(5)),
        "top_error_types": dict(Counter(
            f"{e.get('type')}:{(e.get('data') or {}).get('status_code', '')}" if e.get("type") == "http_error"
            else e.get("source", "?")
            for e in errors
        ).most_common(5)),
    }


def compute_alias_suggestions(days: int = 7) -> list:
    """L1: alias 建议（可自动应用）"""
    corrections = load_events(days, "correction")
    targets = defaultdict(list)
    examples = defaultdict(list)

    for c in corrections:
        data = c.get("data", {})
        inp = data.get("input", "")
        target = data.get("correct_target", "")
        matched = data.get("matched", "")
        if inp and target:
            targets[inp].append(target)
            if matched:
                ex = f"{matched}->{target}"
                if ex not in examples[inp]:
                    examples[inp].append(ex)

    suggestions = []
    for inp, tlist in targets.items():
        tc = Counter(tlist)
        top, count = tc.most_common(1)[0]
        if count >= CORRECTION_THRESHOLD:
            suggestions.append({
                "level": "L1",
                "input": inp,
                "suggested": top,
                "confidence": round(count / len(tlist), 2),
                "evidence": {
                    "corrections": count,
                    "examples": examples[inp][:3],
                },
                "reason": f"corrected>={count}",
            })

    return suggestions


def compute_tool_suggestions(days: int = 7) -> list:
    """L2: tool 建议 — 失败驱动 + 性能驱动"""
    events = load_events(days)
    tool_events = [e for e in events if e.get("type") in ("tool", "task")]
    failed = [e for e in events if e.get("type") in ("tool", "task", "error", "http_error")
              and not (e.get("data") or {}).get("ok", True)]

    # --- Failure Learner ---
    by_tool_fail = defaultdict(list)
    for e in failed:
        data = e.get("data", {})
        tool = data.get("name", data.get("tool", e.get("source", "?")))
        by_tool_fail[tool].append(e)

    suggestions = []
    for tool, errs in by_tool_fail.items():
        if len(errs) < 2:
            continue
        err_types = Counter()
        for e in errs:
            data = e.get("data", {})
            code = data.get("status_code", "")
            err = data.get("err", data.get("error", ""))
            err_types[str(code) if code else err[:50] or "unknown"] += 1
        top_err, _ = err_types.most_common(1)[0]

        suggestions.append({
            "level": "L2",
            "name": tool,
            "action": "cooldown_10m" if len(errs) >= 3 else "monitor",
            "confidence": round(min(len(errs) / 5, 1.0), 2),
            "evidence": {"fails": len(errs), "top_err": top_err},
            "reason": f"repeat_fail>={len(errs)}",
        })

    # --- Perf Learner ---
    import math
    by_tool_perf = defaultdict(list)
    for e in tool_events:
        data = e.get("data", {})
        tool = data.get("name", data.get("tool", e.get("source", "?")))
        ms = data.get("ms", data.get("elapsed_ms", 0))
        if ms > 0:
            by_tool_perf[tool].append(ms)

    for tool, times in by_tool_perf.items():
        if len(times) < 3:
            continue
        times_sorted = sorted(times)
        p95_idx = math.ceil(0.95 * len(times_sorted)) - 1
        p95 = times_sorted[p95_idx]
        median = times_sorted[len(times_sorted) // 2]

        if p95 > 5000:  # p95 > 5s
            suggestions.append({
                "level": "L2",
                "name": tool,
                "action": "optimize_or_cache",
                "confidence": round(min(p95 / 10000, 1.0), 2),
                "evidence": {"p95_ms": p95, "median_ms": median, "samples": len(times)},
                "reason": f"p95>{p95}ms",
            })

    return suggestions


def compute_threshold_warnings(days: int = 7) -> list:
    """L3: 阈值警告（仅报警）"""
    events = load_events(days)
    matches = [e for e in events if e.get("type") == "match"]
    corrections = [e for e in events if e.get("type") == "correction"]
    warnings = []

    total = len(matches) + len(corrections)
    if total > 0:
        cr = len(corrections) / total
        if cr > 0.15:
            warnings.append({
                "field": "correction_rate",
                "current": round(cr, 2),
                "suggested": 0.10,
                "reason": "high_correction_rate",
            })

    if matches:
        low = [m for m in matches if (m.get("data") or {}).get("score", 1.0) < LOW_SCORE_THRESHOLD]
        lsr = len(low) / len(matches)
        if lsr > 0.15:
            warnings.append({
                "field": "low_score_rate",
                "current": round(lsr, 2),
                "suggested": 0.10,
                "reason": "too_many_low_score_matches",
            })

    return warnings


def generate_full_report(days: int = 7) -> dict:
    """完整结构化报告"""
    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "metrics": compute_metrics(days),
        "top_issues": compute_top_issues(days),
        "alias_suggestions": compute_alias_suggestions(days),
        "tool_suggestions": compute_tool_suggestions(days),
        "threshold_warnings": compute_threshold_warnings(days),
    }

    # 写 suggestions.json（只含可操作部分）
    sug = {
        "generated_at": report["generated_at"],
        "alias_suggestions": [{
            "input": s["input"],
            "suggested": s["suggested"],
            "reason": s["reason"],
            "confidence": s["confidence"],
        } for s in report["alias_suggestions"]],
        "threshold_warnings": report["threshold_warnings"],
        "route_suggestions": [],
    }
    (LEARNING_DIR / "suggestions.json").write_text(json.dumps(sug, ensure_ascii=False, indent=2), encoding="utf-8")

    return report


def generate_daily_report(days: int = 1) -> str:
    r = generate_full_report(days)
    m = r["metrics"]
    lines = [
        f"# AIOS Daily Report",
        f"Generated: {r['generated_at']}\n",
        "## A. Metrics",
        f"- correction_rate: {m['match_correction_rate']:.1%}",
        f"- low_score_ratio: {m['low_score_ratio']:.1%}",
        f"- tool_success_rate: {m['tool_success_rate']:.1%} ({m['tool_total']})",
        f"- http_errors: {m['http_error_count']}",
    ]

    lines.append("\n## B. Top Issues")
    for inp, cnt in r["top_issues"].get("top_corrected_inputs", {}).items():
        lines.append(f"- corrected: \"{inp}\" x{cnt}")
    for t, cnt in r["top_issues"].get("top_failed_tools", {}).items():
        lines.append(f"- failed: {t} x{cnt}")

    lines.append("\n## C. Alias Suggestions (L1)")
    for s in r["alias_suggestions"]:
        lines.append(f"- \"{s['input']}\" → \"{s['suggested']}\" conf={s['confidence']} ({s['reason']})")

    lines.append("\n## D. Tool Suggestions (L2)")
    for s in r["tool_suggestions"]:
        lines.append(f"- {s['name']}: {s['action']} conf={s['confidence']} ({s['reason']})")

    if r["threshold_warnings"]:
        lines.append("\n## E. Threshold Warnings")
        for w in r["threshold_warnings"]:
            lines.append(f"- {w['field']}: {w['current']} → {w['suggested']}")

    if not any([r["alias_suggestions"], r["tool_suggestions"], r["threshold_warnings"]]):
        lines.append("\n- No suggestions")

    report_text = "\n".join(lines)
    (LEARNING_DIR / "daily_report.md").write_text(report_text, encoding="utf-8")
    return report_text


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "report"
    if action == "json":
        print(json.dumps(generate_full_report(), ensure_ascii=False, indent=2))
    elif action == "suggestions":
        r = generate_full_report()
        sug = {k: r[k] for k in ("alias_suggestions", "tool_suggestions", "threshold_warnings")}
        sug["generated_at"] = r["generated_at"]
        print(json.dumps(sug, ensure_ascii=False, indent=2))
    elif action == "report":
        print(generate_daily_report())
    else:
        print("Usage: analyze.py [json|suggestions|report]")
