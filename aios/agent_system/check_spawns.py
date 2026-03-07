import json
from paths import SPAWN_REQUESTS

with open(SPAWN_REQUESTS, encoding='utf-8') as f:
    lines = [json.loads(l) for l in f if l.strip()]

pending = [r for r in lines if r.get('status') != 'done']
print(f"Total: {len(lines)}, Pending: {len(pending)}")
print()

for i, r in enumerate(pending):
    ts = r.get("timestamp", "?")
    agent = r.get("agent_id", "?")
    tid = r.get("task_id", "?")
    label = r.get("label", "?")
    task = r.get("task", "")[:100]
    regen = r.get("regeneration", False)
    print(f"[{i+1}] {ts} | {agent} | task_id={tid}")
    print(f"    label: {label}")
    print(f"    regen: {regen}")
    print(f"    task: {task}...")
    print()
