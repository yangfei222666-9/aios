# aios/plugins/gateway/collector.py - 采集 gateway session 的 tool 事件
"""
从 OpenClaw session 日志提取 tool 调用，写入 events.jsonl。
支持两种模式：
  1. live: 实时记录（bridge 调用）
  2. batch: 从 session 日志批量导入
"""
import json, time, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from core.engine import log_tool_event, log_event, append_jsonl, load_events

# 需要追踪的 tool 名单
TRACKED_TOOLS = {
    "web_fetch", "web_search", "exec", "read", "write", "edit",
    "browser", "image", "tts", "message", "cron",
}


def record_tool(name: str, ok: bool, ms: int, err: str = None, meta: dict = None):
    """实时记录一次 tool 调用"""
    if name not in TRACKED_TOOLS:
        return None
    return log_tool_event(name=name, ok=ok, ms=ms, err=err, meta=meta)


def record_session_event(event_type: str, summary: str, data: dict = None):
    """记录 session 级事件（对话开始/结束/错误）"""
    return log_event(event_type, "gateway.session", summary, data)


def batch_import(session_log: list) -> dict:
    """
    从 session 历史批量导入 tool 事件。
    session_log: [{role, content, tool_calls?, ...}]
    """
    imported = 0
    for msg in session_log:
        if msg.get("role") != "assistant":
            continue
        tool_calls = msg.get("tool_calls", [])
        for tc in tool_calls:
            name = tc.get("function", {}).get("name", tc.get("name", ""))
            if name not in TRACKED_TOOLS:
                continue
            # 从 tool response 推断 ok/err
            result = tc.get("result", "")
            ok = "error" not in str(result).lower()[:200]
            log_tool_event(name=name, ok=ok, ms=0, meta={"source": "batch_import"})
            imported += 1

    return {"imported": imported}


def daily_summary() -> dict:
    """今日 tool 使用摘要"""
    events = load_events(days=1, event_type="tool")
    by_tool = {}
    for e in events:
        data = e.get("data", {})
        name = data.get("name", "?")
        if name not in by_tool:
            by_tool[name] = {"calls": 0, "ok": 0, "fail": 0, "total_ms": 0}
        by_tool[name]["calls"] += 1
        if data.get("ok", True):
            by_tool[name]["ok"] += 1
        else:
            by_tool[name]["fail"] += 1
        by_tool[name]["total_ms"] += data.get("ms", 0)

    for name, stats in by_tool.items():
        if stats["calls"] > 0:
            stats["avg_ms"] = round(stats["total_ms"] / stats["calls"])

    return {
        "date": time.strftime("%Y-%m-%d"),
        "tools": by_tool,
        "total_calls": sum(s["calls"] for s in by_tool.values()),
    }


if __name__ == "__main__":
    print(json.dumps(daily_summary(), ensure_ascii=False, indent=2))
