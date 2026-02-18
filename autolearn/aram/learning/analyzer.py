# aram/learning/analyzer.py - 反馈分析器
"""
分析匹配日志，找出：
- 纠正率最高的查询
- 最常被纠正的英雄
- 匹配类型分布
- 学习效果（纠正后是否不再出错）
"""
import json, time, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from aram.learning.feedback_log import load_feedback, load_learned


def analyze(days: int = 30) -> dict:
    logs = load_feedback(days)
    if not logs:
        return {"total": 0, "message": "No feedback data yet"}

    matches = [l for l in logs if l["type"] == "match"]
    corrections = [l for l in logs if l["type"] == "correction"]
    confirms = [l for l in logs if l["type"] == "confirm"]

    # 纠正率
    total_interactions = len(corrections) + len(confirms)
    correction_rate = len(corrections) / total_interactions if total_interactions > 0 else 0

    # 最常被纠正的查询
    correction_queries = Counter(c["query"] for c in corrections)

    # 匹配类型分布
    type_dist = Counter(m.get("match_type", "unknown") for m in matches)

    # 学习效果：纠正过的查询后来是否还被纠正
    corrected_queries = set(c["query"] for c in corrections)
    re_corrections = 0
    for q in corrected_queries:
        q_corrections = [c for c in corrections if c["query"] == q]
        if len(q_corrections) > 1:
            re_corrections += 1

    learned = load_learned()

    return {
        "period_days": days,
        "total_matches": len(matches),
        "total_corrections": len(corrections),
        "total_confirms": len(confirms),
        "correction_rate": round(correction_rate, 3),
        "top_corrected": dict(correction_queries.most_common(10)),
        "match_type_distribution": dict(type_dist),
        "re_correction_count": re_corrections,
        "learned_aliases_count": len(learned),
        "ts": int(time.time()),
    }


def report(days: int = 30) -> str:
    stats = analyze(days)
    lines = [
        f"# Matcher Analysis ({stats['period_days']}d)",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        f"## Overview",
        f"- Matches: {stats['total_matches']}",
        f"- Corrections: {stats['total_corrections']}",
        f"- Confirms: {stats['total_confirms']}",
        f"- Correction rate: {stats['correction_rate']:.1%}",
        f"- Learned aliases: {stats['learned_aliases_count']}",
        f"- Re-corrections: {stats['re_correction_count']}",
    ]

    if stats.get("top_corrected"):
        lines.append(f"\n## Top Corrected Queries")
        for q, count in stats["top_corrected"].items():
            lines.append(f"- '{q}' x{count}")

    if stats.get("match_type_distribution"):
        lines.append(f"\n## Match Type Distribution")
        for t, count in stats["match_type_distribution"].items():
            lines.append(f"- {t}: {count}")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    print(report(days))
