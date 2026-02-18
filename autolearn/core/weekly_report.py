# core/weekly_report.py - 周报生成器 (v1.0 稳定 API)
import json, time, sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.version import MODULE_VERSION, SCHEMA_VERSION

DATA = Path(__file__).parent.parent / "data"
EVENTS = DATA / "events.jsonl"
LESSONS = DATA / "lessons.jsonl"
RESULTS = DATA / "retest_results.jsonl"
REPORTS = Path(__file__).parent.parent / "reports"

def _load_jsonl(path: Path, days: int = 7) -> list:
    if not path.exists():
        return []
    cutoff = time.time() - days * 86400
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            if obj.get("ts", 0) >= cutoff:
                out.append(obj)
        except Exception:
            continue
    return out

def _load_all_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out

# === v1.0 STABLE API ===

def generate(days: int = 7) -> str:
    """生成周报 markdown"""
    events = _load_jsonl(EVENTS, days)
    lessons = _load_all_jsonl(LESSONS)
    results = _load_jsonl(RESULTS, days)
    
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"# Autolearn Report ({days}d)", f"Generated: {ts}", f"Module: {MODULE_VERSION} | Schema: {SCHEMA_VERSION}\n"]
    
    # --- Overview ---
    total_events = len(events)
    failures = [e for e in events if e.get("ok") is False]
    successes = [e for e in events if e.get("ok") is True]
    lines.append(f"## Overview")
    lines.append(f"- Events: {total_events} total ({len(successes)} ok, {len(failures)} fail)")
    lines.append(f"- Lessons: {len(lessons)} total")
    
    status_counts = Counter(l.get("status", "unknown") for l in lessons)
    lines.append(f"- Status: {dict(status_counts)}")
    lines.append("")
    
    # --- Top error_sig ---
    sig_counts = Counter(e.get("error_sig") for e in failures if e.get("error_sig"))
    if sig_counts:
        lines.append("## Top Error Signatures")
        for sig, count in sig_counts.most_common(10):
            matching = [l for l in lessons if l.get("error_sig") == sig]
            title = matching[-1].get("title", "unknown") if matching else "NO LESSON"
            status = matching[-1].get("status", "?") if matching else "missing"
            lines.append(f"- `{sig}` x{count} — {title} [{status}]")
        lines.append("")
    
    # --- Category breakdown ---
    cat_counts = Counter()
    for e in failures:
        sig = e.get("error_sig")
        for l in lessons:
            if l.get("error_sig") == sig:
                for tag in l.get("tags", []):
                    cat_counts[tag] += 1
                break
    if cat_counts:
        lines.append("## Category Breakdown (failures)")
        for cat, count in cat_counts.most_common(10):
            lines.append(f"- {cat}: {count}")
        lines.append("")
    
    # --- Unhardened high-freq ---
    unhardened = [l for l in lessons if l.get("status") not in ("hardened", "deprecated") and not l.get("dup_of")]
    if unhardened:
        lines.append("## Unhardened Lessons (need attention)")
        for l in unhardened:
            sig = l.get("error_sig", "?")
            hits = sig_counts.get(sig, 0)
            if hits > 0:
                lines.append(f"- [{l.get('status')}] {l.get('title')} (hit {hits}x)")
        lines.append("")
    
    # --- Retest results ---
    if results:
        lines.append("## Retest Summary")
        test_results = Counter()
        test_fails = Counter()
        for r in results:
            name = r.get("test", "?")
            if r.get("ok"):
                test_results[name] += 1
            else:
                test_fails[name] += 1
        
        for name in sorted(set(list(test_results.keys()) + list(test_fails.keys()))):
            p = test_results.get(name, 0)
            f = test_fails.get(name, 0)
            lines.append(f"- {name}: {p} pass / {f} fail")
        lines.append("")
    
    # --- Environment changes ---
    envs = []
    for e in events:
        env = e.get("env")
        if env:
            envs.append(env)
    if envs:
        lines.append("## Environment Snapshot")
        latest = envs[-1]
        for k, v in latest.items():
            lines.append(f"- {k}: {v}")
        # Check for changes
        if len(envs) > 1:
            first = envs[0]
            changes = {k: (first.get(k), latest.get(k)) for k in set(list(first.keys()) + list(latest.keys())) if first.get(k) != latest.get(k)}
            if changes:
                lines.append("\nEnvironment changes detected:")
                for k, (old, new) in changes.items():
                    lines.append(f"- {k}: {old} → {new}")
        lines.append("")
    
    return "\n".join(lines)

def save_report(days: int = 7):
    REPORTS.mkdir(exist_ok=True)
    report = generate(days)
    date_str = time.strftime("%Y-%m-%d")
    path = REPORTS / f"report_{date_str}.md"
    path.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nSaved to {path}")
    return path

# backward compat
generate_report = generate

if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    save_report(days)
