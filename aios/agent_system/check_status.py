import json
from pathlib import Path
from paths import TASK_QUEUE, SPAWN_REQUESTS, AGENTS_STATE, AIOS_ROOT
base = AIOS_ROOT

# Task stats
completed = failed = pending = 0
tq = TASK_QUEUE
if tq.exists():
    for line in open(tq, encoding='utf-8'):
        line = line.strip()
        if not line: continue
        t = json.loads(line)
        s = t.get('status','')
        if s == 'completed': completed += 1
        elif s == 'failed': failed += 1
        elif s == 'pending': pending += 1
print(f'Tasks: completed={completed} failed={failed} pending={pending}')

# Spawn requests pending
sp = SPAWN_REQUESTS
pending_spawns = 0
if sp.exists():
    for line in open(sp, encoding='utf-8'):
        line = line.strip()
        if not line: continue
        r = json.loads(line)
        if r.get('status') != 'done':
            pending_spawns += 1
print(f'Pending spawns: {pending_spawns}')

# Low success agents
ag = AGENTS_STATE
if ag.exists():
    agents = json.load(open(ag, encoding='utf-8'))
    low = []
    for a in agents.get('agents', []):
        stats = a.get('stats', {})
        total = stats.get('tasks_completed', 0) + stats.get('tasks_failed', 0)
        if total > 0:
            rate = stats.get('tasks_completed', 0) / total
            if rate < 0.8:
                low.append(f"{a['id']}({rate:.0%})")
    print(f'Low success agents: {low if low else "none"}')

# LanceDB trajectories
try:
    import lancedb
    db = lancedb.connect(str(base / 'experience_db.lance'))
    tbl = db.open_table('success_patterns')
    print(f'LanceDB trajectories: {tbl.count_rows()}')
except:
    print('LanceDB: N/A')
