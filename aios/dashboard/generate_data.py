"""AIOS Dashboard - 数据生成器
读取 AIOS 各数据源，输出 dashboard_data.json 供前端渲染
"""
import json, os, sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

BASE = Path(r"C:\Users\A\.openclaw\workspace\aios")
EVENTS_DIR = BASE / "events"
LEARNING_DIR = BASE / "learning"
OUT = BASE / "dashboard" / "dashboard_data.json"


def load_jsonl(path):
    """Load a JSONL file, skip bad lines."""
    items = []
    if not path.exists():
        return items
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return items


def load_json(path, default=None):
    if not path.exists():
        return default or {}
    return json.loads(path.read_text(encoding="utf-8"))


def get_baseline_history():
    """Read baseline.jsonl → list of snapshots."""
    return load_jsonl(LEARNING_DIR / "baseline.jsonl")


def normalize_ts(ts_val):
    """Convert ts to ISO string regardless of input type."""
    if isinstance(ts_val, (int, float)):
        return datetime.fromtimestamp(ts_val).isoformat()
    return str(ts_val) if ts_val else ""


def get_events(days=7):
    """Merge events from events.jsonl + queue/*.jsonl within N days."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    all_events = []
    # Main events
    for e in load_jsonl(EVENTS_DIR / "events.jsonl"):
        e["ts"] = normalize_ts(e.get("ts"))
        if e["ts"] >= cutoff:
            all_events.append(e)
    # Queue events
    queue_dir = EVENTS_DIR / "queue"
    if queue_dir.exists():
        for f in sorted(queue_dir.glob("*.jsonl")):
            for e in load_jsonl(f):
                e["ts"] = normalize_ts(e.get("ts"))
                if e["ts"] >= cutoff:
                    all_events.append(e)
    return sorted(all_events, key=lambda x: x.get("ts", ""))


def get_alerts():
    """Read alert FSM state."""
    alerts_file = BASE.parent / "data" / "alerts_state.json"
    if not alerts_file.exists():
        # Try alternate location
        alerts_file = EVENTS_DIR / "alerts_state.json"
    return load_json(alerts_file, {"alerts": []})


def get_strategies():
    return load_jsonl(LEARNING_DIR / "strategies.jsonl")


def get_execution_log():
    return load_jsonl(EVENTS_DIR / "execution_log.jsonl")


def build_dashboard():
    now = datetime.now()

    # 1. Baseline history (evolution score over time)
    baselines = get_baseline_history()
    timeline = []
    for b in baselines:
        timeline.append({
            "ts": b.get("ts"),
            "score": b.get("evolution_score", 0),
            "grade": b.get("grade", "unknown"),
            "tsr": b.get("tool_success_rate", 0),
            "cr": b.get("correction_rate", 0),
            "events": b.get("total_events", 0),
        })

    # Latest baseline
    latest = baselines[-1] if baselines else {}

    # 2. Events by layer
    events = get_events(days=7)
    layer_counts = Counter(e.get("layer", "UNKNOWN") for e in events)
    severity_counts = Counter(e.get("severity", "INFO") for e in events)
    status_counts = Counter(e.get("status", "unknown") for e in events)

    # Events per day
    daily_events = Counter()
    for e in events:
        day = e.get("ts", "")[:10]
        if day:
            daily_events[day] += 1

    # 3. Recent events (last 20)
    recent = events[-20:] if events else []
    recent_display = []
    for e in recent:
        recent_display.append({
            "ts": e.get("ts"),
            "layer": e.get("layer"),
            "event": e.get("event"),
            "status": e.get("status"),
            "severity": e.get("severity"),
        })

    # 4. Strategies
    strategies = get_strategies()
    recent_strategies = strategies[-5:] if strategies else []

    # 5. Execution log
    exec_log = get_execution_log()
    exec_states = Counter(e.get("terminal_state", "UNKNOWN") for e in exec_log)

    # 6. Sensor state
    sensor = load_json(EVENTS_DIR / "sensor_state.json")
    sensor_summary = {
        "file_watches": len(sensor.get("file_mtimes", {})),
        "running_procs": len(sensor.get("running_procs", {})),
        "cooldowns_active": len(sensor.get("cooldowns", {})),
        "network_probes": len(sensor.get("network_state", {})),
    }

    dashboard = {
        "generated_at": now.isoformat(),
        "overview": {
            "evolution_score": latest.get("evolution_score", 0),
            "grade": latest.get("grade", "unknown"),
            "tsr": latest.get("tool_success_rate", 0),
            "correction_rate": latest.get("correction_rate", 0),
            "total_events_24h": latest.get("total_events", 0),
            "severity": dict(latest.get("severity_counts", {})),
        },
        "timeline": timeline,
        "events": {
            "by_layer": dict(layer_counts),
            "by_severity": dict(severity_counts),
            "by_status": dict(status_counts),
            "daily": dict(sorted(daily_events.items())),
            "recent": recent_display,
        },
        "sensors": sensor_summary,
        "execution": {
            "terminal_states": dict(exec_states),
            "total": len(exec_log),
        },
        "strategies": [
            {"date": s.get("date"), "rule": s.get("rule"), "priority": s.get("priority"), "content": s.get("content")}
            for s in recent_strategies
        ],
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Dashboard data → {OUT}")
    print(f"   Score: {dashboard['overview']['evolution_score']} ({dashboard['overview']['grade']})")
    print(f"   TSR: {dashboard['overview']['tsr']*100:.0f}% | CR: {dashboard['overview']['correction_rate']*100:.0f}%")
    print(f"   Events (7d): {len(events)} | Layers: {dict(layer_counts)}")


if __name__ == "__main__":
    build_dashboard()
