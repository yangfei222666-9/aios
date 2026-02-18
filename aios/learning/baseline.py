# aios/learning/baseline.py - 基线固化（metrics_history.jsonl）
"""
每次 analyze 后追加一条基线快照，用于画趋势。
"""
import json, time, sys, math
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.engine import load_events
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

    HISTORY_FILE.parent.mkdir(exist_ok=True)
    with HISTORY_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

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


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "snapshot"
    if action == "snapshot":
        r = snapshot()
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif action == "trend":
        print(trend_summary())
    elif action == "history":
        for r in load_history():
            print(json.dumps(r, ensure_ascii=False))
    else:
        print("Usage: baseline.py [snapshot|trend|history]")
