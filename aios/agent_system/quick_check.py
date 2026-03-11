#!/usr/bin/env python3
"""Quick maintenance check for AIOS"""
import json
from pathlib import Path
from datetime import datetime

def check_heartbeat():
    print("=== Heartbeat Status ===")
    hb_log = Path("heartbeat.log")
    if hb_log.exists():
        mtime = datetime.fromtimestamp(hb_log.stat().st_mtime)
        print(f"Last heartbeat: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("Last heartbeat: N/A")

def check_queue():
    print("\n=== Queue Status ===")
    queue = Path("data/task_queue.jsonl")
    if queue.exists() and queue.stat().st_size > 0:
        tasks = [json.loads(line) for line in queue.read_text(encoding='utf-8').strip().split('\n')]
        pending = len([t for t in tasks if t.get("status") == "pending"])
        failed = len([t for t in tasks if t.get("status") == "failed"])
        print(f"Pending tasks: {pending}")
        print(f"Failed tasks: {failed}")
    else:
        print("Queue: empty")

def check_evolution_score():
    print("\n=== Evolution Score ===")
    evo = Path("data/evolution_score.json")
    if evo.exists():
        score_data = json.loads(evo.read_text(encoding='utf-8'))
        print(f"Current score: {score_data.get('current_score', 'N/A')}")
        print(f"Last updated: {score_data.get('last_updated', 'N/A')}")
    else:
        print("Evolution score: not initialized")

def check_deduper_shadow():
    print("\n=== Deduper Shadow ===")
    shadow = Path("data/deduper_shadow.jsonl")
    if shadow.exists():
        lines = shadow.read_text(encoding='utf-8').strip().split('\n')
        print(f"Total records: {len(lines)}")
        if lines:
            recent = json.loads(lines[-1])
            print(f"Last record: {recent.get('timestamp', 'N/A')}")
    else:
        print("Deduper shadow: not found")

if __name__ == "__main__":
    check_heartbeat()
    check_queue()
    check_evolution_score()
    check_deduper_shadow()
    print("\n✅ Quick check completed")
