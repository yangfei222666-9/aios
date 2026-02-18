# aios/scripts/analyze.py - 从事件流分析，产出建议和报告
"""
读取 events.jsonl → 分析模式 → 输出:
  - learning/suggestions.json (机器建议)
  - learning/daily_report.md (每日报告)
  - learning/lessons.md (教训沉淀)
"""
import json, time, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.log_event import load_events, count_by_type

AIOS_ROOT = Path(__file__).resolve().parent.parent
LEARNING_DIR = AIOS_ROOT / "learning"
LEARNING_DIR.mkdir(exist_ok=True)


def analyze_corrections(days: int = 30, threshold: int = 3) -> list:
    """分析纠正事件，找出高频纠正模式"""
    corrections = load_events(days, "correction")
    
    # 按 input 聚合纠正目标
    patterns = defaultdict(list)
    for c in corrections:
        data = c.get("data", {})
        inp = data.get("input", c.get("summary", ""))
        target = data.get("correct_target", "")
        if inp and target:
            patterns[inp].append(target)
    
    suggestions = []
    for inp, targets in patterns.items():
        target_counts = Counter(targets)
        top_target, top_count = target_counts.most_common(1)[0]
        if top_count >= threshold:
            suggestions.append({
                "type": "redirect_alias",
                "input": inp,
                "suggested_target": top_target,
                "correction_count": top_count,
                "confidence": round(top_count / len(targets), 2),
                "reason": f"'{inp}' 被纠正 {top_count} 次 → 建议指向 {top_target}",
            })
    
    return suggestions


def analyze_errors(days: int = 30) -> list:
    """分析错误事件，提取教训"""
    errors = load_events(days, "error")
    
    # 按 source 聚合
    by_source = defaultdict(list)
    for e in errors:
        by_source[e.get("source", "unknown")].append(e)
    
    lessons = []
    for source, errs in by_source.items():
        if len(errs) >= 2:
            summaries = [e.get("summary", "") for e in errs[:5]]
            lessons.append({
                "source": source,
                "count": len(errs),
                "pattern": summaries,
                "lesson": f"{source} 在 {days} 天内出错 {len(errs)} 次，需要关注",
            })
    
    return lessons


def generate_suggestions(days: int = 30) -> list:
    """生成所有建议"""
    suggestions = []
    suggestions.extend(analyze_corrections(days))
    
    # 写入文件
    out_path = LEARNING_DIR / "suggestions.json"
    out_path.write_text(json.dumps(suggestions, ensure_ascii=False, indent=2), encoding="utf-8")
    
    return suggestions


def generate_lessons(days: int = 30) -> list:
    """生成教训"""
    lessons = analyze_errors(days)
    
    # 写入 markdown
    lines = [
        f"# Lessons Learned",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
    ]
    
    if not lessons:
        lines.append("No recurring errors detected. System is healthy.")
    else:
        for i, l in enumerate(lessons, 1):
            lines.append(f"## {i}. {l['source']} ({l['count']} errors)")
            lines.append(f"- Lesson: {l['lesson']}")
            lines.append(f"- Examples: {', '.join(l['pattern'][:3])}")
            lines.append("")
    
    out_path = LEARNING_DIR / "lessons.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    
    return lessons


def generate_daily_report(days: int = 1) -> str:
    """生成每日报告"""
    counts = count_by_type(days)
    events = load_events(days)
    suggestions = analyze_corrections(days)
    lessons = analyze_errors(days)
    
    lines = [
        f"# AIOS Daily Report",
        f"Date: {time.strftime('%Y-%m-%d')}",
        f"Period: last {days} day(s)\n",
        f"## Event Summary",
        f"- Total events: {len(events)}",
    ]
    for t, c in sorted(counts.items()):
        lines.append(f"  - {t}: {c}")
    
    lines.append(f"\n## Suggestions ({len(suggestions)})")
    if suggestions:
        for s in suggestions:
            lines.append(f"- {s['reason']}")
    else:
        lines.append("- None")
    
    lines.append(f"\n## Lessons ({len(lessons)})")
    if lessons:
        for l in lessons:
            lines.append(f"- {l['lesson']}")
    else:
        lines.append("- System healthy, no recurring errors")
    
    report = "\n".join(lines)
    out_path = LEARNING_DIR / "daily_report.md"
    out_path.write_text(report, encoding="utf-8")
    
    return report


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "report"
    
    if action == "suggestions":
        sug = generate_suggestions()
        print(json.dumps(sug, ensure_ascii=False, indent=2))
    elif action == "lessons":
        generate_lessons()
        print((LEARNING_DIR / "lessons.md").read_text(encoding="utf-8"))
    elif action == "report":
        print(generate_daily_report())
    else:
        print(f"Usage: analyze.py [suggestions|lessons|report]")
