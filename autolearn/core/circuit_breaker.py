# core/circuit_breaker.py - 熔断器 (v1.0 稳定 API)
import json, time
from pathlib import Path
from core.version import MODULE_VERSION, SCHEMA_VERSION

DATA = Path(__file__).parent.parent / "data"
EVENTS = DATA / "events.jsonl"
BREAKER_STATE = DATA / "breaker_state.json"

WINDOW_SEC = 1800   # 30 min
THRESHOLD = 3       # 同 sig >= 3 次触发
COOLDOWN_SEC = 3600 # 熔断 1 小时后自动恢复

def _load_state() -> dict:
    if BREAKER_STATE.exists():
        return json.loads(BREAKER_STATE.read_text(encoding="utf-8"))
    return {"tripped": {}}

def _save_state(state: dict):
    BREAKER_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

# === v1.0 STABLE API ===

def allow(sig_strict: str) -> bool:
    """检查是否允许执行。True=允许, False=已熔断"""
    state = _load_state()
    trip = state["tripped"].get(sig_strict)
    if not trip:
        return True
    if time.time() - trip["ts"] > COOLDOWN_SEC:
        del state["tripped"][sig_strict]
        _save_state(state)
        return True
    return False

def check_and_trip(sig_strict: str) -> bool:
    """检查并触发熔断。返回 True=已熔断"""
    if not allow(sig_strict):
        return True
    
    if not EVENTS.exists():
        return False
    
    now = time.time()
    cutoff = now - WINDOW_SEC
    count = 0
    
    for line in EVENTS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
        except Exception:
            continue
        if ev.get("error_sig") == sig_strict and ev.get("ok") is False and ev.get("ts", 0) >= cutoff:
            count += 1
    
    if count >= THRESHOLD:
        state = _load_state()
        state["tripped"][sig_strict] = {
            "ts": int(now),
            "count": count,
            "msg": f"Tripped: {sig_strict} hit {count}x in {WINDOW_SEC}s"
        }
        _save_state(state)
        return True
    
    return False

def get_checklist() -> str:
    return """=== CIRCUIT BREAKER TRIPPED ===
1. Stop retrying the same operation
2. Check recent events.jsonl for the error pattern
3. Review lessons.jsonl for known fixes
4. If no fix exists, escalate to manual investigation
5. Run: python core/retest.py smoke
6. Reset breaker: delete data/breaker_state.json
==============================="""

# backward compat
is_tripped = lambda sig: not allow(sig)
