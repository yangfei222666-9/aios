# aios/core/engine.py - 事件引擎（读写 events.jsonl）
import json, time, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.config import get_path


def _events_path() -> Path:
    return get_path("paths.events") or Path(__file__).resolve().parent.parent / "events" / "events.jsonl"


def log_event(event_type: str, source: str, summary: str, data: dict = None) -> dict:
    """追加一条事件"""
    p = _events_path()
    p.parent.mkdir(exist_ok=True)

    event = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        "ts": int(time.time()),
        "type": event_type,
        "source": source,
        "summary": summary,
    }
    if data:
        event["data"] = data

    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

    return event


def load_events(days: int = 30, event_type: str = None) -> list:
    """加载事件"""
    p = _events_path()
    if not p.exists():
        return []
    cutoff = time.time() - days * 86400
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
            if ev.get("ts", 0) < cutoff:
                continue
            if event_type and ev.get("type") != event_type:
                continue
            out.append(ev)
        except Exception:
            continue
    return out


def count_by_type(days: int = 30) -> dict:
    events = load_events(days)
    counts = {}
    for ev in events:
        t = ev.get("type", "unknown")
        counts[t] = counts.get(t, 0) + 1
    return counts


def log_tool_event(name: str, ok: bool, ms: int, err: str = None, meta: dict = None) -> dict:
    """统一 tool 事件格式: {type:"tool", name, ok, ms, err?, meta?}"""
    data = {"name": name, "ok": ok, "ms": ms}
    if not ok and err:
        data["err"] = err[:500]
    if meta:
        data["meta"] = meta
    return log_event("tool", name, f"{'ok' if ok else 'fail'} {ms}ms", data)
