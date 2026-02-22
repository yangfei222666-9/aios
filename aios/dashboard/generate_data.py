"""AIOS Dashboard - 数据生成器
读取 AIOS 各数据源，输出 dashboard_data.json 供前端渲染
"""
import json, os, sys, io
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

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
    # Main events (v0.2 格式，已有 layer)
    for e in load_jsonl(EVENTS_DIR / "events.jsonl"):
        e["ts"] = normalize_ts(e.get("ts"))
        if e["ts"] >= cutoff:
            all_events.append(e)
    # Queue events (EventBus 格式，需要映射)
    queue_dir = EVENTS_DIR / "queue"
    if queue_dir.exists():
        for f in sorted(queue_dir.glob("*.jsonl")):
            for e in load_jsonl(f):
                e["ts"] = normalize_ts(e.get("ts"))
                if e["ts"] < cutoff:
                    continue
                # 映射 EventBus topic → AIOS layer
                topic = e.get("topic", "")
                source = e.get("source", "")
                if "layer" not in e:
                    if "sensor.system" in topic or "sensor.network" in topic:
                        e["layer"] = "KERNEL"
                    elif "sensor.file" in topic:
                        e["layer"] = "MEM"
                    elif "sensor.process" in topic:
                        e["layer"] = "KERNEL"
                    elif "dispatch" in topic or "action" in topic:
                        e["layer"] = "TOOL"
                    else:
                        e["layer"] = "KERNEL"  # 感知事件默认归 KERNEL
                if "event" not in e:
                    e["event"] = topic or source or "queue_event"
                if "status" not in e:
                    e["status"] = "ok"
                if "severity" not in e:
                    e["severity"] = "INFO"
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


def get_reactor_data():
    """Reactor v0.6 数据"""
    DATA = BASE / "data"
    reactions = load_jsonl(DATA / "reactions.jsonl")
    verify = load_jsonl(DATA / "verify_log.jsonl")
    pb_stats = load_json(DATA / "playbook_stats.json", {})
    fuse = load_json(DATA / "reactor_fuse.json", {"tripped": False, "failures": []})

    total = len(reactions)
    success = sum(1 for r in reactions if r.get("status") == "success")
    pending = sum(1 for r in reactions if r.get("status") == "pending_confirm")
    failed = total - success - pending

    v_total = len(verify)
    v_passed = sum(1 for v in verify if v.get("passed"))

    playbooks = []
    for pid, s in pb_stats.items():
        t = s.get("total", 0)
        rate = s.get("success", 0) / t * 100 if t > 0 else 0
        playbooks.append({"id": pid, "total": t, "success": s.get("success", 0), "fail": s.get("fail", 0), "rate": round(rate, 0)})

    return {
        "total": total,
        "success": success,
        "pending": pending,
        "failed": failed,
        "auto_exec_rate": round(success / max(success + pending, 1) * 100, 0),
        "verify_total": v_total,
        "verify_passed": v_passed,
        "verify_rate": round(v_passed / max(v_total, 1) * 100, 0),
        "fuse_tripped": fuse.get("tripped", False),
        "fuse_failures": len(fuse.get("failures", [])),
        "playbooks": playbooks,
        "recent": [
            {"ts": (r.get("ts") or "")[:16], "pb": r.get("playbook_id", "?"), "status": r.get("status", "?"), "decision_id": (r.get("decision_id") or "")[:8]}
            for r in reactions[-8:]
        ]
    }


def get_evolution_v2_data():
    """Evolution v2 数据"""
    DATA = BASE / "data"
    history = load_jsonl(DATA / "evolution_history.jsonl")
    if not history:
        return {"v2_score": 0, "grade": "unknown", "base": 0, "reactor": 0, "detail": {}, "trend": []}
    latest = history[-1]
    trend = [
        {"ts": (h.get("ts") or "")[:16], "v2": h.get("evolution_v2", 0), "base": h.get("base_score", 0), "reactor": h.get("reactor_score", 0), "grade": h.get("grade", "?")}
        for h in history[-20:]
    ]
    return {
        "v2_score": latest.get("evolution_v2", 0),
        "grade": latest.get("grade", "unknown"),
        "base": latest.get("base_score", 0),
        "reactor": latest.get("reactor_score", 0),
        "detail": latest.get("detail", {}),
        "trend": trend
    }


def get_pipeline_data():
    """Pipeline 运行历史"""
    DATA = BASE / "data"
    runs = load_jsonl(DATA / "pipeline_runs.jsonl")
    recent = runs[-10:] if runs else []
    return {
        "total_runs": len(runs),
        "recent": [
            {
                "ts": (r.get("ts") or "")[:16],
                "ms": r.get("total_ms", 0),
                "errors": len(r.get("errors", [])),
                "grade": r.get("stages", {}).get("evolution", {}).get("result", {}).get("grade", "?")
            }
            for r in recent
        ]
    }


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

    # 7. Tasks (tracker)
    tasks_file = BASE / "data" / "tasks.jsonl"
    tasks = load_jsonl(tasks_file) if tasks_file.exists() else []
    task_summary = {"total": 0, "todo": 0, "in_progress": 0, "blocked": 0, "done": 0, "overdue": 0, "recent": []}
    now_iso = now.isoformat()
    for t in tasks:
        task_summary["total"] += 1
        s = t.get("status", "TODO").upper()
        if s == "TODO":
            task_summary["todo"] += 1
        elif s == "IN_PROGRESS":
            task_summary["in_progress"] += 1
        elif s == "BLOCKED":
            task_summary["blocked"] += 1
        elif s == "DONE":
            task_summary["done"] += 1
        dl = t.get("deadline", "")
        if dl and dl < now_iso and s not in ("DONE",):
            task_summary["overdue"] += 1
    task_summary["recent"] = [
        {"id": t.get("id", "")[:8], "title": t.get("title", "")[:40], "status": t.get("status", ""), "priority": t.get("priority", ""), "deadline": (t.get("deadline") or "")[:10]}
        for t in tasks if t.get("status", "").upper() != "DONE"
    ][-8:]

    # 8. Budget
    budget_config_file = BASE / "data" / "budget_config.json"
    token_usage_file = BASE / "data" / "token_usage.jsonl"
    heartbeat_file = BASE / "data" / "heartbeat_time.jsonl"
    budget_config = load_json(budget_config_file, {"daily_token_budget": 150000, "weekly_token_budget": 800000})
    token_records = load_jsonl(token_usage_file) if token_usage_file.exists() else []
    heartbeat_records = load_jsonl(heartbeat_file) if heartbeat_file.exists() else []
    today_str = now.strftime("%Y-%m-%d")
    daily_tokens = sum(r.get("input_tokens", 0) + r.get("output_tokens", 0) for r in token_records if (r.get("ts") or "").startswith(today_str))
    weekly_tokens = sum(r.get("input_tokens", 0) + r.get("output_tokens", 0) for r in token_records)
    hb_times = [r.get("seconds", 0) for r in heartbeat_records[-20:]]
    budget_summary = {
        "daily_used": daily_tokens,
        "daily_budget": budget_config.get("daily_token_budget", 150000),
        "daily_pct": round(daily_tokens / max(budget_config.get("daily_token_budget", 150000), 1) * 100, 1),
        "weekly_used": weekly_tokens,
        "weekly_budget": budget_config.get("weekly_token_budget", 800000),
        "weekly_pct": round(weekly_tokens / max(budget_config.get("weekly_token_budget", 800000), 1) * 100, 1),
        "heartbeat_avg": round(sum(hb_times) / len(hb_times), 1) if hb_times else 0,
        "heartbeat_count": len(heartbeat_records),
    }

    # 9. Decisions
    decisions_file = BASE / "data" / "decisions.jsonl"
    decisions = load_jsonl(decisions_file) if decisions_file.exists() else []
    dec_outcomes = Counter(d.get("outcome", "pending") for d in decisions)
    dec_total = len(decisions)
    dec_success = dec_outcomes.get("success", 0)
    dec_confs = [d.get("confidence", 0) for d in decisions if d.get("confidence")]
    decision_summary = {
        "total": dec_total,
        "success_rate": round(dec_success / max(dec_total, 1) * 100, 1),
        "avg_confidence": round(sum(dec_confs) / len(dec_confs) * 100, 1) if dec_confs else 0,
        "outcomes": dict(dec_outcomes),
        "recent": [
            {"ts": (d.get("ts") or "")[:16], "context": (d.get("context") or "")[:30], "chosen": (d.get("chosen") or "")[:30], "confidence": d.get("confidence", 0), "outcome": d.get("outcome", "pending")}
            for d in decisions[-5:]
        ],
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
        "tasks": task_summary,
        "budget": budget_summary,
        "decisions": decision_summary,
        "reactor": get_reactor_data(),
        "evolution_v2": get_evolution_v2_data(),
        "pipeline": get_pipeline_data(),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Dashboard data → {OUT}")
    print(f"   Score: {dashboard['overview']['evolution_score']} ({dashboard['overview']['grade']})")
    print(f"   TSR: {dashboard['overview']['tsr']*100:.0f}% | CR: {dashboard['overview']['correction_rate']*100:.0f}%")
    print(f"   Events (7d): {len(events)} | Layers: {dict(layer_counts)}")


if __name__ == "__main__":
    build_dashboard()
