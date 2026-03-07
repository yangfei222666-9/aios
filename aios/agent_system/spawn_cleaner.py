"""
Spawn Cleaner + Executor
1. 去重：同一个 task_id 只保留最新的
2. 输出待执行列表
"""
import json
from pathlib import Path

from paths import SPAWN_REQUESTS

SPAWN_FILE = SPAWN_REQUESTS

def clean_and_dedupe():
    if not SPAWN_FILE.exists():
        print("No spawn_requests.jsonl")
        return []

    with open(SPAWN_FILE, encoding="utf-8") as f:
        all_reqs = [json.loads(l) for l in f if l.strip()]

    print(f"Total requests: {len(all_reqs)}")

    # 按 label 去重，保留最新的
    latest = {}
    for req in all_reqs:
        label = req.get("label", req.get("task_id", "unknown"))
        existing = latest.get(label)
        if existing is None or req.get("timestamp", "") > existing.get("timestamp", ""):
            latest[label] = req

    deduped = list(latest.values())
    removed = len(all_reqs) - len(deduped)
    print(f"After dedup: {len(deduped)} (removed {removed} duplicates)")

    # 写回去重后的文件
    with open(SPAWN_FILE, "w", encoding="utf-8") as f:
        for req in deduped:
            f.write(json.dumps(req, ensure_ascii=False) + "\n")

    # 输出待执行列表
    for i, req in enumerate(deduped, 1):
        label = req.get("label", "?")
        agent = req.get("agent_id", "?")
        task_id = req.get("task_id", "?")
        task_preview = req.get("task", "")[:60].replace("\n", " ")
        print(f"  [{i}] {label} | {agent} | {task_preview}...")

    return deduped

if __name__ == "__main__":
    clean_and_dedupe()
