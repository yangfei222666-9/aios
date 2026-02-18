# core/logger.py - 事件日志 (v1.0 稳定 API)
import json, time
from pathlib import Path
from core.version import MODULE_VERSION, SCHEMA_VERSION

DATA = Path(__file__).parent.parent / "data"
DATA.mkdir(exist_ok=True)
EVENTS = DATA / "events.jsonl"

def log_event(**kw):
    kw["ts"] = int(time.time())
    kw["schema_version"] = SCHEMA_VERSION
    kw["module_version"] = MODULE_VERSION
    with EVENTS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(kw, ensure_ascii=False) + "\n")
