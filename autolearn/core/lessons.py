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

def _jaccard(set_a: set, set_b: set) -> float:
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)

def find(sig_strict: str, sig_loose: str = None, keywords: list = None,
         limit: int = 3, fuzzy_threshold: float = 0.3) -> list:
    """三层匹配 + 可解释性。
    
    Layer 1: strict sig 精确匹配
    Layer 2: loose sig 精确匹配
    Layer 3: 关键词 Jaccard 模糊匹配 (≥ fuzzy_threshold)
    
    返回 tips[]，每条带:
      _match_type: "strict" | "loose" | "fuzzy"
      _similarity_score: float (strict=1.0, loose=0.8, fuzzy=实际 Jaccard)
      _matched_keywords: list (命中的关键词)
      _alternatives: list (其他候选，仅 fuzzy 模式)
    """
    from core.errors import extract_keywords
    all_l = _load_all()
    
    # Layer 1: strict
    strict = _active([l for l in all_l if l.get("error_sig") == sig_strict])
    if strict:
        for l in strict:
            l["_match_type"] = "strict"
            l["_similarity_score"] = 1.0
            l["_matched_keywords"] = keywords or []
        return strict[-limit:]
    
    # Layer 2: loose
    if sig_loose:
        loose = _active([l for l in all_l if l.get("sig_loose") == sig_loose])
        if loose:
            for l in loose:
                l["_match_type"] = "loose"
                l["_similarity_score"] = 0.8
                l["_matched_keywords"] = keywords or []
            return loose[-limit:]
    
    # Layer 3: fuzzy (关键词 Jaccard)
    if not keywords:
        return []
    
    query_kw = set(keywords)
    scored = []
    for l in _active(all_l):
        # 从教训的 error_sig 对应的原始错误提取关键词不可行（sig 是 hash）
        # 用教训的 title + solution + symptom + cause 提取关键词做匹配
        text_parts = " ".join([
            l.get("title", ""), l.get("solution", ""),
            l.get("symptom", ""), l.get("cause", ""),
        ])
        lesson_kw = set(extract_keywords(text_parts))
        if not lesson_kw:
            continue
        score = _jaccard(query_kw, lesson_kw)
        if score >= fuzzy_threshold:
            matched = sorted(query_kw & lesson_kw)
            scored.append((score, matched, l))
    
    if not scored:
        return []
    
    scored.sort(key=lambda x: x[0], reverse=True)
    
    # 主结果
    results = []
    for score, matched, l in scored[:limit]:
        l["_match_type"] = "fuzzy"
        l["_similarity_score"] = round(score, 4)
        l["_matched_keywords"] = matched
        results.append(l)
    
    # alternatives: 超出 limit 的候选
    if len(scored) > limit:
        alts = []
        for score, matched, l in scored[limit:limit + 5]:
            alts.append({
                "id": l.get("id"),
                "title": l.get("title"),
                "similarity_score": round(score, 4),
                "matched_keywords": matched,
            })
        if alts:
            results[0]["_alternatives"] = alts
    
    return results

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
