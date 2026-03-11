import json, os

# 1. Check agents.json
with open('data/agents.json', 'r', encoding='utf-8') as f:
    raw = json.load(f)
    agents = raw.get('agents', []) if isinstance(raw, dict) else raw

total = len(agents)
active = sum(1 for a in agents if a.get('status') == 'active')
shadow = sum(1 for a in agents if a.get('shadow', False))
disabled = sum(1 for a in agents if a.get('disabled', False))

print('=== Agent Summary ===')
print(f'Total: {total}')
print(f'Active: {active}')
print(f'Shadow: {shadow}')
print(f'Disabled: {disabled}')
print()

# 2. Check selflearn-state
sl_path = os.path.join('data', 'selflearn-state.json')
if os.path.exists(sl_path):
    with open(sl_path, 'r', encoding='utf-8') as f:
        sl = json.load(f)
    print('=== Self-Learn State ===')
    lr = sl.get('last_run', 'N/A')
    rd = sl.get('rules_derived_count', 0)
    aa = len(sl.get('activated_agents', []))
    print(f'Last run: {lr}')
    print(f'Rules derived: {rd}')
    print(f'Activated agents: {aa}')
else:
    print('=== Self-Learn State ===')
    print('NOT FOUND')
print()

# 3. Check lessons
lessons_path = os.path.join('data', 'lessons.json')
if os.path.exists(lessons_path):
    with open(lessons_path, 'r', encoding='utf-8') as f:
        lessons = json.load(f)
    items = lessons if isinstance(lessons, list) else lessons.get('lessons', [])
    total_l = len(items)
    pending = sum(1 for l in items if l.get('status') == 'pending')
    derived = sum(1 for l in items if l.get('status') == 'derived')
    print('=== Lessons ===')
    print(f'Total: {total_l} | Pending: {pending} | Derived: {derived}')
    for l in items:
        s = l.get('status', '?')
        t = l.get('title', l.get('description', '?'))[:60]
        print(f'  - [{s}] {t}')
else:
    print('=== Lessons ===')
    print('NOT FOUND')
print()

# 4. Check task queue
tq_path = os.path.join('data', 'task_queue.jsonl')
if os.path.exists(tq_path):
    with open(tq_path, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f if l.strip()]
    pending_tasks = 0
    for line in lines:
        try:
            t = json.loads(line)
            if t.get('status') == 'pending':
                pending_tasks += 1
        except:
            pass
    print('=== Task Queue ===')
    print(f'Total entries: {len(lines)} | Pending: {pending_tasks}')
else:
    print('=== Task Queue ===')
    print('Empty or not found')
print()

# 5. Check evolution score
es_path = os.path.join('data', 'evolution_score.json')
if os.path.exists(es_path):
    with open(es_path, 'r', encoding='utf-8') as f:
        es = json.load(f)
    score = es.get('score', 'N/A')
    updated = es.get('updated_at', es.get('timestamp', 'N/A'))
    print('=== Evolution Score ===')
    print(f'Score: {score}')
    print(f'Updated: {updated}')
else:
    print('=== Evolution Score ===')
    print('NOT FOUND')
print()

# 6. Check recent execution records
rec_path = os.path.join('data', 'agent_execution_record.jsonl')
if os.path.exists(rec_path):
    with open(rec_path, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f if l.strip()]
    recent = lines[-10:] if len(lines) > 10 else lines
    print('=== Recent Executions (last 10) ===')
    for line in recent:
        try:
            r = json.loads(line)
            aid = r.get('agent_id', '?')
            outcome = r.get('outcome', '?')
            ts = r.get('timestamp', '?')[:19]
            print(f'  [{ts}] {aid}: {outcome}')
        except:
            pass
else:
    print('=== Recent Executions ===')
    print('No records')
