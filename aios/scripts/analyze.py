# aios/scripts/analyze.py - 自动分析器：每天产出"改进建议"
"""
从 events.jsonl 分析，产出三类输出：
  A. 质量指标 (Metrics)
  B. Top 问题 (Top Issues)
  C. 建议 (Suggestions)

输出:
  - learning/suggestions.json
  - learning/daily_report.md
  - learning/lessons.md
"""
import json, time, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.log_event import load_events, count_by_type

AIOS_ROOT = Path(__file__).resolve().parent.parent
LEARNING_DIR = AIOS_ROOT / "learning"
LEARNING_DIR.mkdir(exist_ok=True)

CORRECTION_THRESHOLD = 3
LOW_SCORE_THRESHOLD = 0.8


# ==================== A. 质量指标 (Metrics) ====================

def compute_metrics(days: int = 1) -> dict:
    events = load_events(days)
    
    matches = [e for e in events if e.get("type") == "match"]
    corrections = [e for e in events if e.get("type") == "correction"]
    tools = [e for e in events if e.get("type") in ("tool", "task")]
    http_errors = [e for e in events if e.get("type") == "http_error"]
    
    # match 纠正率
    total_match_interactions = len(matches) + len(corrections)
    correction_rate = len(corrections) / total_match_interactions if total_match_interactions > 0 else 0
    
    # 低分匹配占比
    low_score = [m for m in matches if (m.get("data") or {}).get("score", 1.0) < LOW_SCORE_THRESHOLD]
    low_score_ratio = len(low_score) / len(matches) if matches else 0
    
    # tool 成功率
    tool_ok = [t for t in tools if (t.get("data") or {}).get("ok", True)]
    tool_success_rate = len(tool_ok) / len(tools) if tools else 1.0
    
    # 502/404 频率
    http_status_counts = Counter(
        (e.get("data") or {}).get("status_code", "?") for e in http_errors
    )
    
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


# ==================== B. Top 问题 (Top Issues) ====================

def compute_top_issues(days: int = 7) -> dict:
    events = load_events(days)
    corrections = [e for e in events if e.get("type") == "correction"]
    errors = [e for e in events if e.get("type") in ("error", "http_error")]
    tools = [e for e in events if e.get("type") in ("tool", "task") and not (e.get("data") or {}).get("ok", True)]
    
    # 最常被纠正的输入 Top10
    correction_inputs = Counter(
        (e.get("data") or {}).get("input", e.get("summary", "?")) for e in corrections
    )
    
    # 最常失败的 tool Top5
    failed_tools = Counter(
        (e.get("data") or {}).get("tool", e.get("source", "?")) for e in tools
    )
    
    # 最常见错误类型 Top5
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


# ==================== C. 建议 (Suggestions) ====================

def compute_suggestions(days: int = 7) -> list:
    events = load_events(days)
    corrections = [e for e in events if e.get("type") == "correction"]
    matches = [e for e in events if e.get("type") == "match"]
    http_errors = [e for e in events if e.get("type") == "http_error"]
    
    suggestions = []
    
    # 1. alias 建议：纠正 >= N 次
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
            suggestions.append({
                "type": "alias_redirect",
                "severity": "high",
                "reason": f"alias 建议: \"{inp}\" → \"{top}\" (纠正 {count} 次)",
                "input": inp,
                "target": top,
                "count": count,
            })
    
    # 2. 阈值建议：低分且纠正多 → 需要二次确认
    low_score_corrected = set()
    for c in corrections:
        low_score_corrected.add((c.get("data") or {}).get("input", ""))
    low_score_matches = [m for m in matches if (m.get("data") or {}).get("score", 1.0) < LOW_SCORE_THRESHOLD]
    low_corrected_count = sum(1 for m in low_score_matches 
                              if (m.get("data") or {}).get("input", "") in low_score_corrected)
    if low_corrected_count >= 3:
        suggestions.append({
            "type": "threshold_warning",
            "severity": "medium",
            "reason": f"阈值建议: 低分且纠正多 ({low_corrected_count}次) → 提高\"需要二次确认\"",
            "count": low_corrected_count,
        })
    
    # 3. 路由建议：502 多 → 降级
    status_502 = sum(1 for e in http_errors if (e.get("data") or {}).get("status_code") == 502)
    if status_502 >= 3:
        suggestions.append({
            "type": "route_suggestion",
            "severity": "medium",
            "reason": f"路由建议: 502 x{status_502} → 考虑降级或切换备用",
            "count": status_502,
        })
    
    return suggestions


# ==================== 输出 ====================

def generate_suggestions(days: int = 7) -> list:
    sug = compute_suggestions(days)
    out_path = LEARNING_DIR / "suggestions.json"
    out_path.write_text(json.dumps(sug, ensure_ascii=False, indent=2), encoding="utf-8")
    return sug


def generate_lessons(days: int = 7) -> list:
    events = load_events(days)
    errors = [e for e in events if e.get("type") in ("error",)]
    
    by_source = defaultdict(list)
    for e in errors:
        by_source[e.get("source", "unknown")].append(e)
    
    lessons = []
    for source, errs in by_source.items():
        if len(errs) >= 2:
            lessons.append({
                "source": source,
                "count": len(errs),
                "lesson": f"{source} 在周期内出错 {len(errs)} 次",
                "examples": [e.get("summary", "")[:100] for e in errs[:3]],
            })
    
    lines = [f"# Lessons Learned", f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"]
    if not lessons:
        lines.append("No recurring errors. System healthy.")
    else:
        for i, l in enumerate(lessons, 1):
            lines.append(f"## {i}. {l['source']} ({l['count']} errors)")
            lines.append(f"- {l['lesson']}")
            for ex in l["examples"]:
                lines.append(f"  - {ex}")
            lines.append("")
    
    (LEARNING_DIR / "lessons.md").write_text("\n".join(lines), encoding="utf-8")
    return lessons


def generate_daily_report(days: int = 1) -> str:
    metrics = compute_metrics(days)
    issues = compute_top_issues(days)
    suggestions = compute_suggestions(days)
    
    lines = [
        f"# AIOS Daily Report",
        f"Date: {time.strftime('%Y-%m-%d')}",
        f"Period: last {days} day(s)\n",
    ]
    
    # A. Metrics
    lines.append("## A. 质量指标 (Metrics)")
    lines.append(f"- match 纠正率: {metrics['match_correction_rate']:.1%}")
    lines.append(f"- 低分匹配占比: {metrics['low_score_ratio']:.1%}")
    lines.append(f"- tool 成功率: {metrics['tool_success_rate']:.1%} ({metrics['tool_total']} total)")
    lines.append(f"- HTTP 错误: {metrics['http_error_count']}")
    if metrics["http_status_breakdown"]:
        for code, cnt in metrics["http_status_breakdown"].items():
            lines.append(f"  - {code}: x{cnt}")
    lines.append(f"- 总事件数: {metrics['total_events']}")
    
    # B. Top Issues
    lines.append(f"\n## B. Top 问题 (Top Issues)")
    
    if issues["top_corrected_inputs"]:
        lines.append("### 最常被纠正的输入")
        for inp, cnt in issues["top_corrected_inputs"].items():
            lines.append(f"- \"{inp}\" x{cnt}")
    
    if issues["top_failed_tools"]:
        lines.append("### 最常失败的 tool")
        for tool, cnt in issues["top_failed_tools"].items():
            lines.append(f"- {tool} x{cnt}")
    
    if issues["top_error_types"]:
        lines.append("### 最常见错误类型")
        for et, cnt in issues["top_error_types"].items():
            lines.append(f"- {et} x{cnt}")
    
    if not any(issues.values()):
        lines.append("- No issues detected")
    
    # C. Suggestions
    lines.append(f"\n## C. 建议 (Suggestions)")
    if suggestions:
        for s in suggestions:
            lines.append(f"- [{s['severity']}] {s['reason']}")
    else:
        lines.append("- No suggestions")
    
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
    elif action == "lessons":
        generate_lessons()
        print((LEARNING_DIR / "lessons.md").read_text(encoding="utf-8"))
    elif action == "report":
        print(generate_daily_report())
    else:
        print("Usage: analyze.py [metrics|issues|suggestions|lessons|report]")
