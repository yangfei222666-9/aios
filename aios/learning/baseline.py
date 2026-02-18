# aios/learning/baseline.py - 基线固化（metrics_history.jsonl）
"""
每次 analyze 后追加一条基线快照，用于画趋势。
"""
import json, time, sys, math
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.engine import load_events, append_jsonl
from core.config import get_path

LEARNING_DIR = Path(__file__).resolve().parent
HISTORY_FILE = get_path("paths.metrics_history") or (LEARNING_DIR / "metrics_history.jsonl")


def snapshot(days: int = 1) -> dict:
    events = load_events(days)
    matches = [e for e in events if e.get("type") == "match"]
    corrections = [e for e in events if e.get("type") == "correction"]
    tools = [e for e in events if e.get("type") == "tool"]
    http_errors = [e for e in events if e.get("type") == "http_error"]

    total_match = len(matches) + len(corrections)
    correction_rate = len(corrections) / total_match if total_match > 0 else 0

    tool_ok = [t for t in tools if (t.get("data") or {}).get("ok", True)]
    tool_success_rate = len(tool_ok) / len(tools) if tools else 1.0

    # p95 per tool
    by_tool = defaultdict(list)
    for e in tools:
        data = e.get("data", {})
        name = data.get("name", data.get("tool", e.get("source", "?")))
        ms = data.get("ms", data.get("elapsed_ms", 0))
        if ms > 0:
            by_tool[name].append(ms)

    tool_p95 = {}
    for name, times in by_tool.items():
        if len(times) >= 2:
            s = sorted(times)
            idx = math.ceil(0.95 * len(s)) - 1
            tool_p95[name] = s[idx]

    # http error rates
    http_codes = Counter((e.get("data") or {}).get("status_code", 0) for e in http_errors)
    total_http = sum(http_codes.values())

    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "period_days": days,
        "correction_rate": round(correction_rate, 4),
        "tool_success_rate": round(tool_success_rate, 4),
        "tool_p95_ms": tool_p95,
        "http_error_count": total_http,
        "http_502_rate": round(http_codes.get(502, 0) / max(total_http, 1), 3),
        "http_404_rate": round(http_codes.get(404, 0) / max(total_http, 1), 3),
        "total_events": len(events),
    }

    append_jsonl(HISTORY_FILE, record)
    return record


def load_history(limit: int = 30) -> list:
    if not HISTORY_FILE.exists():
        return []
    lines = HISTORY_FILE.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines[-limit:]:
        if line.strip():
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def trend_summary(limit: int = 7) -> str:
    history = load_history(limit)
    if len(history) < 2:
        return "Not enough data for trend (need >= 2 snapshots)"

    first, last = history[0], history[-1]
    lines = [f"Trend ({len(history)} snapshots):"]

    cr_delta = last["correction_rate"] - first["correction_rate"]
    lines.append(f"  correction_rate: {first['correction_rate']:.2%} → {last['correction_rate']:.2%} ({'+' if cr_delta >= 0 else ''}{cr_delta:.2%})")

    ts_delta = last["tool_success_rate"] - first["tool_success_rate"]
    lines.append(f"  tool_success_rate: {first['tool_success_rate']:.2%} → {last['tool_success_rate']:.2%} ({'+' if ts_delta >= 0 else ''}{ts_delta:.2%})")

    # p95 trend per tool
    all_tools = set(list(first.get("tool_p95_ms", {}).keys()) + list(last.get("tool_p95_ms", {}).keys()))
    for t in sorted(all_tools):
        p_first = first.get("tool_p95_ms", {}).get(t)
        p_last = last.get("tool_p95_ms", {}).get(t)
        if p_first and p_last:
            lines.append(f"  {t} p95: {p_first}ms → {p_last}ms")

    return "\n".join(lines)


def evolution_score(limit: int = 7) -> dict:
    """
    进化评分：对比最早和最近的 baseline，综合打分。
    
    维度权重：
      correction_rate  下降=好  权重 30
      tool_success_rate 上升=好  权重 30
      tool_p95_ms      下降=好  权重 25
      http_error_count 下降=好  权重 15
    
    score: -100 (严重退化) ~ 0 (持平) ~ +100 (显著进化)
    """
    history = load_history(limit)
    if len(history) < 2:
        return {"score": 0, "grade": "N/A", "reason": "not_enough_data", "snapshots": len(history)}

    first, last = history[0], history[-1]

    # correction_rate: 下降=好 (0→0 也是好)
    cr_f, cr_l = first["correction_rate"], last["correction_rate"]
    if cr_f == 0 and cr_l == 0:
        cr_score = 10  # 一直是0，小加分
    elif cr_f == 0:
        cr_score = -50  # 从0变差
    else:
        cr_score = (cr_f - cr_l) / cr_f * 100  # 下降比例
    cr_score = max(-100, min(100, cr_score))

    # tool_success_rate: 上升=好
    ts_f, ts_l = first["tool_success_rate"], last["tool_success_rate"]
    if ts_f == 1.0 and ts_l == 1.0:
        ts_score = 10
    elif ts_f == 0:
        ts_score = 50 if ts_l > 0 else 0
    else:
        ts_score = (ts_l - ts_f) / ts_f * 100
    ts_score = max(-100, min(100, ts_score))

    # p95: 下降=好（取所有 tool 平均变化）
    p95_f = first.get("tool_p95_ms", {})
    p95_l = last.get("tool_p95_ms", {})
    common_tools = set(p95_f.keys()) & set(p95_l.keys())
    if common_tools:
        deltas = []
        for t in common_tools:
            if p95_f[t] > 0:
                deltas.append((p95_f[t] - p95_l[t]) / p95_f[t] * 100)
        p95_score = sum(deltas) / len(deltas) if deltas else 0
    else:
        p95_score = 0
    p95_score = max(-100, min(100, p95_score))

    # http_error: 下降=好
    he_f, he_l = first.get("http_error_count", 0), last.get("http_error_count", 0)
    if he_f == 0 and he_l == 0:
        he_score = 10
    elif he_f == 0:
        he_score = -50
    else:
        he_score = (he_f - he_l) / he_f * 100
    he_score = max(-100, min(100, he_score))

    # 加权
    score = round(cr_score * 0.30 + ts_score * 0.30 + p95_score * 0.25 + he_score * 0.15, 1)

    # 评级
    if score >= 20:
        grade = "evolving"
    elif score >= 5:
        grade = "improving"
    elif score >= -5:
        grade = "stable"
    elif score >= -20:
        grade = "declining"
    else:
        grade = "regressing"

    return {
        "score": score,
        "grade": grade,
        "snapshots": len(history),
        "breakdown": {
            "correction_rate": {"weight": 0.30, "score": round(cr_score, 1), "before": cr_f, "after": cr_l},
            "tool_success_rate": {"weight": 0.30, "score": round(ts_score, 1), "before": ts_f, "after": ts_l},
            "tool_p95_ms": {"weight": 0.25, "score": round(p95_score, 1)},
            "http_errors": {"weight": 0.15, "score": round(he_score, 1), "before": he_f, "after": he_l},
        },
    }


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "snapshot"
    if action == "snapshot":
        r = snapshot()
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif action == "trend":
        print(trend_summary())
    elif action == "score":
        print(json.dumps(evolution_score(), ensure_ascii=False, indent=2))
    elif action == "history":
        for r in load_history():
            print(json.dumps(r, ensure_ascii=False))
    else:
        print("Usage: baseline.py [snapshot|trend|score|history]")
