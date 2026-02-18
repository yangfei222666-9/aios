# core/lifecycle.py - 教训生命周期自动推进
# draft → verified: 首次 retest PASS
# verified → hardened: 命中 >= 3 次且 retest 连续 PASS >= 2
# hardened → deprecated: 手动标记
import json, time
from pathlib import Path

DATA = Path(__file__).parent.parent / "data"
EVENTS = DATA / "events.jsonl"
RESULTS = DATA / "retest_results.jsonl"

def _count_hits(error_sig: str) -> int:
    """统计某 sig 在 events 中被命中的次数"""
    if not EVENTS.exists():
        return 0
    count = 0
    for line in EVENTS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
        except Exception:
            continue
        if ev.get("error_sig") == error_sig and ev.get("tips_count", 0) > 0:
            count += 1
    return count

def _retest_pass_streak(retest_id: str) -> int:
    """统计某 retest_id 最近连续 PASS 次数"""
    if not RESULTS.exists() or not retest_id:
        return 0
    results = []
    for line in RESULTS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("test") == retest_id:
            results.append(r.get("ok", False))
    # 从最后往前数连续 PASS
    streak = 0
    for ok in reversed(results):
        if ok:
            streak += 1
        else:
            break
    return streak

def auto_promote(lessons: list) -> list:
    """自动推进教训状态，返回变更列表"""
    changes = []
    for l in lessons:
        status = l.get("status", "draft")
        sig = l.get("error_sig", "")
        retest_id = l.get("retest_id", "")
        
        if status == "deprecated" or l.get("dup_of"):
            continue
        
        if status == "draft":
            streak = _retest_pass_streak(retest_id)
            if streak >= 1:
                l["status"] = "verified"
                l["verified_ts"] = int(time.time())
                changes.append({"id": l.get("id"), "from": "draft", "to": "verified", "reason": f"retest {retest_id} PASS"})
        
        elif status == "verified":
            hits = _count_hits(sig)
            streak = _retest_pass_streak(retest_id)
            if hits >= 3 and streak >= 2:
                l["status"] = "hardened"
                l["hardened_ts"] = int(time.time())
                changes.append({"id": l.get("id"), "from": "verified", "to": "hardened", "reason": f"hits={hits} streak={streak}"})
    
    return changes
