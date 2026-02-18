# core/lessons.py - 教训库 (v1.0 稳定 API, JSONL)
import json, time, uuid
from pathlib import Path
from core.version import MODULE_VERSION, SCHEMA_VERSION

DATA = Path(__file__).parent.parent / "data"
DATA.mkdir(exist_ok=True)
LESSONS = DATA / "lessons.jsonl"

STATUS_PRIORITY = {"hardened": 0, "verified": 1, "draft": 2, "deprecated": 9}

def add_lesson(error_sig: str, title: str, solution: str, tags: list = None,
               sig_loose: str = None, symptom: str = "", cause: str = "",
               fix_steps: str = "", retest_id: str = "", rollback: str = ""):
    rec = {
        "schema_version": SCHEMA_VERSION,
        "module_version": MODULE_VERSION,
        "id": uuid.uuid4().hex[:8],
        "error_sig": error_sig,
        "sig_loose": sig_loose or "",
        "title": title,
        "solution": solution,
        "tags": tags or [],
        "status": "draft",
        "dup_of": None,
        "symptom": symptom,
        "cause": cause,
        "fix_steps": fix_steps,
        "retest_id": retest_id,
        "rollback": rollback,
        "ts": int(time.time()),
    }
    with LESSONS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec

def _load_all() -> list:
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

def _active(lessons: list) -> list:
    active = [l for l in lessons if l.get("status") != "deprecated" and not l.get("dup_of")]
    active.sort(key=lambda l: STATUS_PRIORITY.get(l.get("status", "draft"), 5))
    return active

# === v1.0 STABLE API ===

def find(sig_strict: str, sig_loose: str = None, limit: int = 3) -> list:
    """双层匹配：先 strict，没有再 loose。返回 tips[]"""
    all_l = _load_all()
    
    strict = _active([l for l in all_l if l.get("error_sig") == sig_strict])
    if strict:
        return strict[-limit:]
    
    if sig_loose:
        loose = _active([l for l in all_l if l.get("sig_loose") == sig_loose])
        if loose:
            for l in loose:
                l["_match"] = "loose"
            return loose[-limit:]
    
    return []

# backward compat
find_lessons = find

def all_lessons() -> list:
    return _load_all()

def active_lessons() -> list:
    return _active(_load_all())

def update_status(lesson_id: str, status: str) -> bool:
    all_l = _load_all()
    updated = False
    for l in all_l:
        if l.get("id") == lesson_id:
            l["status"] = status
            updated = True
            break
    if updated:
        _save_all(all_l)
    return updated

def mark_dup(lesson_id: str, dup_of: str):
    all_l = _load_all()
    for l in all_l:
        if l.get("id") == lesson_id:
            l["dup_of"] = dup_of
            l["status"] = "deprecated"
            break
    _save_all(all_l)

def _save_all(lessons: list):
    with LESSONS.open("w", encoding="utf-8") as f:
        for l in lessons:
            f.write(json.dumps(l, ensure_ascii=False) + "\n")
