# core/proposals.py - 自动提案机制 (v1.0 稳定 API)
import json, time, sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.version import MODULE_VERSION, SCHEMA_VERSION

DATA = Path(__file__).parent.parent / "data"
EVENTS = DATA / "events.jsonl"
LESSONS = DATA / "lessons.jsonl"
PROPOSALS = Path(__file__).parent.parent / "proposals.md"

def _load_events(hours: int = 168) -> list:
    if not EVENTS.exists():
        return []
    cutoff = time.time() - hours * 3600
    out = []
    for line in EVENTS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
            if ev.get("ts", 0) >= cutoff:
                out.append(ev)
        except Exception:
            continue
    return out

def _load_lessons() -> list:
    if not LESSONS.exists():
        return []
    out = []
    for line in LESSONS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out

# === v1.0 STABLE API ===

def generate(window_hours: int = 72) -> list:
    """生成提案列表"""
    proposals = []
    events = _load_events(window_hours)
    lessons = _load_lessons()
    
    # 1. 高频 error_sig (7天内 >= 3次)
    sig_counts = Counter(ev.get("error_sig") for ev in events if ev.get("ok") is False and ev.get("error_sig"))
    for sig, count in sig_counts.most_common(10):
        if count >= 3:
            matching = [l for l in lessons if l.get("error_sig") == sig]
            if matching and matching[-1].get("status") == "verified":
                proposals.append({
                    "type": "promote",
                    "sig": sig,
                    "count": count,
                    "suggestion": f"Promote lesson for {sig} from verified → hardened (hit {count}x in 7d)",
                })
            elif not matching:
                proposals.append({
                    "type": "new_lesson",
                    "sig": sig,
                    "count": count,
                    "suggestion": f"No lesson for frequent error {sig} ({count}x in 7d) — create one",
                })
    
    # 2. 类别爆发 (window 内某类别 >= 5次)
    recent = events  # already filtered by window_hours
    tag_counts = Counter()
    for ev in recent:
        if ev.get("ok") is False:
            for l in lessons:
                if l.get("error_sig") == ev.get("error_sig"):
                    for tag in l.get("tags", []):
                        tag_counts[tag] += 1
    for tag, count in tag_counts.most_common(5):
        if count >= 5:
            proposals.append({
                "type": "new_smoke",
                "tag": tag,
                "count": count,
                "suggestion": f"Category '{tag}' burst ({count}x in 3d) — add smoke test",
            })
    
    # 3. 教训有命中但无 retest
    for l in lessons:
        if l.get("status") != "deprecated" and not l.get("dup_of"):
            if not l.get("retest_id") and l.get("error_sig") in sig_counts:
                proposals.append({
                    "type": "add_retest",
                    "id": l.get("id"),
                    "title": l.get("title"),
                    "suggestion": f"Lesson '{l.get('title')}' has hits but no retest_id — add one",
                })
    
    return proposals

def write_proposals(window_hours: int = 72):
    proposals = generate(window_hours)
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    
    lines = [f"# Autolearn Proposals", f"Generated: {ts}", f"Module: {MODULE_VERSION} | Schema: {SCHEMA_VERSION}\n"]
    
    if not proposals:
        lines.append("No proposals at this time. System is healthy.\n")
    else:
        for i, p in enumerate(proposals, 1):
            lines.append(f"## {i}. [{p['type'].upper()}] {p['suggestion']}")
            for k, v in p.items():
                if k not in ("type", "suggestion"):
                    lines.append(f"- {k}: {v}")
            lines.append("")
    
    PROPOSALS.write_text("\n".join(lines), encoding="utf-8")
    return proposals

# backward compat
generate_proposals = generate

if __name__ == "__main__":
    props = write_proposals()
    print(f"Generated {len(props)} proposals")
