"""
experience_feedback_hook.py - 经验回流入口 v0.1

Phase B 的最小底座。
当前只做一件事：从 agent_execution_record.jsonl 读取样本，
提炼经验，写回可被调度系统消费的格式。

v0.1 是空壳预留，明天拿到第一批真实样本后立刻填充逻辑。
"""

import json
import os
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))

RECORD_FILE = os.path.join(os.path.dirname(__file__), "agent_execution_record.jsonl")
FEEDBACK_FILE = os.path.join(os.path.dirname(__file__), "experience_feedback.jsonl")


def load_records(since_hours: int = 24) -> list[dict]:
    """读取最近 N 小时的执行记录"""
    records = []
    if not os.path.exists(RECORD_FILE):
        return records
    cutoff = datetime.now(CST) - timedelta(hours=since_hours)
    with open(RECORD_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                start = rec.get("start_time", "")
                if start:
                    t = datetime.fromisoformat(start)
                    if t >= cutoff:
                        records.append(rec)
            except (json.JSONDecodeError, ValueError):
                continue
    return records


def extract_experience(records: list[dict]) -> list[dict]:
    """从执行记录中提炼经验（Phase B 核心逻辑，待填充）"""
    experiences = []
    for rec in records:
        outcome = rec.get("outcome", "unknown")
        if outcome == "failed":
            # v0.1: 只记录失败样本，后续版本做根因分析
            experiences.append({
                "type": "failure_observation",
                "agent_name": rec.get("agent_name", ""),
                "trigger_type": rec.get("trigger_type", ""),
                "reason": rec.get("reason", ""),
                "duration_ms": rec.get("duration_ms", 0),
                "timestamp": datetime.now(CST).isoformat(),
                "action": None,  # Phase B 填充：timeout_adjust / deprioritize / retry_with_different_params
            })
    return experiences


def write_feedback(experiences: list[dict]):
    """写回经验到反馈文件"""
    if not experiences:
        return 0
    with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
        for exp in experiences:
            f.write(json.dumps(exp, ensure_ascii=False) + "\n")
    return len(experiences)


def run():
    """主入口"""
    records = load_records(since_hours=24)
    if not records:
        print("[EXPERIENCE] No recent execution records found.")
        return

    print(f"[EXPERIENCE] Found {len(records)} records in last 24h")

    failed = [r for r in records if r.get("outcome") == "failed"]
    succeeded = [r for r in records if r.get("outcome") == "success"]
    partial = [r for r in records if r.get("outcome") == "partial"]

    print(f"  Success: {len(succeeded)} | Partial: {len(partial)} | Failed: {len(failed)}")

    experiences = extract_experience(records)
    if experiences:
        count = write_feedback(experiences)
        print(f"[EXPERIENCE] Wrote {count} experience entries to feedback file")
    else:
        print("[EXPERIENCE] No actionable experiences extracted (all good!)")


if __name__ == "__main__":
    run()
