# aram/learning/alias_suggest.py - 别名建议器
"""
基于反馈日志自动建议新别名：
- 高频查询但无别名 → 建议添加
- 多次纠正到同一英雄 → 建议固化
- 相似查询指向同一英雄 → 建议合并
"""
import json, time, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from aram.learning.feedback_log import load_feedback, load_learned

# 内置别名（从 matcher 导入会循环，这里只读 learned）
BUILTIN_ALIASES_COUNT = 80  # 大约数量，用于统计


def suggest(days: int = 30, min_count: int = 2) -> list:
    """生成别名建议列表"""
    logs = load_feedback(days)
    corrections = [l for l in logs if l.get("corrected", False)]
    matches = [l for l in logs if not l.get("corrected", False)]
    learned = load_learned()

    suggestions = []

    # 1. 多次纠正到同一英雄 → 建议固化为别名
    query_to_correct = defaultdict(list)
    for c in corrections:
        query_to_correct[c["input"]].append(c["matched_id"])

    for query, ids in query_to_correct.items():
        if query in learned:
            continue  # 已学习
        id_counts = Counter(ids)
        top_id, top_count = id_counts.most_common(1)[0]
        if top_count >= min_count:
            suggestions.append({
                "type": "promote_to_alias",
                "query": query,
                "champion_id": top_id,
                "count": top_count,
                "confidence": round(top_count / len(ids), 2),
                "reason": f"'{query}' corrected to {top_id} x{top_count}",
            })

    # 2. 高频匹配但低分 → 建议添加别名
    low_score_queries = defaultdict(list)
    for m in matches:
        if m.get("score") is not None and m["score"] < 0.8:
            low_score_queries[m["input"]].append(m["matched_id"])

    for query, ids in low_score_queries.items():
        if query in learned or len(ids) < min_count:
            continue
        top_id = Counter(ids).most_common(1)[0][0]
        suggestions.append({
            "type": "add_alias",
            "query": query,
            "champion_id": top_id,
            "count": len(ids),
            "reason": f"'{query}' matched with low score x{len(ids)}",
        })

    # 3. 相似查询指向同一英雄 → 建议合并
    learned_by_id = defaultdict(list)
    for alias, cid in learned.items():
        learned_by_id[cid].append(alias)

    for cid, aliases in learned_by_id.items():
        if len(aliases) >= 3:
            suggestions.append({
                "type": "merge_aliases",
                "champion_id": cid,
                "aliases": aliases,
                "count": len(aliases),
                "reason": f"Champion {cid} has {len(aliases)} learned aliases, consider promoting to builtin",
            })

    return suggestions


def report(days: int = 30) -> str:
    sug = suggest(days)
    lines = [
        f"# Alias Suggestions",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
    ]

    if not sug:
        lines.append("No suggestions at this time. Matcher is performing well.")
    else:
        for i, s in enumerate(sug, 1):
            lines.append(f"## {i}. [{s['type']}] {s['reason']}")
            for k, v in s.items():
                if k not in ("type", "reason"):
                    lines.append(f"- {k}: {v}")
            lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    print(report(days))
