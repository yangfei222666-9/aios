"""
hexagram_daily_logger.py
每日 23:00 收敛一次卦象快照，写入 data/hexagram_daily.jsonl
用于 14 天 Hexagram History Review
"""

import json
import os
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "hexagram_daily.jsonl")
AGENTS_FILE = os.path.join(BASE_DIR, "agents.json")
HEXAGRAM_STATE_FILE = os.path.join(BASE_DIR, "hexagram_state.json")
GUARDRAIL_LOG_FILE = os.path.join(BASE_DIR, "guardrail_log.jsonl")

KL_TZ = timezone(timedelta(hours=8))  # Asia/Kuala_Lumpur = UTC+8


def _load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _read_jsonl(path):
    lines = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        lines.append(json.loads(line))
                    except Exception:
                        pass
    except Exception:
        pass
    return lines


def _get_global_hexagram():
    """从 hexagram_state.json 读取全局卦象"""
    state = _load_json(HEXAGRAM_STATE_FILE, {})
    return {
        "name": state.get("current_hexagram", state.get("hexagram_name", "未知")),
        "risk_level": state.get("risk_level", state.get("global_risk_level", "unknown")),
        "strategy": state.get("strategy", ""),
        "evolution_score": state.get("evolution_score", None),
    }


def _get_guardrail_summary():
    """统计今日 guardrail 触发情况"""
    today_str = datetime.now(KL_TZ).strftime("%Y-%m-%d")
    records = _read_jsonl(GUARDRAIL_LOG_FILE)
    today_records = [r for r in records if str(r.get("timestamp", "")).startswith(today_str)]
    triggered = len(today_records) > 0
    reasons = list({r.get("reason", r.get("trigger_reason", "")) for r in today_records if r.get("reason") or r.get("trigger_reason")})
    return {
        "triggered": triggered,
        "count": len(today_records),
        "reasons": reasons[:5],  # 最多 5 条
    }


def _get_agent_lifecycle_summary():
    """从 agents.json 提取 active agent 生命周期摘要"""
    agents_data = _load_json(AGENTS_FILE, {})
    agents = agents_data if isinstance(agents_data, list) else agents_data.get("agents", [])
    summary = []
    for agent in agents:
        if not isinstance(agent, dict):
            continue
        mode = agent.get("mode", "")
        enabled = agent.get("enabled", False)
        if not enabled or mode not in ("active", "shadow"):
            continue
        summary.append({
            "name": agent.get("name", ""),
            "mode": mode,
            "lifecycle": agent.get("lifecycle_stage", agent.get("stage", "")),
            "tasks_completed": agent.get("stats", {}).get("tasks_completed", 0),
            "tasks_failed": agent.get("stats", {}).get("tasks_failed", 0),
        })
    return summary[:10]  # 最多 10 个


def collect_snapshot():
    """收集当日快照数据"""
    now = datetime.now(KL_TZ)
    hexagram = _get_global_hexagram()
    guardrail = _get_guardrail_summary()
    lifecycle = _get_agent_lifecycle_summary()

    snapshot = {
        "date": now.strftime("%Y-%m-%d"),
        "timestamp": now.isoformat(),
        "global_hexagram_name": hexagram["name"],
        "global_risk_level": hexagram["risk_level"],
        "strategy": hexagram["strategy"],
        "evolution_score": hexagram["evolution_score"],
        "guardrail_triggered": guardrail["triggered"],
        "guardrail_count": guardrail["count"],
        "guardrail_reasons": guardrail["reasons"],
        "active_agent_lifecycle": lifecycle,
    }
    return snapshot


def append_snapshot(snapshot):
    """追加到 jsonl（同一天只写一次，重复运行会覆盖当天记录）"""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    today = snapshot["date"]

    # 读取现有记录，过滤掉今天的旧记录
    existing = _read_jsonl(DATA_FILE)
    existing = [r for r in existing if r.get("date") != today]
    existing.append(snapshot)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        for record in existing:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return len(existing)


def run():
    print(f"[HEXAGRAM_DAILY] 收集 {datetime.now(KL_TZ).strftime('%Y-%m-%d')} 快照...")
    snapshot = collect_snapshot()
    total = append_snapshot(snapshot)

    print(f"  卦象: {snapshot['global_hexagram_name']} | 风险: {snapshot['global_risk_level']}")
    print(f"  Guardrail: {'触发' if snapshot['guardrail_triggered'] else '未触发'} ({snapshot['guardrail_count']} 次)")
    print(f"  Active agents: {len(snapshot['active_agent_lifecycle'])} 个")
    print(f"  累计记录: {total} 天")
    print(f"  写入: {DATA_FILE}")
    return snapshot


if __name__ == "__main__":
    run()
