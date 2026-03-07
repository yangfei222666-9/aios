import json, os, sys
from datetime import datetime
from paths import AGENTS_STATE, TASK_EXECUTIONS, TASK_QUEUE, EVOLUTION_SCORE

# Agent stats
agents_path = AGENTS_STATE
with open(agents_path, encoding='utf-8') as f:
    data = json.load(f)
agents = data['agents']
print(f"Total agents: {len(agents)}")
for a in agents[:8]:
    s = a.get('state', {})
    print(f"  {a['name']}: completed={s.get('tasks_completed',0)}, failed={s.get('tasks_failed',0)}")

# Executions
exec_path = TASK_EXECUTIONS
if os.path.exists(exec_path):
    lines = open(exec_path, encoding='utf-8').readlines()
    print(f"\nTotal executions: {len(lines)}")
    recent = [json.loads(l) for l in lines[-5:]]
    for r in recent:
        tid = r.get('task_id','?')
        st = r.get('status','?')
        ag = r.get('agent_id','?')
        ts = str(r.get('timestamp',''))[:19]
        print(f"  {tid} | {st} | {ag} | {ts}")

# Queue
queue_path = TASK_QUEUE
if os.path.exists(queue_path):
    lines = open(queue_path, encoding='utf-8').readlines()
    queued = [json.loads(l) for l in lines if '"status": "queued"' in l]
    print(f"\nQueued tasks: {len(queued)}")

# Evolution score
evo_path = EVOLUTION_SCORE
if os.path.exists(evo_path):
    evo = json.load(open(evo_path, encoding='utf-8'))
    print(f"\nEvolution Score: {evo.get('score', evo.get('evolution_score', 'N/A'))}")
