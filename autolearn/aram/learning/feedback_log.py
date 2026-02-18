# aram/learning/feedback_log.py - 反馈日志管理
"""
记录每次匹配结果和用户纠正，供 analyzer 和 alias_suggest 使用。
"""
import json, time
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
FEEDBACK_FILE = DATA_DIR / "feedback_log.jsonl"
LEARNED_FILE = DATA_DIR / "learned_aliases.json"


def log_match(query: str, matched_id: str, matched_title: str, score: float, match_type: str):
    """记录一次匹配（不管对错）"""
    rec = {
        "ts": int(time.time()),
        "type": "match",
        "query": query,
        "matched_id": matched_id,
        "matched_title": matched_title,
        "score": score,
        "match_type": match_type,
    }
    _append(rec)
    return rec


def log_correction(query: str, wrong_id: str, correct_id: str, correct_title: str):
    """记录一次用户纠正"""
    rec = {
        "ts": int(time.time()),
        "type": "correction",
        "query": query,
        "wrong_id": wrong_id,
        "correct_id": correct_id,
        "correct_title": correct_title,
    }
    _append(rec)

    # 自动写入 learned_aliases
    learned = load_learned()
    learned[query] = correct_id
    save_learned(learned)

    return rec


def log_confirm(query: str, matched_id: str):
    """记录一次用户确认（匹配正确）"""
    rec = {
        "ts": int(time.time()),
        "type": "confirm",
        "query": query,
        "matched_id": matched_id,
    }
    _append(rec)
    return rec


def load_feedback(days: int = 30) -> list:
    """加载最近 N 天的反馈"""
    if not FEEDBACK_FILE.exists():
        return []
    cutoff = time.time() - days * 86400
    out = []
    for line in FEEDBACK_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            if rec.get("ts", 0) >= cutoff:
                out.append(rec)
        except Exception:
            continue
    return out


def load_learned() -> dict:
    if not LEARNED_FILE.exists():
        return {}
    try:
        return json.loads(LEARNED_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_learned(aliases: dict):
    LEARNED_FILE.write_text(json.dumps(aliases, ensure_ascii=False, indent=2), encoding="utf-8")


def _append(rec: dict):
    with FEEDBACK_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
