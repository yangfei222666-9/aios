"""Quick AIOS status check"""
import json
from pathlib import Path

BASE = Path(__file__).parent

# 1. Agents status
data = json.load(open(BASE / 'agents.json', 'r', encoding='utf-8'))
agents = data.get('agents', data) if isinstance(data, dict) else data
active = [a for a in agents if a.get('mode') == 'active']
shadow = [a for a in agents if a.get('mode') == 'shadow']
disabled = [a for a in agents if a.get('mode') == 'disabled']

print(f"=== AGENTS ===")
print(f"Total: {len(agents)} | Active: {len(active)} | Shadow: {len(shadow)} | Disabled: {len(disabled)}")
print()
print("Active agents:")
for a in active:
    s = a.get('stats', {})
    c = s.get('tasks_completed', 0)
    f = s.get('tasks_failed', 0)
    print(f"  {a['name']}: completed={c}, failed={f}")

# 2. Task executions
print(f"\n=== TASK EXECUTIONS ===")
f = BASE / 'task_executions_v2.jsonl'
if f.exists():
    lines = [l for l in f.read_text(encoding='utf-8').strip().split('\n') if l.strip()]
    total = len(lines)
    success = sum(1 for l in lines if json.loads(l).get('status') == 'completed')
    failed = sum(1 for l in lines if json.loads(l).get('status') == 'failed')
    print(f"Total: {total} | Success: {success} | Failed: {failed} | Rate: {success/total*100:.1f}%")
    print("\nRecent 5:")
    for l in lines[-5:]:
        r = json.loads(l)
        ts = str(r.get('timestamp', '?'))[:16]
        ag = r.get('agent', '?')
        st = r.get('status', '?')
        desc = r.get('description', '?')[:60]
        print(f"  [{ts}] {ag} | {st} | {desc}")
else:
    print("No task_executions_v2.jsonl")

# 3. Lessons
print(f"\n=== LESSONS ===")
lf = BASE / 'lessons.json'
if lf.exists():
    lessons = json.load(open(lf, 'r', encoding='utf-8'))
    if isinstance(lessons, dict):
        items = lessons.get('lessons', [])
    else:
        items = lessons
    real = [l for l in items if l.get('source') == 'real']
    print(f"Total: {len(items)} | Real: {len(real)}")
else:
    print("No lessons.json")

# 4. Task queue
print(f"\n=== TASK QUEUE ===")
qf = BASE / 'task_queue.jsonl'
if qf.exists() and qf.stat().st_size > 0:
    qlines = [l for l in qf.read_text(encoding='utf-8').strip().split('\n') if l.strip()]
    pending = [l for l in qlines if '"pending"' in l]
    print(f"Total: {len(qlines)} | Pending: {len(pending)}")
else:
    print("Empty / no pending tasks")

# 5. Key files last modified
print(f"\n=== RECENT FILES ===")
for name in ['heartbeat_v5.py', 'agent_lifecycle_engine.py', 'heartbeat_v6.py']:
    p = BASE / name
    if p.exists():
        from datetime import datetime
        mt = datetime.fromtimestamp(p.stat().st_mtime)
        print(f"  {name}: {mt.strftime('%Y-%m-%d %H:%M')}")

# 6. Spawn lock status
print(f"\n=== SPAWN LOCK ===")
sl = BASE / 'spawn_lock_metrics.json'
if sl.exists():
    sm = json.load(open(sl, 'r', encoding='utf-8'))
    print(f"  Idempotent hits: {sm.get('idempotent_hits', '?')}")
    print(f"  Stale recoveries: {sm.get('stale_lock_recoveries', '?')}")
else:
    print("  No spawn_lock_metrics.json")

