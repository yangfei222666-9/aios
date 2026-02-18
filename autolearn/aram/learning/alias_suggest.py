# aram/learning/alias_suggest.py - 别名建议器
"""
基于反馈日志自动建议新别名：
- 同一查询被纠正 N 次到同一英雄 → 建议重定向别名
- 高频低分匹配 → 建议添加别名
- 同一英雄学习别名过多 → 建议合并到内置
"""
import json, time, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from aram.learning.feedback_log import load_feedback, load_learned, save_learned

DEFAULT_THRESHOLD = 3  # 纠正 N 次触发建议


def suggest(days: int = 30, threshold: int = DEFAULT_THRESHOLD) -> list:
    """生成别名建议列表"""
    logs = load_feedback(days)
    corrections = [l for l in logs if l.get("corrected", False)]
    matches = [l for l in logs if not l.get("corrected", False) and not l.get("confirmed", False)]
    learned = load_learned()

    suggestions = []

    # 1. 同一查询多次纠正到同一目标 → 建议重定向
    query_corrections = defaultdict(list)
    for c in corrections:
        query_corrections[c["input"]].append(c.get("correct_id", ""))

    for query, target_ids in query_corrections.items():
        target_counts = Counter(tid for tid in target_ids if tid)
        if not target_counts:
            continue
        top_id, top_count = target_counts.most_common(1)[0]
        if top_count >= threshold:
            # 查当前指向
            current_target = learned.get(query)
            suggestions.append({
                "type": "redirect_alias",
                "input": query,
                "current_target": current_target,
                "suggested_target": top_id,
                "correction_count": top_count,
                "confidence": round(top_count / len(target_ids), 2),
                "reason": f"'{query}' 被纠正 {top_count} 次 → 建议 alias 指向 {top_id}",
            })

    # 2. 高频低分匹配 → 建议添加别名
    low_score_queries = defaultdict(list)
    for m in matches:
        if m.get("score") is not None and m["score"] < 0.8:
            low_score_queries[m["input"]].append(m.get("matched_id", ""))

    for query, ids in low_score_queries.items():
        if query in learned or len(ids) < threshold:
            continue
        top_id = Counter(i for i in ids if i).most_common(1)
        if top_id:
            suggestions.append({
                "type": "add_alias",
                "input": query,
                "suggested_target": top_id[0][0],
                "match_count": len(ids),
                "reason": f"'{query}' 低分匹配 x{len(ids)}，建议添加别名",
            })

    # 3. 同一英雄学习别名过多 → 建议固化到内置
    learned_by_id = defaultdict(list)
    for alias, cid in learned.items():
        learned_by_id[cid].append(alias)

    for cid, aliases in learned_by_id.items():
        if len(aliases) >= 3:
            suggestions.append({
                "type": "promote_to_builtin",
                "champion_id": cid,
                "aliases": aliases,
                "count": len(aliases),
                "reason": f"英雄 {cid} 有 {len(aliases)} 个学习别名，建议固化到内置词典",
            })

    return suggestions


def auto_apply(days: int = 30, threshold: int = DEFAULT_THRESHOLD) -> list:
    """自动应用建议：达到阈值的重定向直接写入 learned_aliases"""
    suggestions = suggest(days, threshold)
    applied = []
    learned = load_learned()

    for s in suggestions:
        if s["type"] == "redirect_alias":
            old = learned.get(s["input"])
            learned[s["input"]] = s["suggested_target"]
            applied.append({
                "input": s["input"],
                "old": old,
                "new": s["suggested_target"],
                "reason": s["reason"],
            })

    if applied:
        save_learned(learned)

    return applied


def report(days: int = 30) -> str:
    sug = suggest(days)
    lines = [
        f"# Alias Suggestions",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
    ]

    if not sug:
        lines.append("No suggestions. Matcher is performing well.")
    else:
        for i, s in enumerate(sug, 1):
            lines.append(f"{i}. [{s['type']}] {s['reason']}")
            for k, v in s.items():
                if k not in ("type", "reason"):
                    lines.append(f"   - {k}: {v}")
            lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

    action = sys.argv[1] if len(sys.argv) > 1 else "report"
    if action == "apply":
        applied = auto_apply()
        if applied:
            for a in applied:
                print(json.dumps(a, ensure_ascii=False))
        else:
            print("Nothing to apply.")
    else:
        print(report())
