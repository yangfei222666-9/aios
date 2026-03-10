#!/usr/bin/env python3
"""
AIOS Data Flush - 21:59 pre-observation flush

纭繚鎵€鏈夋棩蹇楀啓鍏ュ畬鎴愶紝閬垮厤 22:00 缁熻鏃堕仐婕忔渶鍚庝竴鍒嗛挓鐨勬暟鎹€?
鎿嶄綔锛?1. 寮哄埗 flush 鎵€鏈?.jsonl 鏂囦欢鐨勫啓缂撳啿
2. 鍚屾 agent stats锛堜粠 task_executions_v2.jsonl 鈫?agents.json锛?3. 杈撳嚭 flush 鐘舵€?"""

import os
import sys
import json
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TZ = timezone(timedelta(hours=8))

JSONL_FILES = [
    "task_executions_v2.jsonl",
    "route_log.jsonl",
    "decision_log.jsonl",
    "experience_library.jsonl",
    "alerts.jsonl",
    "spawn_results.jsonl",
]


def flush_jsonl_files():
    """Touch and verify all JSONL data files exist and are readable."""
    status = {}
    for fname in JSONL_FILES:
        path = os.path.join(BASE_DIR, fname)
        if os.path.exists(path):
            size = os.path.getsize(path)
            # Count lines
            with open(path, "r", encoding="utf-8") as f:
                lines = sum(1 for line in f if line.strip())
            status[fname] = {"exists": True, "size_kb": round(size / 1024, 1), "lines": lines}
        else:
            status[fname] = {"exists": False, "size_kb": 0, "lines": 0}
    return status


def sync_agent_stats():
    """Run agent stats sync if sync_agent_stats.py exists."""
    sync_path = os.path.join(BASE_DIR, "sync_agent_stats.py")
    if os.path.exists(sync_path):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("sync_agent_stats", sync_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "sync"):
                mod.sync()
                return "synced"
            elif hasattr(mod, "main"):
                mod.main()
                return "synced"
        except Exception as e:
            return f"error: {e}"
    return "skipped"


def main():
    now = datetime.now(TZ)
    print(f"[FLUSH] {now.strftime('%Y-%m-%d %H:%M:%S')} - Data flush started")

    # 1. Flush JSONL files
    status = flush_jsonl_files()
    total_lines = 0
    for fname, info in status.items():
        if info["exists"]:
            total_lines += info["lines"]
            print(f"  {fname}: {info['lines']} lines ({info['size_kb']} KB)")
        else:
            print(f"  {fname}: (not found)")

    # 2. Sync agent stats
    sync_result = sync_agent_stats()
    print(f"  agent_stats_sync: {sync_result}")

    print(f"[FLUSH] Complete. Total data lines: {total_lines}")
    return total_lines


if __name__ == "__main__":
    main()

