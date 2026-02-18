# aios/scripts/log_event.py - 追加事件到 events.jsonl（唯一事实来源）
"""
用法:
  python log_event.py <type> <source> <summary> [--data '{"key":"val"}']

事件类型:
  match       - 匹配事件
  correction  - 用户纠正
  confirm     - 用户确认
  error       - 错误事件
  task        - 任务执行
  lesson      - 教训沉淀
  suggestion  - 系统建议
"""
import argparse, json, time, sys
from pathlib import Path

AIOS_ROOT = Path(__file__).resolve().parent.parent

# 从 config 加载路径
try:
    sys.path.insert(0, str(AIOS_ROOT))
    from scripts.config_loader import get_path
    _events_path = get_path("events")
    EVENTS_FILE = _events_path if _events_path and str(_events_path) != "." else AIOS_ROOT / "events" / "events.jsonl"
except Exception:
    EVENTS_FILE = AIOS_ROOT / "events" / "events.jsonl"


def log_event(event_type: str, source: str, summary: str, data: dict = None) -> dict:
    """追加一条事件"""
    EVENTS_FILE.parent.mkdir(exist_ok=True)
    
    event = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        "ts": int(time.time()),
        "type": event_type,
        "source": source,
        "summary": summary,
    }
    if data:
        event["data"] = data
    
    with EVENTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    
    return event


def load_events(days: int = 30, event_type: str = None) -> list:
    """加载事件"""
    if not EVENTS_FILE.exists():
        return []
    cutoff = time.time() - days * 86400
    out = []
    for line in EVENTS_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
            if ev.get("ts", 0) < cutoff:
                continue
            if event_type and ev.get("type") != event_type:
                continue
            out.append(ev)
        except Exception:
            continue
    return out


def count_by_type(days: int = 30) -> dict:
    """按类型统计事件数"""
    events = load_events(days)
    counts = {}
    for ev in events:
        t = ev.get("type", "unknown")
        counts[t] = counts.get(t, 0) + 1
    return counts


if __name__ == "__main__":
    p = argparse.ArgumentParser(prog="log_event")
    p.add_argument("type", help="事件类型")
    p.add_argument("source", help="来源模块")
    p.add_argument("summary", help="摘要")
    p.add_argument("--data", default=None, help="附加数据 JSON")
    args = p.parse_args()
    
    data = json.loads(args.data) if args.data else None
    ev = log_event(args.type, args.source, args.summary, data)
    print(json.dumps(ev, ensure_ascii=False))
